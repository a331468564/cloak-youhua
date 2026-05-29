# AGENTS.md

## Project Purpose

This repository is the Ron Group local lead research MVP. The active workflow is Australia-first restaurant/hotel final-customer lead enrichment, with key-person contact discovery as the main bottleneck.

## Read First

At the start of a Codex session in this project folder, use this file as the entry rule and read the relevant active Markdown before acting.

For broad, unclear, configuration, tooling, or workflow tasks, read these files before acting:

- `README.md`
- `docs/guides/cli-operating-rules.md`
- `docs/request-solution-log.md`
- `docs/guides/codex-agent-usage.md`
- `docs/workflows/lead-enrichment-workflow.md`
- `docs/workflows/lead-collection-workflow.md`
- `docs/architecture/lead-table-fields.md`

For narrow tasks, read `docs/guides/cli-operating-rules.md` first, then follow its task-specific context list. For Codex hook, agent, config, or startup errors, also read `docs/guides/codex-agent-usage.md` before editing or troubleshooting.

For keyword scheduler tasks（关键词拓展、关键词生成、关键词驱动搜索），read `docs/guides/keyword-scheduler-guide.md` in addition to the task-specific context list.

Use `docs/current-progress.md` only for handoff/checkpoint context. Do not update it for routine or early small iterations.

## Operating Rules

- Prefer official company websites, official contact pages, official PDFs, and reviewable public evidence.
- Do not fabricate contacts, job titles, emails, phones, or LinkedIn URLs.
- Treat LinkedIn personal URLs as manual review entry points unless a person/company match is verified. Do not automate LinkedIn login, browsing, messaging, or export without explicit approval.
- Extracted company contact routes and KP candidates may be written to `data/leads.csv` or `data/contacts.csv` when a public source is recorded. Mark uncertain KP rows as Low/Medium confidence and pending verification; do not fabricate or mark them as verified direct contacts.
- Preserve row counts and CSV schemas unless the user explicitly approves a schema/data migration.
- Keep the dashboard simple. Do not add new segmentation or classification layers unless explicitly requested.
- Use project-local tooling first: `.venv`, `.ms-playwright`, `requirements.txt`, and `scripts/utils/check_capability_inventory.py`.
- Keep important durable decisions in `docs/request-solution-log.md`. Include `Achievements` and `Issues / limits` lists for new task records. When encountering a blocker (same issue, 2–3 attempts with no progress): (1) classify it with the `[MAJOR-SUBCATEGORY]` tag from `docs/logs/changelog.md`; (2) lookup the "Historical Blocker Index" — if a match exists, apply the recorded fix directly; (3) if no match, solve it and record Symptom / Root Cause / Fix / Best Practice, then update the index table.
- Default to writing the `docs/request-solution-log.md` entry in the same turn when a task changes files, rules, workflow, data standards, tools, or future operating context, unless the user explicitly forbids it or limits edits to files that exclude the log.
- Preserve user and project content formatting by default. Only add boundary labels, compact repeated structures, or strict machine-readable formats when the trigger rules in `docs/guides/cli-operating-rules.md` are clearly met.
- Before modifying Codex hooks, confirm the current Codex-supported TOML structure. Do not copy Claude Code `[[hooks]] event = "..."` hook config directly into Codex; use Codex event-grouped hook tables instead.

## Data Operation Rules

The project operates on CSV master tables (`data/leads.csv`, `data/contacts.csv`). These rules prevent data loss.

**Default auto-execute (no confirmation needed):**
- Read/search/write raw files
- Clean and dedup new data only
- Write rejected files, mark needs_review
- Backup, dry-run, generate diff/merge report
- Append new qualified records without touching existing ones

**Must pause for confirmation:**
- Delete or overwrite existing records in master tables
- Modify non-empty fields in existing records
- Run `git checkout` / `restore` / `reset` / `reset --hard` on data files
- Switch task zones (A ↔ B)
- Master table record count decreases
- Valid rate < 50% but batch extraction would continue
- Script attempts to delete unverifiable data

**Data safety rules:**
1. Never destructively modify master data files. `data/leads.csv` and `data/contacts.csv` are append-only; no delete, overwrite, or rebuild. If data is lost, check recovery sources in CLAUDE.md "Data Provenance & Recovery" section.
2. Auto-append is allowed; auto-delete, auto-overwrite, and auto-rewrite are not. Any delete or overwrite requires user confirmation.
3. Before writing to master tables: backup → dry-run → merge report → confirm record count only increases.
4. Cleaning and filtering apply to new data only. Never scan the full master table and delete historical records. Dedup compares new data against existing data; existing records are never modified.
5. Filtered-out data must be written to a rejected file. No silent deletion. Rejected file format: `reports/rejected-{timestamp}.csv`.
6. If data cannot be confirmed, mark it `needs_review`. Do not delete it.
7. Do not use domain suffix as the sole country indicator. Many Australian companies use `.com`, `.net.au`, `.io`, not just `.com.au`.
8. Search tasks must define qualification criteria before running and track valid rate per batch. Valid rate = qualified results / total results.
9. If valid rate < 50%, automatically pause batch expansion and optimize keywords/filtering. Report current valid rate and suggested improvements.
10. Do not switch task zones without confirmation. Keyword discovery that serves form collection may continue; switching to a different task zone requires confirmation.

