<!-- DOC_META
lifecycle:  long-term
audience:   both
write_when: 计划内容变更时更新
read_when:  执行项目优化任务前读取
delete_when: 计划完成后归档到 archive/
-->
# Project Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize Ron Group Lead Research MVP project structure for better maintainability and clarity.

**Architecture:** Restructure directories, clean up documentation, update file references, preserve all functionality.

**Tech Stack:** Python, PowerShell, Markdown

---

## Pre-Implementation Checklist

- [ ] Verify source project exists at `E:\AI\TestProject-v2`
- [ ] Create backup of current state
- [ ] Verify all scripts are syntactically correct

---

## Task 1: Create New Directory Structure

**Files:**
- Create: `scripts/extraction/`
- Create: `scripts/analysis/`
- Create: `scripts/utils/`
- Create: `docs/architecture/`
- Create: `docs/workflows/`
- Create: `docs/guides/`
- Create: `docs/logs/archive/`

- [ ] **Step 1: Create extraction scripts directory**

```bash
mkdir -p E:/AI/TestProject-v2/scripts/extraction
```

- [ ] **Step 2: Create analysis scripts directory**

```bash
mkdir -p E:/AI/TestProject-v2/scripts/analysis
```

- [ ] **Step 3: Create utils scripts directory**

```bash
mkdir -p E:/AI/TestProject-v2/scripts/utils
```

- [ ] **Step 4: Create architecture docs directory**

```bash
mkdir -p E:/AI/TestProject-v2/docs/architecture
```

- [ ] **Step 5: Create workflows docs directory**

```bash
mkdir -p E:/AI/TestProject-v2/docs/workflows
```

- [ ] **Step 6: Create guides docs directory**

```bash
mkdir -p E:/AI/TestProject-v2/docs/guides
```

- [ ] **Step 7: Create logs archive directory**

```bash
mkdir -p E:/AI/TestProject-v2/docs/logs/archive
```

- [ ] **Step 8: Verify directory structure**

```bash
find E:/AI/TestProject-v2 -type d | sort
```

Expected: All new directories created.

---

## Task 2: Move Extraction Scripts

**Files:**
- Move: `scripts/extract_public_contact_candidates.py` → `scripts/extraction/`
- Move: `scripts/build_form_kp_candidate_queue.py` → `scripts/extraction/`
- Move: `scripts/generate_kp_search_tasks.py` → `scripts/extraction/`
- Move: `scripts/generate_kp_form_queries.py` → `scripts/extraction/`
- Move: `scripts/build_au_review_queue.py` → `scripts/extraction/`

- [ ] **Step 1: Move extract_public_contact_candidates.py**

```bash
mv E:/AI/TestProject-v2/scripts/extract_public_contact_candidates.py E:/AI/TestProject-v2/scripts/extraction/
```

- [ ] **Step 2: Move build_form_kp_candidate_queue.py**

```bash
mv E:/AI/TestProject-v2/scripts/build_form_kp_candidate_queue.py E:/AI/TestProject-v2/scripts/extraction/
```

- [ ] **Step 3: Move generate_kp_search_tasks.py**

```bash
mv E:/AI/TestProject-v2/scripts/generate_kp_search_tasks.py E:/AI/TestProject-v2/scripts/extraction/
```

- [ ] **Step 4: Move generate_kp_form_queries.py**

```bash
mv E:/AI/TestProject-v2/scripts/generate_kp_form_queries.py E:/AI/TestProject-v2/scripts/extraction/
```

- [ ] **Step 5: Move build_au_review_queue.py**

```bash
mv E:/AI/TestProject-v2/scripts/build_au_review_queue.py E:/AI/TestProject-v2/scripts/extraction/
```

- [ ] **Step 6: Verify extraction directory**

```bash
ls -la E:/AI/TestProject-v2/scripts/extraction/
```

Expected: 5 Python files moved successfully.

---

## Task 3: Move Analysis Scripts

**Files:**
- Move: `scripts/build_boss_report.py` → `scripts/analysis/`

- [ ] **Step 1: Move build_boss_report.py**

```bash
mv E:/AI/TestProject-v2/scripts/build_boss_report.py E:/AI/TestProject-v2/scripts/analysis/
```

- [ ] **Step 2: Verify analysis directory**

