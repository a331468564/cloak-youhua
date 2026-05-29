"""
PostToolUse hook: Check if current-progress.md was updated after pipeline run.

Triggers when merge_run*.py or generate_run_report.py are executed.
Warns if current-progress.md was not modified after those scripts.
"""
import json
import os
import re
import sys
from pathlib import Path


def read_event():
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def get_project_root():
    return Path(__file__).resolve().parents[2]


RUN_SCRIPTS = [
    r"merge_run\d+\.py",
    r"generate_run_report\.py",
    r"run_pipeline\.py",
]


def is_pipeline_run_command(command):
    for pattern in RUN_SCRIPTS:
        if re.search(pattern, command):
            return True
    return False


def main():
    event = read_event()
    command = event.get("tool_input", {}).get("command", "")

    if not is_pipeline_run_command(command):
        sys.exit(0)

    root = get_project_root()
    progress_file = root / "docs" / "current-progress.md"

    if not progress_file.exists():
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    "⚠️ docs/current-progress.md 不存在。"
                    "管线已运行，请创建或更新进度文件。"
                ),
            }
        }))
        sys.exit(0)

    # Check if progress file was modified in the last 2 minutes
    mtime = os.path.getmtime(progress_file)
    import time
    age_seconds = time.time() - mtime

    if age_seconds > 120:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    "⚠️ 管线脚本已运行，但 docs/current-progress.md 超过 2 分钟未更新。\n"
                    "请更新 A 区（或 B 区）的数据快照和运行记录，然后再结束任务。\n"
                    "更新清单见 current-progress.md 的\"更新规则\"一节。"
                ),
            }
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()
