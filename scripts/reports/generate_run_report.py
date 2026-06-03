"""
表单收集 Run 报告生成器（合并版）
==================================
每轮跑完后由 agent 调用，追加到单一报告文件。
输出：E:\自动跑表单的成果和情况\run-log.md

用法：
  python scripts/reports/generate_run_report.py --input run_data.json --auto-stats
  python scripts/reports/generate_run_report.py --run 15 --title "表单收集" --task "提取联系路由" ...
"""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

try:
    from scripts.reports.timer import RunTimer
except ImportError:
    from timer import RunTimer

REPORT_DIR = Path(r"E:\自动跑表单的成果和情况")
REPORT_FILE = REPORT_DIR / "run-log.md"
DATA_DIR = Path("data")

HEADER = """# 运行记录

> 表单收集、KP 富化、关键词发现等任务的每轮运行汇总。
> 详细数据见 `docs/current-progress.md`。

"""


def load_lead_stats():
    leads_path = DATA_DIR / "leads.csv"
    if not leads_path.exists():
        return {}
    with open(leads_path, "r", encoding="utf-8-sig") as f:
        leads = list(csv.DictReader(f))
    contact_fields = [
        "email_address", "company_email", "phone_number", "company_phone",
        "company_contact_form_url", "contact_form_url",
        "contact_page_url", "official_contact_page", "company_contact_page",
    ]
    has_any = sum(1 for l in leads if any(l.get(f, "").strip() for f in contact_fields))
    au_leads = [l for l in leads if l.get("country", "").strip() == "Australia"]
    au_no = sum(1 for l in au_leads if not any(l.get(f, "").strip() for f in contact_fields))
    return {
        "total_leads": len(leads),
        "has_any_contact": has_any,
        "au_no_contact": au_no,
        "has_email": sum(1 for l in leads if l.get("email_address", "").strip() or l.get("company_email", "").strip()),
        "has_phone": sum(1 for l in leads if l.get("phone_number", "").strip() or l.get("company_phone", "").strip()),
        "has_kc_email": sum(1 for l in leads if l.get("key_contact_email", "").strip()),
        "has_kc_phone": sum(1 for l in leads if l.get("key_contact_phone", "").strip()),
        "has_form": sum(1 for l in leads if l.get("company_contact_form_url", "").strip() or l.get("contact_form_url", "").strip()),
    }


def next_run_number():
    if not REPORT_FILE.exists():
        return 1
    text = REPORT_FILE.read_text(encoding="utf-8")
    import re
    nums = [int(m) for m in re.findall(r"^## (?:A-Run|Run) (\d+)", text, re.MULTILINE)]
    return max(nums) + 1 if nums else 1


# 跑后表格中"指标"列的关键词 → leads_before dict 的 key
_METRIC_MAP = {
    "公司数": "total_leads",
    "联系人数": "total_contacts",
    "有邮箱": "has_email",
    "有电话": "has_phone",
    "有表单": "has_form",
}


def load_previous_run_stats() -> dict:
    """从 run-log.md 最后一个 A-Run section 解析跑后数据，作为下一轮的跑前 fallback。

    解析 Markdown 表格中的"跑后"列：
    | 指标 | 跑前 | 跑后 | 变化 |
    """
    if not REPORT_FILE.exists():
        return {}
    import re
    text = REPORT_FILE.read_text(encoding="utf-8")

    # 找到最后一个 A-Run section 的表格
    # 匹配从 "## A-Run N" 到下一个 "---" 或文件末尾
    sections = re.split(r"\n---\n", text)
    last_section = sections[-1] if sections else ""

    # 找表格行：| 指标 | 跑前 | 跑后 | 变化 |
    result = {}
    for line in last_section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]  # 去掉首尾空
        if len(cells) < 3:
            continue
        metric_name = cells[0]
        after_val = cells[2]  # "跑后" 列

        if metric_name in _METRIC_MAP:
            parsed = _parse_int(after_val)
            if parsed is not None:
                result[_METRIC_MAP[metric_name]] = parsed

    # 特殊处理：覆盖率需要从百分比反推 has_any_contact 数
    if "total_leads" in result:
        for line in last_section.splitlines():
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 3 and cells[0] == "覆盖率":
                after_pct = cells[2].rstrip("%")
                try:
                    pct_val = float(after_pct)
                    result["has_any_contact"] = round(pct_val * result["total_leads"] / 100)
                except (ValueError, TypeError):
                    pass

    # AU 无联系
    for line in last_section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= 3 and cells[0] == "AU 无联系":
            parsed = _parse_int(cells[2])
            if parsed is not None:
                result["au_no_contact"] = parsed

    return result