```bash
ls -la E:/AI/TestProject-v2/scripts/analysis/
```

Expected: 1 Python file moved successfully.

---

## Task 4: Move Utility Scripts

**Files:**
- Move: `scripts/check_capability_inventory.py` → `scripts/utils/`
- Move: `scripts/start_dashboard.ps1` → `scripts/utils/`
- Move: `scripts/install_codex_notification_permission.ps1` → `scripts/utils/`
- Move: `scripts/notify_user.ps1` → `scripts/utils/`
- Move: `scripts/notify_user_persistent.ps1` → `scripts/utils/`

- [ ] **Step 1: Move check_capability_inventory.py**

```bash
mv E:/AI/TestProject-v2/scripts/check_capability_inventory.py E:/AI/TestProject-v2/scripts/utils/
```

- [ ] **Step 2: Move start_dashboard.ps1**

```bash
mv E:/AI/TestProject-v2/scripts/start_dashboard.ps1 E:/AI/TestProject-v2/scripts/utils/
```

- [ ] **Step 3: Move install_codex_notification_permission.ps1**

```bash
mv E:/AI/TestProject-v2/scripts/install_codex_notification_permission.ps1 E:/AI/TestProject-v2/scripts/utils/
```

- [ ] **Step 4: Move notify_user.ps1**

```bash
mv E:/AI/TestProject-v2/scripts/notify_user.ps1 E:/AI/TestProject-v2/scripts/utils/
```

- [ ] **Step 5: Move notify_user_persistent.ps1**

```bash
mv E:/AI/TestProject-v2/scripts/notify_user_persistent.ps1 E:/AI/TestProject-v2/scripts/utils/
```

- [ ] **Step 6: Verify utils directory**

```bash
ls -la E:/AI/TestProject-v2/scripts/utils/
```

Expected: 5 files moved successfully.

---

## Task 5: Move Documentation Files

**Files:**
- Move: `docs/project-overview.md` → `docs/architecture/`
- Move: `docs/lead-table-fields.md` → `docs/architecture/`
- Move: `docs/lead-collection-workflow.md` → `docs/workflows/`
- Move: `docs/lead-enrichment-workflow.md` → `docs/workflows/`
- Move: `docs/dashboard-guide.md` → `docs/guides/`
- Move: `docs/chinese-user-guide.md` → `docs/guides/`
- Move: `docs/iteration-setup.md` → `docs/guides/`
- Move: `docs/cli-operating-rules.md` → `docs/guides/`
- Move: `docs/codex-agent-usage.md` → `docs/guides/`

- [ ] **Step 1: Move project-overview.md to architecture**

```bash
mv E:/AI/TestProject-v2/docs/project-overview.md E:/AI/TestProject-v2/docs/architecture/
```

- [ ] **Step 2: Move lead-table-fields.md to architecture**

```bash
mv E:/AI/TestProject-v2/docs/lead-table-fields.md E:/AI/TestProject-v2/docs/architecture/
```

- [ ] **Step 3: Move lead-collection-workflow.md to workflows**

```bash
mv E:/AI/TestProject-v2/docs/lead-collection-workflow.md E:/AI/TestProject-v2/docs/workflows/
```

- [ ] **Step 4: Move lead-enrichment-workflow.md to workflows**

```bash
mv E:/AI/TestProject-v2/docs/lead-enrichment-workflow.md E:/AI/TestProject-v2/docs/workflows/
```

- [ ] **Step 5: Move dashboard-guide.md to guides**

```bash
mv E:/AI/TestProject-v2/docs/dashboard-guide.md E:/AI/TestProject-v2/docs/guides/
```

- [ ] **Step 6: Move chinese-user-guide.md to guides**

```bash
mv E:/AI/TestProject-v2/docs/chinese-user-guide.md E:/AI/TestProject-v2/docs/guides/
```

- [ ] **Step 7: Move iteration-setup.md to guides**

```bash
mv E:/AI/TestProject-v2/docs/iteration-setup.md E:/AI/TestProject-v2/docs/guides/
```

- [ ] **Step 8: Move cli-operating-rules.md to guides**

```bash
mv E:/AI/TestProject-v2/docs/cli-operating-rules.md E:/AI/TestProject-v2/docs/guides/
```

