---
paths:
  - "data/**"
---

# Data File Safety Rules

## Core Rule: Append-Only

Master data files are append-only. Never delete or overwrite existing records.

- `data/leads.csv` and `data/contacts.csv` — only append new qualified records.
- Before writing: backup original → dry-run → generate merge report → confirm record count only increases.
- Filtered-out data must be written to `reports/rejected-{timestamp}.csv`, never silently deleted.
- Unverifiable data: mark `needs_review`, do not delete.

## Dedup and Cleaning Scope

- Only operate on new data; never scan the full master table and delete historical records.
- Dedup compares new data against existing data; existing records are never modified.

## Country Detection

- Do not use domain suffix as the sole country indicator.
- Many Australian companies use `.com`, `.net.au`, `.io` — not just `.com.au`.

## Batch Quality Control

- Define qualification criteria before running search tasks.
- Track valid rate per batch (qualified / total).
- If valid rate < 50%: pause batch expansion, optimize keywords/filtering, report valid rate and suggestions.

## Must Pause for User Confirmation

- Delete or overwrite existing records in master tables.
- `git checkout` / `restore` / `reset` / `reset --hard` on data files.
- Master table record count decreases.
- Valid rate < 50% but batch would continue.

## Data Operation Defaults

**Auto-execute (no confirmation needed):**
- Read/search/write raw files
- Clean and dedup new data only
- Write rejected files, mark needs_review
- Backup, dry-run, generate diff/merge report
- Append new qualified records without touching existing ones

**Must pause for confirmation:**
- Delete or overwrite existing records in master tables
- Modify non-empty fields in existing records
- Switch task zones (A ↔ B)

## Auto-Merge Conditions (all must be met)

- Operation only appends new qualified records
- No delete, overwrite, or modification of existing records
- Master table backed up
- Dry-run completed with merge report generated
- Rejected file generated (if any disqualified data)
- Valid rate ≥ 50%
- Post-merge record count = original count + new qualified records (only increase)

## Data Provenance & Recovery

| Master File | Written By | Recovery Source |
|---|---|---|
| `data/leads.csv` | extraction scripts, keyword_discovery.py | git history |
| `data/contacts.csv` | extraction scripts, KP pipeline | git history |
| `data/search_keywords.csv` | import_suggestions.py, manual edits | git history |
| `data/keyword_runs.csv` | tracker.py | git history |
| `data/kp_metrics.json` | metrics.py | git history |
| `data/kp_validation_log.csv` | stage3_validate.py | git history |

**Recovery checklist:**
1. Check `git log` and `git show` for committed versions
2. Check `reports/` for extraction results and merge records
3. Check `data/*.bak.*` for pre-operation backups
4. Check `data/contacts.csv` for cross-references via lead_id