def pct(val, tot):
    if isinstance(val, int) and isinstance(tot, int) and tot > 0:
        return f"{val * 100 / tot:.1f}%"
    return "?"


def _parse_int(val):
    """尝试从各种格式解析整数：'340', '21.6%', '?', '—' 等。"""
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        val = val.strip().rstrip("%")
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None
    return None


def diff_str(before, after):
    if before == "?" or after == "?":
        return "—"
    if not isinstance(before, (int, float)) or not isinstance(after, (int, float)):
        return "—"
    d = after - before
    if d == 0:
        return "→"
    return f"+{d}" if d > 0 else str(d)


def _diff_int(before, after):
    """返回 int 差值，任一无效则返回 None。"""
    if isinstance(before, int) and isinstance(after, int):
        return after - before
    return None


def auto_detect(data: dict) -> tuple[list[str], list[str]]:
    """根据 before/after 数据自动检测亮点和问题。

    Returns:
        (highlights, issues)
    """
    highlights = []
    issues = []

    before = data.get("leads_before", {})
    after = data.get("leads_after", {})
    if not before or not after:
        return highlights, issues

    # === 亮点检测 ===

    # 新增公司
    d = _diff_int(before.get("total_leads"), after.get("total_leads"))
    if d and d > 0:
        highlights.append(f"新增 {d} 家公司")

    # 新增联系人
    d = _diff_int(before.get("total_contacts"), after.get("total_contacts"))
    if d and d > 0:
        highlights.append(f"新增 {d} 个联系人")

    # 新增邮箱
    d = _diff_int(before.get("has_email"), after.get("has_email"))
    if d and d > 0:
        highlights.append(f"新增 {d} 个邮箱")

    # 新增电话
    d = _diff_int(before.get("has_phone"), after.get("has_phone"))
    if d and d > 0:
        highlights.append(f"新增 {d} 个电话")

    # 新增表单
    d = _diff_int(before.get("has_form"), after.get("has_form"))
    if d and d > 0:
        highlights.append(f"新增 {d} 个表单")

    # 新增直联（人名邮箱或手机）
    d_email = _diff_int(before.get("has_kc_email"), after.get("has_kc_email"))
    d_phone = _diff_int(before.get("has_kc_phone"), after.get("has_kc_phone"))
    d_direct = (d_email or 0) + (d_phone or 0)
    if d_direct > 0:
        highlights.append(f"新增 {d_direct} 个直联")

    # 覆盖率提升
    total = after.get("total_leads", 0)
    if isinstance(total, int) and total > 0:
        cov_before = before.get("has_any_contact")
        cov_after = after.get("has_any_contact")
        if isinstance(cov_before, int) and isinstance(cov_after, int):
            pct_before = cov_before * 100 / total
            pct_after = cov_after * 100 / total
            if pct_after - pct_before >= 1.0:
                highlights.append(f"覆盖率 +{pct_after - pct_before:.1f}%")

    # AU 无联系减少
    d = _diff_int(before.get("au_no_contact"), after.get("au_no_contact"))
    if d and d < 0:
        highlights.append(f"AU 无联系减少 {-d} 家")

    # === 问题检测 ===

    # 无任何变化
    if not highlights:
        issues.append("本轮无数据变化")

    # 直联率为 0 或下降
    kc_email = after.get("has_kc_email", 0)
    kc_phone = after.get("has_kc_phone", 0)
    total_contacts = after.get("total_contacts", 0)
    if isinstance(kc_email, int) and isinstance(kc_phone, int) and isinstance(total_contacts, int) and total_contacts > 0:
        direct_rate = (kc_email + kc_phone) / total_contacts
        if direct_rate == 0:
            issues.append("直联率为 0%")

    # AU 无联系未减少
    au_before = before.get("au_no_contact")
    au_after = after.get("au_no_contact")
    if isinstance(au_before, int) and isinstance(au_after, int) and au_after >= au_before and au_before > 0:
        issues.append(f"AU 无联系未改善（{au_after} 家）")

    return highlights, issues


