# scripts/kp_pipeline/run_pipeline.py
"""
KP 半自动化管线编排器

复用已有脚本 + 补缺模块，串联三阶段：
- Stage 1: 复用 extract_public_contact_candidates.py + build_form_kp_candidate_queue.py
- Stage 2: 新模块 — 对已知 KP 搜索直联
- Stage 3: 新模块 — 验证门控分流

用法:
    python -m scripts.kp_pipeline.run_pipeline --limit 10
    python -m scripts.kp_pipeline.run_pipeline --country Australia --limit 20 --stage 2
    python -m scripts.kp_pipeline.run_pipeline --stage 3  # 仅运行验证门控
"""
import argparse
import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .config import load_config
from .metrics import log_run_metrics, compute_accuracy_metrics, init_metrics_log, init_validation_log
from .stage2_enrich import run_stage2
from .stage3_validate import run_stage3

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"
DATA = PROJECT_ROOT / "data"
REPORTS = PROJECT_ROOT / "reports" / "kp-pipeline"


def read_leads(path, country=None):
    """读取线索 CSV。"""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if country:
        rows = [r for r in rows if r.get("country") == country]
    return rows


def find_leads_needing_kp(leads):
    """找出已有 KP 名字但缺直联的线索。"""
    need_enrichment = []
    for lead in leads:
        kp_name = (lead.get("key_contact_name") or "").strip()
        kp_email = (lead.get("key_contact_email") or "").strip()
        kp_phone = (lead.get("key_contact_phone") or "").strip()
        website = (lead.get("website") or "").strip()

        # 有 KP 名字但没直联
        if kp_name and not kp_email and not kp_phone and website:
            need_enrichment.append(lead)
    return need_enrichment


def find_leads_needing_kp_discovery(leads):
    """找出没有 KP 且没有联系人的线索。"""
    needs_discovery = []
    for lead in leads:
        kp_name = (lead.get("key_contact_name") or "").strip()
        contact_level = (lead.get("contact_data_level") or "").strip()
        website = (lead.get("website") or "").strip()

        if not kp_name and contact_level in ("Company Contact Only", "") and website:
            needs_discovery.append(lead)
    return needs_discovery


