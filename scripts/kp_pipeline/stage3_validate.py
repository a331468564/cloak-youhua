# scripts/kp_pipeline/stage3_validate.py
"""
Stage 3: 验证与人工审核门控

对 KP 候选人进行验证，自动批准/拒绝/排队人工审核。
"""
from datetime import datetime
from .metrics import log_run_metrics


FALSE_POSITIVE_NAMES = {
    "contact", "dining", "menu", "home", "about", "team", "leadership",
    "management", "staff", "people", "careers", "our team", "the team",
    "our people", "meet the", "read more", "learn more", "find out",
    "get in", "click here", "sign up", "subscribe", "privacy", "terms",
}


def validate_candidate(candidate, rules):
    """根据规则验证单个 KP 候选人。"""
    issues = []
    name = (candidate.get("name") or "").strip()
    source_url = (candidate.get("source_url") or "").strip()

    # 检查误报
    reject_list = rules.get("reject_common_false_positives", [])
    reject_set = {fp.lower() for fp in reject_list} | FALSE_POSITIVE_NAMES
    if name.lower() in reject_set:
        issues.append(f"误报: '{name}'")

    # 检查名字长度
    min_len = rules.get("min_name_length", 4)
    max_len = rules.get("max_name_length", 50)
    if len(name) < min_len:
        issues.append(f"名字太短: '{name}'")
    if len(name) > max_len:
        issues.append(f"名字太长: '{name}'")

    # 检查来源
    if rules.get("require_source_link", True) and not source_url:
        issues.append("缺少来源链接")

    return {"valid": len(issues) == 0, "issues": issues}


def classify_auto_decision(score, config, is_valid):
    """将候选人分类为 auto_approve / auto_reject / human_review。"""
    if not is_valid:
        return "auto_reject"
    if score >= config.get("auto_approve_threshold", 85):
        return "auto_approve"
    if score < config.get("auto_reject_threshold", 30):
        return "auto_reject"
    return "human_review"


def compute_score(candidate):
    """为候选人计算综合分数。"""
    score = 50  # 基础分

    email = (candidate.get("best_email") or "").strip()
    phone = (candidate.get("best_phone") or "").strip()
    linkedin = (candidate.get("linkedin_url") or candidate.get("best_linkedin") or "").strip()
    directness = candidate.get("directness", "")
    confidence = candidate.get("confidence", "")

    # 无任何联系方式 → 大幅扣分（仅名字无价值）
    has_any_contact = bool(email or phone or linkedin)
    if not has_any_contact:
        return 20  # 低于 30 自动拒绝

    # 公司通用邮箱扣分
    if email:
        local = email.split("@")[0].lower()
        company_locals = {"info", "admin", "contact", "hello", "enquiries", "enquiry", "sales", "accounts", "hr", "marketing", "media"}
        if local in company_locals:
            score -= 10  # 公司邮箱降低价值

    # 直联程度加分
    if directness == "direct" and confidence == "High":
        score += 35
    elif directness == "direct" and confidence == "Medium":
        score += 25
    elif directness == "linkedin_only":
        score += 15  # LinkedIn 有价值但不如直联
    elif directness == "company_route":
        score += 5  # 公司路径降低加分

    # 个人邮箱加分
    if candidate.get("person_email_found"):
        score += 15

    # LinkedIn 加分
    if linkedin:
        score += 10

    # 角色上下文加分
    role = (candidate.get("role_context") or candidate.get("candidate_title") or "").lower()
    if any(r in role for r in ["managing director", "ceo", "founder", "owner", "director"]):
        score += 15
    elif any(r in role for r in ["operations", "procurement", "general manager"]):
        score += 10

    return max(min(score, 100), 0)


def run_stage3(candidates, config):
    """对候选人列表运行 Stage 3 验证。"""
    stage_config = config.get("stages", {}).get("stage3_validate", {})
    if not stage_config.get("enabled", True):
        return {"skipped": True}

    run_id = f"S3-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    rules = stage_config.get("validation_rules", {})

    auto_approved = []
    auto_rejected = []
    human_review = []

    for candidate in candidates:
        score = compute_score(candidate)
        candidate["score"] = score

        validation = validate_candidate(candidate, rules)
        decision = classify_auto_decision(score, stage_config, validation["valid"])
        candidate["decision"] = decision
        candidate["validation_issues"] = validation["issues"]

        if decision == "auto_approve":
            auto_approved.append(candidate)
        elif decision == "auto_reject":
            auto_rejected.append(candidate)
        else:
            human_review.append(candidate)

    metrics = {
        "total_candidates": len(candidates),
        "auto_approved": len(auto_approved),
        "auto_rejected": len(auto_rejected),
        "human_review": len(human_review),
        "auto_approve_rate": round(len(auto_approved) / max(len(candidates), 1), 3),
    }
    log_run_metrics(run_id, "stage3_validate", metrics)

    return {
        "auto_approved": auto_approved,
        "auto_rejected": auto_rejected,
        "human_review": human_review,
        "metrics": metrics,
    }