def generate_section(data: dict) -> str:
    """生成单个 run 的 section（不含文件 header）。"""
    run = data.get("run", "?")
    ts = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M"))
    duration = data.get("duration", "未知")
    batches = data.get("batches", 0)
    candidates = data.get("candidates", 0)
    task = data.get("task", "")

    leads_before = data.get("leads_before", {})
    leads_after = data.get("leads_after", {})
    au_before = data.get("au_no_contact_before", "?")
    au_after = data.get("au_no_contact_after", "?")

    highlights = data.get("highlights", [])
    issues = data.get("issues", [])
    changes = data.get("changes", [])
    baseline = data.get("baseline", {})

    end_time = data.get("end_time", "")

    lines = []
    lines.append(f"## A-Run {run}")
    lines.append("")
    if end_time:
        meta = f"> {ts} → {end_time}（耗时 {duration}）"
    else:
        meta = f"> {ts}（耗时 {duration}）"
    lines.append(meta)
    if task:
        lines.append(f"> **任务：** {task}")
    lines.append("")

    # 本次变更
    if changes:
        lines.append("**本次变更：**")
        for item in changes:
            lines.append(f"- {item}")
        lines.append("")

    # 进度
    cov_before = leads_before.get("has_any_contact", "?")
    cov_after = leads_after.get("has_any_contact", "?")
    total = leads_after.get("total_leads", "?")
    total_contacts = leads_after.get("total_contacts", "?")

    if isinstance(cov_before, int) and isinstance(cov_after, int) and isinstance(total, int) and total > 0:
        p_diff = (cov_after - cov_before) * 100 / total
        cov_diff = f"+{p_diff:.1f}%" if p_diff > 0 else f"{p_diff:.1f}%"
    else:
        cov_diff = "—"

    # 直联率 = (人名邮箱 + 手机) / 联系人数
    kc_email = leads_after.get("has_kc_email", "?")
    kc_phone = leads_after.get("has_kc_phone", "?")
    if isinstance(kc_email, int) and isinstance(kc_phone, int) and isinstance(total_contacts, int) and total_contacts > 0:
        direct_rate = f"{(kc_email + kc_phone) * 100 / total_contacts:.1f}%"
    else:
        direct_rate = "—"

    # 表头：有 baseline 时加一列
    if baseline:
        lines.append("| 指标 | 跑前 | 跑后 | 变化 | vs 基线 |")
        lines.append("|------|------|------|------|---------|")
    else:
        lines.append("| 指标 | 跑前 | 跑后 | 变化 |")
        lines.append("|------|------|------|------|")

    def _row(metric, before, after, diff, baseline_key=None, after_raw=None, is_pct=False):
        base_str = ""
        if baseline and baseline_key:
            base_val = baseline.get(baseline_key)
            compare_val = after_raw if after_raw is not None else after
            if isinstance(base_val, int) and isinstance(compare_val, int):
                if is_pct and isinstance(total, int) and total > 0:
                    # 覆盖率：显示百分比对比
                    base_pct = f"{base_val * 100 / total:.1f}%"
                    after_pct = f"{compare_val * 100 / total:.1f}%"
                    base_str = f"{after_pct} vs {base_pct}"
                else:
                    d = compare_val - base_val
                    if d > 0:
                        base_str = f"+{d}"
                    elif d < 0:
                        base_str = str(d)
                    else:
                        base_str = "→"
        if baseline:
            return f"| {metric} | {before} | {after} | {diff} | {base_str} |"
        return f"| {metric} | {before} | {after} | {diff} |"

    lines.append(_row("公司数", "—", total, "—", "total_leads"))
    lines.append(_row("联系人数", "—", total_contacts, "—", "total_contacts"))
    lines.append(_row("覆盖率", pct(cov_before, total), pct(cov_after, total), cov_diff, "has_any_contact", after_raw=cov_after, is_pct=True))
    lines.append(_row("AU 无联系", au_before, au_after, diff_str(au_before, au_after), "au_no_contact"))
    lines.append(_row("有邮箱", leads_before.get('has_email', '?'), leads_after.get('has_email', '?'), diff_str(leads_before.get('has_email', '?'), leads_after.get('has_email', '?')), "has_email"))
    lines.append(_row("有电话", leads_before.get('has_phone', '?'), leads_after.get('has_phone', '?'), diff_str(leads_before.get('has_phone', '?'), leads_after.get('has_phone', '?')), "has_phone"))
    lines.append(_row("有表单", leads_before.get('has_form', '?'), leads_after.get('has_form', '?'), diff_str(leads_before.get('has_form', '?'), leads_after.get('has_form', '?')), "has_form"))
    lines.append(_row("直联率", "—", direct_rate, "—"))
    lines.append(_row("批次数", "—", batches, "—"))
    lines.append(_row("候选数", "—", candidates, "—"))
    lines.append("")

    # Baseline 摘要
    if baseline:
        base_run = data.get("baseline_run", "?")
        lines.append(f"> **基线对比：** A-Run {base_run}")
        lines.append("")

    # 亮点
    if highlights:
        for item in highlights:
            lines.append(f"- {item}")
        lines.append("")

    # 问题
    if issues:
        lines.append("**问题：**")
        for item in issues:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)


