<!-- DOC_META
lifecycle:  long-term
audience:   agent
write_when: Agent 使用方式、工具配置变更时更新
read_when:  Agent 需要了解自身使用规范时读取
delete_when: 不删除
-->
# Codex Agent Usage

*Updated: 2026-05-12*

## Purpose

This document explains how agents should use this repository's guidance and project-local hooks.

The project supports two agent entry points:

- **Claude Code**: Reads `CLAUDE.md` as primary instructions, then `AGENTS.md` for supplementary rules.
- **Codex CLI**: Reads `AGENTS.md` as primary instructions, then `docs/guides/cli-operating-rules.md` for task-specific context.

Both agents share the same `docs/` workflow files, `data/` CSV files, and `scripts/` tools. The instruction sets are complementary, not conflicting.

## Instruction Loading

Codex reads `AGENTS.md` files from the repository root down to the current working directory. More specific files closer to the current directory override broader instructions. Keep the root `AGENTS.md` short and operational; put long project details in `docs/`.

For this project, start Codex from the repository root:

```powershell
cd E:\AI\TestProject-v2
codex
```

To check which instructions are active:

```powershell
codex --ask-for-approval never "Summarize the active project instructions and hook setup."
```

## Hook Setup

The project-local hook config is in `.codex/config.toml`.

If the local Codex installation does not automatically load project-local `.codex/config.toml`, copy or merge the hook section into the active Codex config, usually:

```powershell
notepad $env:USERPROFILE\.codex\config.toml
```

Keep the hook commands pointing to this repository's project-local Python.

For notifications across all Codex projects, use the user-level config at:

```powershell
$env:USERPROFILE\.codex\config.toml
```

Global notification setup should stay generic: use `E:\AI\Codex\GlobalHooks\global_task_end_notify.ps1` from a `[[hooks.Stop]]` hook to launch `E:\AI\Codex\GlobalHooks\notify_user_persistent.ps1` asynchronously. Do not copy this project's safety, request-log, capability, or lead-workflow hooks into the user-level config because those rules are project-specific.

Do not start the persistent WinForms notification with `-WindowStyle Hidden` or Python `CREATE_NO_WINDOW`. Those modes can also hide the confirmation form even though the script exits without errors. Silent flags are acceptable for MCP/toast helpers, but visible persistent popup launchers must allow a normal desktop window.

Global notification validation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "E:\AI\Codex\GlobalHooks\global_task_end_notify.ps1" -Title "Global launcher test" -Message "Launcher test. Auto closes." -AutoCloseMs 1000
```

### Hook TOML Format

Codex hooks must use Codex's event-grouped TOML structure. Do not copy Claude Code hook arrays directly into Codex config.

Do not use:

```toml
[[hooks]]
event = "UserPromptSubmit"
command = '.\.venv\Scripts\python.exe .\.codex\hooks\safety_hook.py'
```

Use event-name groups and nested hook entries:

```toml
[[hooks.PreToolUse]]
matcher = "^(Bash|PowerShell|shell_command)$"

[[hooks.PreToolUse.hooks]]
type = "command"
command = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "& .\.venv\Scripts\python.exe .\.codex\hooks\safety_hook.py"'
timeout = 30
statusMessage = "Checking tool safety"
```

The same structure applies to other events, such as `[[hooks.UserPromptSubmit]]` plus `[[hooks.UserPromptSubmit.hooks]]`, or `[[hooks.Stop]]` plus `[[hooks.Stop.hooks]]`.

Before changing hooks, verify the active Codex version's supported TOML structure. A config with `[[hooks]]` and `event = "..."` can fail at startup with:

```text
Error loading config.toml: invalid type: sequence, expected struct HooksToml in `hooks`
```

Quick self-check:

```powershell
Select-String -Path .\.codex\config.toml -Pattern '\[\[hooks\]\]|event\s*='
```

Correct result: no output.

## Hook Categories

### Safety and Scope

Script: `.codex/hooks/safety_hook.py`

Events:

- `UserPromptSubmit`
- `PreToolUse`

Purpose:

- Block obvious destructive shell commands.
- Warn before high-capability extraction runs when scope, batch size, rate limit, cooldown, output path, or ban-risk stop conditions are missing.
- Remind Codex to prefer project-local/non-C: installs for Python and browser tooling.
- Log decisions to `.codex/logs/safety.jsonl`.

### Post Tool Checks

Script: `.codex/hooks/post_tool_hook.py`

Events:

- `PostToolUse`

Purpose:

- Warn if `docs/current-progress.md` is edited outside checkpoint/handoff-style work.
- Run Python compile checks after project scripts are changed.
- Warn when tool/capability changes may also need README, requirements, capability inventory, or request-log updates.
- Check Markdown files remain UTF-8 readable after edits.
- Remind Codex to check `docs/request-solution-log.md` after project file changes.

### Task End Check

Script: `.codex/hooks/task_end_hook.py`

Event:

- `Stop`

Purpose:

- Record final assistant-message preview and turn metadata to `.codex/logs/task_end.jsonl`.
- Remind Codex to update `docs/request-solution-log.md` when the task changed files, rules, tools, workflow, data standards, or future operating context.
- Remind Codex to report script/hook verification when relevant.
- Trigger a best-effort desktop notification when a Codex task ends, so the user can notice completed work or reminders without watching the terminal.

Notification behavior:

- The notification is local-only and does not write secrets or project data.
- Hook stdout remains empty; notification failures are swallowed and recorded only through the normal task-end JSONL log.
- When a task ends with project reminders or detected file changes, the Stop hook first tries `scripts/utils/notify_user_persistent.ps1`, a local topmost confirmation window that stays open until the user clicks `OK`. This persistent branch must not use `CREATE_NO_WINDOW`, otherwise the form may be created invisibly.
- The Stop hook now prefers `scripts/send_mcp_notification.mjs`, which starts the project-local `@topvisor/mcp-notifications` MCP server, calls `send_notification`, enables sound, and exits.
- `scripts/utils/notify_user.ps1` uses Windows toast notifications first with AppUserModelID `Codex.Project.Notifier`, then falls back to a tray balloon if toast creation fails.
- `scripts/send_mcp_notification.mjs` and `scripts/utils/notify_user.ps1` remain fallbacks for ordinary completion notifications or if the persistent helper cannot start.
- If Windows blocks the notification source, run `scripts/utils/install_codex_notification_permission.ps1` once from the project root. It creates a Start Menu shortcut named `Codex Project Notifier`, enables the current user's notification settings for `Codex.Project.Notifier`, and sends a test notification. On some Windows builds the shortcut AppUserModelID COM write can warn and continue; this does not stop the test notification.
- Manual test command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\utils\notify_user.ps1" -Title "Codex test" -Message "Notification test"
```

