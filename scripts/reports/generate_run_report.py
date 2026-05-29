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
    nums = [int(m) for m in re.findall(r"^## Run (\d+)", text, re.MULTILINE)]
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
    title = data.get("title", "表单收集批次")
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
    optimizations = data.get("optimizations", [])

    ai_turns = data.get("ai_turns")
    ai_tool_calls = data.get("ai_tool_calls")

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

    lines.append("| 指标 | 跑前 | 跑后 | 变化 |")
    lines.append("|------|------|------|------|")
    lines.append(f"| 公司数 | — | {total} | — |")
    lines.append(f"| 联系人数 | — | {total_contacts} | — |")
    lines.append(f"| 覆盖率 | {pct(cov_before, total)} | {pct(cov_after, total)} | {cov_diff} |")
    lines.append(f"| AU 无联系 | {au_before} | {au_after} | {diff_str(au_before, au_after)} |")
    lines.append(f"| 有邮箱 | {leads_before.get('has_email', '?')} | {leads_after.get('has_email', '?')} | {diff_str(leads_before.get('has_email', '?'), leads_after.get('has_email', '?'))} |")
    lines.append(f"| 有电话 | {leads_before.get('has_phone', '?')} | {leads_after.get('has_phone', '?')} | {diff_str(leads_before.get('has_phone', '?'), leads_after.get('has_phone', '?'))} |")
    lines.append(f"| 有表单 | {leads_before.get('has_form', '?')} | {leads_after.get('has_form', '?')} | {diff_str(leads_before.get('has_form', '?'), leads_after.get('has_form', '?'))} |")
    lines.append(f"| 直联率 | — | {direct_rate} | — |")
    lines.append(f"| 批次数 | — | {batches} | — |")
    lines.append(f"| 候选数 | — | {candidates} | — |")
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

    # 系统优化
    if optimizations:
        lines.append("**系统优化：**")
        for item in optimizations:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)


def append_to_log(section: str, run_num):
    """追加 section 到合并文件。"""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if REPORT_FILE.exists():
        existing = REPORT_FILE.read_text(encoding="utf-8")
        # 检查是否已有该 run
        if f"## Run {run_num} —" in existing:
            print(f"Run {run_num} already exists in {REPORT_FILE}, skipping")
            return
        # 追加
        content = existing.rstrip() + "\n\n---\n\n" + section + "\n"
    else:
        content = HEADER + section + "\n"

    REPORT_FILE.write_text(content, encoding="utf-8")
    print(f"Run {run_num} appended to {REPORT_FILE}")


def main():
    parser = argparse.ArgumentParser(description="生成表单收集 Run 报告")
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
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
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
            data["end_time"] = timing["end"]
            seconds = timing["duration_seconds"]
            if seconds < 60:
                data["duration"] = f"{seconds:.0f}s"
            else:
                m, s = divmod(int(seconds), 60)
                data["duration"] = f"{m}m{s:02d}s" if m < 60 else f"{m // 60}h{m % 60:02d}m{s:02d}s"
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
