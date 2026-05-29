"""
PreToolUse hook: Block destructive shell commands.

Blocks: rm -rf, git reset --hard, git push --force, Remove-Item -Recurse
"""
import json
import os
import re
import sys


def read_event():
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


DESTRUCTIVE_PATTERNS = [
    r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+push\s+.*--force\b",
    r"\bgit\s+checkout\s+\.\s*$",
    r"\bgit\s+clean\s+-[a-zA-Z]*f\b",
    r"\bRemove-Item\s+.*-Recurse\s+.*-Force\b",
    r"\brmdir\s+/s\s+/q\b",
    r"\bdel\s+/[fq]\b",
]


def main():
    event = read_event()
    command = event.get("tool_input", {}).get("command", "")

    if not command:
        sys.exit(0)

    for pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            reason = f"Destructive command blocked by safety hook: matched pattern '{pattern}'"
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }))
            sys.exit(0)

    # Auto-approve all non-destructive Bash commands
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "approve",
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