Persistent confirmation test command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\utils\notify_user_persistent.ps1" -Title "Codex persistent test" -Message "This window should stay until confirmed." -Sound
```

Permission installer:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\utils\install_codex_notification_permission.ps1"
```

### MCP Notification Server

Project-local install:

```powershell
npm.cmd install --prefix .codex\tools\mcp-notifications @topvisor/mcp-notifications
```

Codex config:

```toml
[mcp_servers.notifications]
enabled = true
command = "E:\\AI\\TestProject-v2\\.codex\\tools\\mcp-notifications\\node_modules\\.bin\\mcp-notifications.cmd"
args = []
env = { MCP_NOTIFICATIONS_APP_ID = "Codex.Project.Notifier", MCP_NOTIFICATIONS_BACKEND = "node-notifier" }
```

After restarting Codex, the MCP server should expose `send_notification`. Use it for explicit agent notifications with a short title/message and optional `play_sound = true`.

The Stop hook also uses the same package through the one-shot helper:

```powershell
node scripts\send_mcp_notification.mjs --title "Codex MCP hook test" --message "Task-end hook MCP helper test" --sound
```

## Claude Code Hooks

Claude Code uses `.claude/settings.json` for hook configuration (JSON format, not TOML).

### Hook Configuration

File: `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/pre_bash_safety.py"],
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/post_bash_check.py"],
            "timeout": 15
          },
          {
            "type": "command",
            "command": "python",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/context_freshness_check.py"],
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/post_write_check.py"],
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/stop_check.py"],
            "timeout": 15
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/stop_check.py"],
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

### Claude Code Hook Scripts

All in `.claude/hooks/`:

| Script | Event | Purpose |
|--------|-------|---------|
| `pre_bash_safety.py` | PreToolUse (Bash) | Block destructive commands (`rm -rf`, `git reset --hard`) |
| `post_bash_check.py` | PostToolUse (Bash) | Check for test artifacts after Python script execution |
| `context_freshness_check.py` | PostToolUse (Bash) | Count tool calls, warn at 15+ to update progress and start new window |
| `post_write_check.py` | PostToolUse (Write) | Check new `.md` files for `<!-- DOC_META` metadata |
| `stop_check.py` | Stop / SubagentStop | Block agent from finishing if stray files exist or heavy session without progress update |

### Protocol Differences from Codex

- Claude Code hooks output JSON to stdout (Codex hooks use stderr only)
- Claude Code hooks use `additionalContext` to send messages to Claude
- Claude Code Stop hook uses `decision: "block"` + exit 2 to prevent stopping
- Claude Code PreToolUse uses `permissionDecision: "deny"` in stdout JSON
- Path placeholder: `${CLAUDE_PROJECT_DIR}` (Codex has no equivalent)

### Verification

Type `/hooks` in Claude Code to verify all hooks are registered and check their sources.

## Validation

Run these checks after changing agent or hook files:

```powershell
.\.venv\Scripts\python -c "import py_compile, pathlib; out=pathlib.Path('reports/hook-pycompile'); out.mkdir(exist_ok=True); files=['hook_utils','safety_hook','post_tool_hook','task_end_hook']; [py_compile.compile(f'.codex/hooks/{name}.py', cfile=str(out / f'{name}.pyc'), doraise=True) for name in files]; print('hook compile OK')"
```

The explicit `cfile` path avoids Python trying to write `.codex/hooks/__pycache__`, which can be blocked by local ACLs in this workspace.

Run a normal project capability check:

```powershell
.\.venv\Scripts\python scripts\utils\check_capability_inventory.py
```

## Logging Policy

- `.codex/logs/` is local runtime output and should not be committed.
- `reports/hook-pycompile/` is temporary validation output and should not be committed.
- `docs/request-solution-log.md` remains the durable project decision log. `docs/logs/changelog.md` holds current entries and the blocker taxonomy index.
- `docs/current-progress.md` is only for real checkpoints: account/session handoff, context risk, meaningful completed stage, major data/tool milestone, or resume-critical next plan.

## Current Boundaries

- Hooks currently cover the selected guardrails only: destructive command blocking, task-end request-log reminders, current-progress threshold warnings, script compile checks, capability inventory reminders, high-capability extraction scope warnings, and UTF-8 Markdown checks.
- CSV row-count/schema checks, candidate-evidence-first enforcement, LinkedIn automation blocking, CODEx block enforcement, dashboard scope checks, and outreach-log checks are intentionally not included.
- Hook failures should not break routine work unless a safety rule blocks a risky action.
