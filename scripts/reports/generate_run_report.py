"""
表单收集 Run 报告生成器（V2）
==============================
每轮跑完后由 agent 调用，追加到单一报告文件。
输出：E:\自动跑表单的成果和情况\run-log.md

用法：
  python scripts/reports/generate_run_report.py --input run_data.json --auto-stats
  python scripts/reports/generate_run_report.py --run 15 --title "表单收集" --task "提取联系路由" --auto-timing
"""

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path

try:
    from scripts.reports.timer import RunTimer
except ImportError:
    from timer import RunTimer

REPORT_DIR = Path(r"E:\自动跑表单的成果和情况")
REPORT_FILE = REPORT_DIR / "run-log.md"
DATA_DIR = Path("data")

FIELD_TABLE = """\
> **字段说明**

| 字段 | 含义 | 计算方式 |
|------|------|----------|
| 公司数 | leads.csv 总行数 | csv 行计数 |
| 联系人数 | contacts.csv 总行数 | csv 行计数 |
| 覆盖率 | 有至少一种联系信息的公司比例 | 有联系的公司数 / 总公司数 × 100% |
| AU 无联系 | 澳洲公司中无任何联系信息的数量 | country=Australia 且无邮箱/电话/表单 |
| 有邮箱 | 有公司邮箱或人名邮箱的公司数 | company_email 或 email_address 非空 |
| 有电话 | 有公司电话或手机的公司数 | company_phone 或 phone_number 非空 |
| 有表单 | 有联系表单 URL 的公司数 | company_contact_form_url 非空 |
| 直联率 | 有人名邮箱+手机的联系人比例 | (人名邮箱+手机) / 联系人数 × 100% |
| 批次数 | 本次 extraction 跑了几批 | --limit 参数值 |
| 候选数 | extraction 产出的原始候选总数 | 报告 CSV 行数 |
"""

