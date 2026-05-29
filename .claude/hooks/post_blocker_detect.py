"""
PostToolUse hook: Detect consecutive bash failures and remind agent to check
the Historical Blocker Index before re-attempting.

After 2 consecutive non-zero exit codes, injects a blocker lookup reminder.
State is persisted in .claude/hooks/.blocker_state.json across invocations.
"""
import json
import os
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


def state_path():
    return Path(__file__).resolve().parent / ".blocker_state.json"


def load_state():
    p = state_path()
    if not p.exists():
        return {"consecutive_failures": 0, "last_command": "", "last_error": ""}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"consecutive_failures": 0, "last_command": "", "last_error": ""}


def save_state(state):
    p = state_path()
    p.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def is_failure(event):
    """Check if the bash command failed."""
    # Check exit code from tool result
    result = event.get("tool_result", {})
    if isinstance(result, dict):
        exit_code = result.get("exitCode") or result.get("exit_code")
        if exit_code is not None and exit_code != 0:
            return True
        stderr = result.get("stderr", "")
        if stderr and ("error" in stderr.lower() or "traceback" in stderr.lower()):
            return True

    # Check for error patterns in stdout
    stdout = ""
    if isinstance(result, dict):
        stdout = result.get("stdout", "") or result.get("output", "")
    elif isinstance(result, str):
        stdout = result

    error_patterns = [
        "Traceback (most recent call last)",
        "Error:",
        "FAILED",
        "fatal:",
        "command not found",
        "No such file or directory",
        "Permission denied",
        "ModuleNotFoundError",
        "ImportError",
        "ConnectionError",
        "TimeoutError",
        "SSLError",
        "TLS connect error",
    ]
    for pattern in error_patterns:
        if pattern in stdout:
            return True

    return False


def extract_command(event):
    """Get the bash command that was run."""
    return event.get("tool_input", {}).get("command", "")


def extract_error_hint(event):
    """Get a short error hint from the result."""
    result = event.get("tool_result", {})
    if isinstance(result, dict):
        stderr = result.get("stderr", "")
        stdout = result.get("stdout", "") or result.get("output", "")
    elif isinstance(result, str):
        stderr = ""
        stdout = result
    else:
        return ""

    combined = (stderr + "\n" + stdout)[-500:]
    for line in combined.split("\n"):
        lower = line.lower()
        if any(k in lower for k in ["error:", "traceback", "failed", "exception"]):
            return line.strip()[:200]
    return ""


def main():
    event = read_event()
    tool_name = event.get("tool_name", "")

    # Only monitor Bash tool
    if tool_name != "Bash":
        sys.exit(0)

    command = extract_command(event)
    state = load_state()

    if is_failure(event):
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        state["last_command"] = command[:200]
        state["last_error"] = extract_error_hint(event) or state.get("last_error", "")
        state["last_failure_time"] = time.time()
        save_state(state)

        if state["consecutive_failures"] >= 2:
            last_cmd = state.get("last_command", "")
            last_err = state.get("last_error", "")
            reminder = (
                f"⚠️ 连续 {state['consecutive_failures']} 次失败。"
                "在重试前，先查 Historical Blocker Index（docs/logs/changelog.md）。\n"
                f"最近命令: {last_cmd}\n"
                f"最近错误: {last_err}\n"
                "流程: 分类 → 查表 → 有记录则直接应用修复 → 无记录再调试。"
            )
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": reminder,
                }
            }))
    else:
        # Success resets the counter
        if state.get("consecutive_failures", 0) > 0:
            state["consecutive_failures"] = 0
            state["last_command"] = ""
            state["last_error"] = ""
            save_state(state)

    sys.exit(0)


if __name__ == "__main__":
    main()
