# Full Auto Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a self-contained `/full-auto-pipeline` skill that orchestrates the entire B2B lead research pipeline (form collection → KP enrichment → keyword discovery → reporting) with zero permission prompts, daily data snapshots, and clear human-review gates.

**Architecture:** A skill file (`SKILL.md`) defines the pipeline stages and decision logic. A daily auto-commit hook (`daily_snapshot.py`) ensures data safety. VSCode extension settings enforce bypass-permissions mode. All existing safety hooks (`pre_bash_safety.py`, `stop_check.py`, etc.) remain as the security net.

**Tech Stack:** Python (hooks, pipeline scripts), Claude Code skills (SKILL.md), VSCode extension settings, git (snapshots)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `~/.claude/skills/full-auto-pipeline/SKILL.md` | Create | Skill definition: pipeline stages, decision flow, human-review gates, token budgets |
| `.claude/hooks/daily_snapshot.py` | Create | Auto-commit `data/` once per day if changes exist |
| `.claude/settings.json` | Modify | Add `daily_snapshot` to `SessionStart` hook |
| `.vscode/settings.json` | Verify | Confirm `allowDangerouslySkipPermissions` + `initialPermissionMode` are set |
| `.claude/settings.local.json` | Modify | Clean up one-off allow rules, keep only wildcard patterns |
| `~/.claude/CLAUDE.md` | Verify | Confirm Karpathy 7 rules are present |
| `~/.claude/skills/karpathy-guidelines/SKILL.md` | Verify | Confirm skill is installed |

---

### Task 1: Verify and Clean Permission Configuration

**Files:**
- Verify: `.vscode/settings.json`
- Modify: `.claude/settings.local.json`

- [ ] **Step 1: Verify VSCode settings have bypass permissions**

Read `.vscode/settings.json` and confirm these two lines exist:
```json
"claudeCode.allowDangerouslySkipPermissions": true,
"claudeCode.initialPermissionMode": "bypassPermissions"
```

If missing, add them.

- [ ] **Step 2: Clean up settings.local.json**

Replace all one-off `Bash(rm ...)` and `Bash(ls ...)` rules with a clean wildcard-only list. The final allow list should be:

```json
{
  "permissions": {
    "defaultMode": "bypassPermissions",
    "allow": [
      "Bash(*)",
      "Read(*)",
      "Write(*)",
      "Edit(*)",
      "Agent(*)",
      "WebFetch(*)",
      "WebSearch",
      "Skill(*)"
    ],
    "additionalDirectories": [
      "D:\\antd-components\\public",
      "D:\\antd-components",
      "C:\\Users\\Administrator\\Desktop",
      "C:\\Users\\Administrator\\.claude",
      "C:\\Users\\Administrator\\.claude\\plans",
      "E:\\AI\\TestProject-v2\\.claude\\hooks",
      "E:\\AI\\TestProject-v2\\.claude",
      "C:\\Users\\Administrator\\.claude\\skills",
      "C:\\Users\\Administrator\\.claude\\skills\\karpathy-guidelines",
      "\\tmp",
      "E:\\自动跑表单的成果和情况"
    ]
  }
}
```

- [ ] **Step 3: Verify global CLAUDE.md has Karpathy 7 rules**

Read `~/.claude/CLAUDE.md` and confirm it contains all 7 sections: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution, No Non-Language Work, Hard Token Budgets, Surface Conflicts.

- [ ] **Step 4: Verify karpathy skill is installed**

Read `~/.claude/skills/karpathy-guidelines/SKILL.md` and confirm it exists with correct frontmatter.

- [ ] **Step 5: Commit**

```bash
git add .vscode/settings.json .claude/settings.local.json
git commit -m "chore: clean permission config, verify bypass mode"
```

---

### Task 2: Create Daily Auto-Commit Hook

**Files:**
- Create: `.claude/hooks/daily_snapshot.py`
- Modify: `.claude/settings.json`

- [ ] **Step 1: Create daily_snapshot.py**

```python
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
```

- [ ] **Step 2: Run the hook manually to test**

```bash
python .claude/hooks/daily_snapshot.py
```

Expected: No error. If `data/` has changes, a commit is created.

- [ ] **Step 3: Verify the commit was created**

```bash
git log --oneline -3
```