HEADER = f"""# A-Run 运行记录

> A区（表单收集、KP 富化）每轮运行汇总。
> 详细数据见 `docs/current-progress.md`。

{FIELD_TABLE}
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
        "has_form": sum(1 for l in leads if l.get("company_contact_form_url", "").strip() or l.get("contact_form_url", "").strip()),
    }


def next_run_number():
    if not REPORT_FILE.exists():
        return 1
    text = REPORT_FILE.read_text(encoding="utf-8")
    nums = [int(m) for m in re.findall(r"^## A-Run (\d+)", text, re.MULTILINE)]
    return max(nums) + 1 if nums else 1


def pct(val, tot):
    if isinstance(val, int) and isinstance(tot, int) and tot > 0:
        return f"{val * 100 / tot:.1f}%"
    return "?"


def diff_str(before, after):
    if before == "?" or after == "?":
        return "—"
    if not isinstance(before, (int, float)) or not isinstance(after, (int, float)):
        return "—"
    d = after - before
    if d == 0:
        return "→"
    return f"+{d}" if d > 0 else str(d)


def generate_section(data: dict) -> str:
    """生成单个 run 的 section（不含文件 header）。"""
    run = data.get("run", "?")
    ts = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
    optimizations = data.get("optimizations", [])

    ai_turns = data.get("ai_turns")
    ai_tool_calls = data.get("ai_tool_calls")

    lines = []
    lines.append(f"## A-Run {run}")
    lines.append("")
    meta = f"> {ts}  |  耗时 {duration}  |  {batches} 批 / {candidates} 候选"
    if ai_turns is not None and ai_tool_calls is not None:
        meta += f"  |  AI {ai_turns} 轮 / {ai_tool_calls} 次调用"
    lines.append(meta)
    if task:
        lines.append(f"> **任务：** {task}")
    lines.append("")

    # 进度
    cov_before = leads_before.get("has_any_contact", "?")
    cov_after = leads_after.get("has_any_contact", "?")
    total = leads_after.get("total_leads", "?")

    if isinstance(cov_before, int) and isinstance(cov_after, int) and isinstance(total, int) and total > 0:
        p_diff = (cov_after - cov_before) * 100 / total
        cov_diff = f"+{p_diff:.1f}%" if p_diff > 0 else f"{p_diff:.1f}%"
    else:
        cov_diff = "—"

    lines.append("| 指标 | 跑前 | 跑后 | 变化 |")
    lines.append("|------|------|------|------|")
    lines.append(f"| 公司数 | — | {total} | — |")
    lines.append(f"| 联系人数 | — | {leads_after.get('total_contacts', '?')} | — |")
    lines.append(f"| 覆盖率 | {pct(cov_before, total)} | {pct(cov_after, total)} | {cov_diff} |")
    lines.append(f"| AU 无联系 | {au_before} | {au_after} | {diff_str(au_before, au_after)} |")
    lines.append(f"| 有邮箱 | {leads_before.get('has_email', '?')} | {leads_after.get('has_email', '?')} | {diff_str(leads_before.get('has_email', '?'), leads_after.get('has_email', '?'))} |")
    lines.append(f"| 有电话 | {leads_before.get('has_phone', '?')} | {leads_after.get('has_phone', '?')} | {diff_str(leads_before.get('has_phone', '?'), leads_after.get('has_phone', '?'))} |")
    lines.append(f"| 有表单 | {leads_before.get('has_form', '?')} | {leads_after.get('has_form', '?')} | {diff_str(leads_before.get('has_form', '?'), leads_after.get('has_form', '?'))} |")
    lines.append("")

    if highlights:
        for item in highlights:
            lines.append(f"- {item}")
        lines.append("")

    if issues:
        lines.append("**问题：**")
        for item in issues:
            lines.append(f"- {item}")
        lines.append("")

    if optimizations:
        lines.append("**系统优化：**")
        for item in optimizations:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)


def format_duration(seconds: float) -> str:
    """Format duration_seconds into human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m{s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m{s:02d}s"


def append_to_log(section: str, run_num):
    """追加 section 到合并文件。"""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if REPORT_FILE.exists():
        existing = REPORT_FILE.read_text(encoding="utf-8")
        if f"## A-Run {run_num}" in existing:
            print(f"A-Run {run_num} already exists in {REPORT_FILE}, skipping")
            return
        content = existing.rstrip() + "\n\n---\n\n" + section + "\n"
    else:
        content = HEADER + section + "\n"

    REPORT_FILE.write_text(content, encoding="utf-8")
    print(f"A-Run {run_num} appended to {REPORT_FILE}")


def main():
    parser = argparse.ArgumentParser(description="生成表单收集 A-Run 报告")
    parser.add_argument("--input", help="JSON 输入文件路径")
    parser.add_argument("--run", type=int, help="Run 编号（不指定则自动递增）")
    parser.add_argument("--title", default="表单收集批次")
    parser.add_argument("--task", default="", help="本次任务简述")
    parser.add_argument("--highlights", nargs="*", default=[], help="亮点")
    parser.add_argument("--issues", nargs="*", default=[], help="问题")
    parser.add_argument("--optimizations", nargs="*", default=[], help="系统优化")
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
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration": args.duration,
            "batches": args.batches,
            "candidates": args.candidates,
            "highlights": args.highlights,
            "issues": args.issues,
            "optimizations": args.optimizations,
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
        timing = RunTimer.load()
        if timing:
            data["timestamp"] = timing["start"]
            data["duration"] = format_duration(timing["duration_seconds"])
        else:
            print("Warning: timing.json not found, using current time")

    if args.auto_stats:
        stats = load_lead_stats()
        data["leads_after"] = stats
        contacts_path = DATA_DIR / "contacts.csv"
        if contacts_path.exists():
            with open(contacts_path, "r", encoding="utf-8-sig") as f:
                contacts = list(csv.DictReader(f))
            data["leads_after"]["total_contacts"] = len(contacts)
        if "au_no_contact_after" not in data or data["au_no_contact_after"] is None:
            data["au_no_contact_after"] = stats.get("au_no_contact", "?")

    run_num = data.get("run", next_run_number())
    section = generate_section(data)

    if args.force and REPORT_FILE.exists():
        text = REPORT_FILE.read_text(encoding="utf-8")
        pattern = rf"\n---\n\n## A-Run {run_num}.*?(?=\n---\n\n## A-Run \d+|$)"
        text = re.sub(pattern, "", text, flags=re.DOTALL)
        REPORT_FILE.write_text(text.rstrip() + "\n", encoding="utf-8")

    append_to_log(section, run_num)


if __name__ == "__main__":
    main()