**Auto-merge conditions (all must be met):**
- Operation only appends new qualified records
- No delete, overwrite, or modification of existing records
- Master table backed up
- Dry-run completed with merge report generated
- Rejected file generated (if any disqualified data)
- Valid rate ≥ 50%
- Post-merge record count = original count + new qualified records (only increase)

## Commands

Capability check:

```powershell
.\.venv\Scripts\python scripts\utils\check_capability_inventory.py
```

Python compile check:

```powershell
.\.venv\Scripts\python -m py_compile scripts\extraction\build_form_kp_candidate_queue.py scripts\extraction\extract_public_contact_candidates.py scripts\utils\check_capability_inventory.py
```

Small public candidate extraction test:

```powershell
.\.venv\Scripts\python scripts\extraction\extract_public_contact_candidates.py --limit 3 --follow-links 1 --delay 2 --output-prefix reports\test-candidates
```

Dashboard:

```powershell
.\scripts\utils\start_dashboard.ps1
```

Run 报告生成（每轮任务跑完后执行）：

```powershell
.\.venv\Scripts\python scripts\reports\generate_run_report.py --input run_data.json --auto-stats
```

## Documentation Rules

- `docs/request-solution-log.md`: durable user requests, workflow/tool behavior changes, file-changing tasks, achievements, issues, follow-up.
- `docs/current-progress.md`: only account/session handoff, context-risk checkpoint, meaningful completed stage, major data/tool milestone, or resume-critical next plan.
- `docs/workflows/lead-enrichment-workflow.md`: contact/KP confidence, LinkedIn boundaries, extraction helper behavior.
- `docs/workflows/lead-collection-workflow.md`: source/tool access and collection scope.
- `docs/guides/cli-operating-rules.md`: agent behavior, checkpoint rules, project-level boundaries.
- **Run 报告（每轮跑完必须生成）：** 表单收集、KP 富化、关键词发现等任务跑完后，用 `scripts/reports/generate_run_report.py` 生成人类可读报告，输出到 `E:\自动跑表单的成果和情况\`。用 `--title` 区分任务类型。报告仅用于人类观察，agent 不需要回读。
- **CODEx 标记治理：** 标记按大类划分（如 `keyword_strategy`、`enrichment_stopping_rules`），不要拆成细粒度子标记。新增标记前必须确认：(1) 现有标记确实无法覆盖该内容；(2) 该环节是工作流中缺失的步骤。A 区和 B 区的标记名不重复。禁止为了"规范化"或"细分"而拆分已有标记。

## Safety Boundaries

- Ask before broad new collection/enrichment batches, schema changes, high-risk access modes, authenticated platform automation, paid-source extraction, CAPTCHA handling, or account-risky workflows.
- Do not run destructive commands such as recursive delete, `git reset --hard`, or forced checkout unless the user explicitly requested and approved the action.

## Blocker Handling

Shared rule for A区 and B区. When a blocker is hit (same issue, 2–3 attempts with no progress), stop debugging and follow this sequence:

1. **Classify** — Tag with `[CATEGORY-SUBCATEGORY]` from `docs/logs/changelog.md` (e.g. `NET-FETCH-HTTP-429`, `DATA-QUALITY-FILTER`, `TOOL-SCRAPE-TLS`).
2. **Lookup** — Check the "Historical Blocker Index" in `docs/logs/changelog.md`. If a matching tag exists, apply the recorded fix directly.
3. **Solve and Record** — If no match, solve normally, then append a new entry with Symptom / Root Cause / Fix / Best Practice and update the index table.

Common blocker tags:

| Tag | Meaning | Typical Fix |
|-----|---------|-------------|
| `NET-FETCH-HTTP-429` | Search engine rate limit | Wait, use CloakBrowser |
| `NET-FETCH-HTTP-403` | Anti-scrape block | CloakBrowser fallback |
| `NET-FETCH-TLS` | TLS/SSL handshake failure | Skip site, mark as blocked |
| `DATA-QUALITY-FILTER` | Filter too aggressive or too loose | Adjust filter rules |
| `DATA-QUALITY-DEDUP` | Same company entered twice | Merge, add domain check |
| `DATA-QUALITY-NAME` | Company name extraction bad | Fix extraction parser |
| `TOOL-SCRIPT-ERROR` | Script crash or import error | Fix script, check venv |