def append_to_log(section: str, run_num):
    """追加 section 到合并文件。"""
    import re
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if REPORT_FILE.exists():
        existing = REPORT_FILE.read_text(encoding="utf-8")
        # 同时匹配 "## Run N" 和 "## A-Run N" 两种格式
        if re.search(rf"^## (?:A-Run|Run) {run_num}\b", existing, re.MULTILINE):
            print(f"A-Run {run_num} already exists in {REPORT_FILE}, skipping")
            return
        # 追加
        content = existing.rstrip() + "\n\n---\n\n" + section + "\n"
    else:
        content = HEADER + section + "\n"

    REPORT_FILE.write_text(content, encoding="utf-8")
    print(f"A-Run {run_num} appended to {REPORT_FILE}")


def _parse_run_section(text: str, run_num: int) -> dict | None:
    """从 run-log.md 解析指定 run 的跑后数据。"""
    import re
    # 匹配 "## A-Run N" 或 "## Run N" 开头的 section
    pattern = rf"^## (?:A-Run|Run) {run_num}\b.*?(?=^## (?:A-Run|Run) \d+|\Z)"
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if not m:
        return None
    section_text = m.group(0)

    result = {}
    for line in section_text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 3:
            continue
        metric_name = cells[0]
        after_val = cells[2]

        if metric_name in _METRIC_MAP:
            parsed = _parse_int(after_val)
            if parsed is not None:
                result[_METRIC_MAP[metric_name]] = parsed

    # 覆盖率特殊处理
    if "total_leads" in result:
        for line in section_text.splitlines():
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 3 and cells[0] == "覆盖率":
                try:
                    result["has_any_contact"] = round(float(cells[2].rstrip("%")) * result["total_leads"] / 100)
                except (ValueError, TypeError):
                    pass

    # AU 无联系
    for line in section_text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= 3 and cells[0] == "AU 无联系":
            parsed = _parse_int(cells[2])
            if parsed is not None:
                result["au_no_contact"] = parsed

    return result


