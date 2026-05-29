"""
SessionStart hook: Auto-commit data/ directory once per day.

Checks if today's date has already been committed (looks for commit message
pattern "daily snapshot YYYY-MM-DD"). If not, commits all changes in data/.
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_project_root():
    return Path(__file__).resolve().parents[2]


def already_committed_today(root):
    """Check if a daily snapshot commit already exists for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--since=today", "--grep=daily snapshot"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return today in result.stdout
    except Exception:
        return True  # Assume committed to avoid duplicate commits


def has_changes(root):
    """Check if data/ has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--short", "data/"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def main():
    root = get_project_root()

    if already_committed_today(root):
        sys.exit(0)

    if not has_changes(root):
        sys.exit(0)

    today = datetime.now().strftime("%Y-%m-%d")
    try:
        subprocess.run(
            ["git", "add", "data/"],
            cwd=str(root),
            capture_output=True,
            timeout=15,
        )
        result = subprocess.run(
            ["git", "commit", "-m", f"chore: daily snapshot {today}"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": f"Daily snapshot committed: {today}",
                }
            }))
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
