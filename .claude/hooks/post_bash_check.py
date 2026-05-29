"""
PostToolUse hook: Check for test artifacts after script execution.

Runs after Python script commands. Checks git status for untracked files
that look like test artifacts (temp_*, test_*, debug_*, root-level .csv/.md).
Warns Claude via additionalContext if found.
"""
import json
import os
import re
import subprocess
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


ALLOWED_ROOT_FILES = {
    "CLAUDE.md", "README.md", "AGENTS.md", "requirements.txt",
    ".gitignore", "LICENSE",
}


def check_git_status(root):
    """Check for untracked files that look like test artifacts."""
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

                if is_stray:
                    stray.append(f"  - {filepath} ({reason})")

        return stray
    except Exception:
        return []


def main():
    event = read_event()
    command = event.get("tool_input", {}).get("command", "")

    if not re.search(r"python\s+", command):
        sys.exit(0)

    root = get_project_root()
    stray = check_git_status(root)

    if stray:
        warning = (
            "Test artifact check: found untracked files after script execution:\n"
            + "\n".join(stray)
            + "\nClean up before finishing (delete temp files, move reports to reports/)."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": warning,
            }
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()
