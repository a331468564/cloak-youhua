"""
B-Run 关键词发现报告生成器
==========================
读取 keyword_runs.csv，生成关键词级别的运行报告。
输出：E:\\自动跑表单的成果和情况\\keyword-log.md

用法：
  python scripts/reports/generate_keyword_report.py --auto-timing
  python scripts/reports/generate_keyword_report.py --run 1 --task "首次关键词发现"
"""

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path

try:
    from scripts.reports.timer import RunTimer
except ImportError:
    from timer import RunTimer

REPORT_DIR = Path(r"E:\自动跑表单的成果和情况")
REPORT_FILE = REPORT_DIR / "keyword-log.md"
DATA_DIR = Path("data")
KEYWORD_CSV = DATA_DIR / "keyword_runs.csv"

FIELD_TABLE = """\
> **字段说明**

| 字段 | 含义 | 计算方式 |
|------|------|----------|
| 产出数 | 该关键词搜到的新公司数 | 入库 leads.csv 的行数 |
| 有效率 | 搜到的公司中符合目标客户的比例 | ready_to_contact / actual_leads × 100% |
| 去重率 | 搜到但已存在的公司比例 | duplicate_count / actual_leads × 100% |
| 搜索耗时 | Google 搜索 + 页面抓取总时间 | 自动计时（RunTimer） |
| 429 次数 | Google 返回限流错误的次数 | CSV 记录（暂无则为 —） |
| 过滤命中 | 被过滤器拦截的非目标结果数 | CSV 记录（暂无则为 —） |
| 备注 | 阻塞事件、意外发现、优化建议 | notes 列 |
"""

HEADER = f"""# B-Run 运行记录

> B区（关键词发现）每轮运行汇总。
> 数据来源：`data/keyword_runs.csv`

{FIELD_TABLE}
"""


def load_keyword_runs() -> list[dict]:
    """Load keyword_runs.csv and return list of row dicts."""
    if not KEYWORD_CSV.exists():
        return []
    with open(KEYWORD_CSV, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def next_run_number():
    if not REPORT_FILE.exists():
        return 1
    text = REPORT_FILE.read_text(encoding="utf-8")
    nums = [int(m) for m in re.findall(r"^## B-Run (\d+)", text, re.MULTILINE)]
    return max(nums) + 1 if nums else 1


def safe_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def pct_str(num, den):
    if den > 0:
        return f"{num * 100 / den:.1f}%"
    return "—"


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m{s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m{s:02d}s"


def generate_section(data: dict, rows: list[dict]) -> str:
    """Generate a single B-Run section."""
    run = data.get("run", "?")
    ts = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    duration = data.get("duration", "未知")
    task = data.get("task", "")
    highlights = data.get("highlights", [])
    issues = data.get("issues", [])

    lines = []
    lines.append(f"## B-Run {run}")
    lines.append("")
    lines.append(f"> {ts}  |  耗时 {duration}  |  {len(rows)} 个关键词")
    if task:
        lines.append(f"> **任务：** {task}")
    lines.append("")

    # Table header
    lines.append("| 关键词 | 产出 | 有效率 | 去重率 | 搜索耗时 | 429 | 过滤命中 | 备注 |")
    lines.append("|--------|------|--------|--------|----------|-----|----------|------|")

    total产出 = 0
    total有效 = 0
    total去重 = 0
    total总数 = 0

    for row in rows:
        kw = row.get("keyword_source_query", "?")
        actual = safe_int(row.get("actual_leads_collected"))
        ready = safe_int(row.get("ready_to_contact_count"))
        dup = safe_int(row.get("duplicate_count"))
        notes = row.get("notes", "")

        有效率 = pct_str(ready, actual)
        去重率 = pct_str(dup, actual)

        total产出 += actual
        total有效 += ready
        total去重 += dup
        total总数 += actual

        # Truncate long keywords for table readability
        kw_display = kw if len(kw) <= 30 else kw[:27] + "..."
        notes_display = notes.replace("|", "\\|") if notes else ""

        lines.append(f"| {kw_display} | {actual} | {有效率} | {去重率} | — | — | — | {notes_display} |")

    # Totals row
    if rows:
        有效率合 = pct_str(total有效, total总数)
        去重率合 = pct_str(total去重, total总数)
        lines.append(f"| **合计** | **{total产出}** | **{有效率合}** | **{去重率合}** | — | — | — | |")

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

    return "\n".join(lines)


def append_to_log(section: str, run_num):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if REPORT_FILE.exists():
        existing = REPORT_FILE.read_text(encoding="utf-8")
        if f"## B-Run {run_num}" in existing:
            print(f"B-Run {run_num} already exists in {REPORT_FILE}, skipping")
            return
        content = existing.rstrip() + "\n\n---\n\n" + section + "\n"
    else:
        content = HEADER + section + "\n"

    REPORT_FILE.write_text(content, encoding="utf-8")
    print(f"B-Run {run_num} appended to {REPORT_FILE}")


def main():
    parser = argparse.ArgumentParser(description="生成关键词发现 B-Run 报告")
    parser.add_argument("--run", type=int, help="Run 编号（不指定则自动递增）")
    parser.add_argument("--task", default="", help="本次任务简述")
    parser.add_argument("--highlights", nargs="*", default=[])
    parser.add_argument("--issues", nargs="*", default=[])
    parser.add_argument("--auto-timing", action="store_true", help="从 timing.json 自动读取时间")
    parser.add_argument("--batch-id", help="只处理指定 batch_id 的行")
    args = parser.parse_args()

    rows = load_keyword_runs()
    if not rows:
        print("No keyword_runs.csv found or empty, nothing to report")
        return

    # Filter by batch_id if specified
    if args.batch_id:
        rows = [r for r in rows if r.get("batch_id") == args.batch_id]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    duration = "未知"

    if args.auto_timing:
        timing = RunTimer.load("b")
        if timing:
            timestamp = timing["start"]
            duration = format_duration(timing["duration_seconds"])

    data = {
        "run": args.run or next_run_number(),
        "task": args.task,
        "timestamp": timestamp,
        "duration": duration,
        "highlights": args.highlights,
        "issues": args.issues,
    }

    section = generate_section(data, rows)
    append_to_log(section, data["run"])


if __name__ == "__main__":
    main()