def run_stage1_via_existing_scripts(leads, config, limit=10):
    """Stage 1: 调用已有的提取脚本。"""
    run_id = f"S1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # 先构建候选队列
    queue_cmd = [
        sys.executable,
        str(SCRIPTS / "extraction" / "build_form_kp_candidate_queue.py"),
    ]

    print(f"  [Stage 1] 构建候选队列...")
    try:
        result = subprocess.run(queue_cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            print(f"  [Stage 1] 队列构建失败: {result.stderr[:200]}")
            return [], {"error": result.stderr[:200]}
    except Exception as e:
        print(f"  [Stage 1] 队列构建异常: {e}")
        return [], {"error": str(e)}

    # 找到最新生成的队列文件（队列脚本输出到 reports/ 根目录）
    queue_files = sorted((PROJECT_ROOT / "reports").glob("au-form-kp-candidate-queue-*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not queue_files:
        print("  [Stage 1] 未找到候选队列文件")
        return [], {"error": "no_queue_file"}

    queue_file = queue_files[0]
    print(f"  [Stage 1] 使用队列: {queue_file.name}")

    # 运行提取
    output_prefix = REPORTS / f"kp-pipeline-s1-{run_id}"
    extract_cmd = [
        sys.executable,
        str(SCRIPTS / "extraction" / "extract_public_contact_candidates.py"),
        "--input", str(queue_file),
        "--skip", "0",
        "--limit", str(limit),
        "--follow-links", "2",
        "--fetcher", "static",
        "--skip-existing",
        "--output-prefix", str(output_prefix),
    ]

    print(f"  [Stage 1] 运行提取 ({limit} 条线索)...")
    try:
        result = subprocess.run(extract_cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=600)
        if result.returncode != 0:
            print(f"  [Stage 1] 提取失败: {result.stderr[:200]}")
            return [], {"error": result.stderr[:200]}
        print(f"  [Stage 1] {result.stdout.strip()}")
    except subprocess.TimeoutExpired:
        print("  [Stage 1] 提取超时 (600s)")
        return [], {"error": "timeout"}
    except Exception as e:
        print(f"  [Stage 1] 提取异常: {e}")
        return [], {"error": str(e)}

    # 读取提取结果
    result_csv = output_prefix.with_suffix(".csv")
    if not result_csv.exists():
        print(f"  [Stage 1] 结果文件不存在: {result_csv}")
        return [], {"error": "no_output"}

    with open(result_csv, newline="", encoding="utf-8-sig") as f:
        candidates = list(csv.DictReader(f))

    metrics = {
        "candidates_found": len(candidates),
        "leads_processed": limit,
    }
    log_run_metrics(run_id, "stage1_discover", metrics)
    return candidates, metrics


def write_report(output_path, results, metrics_all):
    """写入管线运行报告。"""
    lines = [
        "# KP 管线运行报告",
        "",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    # Stage 1
    s1 = metrics_all.get("stage1", {})
    lines.extend([
        "## Stage 1: KP 发现（复用已有脚本）",
        "",
        f"- 处理线索: {s1.get('leads_processed', 'N/A')}",
        f"- 发现候选人: {s1.get('candidates_found', 0)}",
        "",
    ])

    # Stage 2
    s2 = metrics_all.get("stage2", {})
    lines.extend([
        "## Stage 2: 直联富化（补缺模块）",
        "",
        f"- 处理候选人: {s2.get('candidates_processed', 0)}",
        f"- 富化成功: {s2.get('enriched', 0)}",
        f"- 发现直联: {s2.get('direct_contacts_found', 0)}",
        f"- 直联率: {s2.get('direct_contact_rate', 0):.1%}",
        "",
    ])

    # Stage 3
    s3 = results.get("stage3", {})
    s3m = s3.get("metrics", {})
    lines.extend([
        "## Stage 3: 验证门控（补缺模块）",
        "",
        f"- 候选人总数: {s3m.get('total_candidates', 0)}",
        f"- 自动批准: {s3m.get('auto_approved', 0)}",
        f"- 自动拒绝: {s3m.get('auto_rejected', 0)}",
        f"- 需人工审核: {s3m.get('human_review', 0)}",
        "",
    ])

    # 人工审核列表
    human_review = s3.get("human_review", [])
    if human_review:
        lines.extend([
            "## 需人工审核候选人",
            "",
            "| # | 姓名 | 公司 | 邮箱 | 电话 | 直联程度 | 分数 |",
            "|---|------|------|------|------|---------|------|",
        ])
        for i, c in enumerate(human_review, 1):
            lines.append(
                f"| {i} | {c.get('name', '')} | {c.get('company_name', '')} | "
                f"{c.get('best_email', '')} | {c.get('best_phone', '')} | "
                f"{c.get('directness', '')} | {c.get('score', '')} |"
            )
        lines.append("")

    # 自动化门槛
    accuracy = compute_accuracy_metrics()
    lines.extend([
        "## 自动化门槛状态",
        "",
    ])
    if accuracy and accuracy.get("total_decisions", 0) > 0:
        lines.extend([
            f"- 历史决策: {accuracy.get('total_decisions', 0)}",
            f"- 准确率: {accuracy.get('accuracy_rate', 0):.1%}",
            f"- 误报率: {accuracy.get('false_positive_rate', 0):.1%}",
        ])
    else:
        lines.append("- 尚无验证历史，运行人工审核以积累数据。")

    lines.append("")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="KP 半自动化管线编排器。")
    parser.add_argument("--leads", default=str(DATA / "leads.csv"))
    parser.add_argument("--country", default="Australia")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--stage", choices=["1", "2", "3", "all"], default="all")
    parser.add_argument("--output-prefix", default="")
    parser.add_argument("--keyword-driven", action="store_true", help="Run keyword scheduler before Stage 1 to discover new leads")
    args = parser.parse_args()

    init_metrics_log()
    init_validation_log()

    config = load_config()
    leads = read_leads(args.leads, args.country)
    if not leads:
        print("未找到符合条件的线索。")
        return

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    prefix = Path(args.output_prefix) if args.output_prefix else REPORTS / f"kp-pipeline-run-{ts}"

    print(f"=== KP 半自动化管线 ===")
    print(f"线索: {len(leads)} 条 ({args.country})")
    print(f"阶段: {args.stage}")
    print()

    # Keyword-driven discovery: run scheduler before Stage 1
    if args.keyword_driven:
        print("--- Keyword Scheduler (pre-stage) ---")
        from scripts.keyword_scheduler.scheduler import main as scheduler_main
        old_argv = sys.argv
        sys.argv = ["scheduler", "--limit", str(args.limit or 5)]
        try:
            scheduler_main()
        finally:
            sys.argv = old_argv
        print("--- Keyword Scheduler complete ---")
        print()

    results = {}
    metrics_all = {}

    # Stage 1
    if args.stage in ("1", "all"):
        print("--- Stage 1: KP 发现 ---")
        candidates_s1, metrics_s1 = run_stage1_via_existing_scripts(leads, config, limit=args.limit)
        results["stage1_candidates"] = candidates_s1
        metrics_all["stage1"] = metrics_s1
        print(f"  结果: {metrics_s1.get('candidates_found', 0)} 个候选人")
        print()

    # Stage 2
    if args.stage in ("2", "all"):
        print("--- Stage 2: 直联富化 ---")
        # 找出需要富化的线索
        need_enrichment = find_leads_needing_kp(leads)[:args.limit]
        if not need_enrichment:
            print("  没有需要富化的线索（已有 KP + 缺直联）。")
            metrics_all["stage2"] = {"skipped": True, "reason": "no_candidates"}
        else:
            print(f"  找到 {len(need_enrichment)} 条需富化线索")
            enriched, metrics_s2 = run_stage2(need_enrichment, config)
            results["stage2_enriched"] = enriched
            metrics_all["stage2"] = metrics_s2
            print(f"  富化: {metrics_s2.get('enriched', 0)} 条")
            print(f"  直联: {metrics_s2.get('direct_contacts_found', 0)} 条")
            print()

    # Stage 3
    if args.stage in ("3", "all"):
        print("--- Stage 3: 验证门控 ---")
        # 合并 Stage 1 和 Stage 2 的候选人
        s1_candidates = results.get("stage1_candidates", [])
        s2_candidates = results.get("stage2_enriched", [])
        all_candidates = s2_candidates + [
            c for c in s1_candidates
            if not any(c2.get("source_url") == c.get("source_url") for c2 in s2_candidates)
        ]

        if not all_candidates:
            print("  没有候选人需要验证。")
            results["stage3"] = {"metrics": {"total_candidates": 0}}
        else:
            stage3_results = run_stage3(all_candidates, config)
            results["stage3"] = stage3_results
            s3m = stage3_results.get("metrics", {})
            print(f"  自动批准: {s3m.get('auto_approved', 0)}")
            print(f"  自动拒绝: {s3m.get('auto_rejected', 0)}")
            print(f"  人工审核: {s3m.get('human_review', 0)}")
            print()

    # 写报告
    report_path = prefix.with_suffix(".md")
    write_report(report_path, results, metrics_all)
    print(f"报告: {report_path}")

    print("\n完成。")


if __name__ == "__main__":
    main()
