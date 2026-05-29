<!-- DOC_META
lifecycle:  long-term
audience:   agent
write_when: 迭代设置流程变更时更新
read_when:  开始新一轮迭代时读取
delete_when: 不删除
-->
# Iteration Setup Guide

<!-- CODEx_START: iteration_setup_overview -->
*Updated: 2026-05-11 00:00*

This guide explains safe project updates, key-checkpoint backups, timestamps, rollback, and Markdown update tags.

This file should not contain lead collection, lead enrichment, or dashboard usage instructions. Those topics live in their own specialized documents.

<!-- CODEx_END: iteration_setup_overview -->

## Update Tag Usage

<!-- CODEx_START: update_tag_usage -->
*Updated: 2026-05-08 12:05*

Markdown files should use update tags around sections that Codex is allowed to update.

Use this format:

```text
<!-- CODEx_START: section_name -->
*Updated: YYYY-MM-DD HH:MM*

Section content goes here.

<!-- CODEx_END: section_name -->
```

Rules:

- Update only content inside marked blocks when possible.
- Do not rewrite unrelated blocks.
- Use short and clear section names.
- Keep one main topic inside each block.
- If a requested update does not match an existing block, create a clearly named new block or ask for confirmation when risky.

<!-- CODEx_END: update_tag_usage -->

## Backup Folder and Naming Convention

<!-- CODEx_START: backup_rules -->
*Updated: 2026-05-11 00:00*

Backups are required only at key checkpoints, not after every routine task.

Create a timestamped backup in the `backup/` folder before changes that affect:

- Active project direction, workflow rules, or quality standards.
- CSV schemas, field meanings, scoring/status rules, or dashboard behavior.
- Large or irreversible data edits.
- Batch lead/contact updates where many rows will change.
- Tool access rules, account-risk rules, or outreach-readiness rules.

Backups are optional for:

- Read-only analysis.
- Small documentation wording edits that do not change rules.
- Single-row CSV corrections with clear `change_note`.
- Report creation that does not modify existing data or rules.

Use this naming format:

```text
backup/FILENAME_YYYYMMDD_HHMMSS.EXTENSION
```

Examples:

```text
backup/README_20260508_120532.md
backup/leads_20260508_120532.csv
backup/dashboard-guide_20260508_120532.md
```

Suggested backup limit:

- Keep the latest `10` backups for each file.
- Older backups can be deleted manually after review.
- Do not automatically read backup files as project context.

<!-- CODEx_END: backup_rules -->

## Time-Stamp Format

<!-- CODEx_START: timestamp_format -->
*Updated: 2026-05-08 12:05*

Use this timestamp format for Markdown update blocks:

```text
*Updated: YYYY-MM-DD HH:MM*
```

Use this date-time format for CSV rows:

```text
YYYY-MM-DD HH:MM
```

CSV files should include:

- `last_updated`
- `change_note`

`last_updated` records when the row was last changed.

`change_note` records why the row was created or changed.

<!-- CODEx_END: timestamp_format -->

## Incremental Update Rules

<!-- CODEx_START: incremental_update_rules -->
*Updated: 2026-05-08 12:05*

Future updates should follow these rules:

- Read only the files needed for the requested task.
- Follow `docs/guides/cli-operating-rules.md` when deciding which documents to read.
- Check `docs/request-solution-log.md` for recent project-level decisions when the task changes direction, workflow, schema, tool access, or backup/reporting rules.
- Do not automatically read files inside `backup/`.
- For Markdown files, update only relevant `CODEx` blocks when possible.
- For CSV files, keep existing columns unless the user approves a structure change.
- When changing a CSV row, update `last_updated` and `change_note`.
- Add a short entry to `docs/request-solution-log.md` for important user requirements and handling decisions.
- Keep updates concise.
- Do not overwrite conflicting content without noting the conflict or asking for approval.

Suggested conflict note:

```text
MANUAL REVIEW NEEDED:
This requested update may conflict with existing project rules.
Reason: [short explanation]
```

<!-- CODEx_END: incremental_update_rules -->

## Safe Update Workflow

<!-- CODEx_START: safe_update_workflow -->
*Updated: 2026-05-11 00:00*

Use this process for safe updates:

1. Identify the task type.
2. Read only the files recommended in `docs/guides/cli-operating-rules.md`.
3. Create timestamped backups only when the task is a key checkpoint under the backup rules.
4. Update only relevant files and blocks.
5. Add or update the `*Updated: YYYY-MM-DD HH:MM*` line.
6. For CSV changes, update `last_updated` and `change_note`.
7. Add or update `docs/request-solution-log.md` when the request should be remembered by future sessions.
8. Verify the changed files.
9. Summarize what changed.

<!-- CODEx_END: safe_update_workflow -->

## Manual Rollback

<!-- CODEx_START: manual_rollback -->
*Updated: 2026-05-08 12:05*

If an update is wrong, restore a backup manually.

Steps:

1. Open the `backup/` folder.
2. Find the backup file with the correct timestamp.
3. Copy the backup file.
4. Rename it back to the original filename.
5. Replace the incorrect current file.

Example:

```text
backup/README_20260508_120532.md
```

Can be manually restored as:

```text
README.md
```

Do not delete backups until you are sure the current version is correct.

<!-- CODEx_END: manual_rollback -->