- [ ] **Step 9: Move codex-agent-usage.md to guides**

```bash
mv E:/AI/TestProject-v2/docs/codex-agent-usage.md E:/AI/TestProject-v2/docs/guides/
```

- [ ] **Step 10: Verify docs structure**

```bash
find E:/AI/TestProject-v2/docs -name "*.md" | sort
```

Expected: All documentation files moved to appropriate subdirectories.

---

## Task 6: Archive Old Logs

**Files:**
- Archive: `docs/request-solution-log.md` (entries older than 30 days)

- [ ] **Step 1: Identify entries to archive**

Read `docs/request-solution-log.md` and identify entries older than 2026-04-18 (30 days ago).

- [ ] **Step 2: Create archive file**

Create `docs/logs/archive/request-solution-log-2026-04.md` with entries from April 2026.

- [ ] **Step 3: Create current log file**

Create `docs/logs/changelog.md` with entries from May 2026 (last 30 days).

- [ ] **Step 4: Update original file**

Update `docs/request-solution-log.md` to reference the archive and current log.

- [ ] **Step 5: Verify archive structure**

```bash
ls -la E:/AI/TestProject-v2/docs/logs/
ls -la E:/AI/TestProject-v2/docs/logs/archive/
```

Expected: Archive and current log files created.

---

## Task 7: Update File References in README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read current README.md**

Read the file and identify all file path references.

- [ ] **Step 2: Update script references**

Update all references to moved scripts:
- `scripts/extract_public_contact_candidates.py` → `scripts/extraction/extract_public_contact_candidates.py`
- `scripts/build_form_kp_candidate_queue.py` → `scripts/extraction/build_form_kp_candidate_queue.py`
- `scripts/generate_kp_search_tasks.py` → `scripts/extraction/generate_kp_search_tasks.py`
- `scripts/generate_kp_form_queries.py` → `scripts/extraction/generate_kp_form_queries.py`
- `scripts/build_au_review_queue.py` → `scripts/extraction/build_au_review_queue.py`
- `scripts/build_boss_report.py` → `scripts/analysis/build_boss_report.py`
- `scripts/check_capability_inventory.py` → `scripts/utils/check_capability_inventory.py`
- `scripts/start_dashboard.ps1` → `scripts/utils/start_dashboard.ps1`

- [ ] **Step 3: Update documentation references**

Update all references to moved documentation:
- `docs/project-overview.md` → `docs/architecture/project-overview.md`
- `docs/lead-table-fields.md` → `docs/architecture/lead-table-fields.md`
- `docs/lead-collection-workflow.md` → `docs/workflows/lead-collection-workflow.md`
- `docs/lead-enrichment-workflow.md` → `docs/workflows/lead-enrichment-workflow.md`
- `docs/dashboard-guide.md` → `docs/guides/dashboard-guide.md`
- `docs/cli-operating-rules.md` → `docs/guides/cli-operating-rules.md`
- `docs/codex-agent-usage.md` → `docs/guides/codex-agent-usage.md`

- [ ] **Step 4: Update Folder Structure section**

Update the folder structure diagram in README.md to reflect new organization.

- [ ] **Step 5: Verify README.md**

Read the updated file and verify all references are correct.

---

## Task 8: Update File References in AGENTS.md

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Read current AGENTS.md**

Read the file and identify all file path references.

- [ ] **Step 2: Update documentation references**

Update all references to moved documentation files.

- [ ] **Step 3: Update command references**

Update all command references to use new script paths.

- [ ] **Step 4: Verify AGENTS.md**

Read the updated file and verify all references are correct.

---

## Task 9: Update File References in current-progress.md

**Files:**
- Modify: `docs/current-progress.md`

- [ ] **Step 1: Read current file**

Read the file and identify all file path references.

- [ ] **Step 2: Update references**

Update all references to moved files.

- [ ] **Step 3: Verify current-progress.md**

Read the updated file and verify all references are correct.

---

## Task 10: Update Python Script Imports

**Files:**
- Modify: All Python scripts that import from moved files

- [ ] **Step 1: Identify import dependencies**

Search for imports between scripts:
```bash
grep -r "import\|from" E:/AI/TestProject-v2/scripts/ --include="*.py"
```

- [ ] **Step 2: Update import paths**

If any scripts import from moved files, update the import paths.