Expected: A commit with message "chore: daily snapshot 2026-05-28" (or today's date).

- [ ] **Step 4: Add hook to .claude/settings.json**

Add to the `SessionStart` hooks array in `.claude/settings.json`:

```json
{
  "type": "command",
  "command": "python",
  "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/daily_snapshot.py"],
  "timeout": 20
}
```

- [ ] **Step 5: Commit**

```bash
git add .claude/hooks/daily_snapshot.py .claude/settings.json
git commit -m "feat: add daily data snapshot hook"
```

---

### Task 3: Create the Full Auto Pipeline Skill

**Files:**
- Create: `~/.claude/skills/full-auto-pipeline/SKILL.md`

- [ ] **Step 1: Create skill directory**

```bash
mkdir -p ~/.claude/skills/full-auto-pipeline
```

- [ ] **Step 2: Write SKILL.md**

```markdown
---
name: full-auto-pipeline
description: >
  Fully automated B2B lead research pipeline. Orchestrates form collection,
  KP enrichment, keyword discovery, and reporting. Only pauses for human
  review at defined gates. Use when the user says "run pipeline", "auto mode",
  "start collection", or "/full-auto-pipeline".
---

# Full Auto Pipeline

## Overview

This skill runs the complete B2B lead research pipeline with minimal human intervention.
It orchestrates three stages: form collection, KP enrichment, and keyword discovery.

**Pre-requisites:**
- `data/leads.csv` exists with AU leads
- `.claude/hooks/pre_bash_safety.py` is active (destructive command blocker)
- `docs/current-progress.md` is up to date

**Token budget:** Max 3 pipeline rounds per invocation. Each round = 1 form batch + 1 KP enrichment pass. After 3 rounds, stop and report results.

## Pipeline Flow

```
START
  |
  v
[Read docs/current-progress.md]
  |
  v
[Stage 1: Form Collection]
  |-> build_form_kp_candidate_queue.py --limit 50
  |-> extract_public_contact_candidates.py (batch, --skip-existing)
  |-> Auto-merge: append to leads.csv if valid_rate >= 50%
  |-> If valid_rate < 50%: PAUSE, report, ask user
  |
  v
[Stage 2: KP Enrichment]
  |-> run_pipeline.py --stage 2 --limit 30
  |-> Auto-approve: score >= 85 -> contacts.csv
  |-> Auto-reject: score < 30
  |-> Human review: score 30-85 -> reports/pending-review-{date}.csv
  |
  v
[Stage 3: Keyword Discovery]
  |-> scheduler.py --max 20 (dry-run first)
  |-> If new keywords found: generate + import
  |-> If no new keywords: skip
  |
  v
[Reporting]
  |-> generate_run_report.py --auto-stats
  |-> Update docs/current-progress.md
  |
  v
[Round Check]
  |-> If rounds < 3 and new data found: loop to Stage 1
  |-> If rounds >= 3 or no new data: STOP, report summary
  |
  v
END
```

## Human-Review Gates

These are the ONLY points where the pipeline pauses:

| Gate | Condition | Action |
|------|-----------|--------|
| Low valid rate | valid_rate < 50% | Pause, report batch quality, ask user |
| Low-confidence KP | score 30-85 | Save to pending-review, continue pipeline |
| LinkedIn URL | Unverified person/company match | Save to pending-review, continue pipeline |
| Data count decrease | post-merge record count < pre-merge | STOP immediately, do NOT commit |
| Pipeline error | Script exits non-zero | Log error, skip to next stage, report at end |

**Everything else runs automatically.** No permission prompts, no confirmations.

## Stage Details

### Stage 1: Form Collection

**Script:** `scripts/extraction/build_form_kp_candidate_queue.py` + `extract_public_contact_candidates.py`

**Command pattern:**
```bash
# Build queue
./.venv/Scripts/python scripts/extraction/build_form_kp_candidate_queue.py

# Run extraction (auto-skip existing)
./.venv/Scripts/python scripts/extraction/extract_public_contact_candidates.py \
  --input reports/au-form-kp-candidate-queue-{timestamp}.csv \
  --skip 0 --limit 50 --follow-links 3 --fetcher static --skip-existing \
  --output-prefix "auto-form-"
```

**Auto-merge rules (per AGENTS.md Rule 9):**
- Backup `data/leads.csv` before merge
- Dry-run: generate merge report
- Only append new qualified records
- Valid rate must be >= 50%
- Post-merge record count must only increase

**If valid_rate < 50%:** Stop this stage, report valid rate and suggestions, continue to Stage 2.

### Stage 2: KP Enrichment

**Script:** `scripts/kp_pipeline/run_pipeline.py`

**Command pattern:**
```bash
./.venv/Scripts/python -m scripts.kp_pipeline.run_pipeline --stage 2 --limit 30
```

**Auto-approval rules (per config/kp_pipeline.json):**
- score >= 85: auto-approve -> append to `data/contacts.csv`
- score < 30: auto-reject -> `reports/rejected-{date}.csv`
- score 30-85: human review -> `reports/pending-review-{date}.csv`

### Stage 3: Keyword Discovery

**Script:** `scripts/keyword_scheduler/scheduler.py` + `generator.py`

**Command pattern:**
```bash
# Dry-run first
./.venv/Scripts/python -m scripts.keyword_scheduler.generator --max 20 --dry-run

# If results look good, run for real
./.venv/Scripts/python -m scripts.keyword_scheduler.generator --max 20
./.venv/Scripts/python -m scripts.keyword_scheduler.import_suggestions reports/suggested_keywords.csv
```

**Gate:** If dry-run shows 0 new unique keywords, skip this stage entirely.

### Reporting

**Script:** `scripts/reports/generate_run_report.py`

```bash
./.venv/Scripts/python scripts/reports/generate_run_report.py \
  --title "Auto Pipeline Run" \
  --task "Full auto pipeline: form + KP + keywords" \
  --auto-stats
```

**Auto-update:** After reporting, update `docs/current-progress.md` with:
- New data snapshot (row counts)
- Pipeline run results
- Next steps

## Safety Rules

1. **Append-only:** Never delete or overwrite records in `data/leads.csv` or `data/contacts.csv`
2. **Backup before merge:** Always backup master files before any write operation
3. **Record count check:** Post-merge count must equal pre-merge + new records
4. **Daily snapshot:** The `daily_snapshot.py` hook auto-commits `data/` once per day
5. **Destructive command block:** `pre_bash_safety.py` blocks `rm -rf`, `git reset --hard`, etc.
6. **Stray file check:** `stop_check.py` blocks exit if test artifacts remain

## Invocation

User says any of:
- `/full-auto-pipeline`
- "run the pipeline"
- "start auto mode"
- "run collection and enrichment"

The skill reads `docs/current-progress.md`, determines what's needed, and runs the appropriate stages.

## Error Handling

- If a script fails: log the error, skip to next stage, report at end
- If a stage has 0 results: skip dependent stages, report
- If all 3 rounds produce 0 new data: stop early, report "pipeline plateau"
- Never retry a failed script more than once (Rule 6: Hard Token Budgets)
```

- [ ] **Step 3: Verify the skill appears in the skill list**

Check that `full-auto-pipeline` appears in the available skills when the session restarts.

- [ ] **Step 4: Commit**

```bash
git add ~/.claude/skills/full-auto-pipeline/SKILL.md
git commit -m "feat: add full-auto-pipeline skill"
```

---

### Task 4: Test the Pipeline End-to-End

**Files:**
- Test: Run the skill on a small batch (limit 5)

- [ ] **Step 1: Invoke the skill**

Use `/full-auto-pipeline` or manually trigger the pipeline with a small limit:

```bash
./.venv/Scripts/python scripts/extraction/build_form_kp_candidate_queue.py
```

- [ ] **Step 2: Verify form collection runs without permission prompts**

The extraction should run without any approval dialogs.

- [ ] **Step 3: Verify auto-merge works**

Check that new records are appended to `data/leads.csv` and the record count only increases.

- [ ] **Step 4: Verify KP enrichment auto-approves high-score results**

```bash
./.venv/Scripts/python -m scripts.kp_pipeline.run_pipeline --stage 2 --limit 5
```

Check that score >= 85 results are auto-appended to `data/contacts.csv`.

- [ ] **Step 5: Verify daily snapshot hook works**

```bash
python .claude/hooks/daily_snapshot.py
git log --oneline -3
```

Expected: A daily snapshot commit exists.

- [ ] **Step 6: Verify reporting works**

```bash
./.venv/Scripts/python scripts/reports/generate_run_report.py \
  --title "Test Run" --task "E2E test" --auto-stats
```

Expected: Report generated in `E:\自动跑表单的成果和情况\`.

- [ ] **Step 7: Commit test results**

```bash
git add data/ docs/current-progress.md
git commit -m "test: verify full-auto-pipeline e2e"
```

---

### Task 5: Wire Up Loop/Scheduling (Optional)

**Files:**
- Modify: None (uses existing `/loop` skill)

- [ ] **Step 1: Test /loop integration**

The user can schedule recurring pipeline runs:
```
/loop 30m /full-auto-pipeline
```

This runs the pipeline every 30 minutes. The skill's token budget (max 3 rounds per invocation) prevents runaway loops.

- [ ] **Step 2: Document the scheduling options**

Add to `docs/current-progress.md` under "Automation":
```
## Automation
- `/full-auto-pipeline` — run one full cycle
- `/loop 30m /full-auto-pipeline` — run every 30 minutes
- Daily snapshot: auto-commit at session start
```

---

## Verification Checklist

After all tasks, verify:

- [ ] `.vscode/settings.json` has `allowDangerouslySkipPermissions: true` and `initialPermissionMode: "bypassPermissions"`
- [ ] `.claude/settings.local.json` has clean wildcard allow rules (no one-off commands)
- [ ] `~/.claude/CLAUDE.md` has Karpathy 7 rules
- [ ] `~/.claude/skills/karpathy-guidelines/SKILL.md` exists
- [ ] `~/.claude/skills/full-auto-pipeline/SKILL.md` exists
- [ ] `.claude/hooks/daily_snapshot.py` exists and is registered in `.claude/settings.json`
- [ ] `.claude/hooks/pre_bash_safety.py` blocks destructive commands
- [ ] `.claude/hooks/stop_check.py` blocks exit with stray files
- [ ] Pipeline runs without permission prompts
- [ ] Daily snapshot creates a git commit
- [ ] Form collection auto-merges when valid_rate >= 50%
- [ ] KP enrichment auto-approves score >= 85
- [ ] Low-confidence KP goes to pending-review
- [ ] Report is generated after pipeline completes
