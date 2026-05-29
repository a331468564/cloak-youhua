"""
Stop / SubagentStop hook: Pre-exit self-check.

Before agent finishes, checks git status for untracked test artifacts.
Blocks with exit 2 if stray files found.
"""
import json
import os
import re
import subprocess
import sys
import time
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


ALLOWED_ROOT_FILES = {
    "CLAUDE.md", "README.md", "AGENTS.md", "requirements.txt",
    ".gitignore", "LICENSE",
}


def check_stray_files(root):
    """Check for untracked files that should be cleaned up."""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []

        stray = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            if line.startswith("??"):
                filepath = line[3:].strip()
                basename = os.path.basename(filepath)

                is_stray = False
                reason = ""

                if re.match(r"^(temp_|test_|debug_)", basename):
                    is_stray = True
                    reason = "temp/test/debug prefix"
                elif "/" not in filepath and "\\" not in filepath:
                    if basename.endswith((".csv", ".md")) and basename not in ALLOWED_ROOT_FILES:
                        is_stray = True
                        reason = "root-level file"
                elif "__pycache__" in filepath and ".claude" in filepath:
                    is_stray = True
                    reason = "__pycache__ in .claude"

                if is_stray:
                    stray.append(f"  - {filepath} ({reason})")

        return stray
    except Exception:
        return []


def check_session_heaviness(root):
    """Check if session has too many tool calls without progress update."""
    counter_path = root / ".claude" / ".session_counter"
    if not counter_path.exists():
        return []
    try:
        data = json.loads(counter_path.read_text(encoding="utf-8"))
        count = data.get("count", 0)
        if count < 15:
            return []
        progress_path = root / "docs" / "current-progress.md"
        if progress_path.exists():
            mtime = progress_path.stat().st_mtime
            if time.time() - mtime > 7200:
                return [f"  - 会话已执行 {count} 次工具调用但未更新 docs/current-progress.md，请先更新进度"]
    except Exception:
        pass
    return []


def main():
    event = read_event()
    root = get_project_root()
    stray = check_stray_files(root)
    stray.extend(check_session_heaviness(root))

    if stray:
        reason = (
            f"Stop blocked: found {len(stray)} untracked test artifact(s). Clean up before finishing:\n"
            + "\n".join(stray)
            + "\n\nDelete these files or move them to reports/archive/, then try again."
        )
        print(json.dumps({
            "decision": "block",
            "reason": reason,
        }))
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
