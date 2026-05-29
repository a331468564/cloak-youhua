"""
PostToolUse hook: Check new .md files for DOC_META metadata.

After Write tool creates a .md file, checks if it contains <!-- DOC_META.
Warns Claude if missing.
"""
import json
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


def main():
    event = read_event()
    file_path = event.get("tool_input", {}).get("file_path", "")

    if not file_path or not file_path.endswith(".md"):
        sys.exit(0)

    path = Path(file_path)
    if not path.exists():
        sys.exit(0)

    normalized = str(path).replace("\\", "/")
    skip_patterns = ["/archive/", "/plans/", ".claude/plans/", ".claude/memory/"]
    if any(p in normalized for p in skip_patterns):
        sys.exit(0)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            head = "".join(f.readline() for _ in range(15))
    except Exception:
        sys.exit(0)

    if "<!-- DOC_META" not in head:
        rel = normalized.split("TestProject-v2/")[-1] if "TestProject-v2/" in normalized else path.name
        warning = (
            f"DOC_META check: new MD file `{rel}` is missing `<!-- DOC_META ... -->` metadata block. "
            f"Add it at the top of the file (see docs/guides/cli-operating-rules.md)."
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