def main():
    parser = argparse.ArgumentParser(description="生成表单收集 Run 报告")
    parser.add_argument("--input", help="JSON 输入文件路径")
    parser.add_argument("--run", type=int, help="Run 编号（不指定则自动递增）")
    parser.add_argument("--title", default="表单收集批次")
    parser.add_argument("--task", default="", help="本次任务简述")
    parser.add_argument("--highlights", nargs="*", default=[], help="亮点")
    parser.add_argument("--issues", nargs="*", default=[], help="问题")
    parser.add_argument("--changes", nargs="*", default=[], help="本次变更/优化点（如 --changes '优化搜索查询' '缩短冷却时间'）")
    parser.add_argument("--baseline-run", type=int, help="基线 Run 编号，自动对比指标变化")
    parser.add_argument("--batches", type=int, default=0)
    parser.add_argument("--candidates", type=int, default=0)
    parser.add_argument("--duration", default="未知")
    parser.add_argument("--leads-before", type=int)
    parser.add_argument("--au-no-contact-before", type=int)
    parser.add_argument("--au-no-contact-after", type=int)
    parser.add_argument("--ai-turns", type=int)
    parser.add_argument("--ai-tool-calls", type=int)
    parser.add_argument("--auto-stats", action="store_true")
    parser.add_argument("--auto-timing", action="store_true", help="从 timing.json 自动读取时间")
    parser.add_argument("--auto-detect", action="store_true", help="自动检测亮点和问题（基于 before/after 数据差异）")
    parser.add_argument("--force", action="store_true", help="强制覆盖已有 run")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "run": args.run or next_run_number(),
            "title": args.title,
            "task": args.task,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration": args.duration,
            "batches": args.batches,
            "candidates": args.candidates,
            "highlights": args.highlights,
            "issues": args.issues,
            "changes": args.changes,
            "ai_turns": args.ai_turns,
            "ai_tool_calls": args.ai_tool_calls,
        }
        if args.leads_before is not None:
            data.setdefault("leads_before", {})["has_any_contact"] = args.leads_before
        if args.au_no_contact_before is not None:
            data["au_no_contact_before"] = args.au_no_contact_before
        if args.au_no_contact_after is not None:
            data["au_no_contact_after"] = args.au_no_contact_after

    # Auto-timing from timing.json
    if args.auto_timing:
        timing = RunTimer.load("a")
        if timing:
            data["timestamp"] = timing["start"]
            data["end_time"] = timing["end"]
            seconds = timing["duration_seconds"]
            if seconds < 60:
                data["duration"] = f"{seconds:.0f}s"
            else:
                m, s = divmod(int(seconds), 60)
                data["duration"] = f"{m}m{s:02d}s" if m < 60 else f"{m // 60}h{m % 60:02d}m{s:02d}s"
            # 跑前快照
            if "leads_before" in timing:
                data["leads_before"] = timing["leads_before"]
                data["au_no_contact_before"] = timing["leads_before"].get("au_no_contact", "?")
            # 跑后快照（仅当未指定 --auto-stats 时使用 timing.json 中的）
            if "leads_after" in timing and not args.auto_stats:
                data["leads_after"] = timing["leads_after"]
                data["au_no_contact_after"] = timing["leads_after"].get("au_no_contact", "?")
        else:
            print("Warning: timing.json not found, using current time")

    if args.auto_stats:
        stats = load_lead_stats()
        data["leads_after"] = stats
        # 也加载联系人统计
        contacts_path = DATA_DIR / "contacts.csv"
        if contacts_path.exists():
            with open(contacts_path, "r", encoding="utf-8-sig") as f:
                contacts = list(csv.DictReader(f))
            data["leads_after"]["total_contacts"] = len(contacts)
        if "au_no_contact_after" not in data or data["au_no_contact_after"] is None:
            data["au_no_contact_after"] = stats.get("au_no_contact", "?")

    # Fallback: 如果 leads_before 仍为空，从 run-log.md 上一轮跑后数据推断
    if not data.get("leads_before"):
        prev_stats = load_previous_run_stats()
        if prev_stats:
            data["leads_before"] = prev_stats
            if "au_no_contact" in prev_stats:
                data.setdefault("au_no_contact_before", prev_stats["au_no_contact"])

    # Auto-detect: 自动检测亮点和问题
    if args.auto_detect:
        detected_highlights, detected_issues = auto_detect(data)
        # 合并（手动传入的优先）
        data["highlights"] = data.get("highlights", []) + detected_highlights
        data["issues"] = data.get("issues", []) + detected_issues

    # Baseline 对比：从 run-log.md 解析指定 run 的跑后数据
    if args.baseline_run:
        if REPORT_FILE.exists():
            text = REPORT_FILE.read_text(encoding="utf-8")
            baseline_data = _parse_run_section(text, args.baseline_run)
            if baseline_data:
                data["baseline"] = baseline_data
                data["baseline_run"] = args.baseline_run
            else:
                print(f"Warning: A-Run {args.baseline_run} not found in {REPORT_FILE}")
        else:
            print(f"Warning: {REPORT_FILE} not found, skipping baseline comparison")

    run_num = data.get("run", next_run_number())
    section = generate_section(data)

    if args.force and REPORT_FILE.exists():
        # 删除已有该 run 的 section
        text = REPORT_FILE.read_text(encoding="utf-8")
        import re
        pattern = rf"\n---\n\n## A-Run {run_num}\n.*?(?=\n---\n\n## (?:A-Run|Run) \d+|$)"
        text = re.sub(pattern, "", text, flags=re.DOTALL)
        REPORT_FILE.write_text(text.rstrip() + "\n", encoding="utf-8")

    append_to_log(section, run_num)


if __name__ == "__main__":
    main()