- [ ] **Step 3: Verify imports**

Run Python syntax check on all scripts:
```bash
cd E:/AI/TestProject-v2
.\.venv\Scripts\python -m py_compile scripts/extraction/*.py
.\.venv\Scripts\python -m py_compile scripts/analysis/*.py
.\.venv\Scripts\python -m py_compile scripts/utils/*.py
```

Expected: All scripts compile successfully.

---

## Task 11: Update .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Read current .gitignore**

Read the file and check if any paths need updating.

- [ ] **Step 2: Update paths if needed**

If any ignored paths reference moved directories, update them.

- [ ] **Step 3: Verify .gitignore**

Read the updated file and verify all paths are correct.

---

## Task 12: Create Documentation Index

**Files:**
- Create: `docs/README.md`

- [ ] **Step 1: Create docs README**

Create a documentation index file that lists all documentation with descriptions and locations.

```markdown
# Documentation Index

## Architecture
- [Project Overview](architecture/project-overview.md) - Business background and MVP scope
- [Lead Table Fields](architecture/lead-table-fields.md) - CSV schema and field definitions

## Workflows
- [Lead Collection](workflows/lead-collection-workflow.md) - Lead discovery workflow
- [Lead Enrichment](workflows/lead-enrichment-workflow.md) - Contact enrichment workflow

## Guides
- [Dashboard Guide](guides/dashboard-guide.md) - Dashboard usage instructions
- [CLI Operating Rules](guides/cli-operating-rules.md) - Agent behavior rules
- [Codex Agent Usage](guides/codex-agent-usage.md) - Codex configuration guide
- [Chinese User Guide](guides/chinese-user-guide.md) - Chinese user instructions
- [Iteration Setup](guides/iteration-setup.md) - Backup and iteration setup

## Logs
- [Changelog](logs/changelog.md) - Recent changes (last 30 days)
- [Archive](logs/archive/) - Archived older logs

## Planning
- [Optimization Design](superpowers/specs/2026-05-18-project-optimization-design.md) - Design document
- [Implementation Plan](superpowers/plans/2026-05-18-project-optimization.md) - This plan
```

- [ ] **Step 2: Verify docs README**

Read the created file and verify all links are correct.

---

## Task 13: Final Verification

**Files:**
- Verify: All files in new locations

- [ ] **Step 1: Verify directory structure**

```bash
find E:/AI/TestProject-v2 -type d | sort
```

Expected: All new directories created.

- [ ] **Step 2: Verify script locations**

```bash
find E:/AI/TestProject-v2/scripts -name "*.py" -o -name "*.ps1" | sort
```

Expected: All scripts in correct subdirectories.

- [ ] **Step 3: Verify documentation locations**

```bash
find E:/AI/TestProject-v2/docs -name "*.md" | sort
```

Expected: All documentation in correct subdirectories.

- [ ] **Step 4: Verify file references**

```bash
grep -r "scripts/extract_public_contact_candidates" E:/AI/TestProject-v2/*.md E:/AI/TestProject-v2/docs/*.md
```

Expected: No references to old paths.

- [ ] **Step 5: Run Python syntax check**

```bash
cd E:/AI/TestProject-v2
.\.venv\Scripts\python -m py_compile scripts/extraction/*.py
.\.venv\Scripts\python -m py_compile scripts/analysis/*.py
.\.venv\Scripts\python -m py_compile scripts/utils/*.py
```

Expected: All scripts compile successfully.

- [ ] **Step 6: Verify data integrity**

```bash
wc -l E:/AI/TestProject-v2/data/*.csv
```

Expected: Same row counts as before optimization.

---

## Post-Implementation Checklist

- [ ] All files accessible from new locations
- [ ] No broken references in documentation
- [ ] All scripts compile successfully
- [ ] Data files intact
- [ ] Dashboard still functional
- [ ] Git repository clean

---

## Rollback Plan

If issues are found:

1. Restore from backup: `E:\AI\TestProject-v2-backup`
2. Identify the specific issue
3. Fix the issue
4. Re-run verification

---

## Success Criteria

- [ ] All files accessible from new locations
- [ ] No broken references
- [ ] All scripts compile
- [ ] Data integrity preserved
- [ ] Documentation organized
- [ ] Project structure clear and maintainable
