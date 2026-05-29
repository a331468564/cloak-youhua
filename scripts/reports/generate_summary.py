"""
汇总仪表盘生成器
=================
解析 run-log.md 和 keyword-log.md，生成 summary.md。
输出：E:\\自动跑表单的成果和情况\\summary.md

用法：
  python scripts/reports/generate_summary.py
"""

import re
from datetime import datetime
from pathlib import Path

REPORT_DIR = Path(r"E:\自动跑表单的成果和情况")
RUN_LOG = REPORT_DIR / "run-log.md"
KEYWORD_LOG = REPORT_DIR / "keyword-log.md"
SUMMARY_FILE = REPORT_DIR / "summary.md"


def parse_arun_sections(text: str) -> list[dict]:
    """Parse A-Run (or legacy Run) sections from run-log.md."""
    sections = []
    # Match both "## A-Run N" and "## Run N" (legacy)
    parts = re.split(r"(?=^## (?:A-Run|Run) \d+)", text, flags=re.MULTILINE)
    for part in parts:
        m = re.match(r"^## (?:A-Run|Run) (\d+)", part)
        if not m:
            continue
        run_num = int(m.group(1))

        # Extract timestamp line
        ts_match = re.search(r"^>\s*(.+?)(?:\s*\|\s*耗时\s*(.+?))?(?:\s*\|\s*\d+ 批.*)?$", part, re.MULTILINE)
        timestamp = ts_match.group(1).strip() if ts_match else "?"
        duration = ts_match.group(2).strip() if ts_match and ts_match.group(2) else "?"

        # Extract metrics table
        metrics = {}
        for row in re.finditer(r"\|\s*(公司数|联系人数|覆盖率|AU 无联系|有邮箱|有电话|有表单)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", part):
            key = row.group(1).strip()
            after = row.group(3).strip()
            metrics[key] = after

        sections.append({
            "run": run_num,
            "timestamp": timestamp,
            "duration": duration,
            "metrics": metrics,
        })
    return sections


def parse_brun_sections(text: str) -> list[dict]:
    """Parse B-Run sections from keyword-log.md."""
    sections = []
    parts = re.split(r"(?=^## B-Run \d+)", text, flags=re.MULTILINE)
    for part in parts:
        m = re.match(r"^## B-Run (\d+)", part)
        if not m:
            continue
        run_num = int(m.group(1))

        ts_match = re.search(r"^>\s*(.+?)(?:\s*\|\s*耗时\s*(.+?))?(?:\s*\|\s*\d+ 个关键词.*)?$", part, re.MULTILINE)
        timestamp = ts_match.group(1).strip() if ts_match else "?"
        duration = ts_match.group(2).strip() if ts_match and ts_match.group(2) else "?"

        # Extract totals row
        totals_match = re.search(r"\|\s*\*\*合计\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|\s*\*\*(.+?)\*\*\s*\|\s*\*\*(.+?)\*\*", part)
        total产出 = int(totals_match.group(1)) if totals_match else 0
        有效率 = totals_match.group(2) if totals_match else "?"
        去重率 = totals_match.group(3) if totals_match else "?"

        sections.append({
            "run": run_num,
            "timestamp": timestamp,
            "duration": duration,
            "total产出": total产出,
            "有效率": 有效率,
            "去重率": 去重率,
        })
    return sections


def generate_summary(aruns: list[dict], bruns: list[dict]) -> str:
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"# 汇总仪表盘")
    lines.append("")
    lines.append(f"> 自动生成于 {now}")
    lines.append("")

    # Latest status from last A-Run
    if aruns:
        last = aruns[-1]
        m = last["metrics"]
        lines.append("## 最新状态")
        lines.append("")
        lines.append(f"| 指标 | 值 |")
        lines.append(f"|------|-----|")
        lines.append(f"| 最新 A-Run | A-Run {last['run']} |")
        lines.append(f"| 公司数 | {m.get('公司数', '?')} |")
        lines.append(f"| 联系人数 | {m.get('联系人数', '?')} |")
        lines.append(f"| 覆盖率 | {m.get('覆盖率', '?')} |")
        lines.append(f"| AU 无联系 | {m.get('AU 无联系', '?')} |")
        lines.append(f"| 有邮箱 | {m.get('有邮箱', '?')} |")
        lines.append(f"| 有电话 | {m.get('有电话', '?')} |")
        lines.append(f"| 有表单 | {m.get('有表单', '?')} |")
        if bruns:
            lines.append(f"| 最新 B-Run | B-Run {bruns[-1]['run']} |")
        lines.append("")

    # A-Run trends (last 5)
    recent_a = aruns[-5:] if len(aruns) > 5 else aruns
    if recent_a:
        lines.append("## A-Run 趋势（最近 5 次）")
        lines.append("")
        lines.append("| Run | 时间 | 公司数 | 覆盖率 | 联系人数 | 耗时 |")
        lines.append("|-----|------|--------|--------|----------|------|")
        for s in recent_a:
            m = s["metrics"]
            lines.append(f"| {s['run']} | {s['timestamp']} | {m.get('公司数', '?')} | {m.get('覆盖率', '?')} | {m.get('联系人数', '?')} | {s['duration']} |")
        lines.append("")

    # B-Run trends (last 5)
    recent_b = bruns[-5:] if len(bruns) > 5 else bruns
    if recent_b:
        lines.append("## B-Run 趋势（最近 5 次）")
        lines.append("")
        lines.append("| Run | 时间 | 关键词产出 | 有效率 | 去重率 | 耗时 |")
        lines.append("|-----|------|-----------|--------|--------|------|")
        for s in recent_b:
            lines.append(f"| {s['run']} | {s['timestamp']} | {s['total产出']} | {s['有效率']} | {s['去重率']} | {s['duration']} |")
        lines.append("")

    return "\n".join(lines)


def main():
    aruns = []
    bruns = []

    if RUN_LOG.exists():
        aruns = parse_arun_sections(RUN_LOG.read_text(encoding="utf-8"))
    else:
        print(f"Warning: {RUN_LOG} not found")

    if KEYWORD_LOG.exists():
        bruns = parse_brun_sections(KEYWORD_LOG.read_text(encoding="utf-8"))
    else:
        print(f"Info: {KEYWORD_LOG} not found, skipping B-Run trends")

    if not aruns and not bruns:
        print("No data to summarize")
        return

    content = generate_summary(aruns, bruns)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(content, encoding="utf-8")
    print(f"Summary written to {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
