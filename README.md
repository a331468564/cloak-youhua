<!-- DOC_META
lifecycle:  long-term
audience:   both
write_when: 项目结构、功能、技术栈重大变更时更新
read_when:  新用户/新 agent 了解项目时读取
delete_when: 不删除
-->
# Ron Group Lead Research MVP

<!-- CODEx_START: project_index -->
*Updated: 2026-05-12 12:10*

## Purpose

This project is a local MVP for Ron Group to collect, organize, review, and enrich potential B2B customer leads in the restaurant and hospitality industry.

The main goal is lead collection and contact enrichment for future outreach. The dashboard is now a lightweight manual fill tool for reviewing country-level lead gaps and exporting updated CSV files.

The current active focus is Australia first. The near-term workflow should prioritize Australia restaurant and hotel final customers, key-person contact discovery, and a repeatable process that can later become a local tool.

The CSV and dashboard now separate company-level contact channels from key contact person information so outreach readiness is easier to judge. The current dashboard should stay simple: country filter first, then manual filling of missing company contact, form, and key-person fields.

## Folder Structure

```text
project-folder/
  README.md
  data/
    leads.csv
    contacts.csv
    search_keywords.csv
    keyword_runs.csv
    outreach_log.csv
  dashboard/
    index.html
    app.js
    style.css
  docs/
    architecture/
      project-overview.md
      lead-table-fields.md
    workflows/
      lead-collection-workflow.md
      lead-enrichment-workflow.md
    guides/
      dashboard-guide.md
      iteration-setup.md
      cli-operating-rules.md
      codex-agent-usage.md
      chinese-user-guide.md
    request-solution-log.md
    current-progress.md
  scripts/
    extraction/
      extract_public_contact_candidates.py
      build_form_kp_candidate_queue.py
      generate_kp_search_tasks.py
      generate_kp_form_queries.py
      build_au_review_queue.py
    analysis/
      build_boss_report.py
    utils/
      check_capability_inventory.py
      start_dashboard.ps1
  backup/
  exports/
  reports/
  skills/
```

## Specialized Documentation

- `docs/architecture/project-overview.md`: Business background, target customers, and MVP scope.
- `docs/workflows/lead-collection-workflow.md`: Lead discovery workflow and public-source rules.
- `docs/workflows/lead-enrichment-workflow.md`: Contact enrichment workflow and stopping rules.
- `docs/architecture/lead-table-fields.md`: `leads.csv` fields, statuses, scoring, and value rules.
- `docs/guides/dashboard-guide.md`: Local country-based dashboard fill/export workflow.
- `docs/guides/iteration-setup.md`: Backups, timestamps, update tags, and rollback.
- `docs/guides/cli-operating-rules.md`: Which files Codex should read for each task type.
- `docs/guides/codex-agent-usage.md`: Codex agent usage patterns and best practices.
- `docs/guides/chinese-user-guide.md`: Chinese-language user guide for the project.
- `docs/request-solution-log.md`: Concise record of important user requests and CLI/Codex handling plans.
- `docs/current-progress.md`: Current project state, next work, and commands for resuming.

## Current Data Files

- `data/leads.csv`: Lead records and enrichment status.
- `data/contacts.csv`: Person-level contact records linked to `leads.csv` by `lead_id`.
- `data/search_keywords.csv`: Search keyword templates for lead discovery.
- `data/keyword_runs.csv`: Keyword run and batch tracking.
- `data/outreach_log.csv`: Future outreach conflict-prevention template. Do not fill it until outreach is actually planned or sent.

## Project Tools

- `dashboard/index.html`, `dashboard/app.js`, `dashboard/style.css`: Manual fill dashboard for reviewing country-level lead gaps, editing company/contact fields, and exporting canonical CSV files.
- `scripts/utils/start_dashboard.ps1`: Starts the local dashboard server so the browser can read default CSV files.
- `scripts/extraction/build_au_review_queue.py`: Auxiliary historical Australia review queue; this segmentation path is paused unless explicitly requested.
- `scripts/extraction/build_form_kp_candidate_queue.py`: Builds the current Australia form/KP queue from existing CSV data and marks missing form, KP, or direct-contact gaps.
- `scripts/extraction/generate_kp_search_tasks.py`: Builds direct KP search-task queues from existing leads, prioritizing Australia restaurant/hotel final-customer candidates, known KP names, official-site queries, PDF/news queries, and LinkedIn manual-review entry points.
- `scripts/extraction/generate_kp_form_queries.py`: Generates KP form queries for lead enrichment.
- `scripts/extraction/extract_public_contact_candidates.py`: Uses Scrapling static, dynamic, or stealth fetching to extract candidate emails, phones, contact/team links, LinkedIn URLs, and role snippets from queued official websites. Supports one-level same-domain link follow-up and outputs candidate evidence for CSV registration with confidence/status notes.
- `scripts/analysis/build_boss_report.py`: Builds boss-level summary reports from lead data.
- `scripts/utils/check_capability_inventory.py`: Checks whether the current computer has the project capabilities needed for the current workflow and suggests setup commands when something is missing.
- `requirements.txt`: Python package inventory for recreating the project-local extraction environment.
- Project-local `.venv`: Preferred Python environment for newly installed tools. Do not use global C: drive installs when the tool can run from the project directory.
- Project-local `.ms-playwright`: Preferred Playwright browser directory. Use `PLAYWRIGHT_BROWSERS_PATH` to keep browser binaries outside C: when possible.
- Project-local `.codex/tools/mcp-notifications`: Node/npm MCP server used for lightweight desktop notifications from Codex. `node_modules` is ignored; reinstall with `npm.cmd install --prefix .codex\tools\mcp-notifications @topvisor/mcp-notifications` if needed.
- Scrapling `Fetcher`: Static public-page extraction to reduce manual page reading and token usage. Installed in `.venv`.
- Scrapling `DynamicFetcher`: Browser extraction for pages that need JavaScript rendering. Uses project-local Playwright Chromium.
- Scrapling `StealthyFetcher`: Stealth browser extraction for approved high-capability runs with anti-ban controls. Uses project-local Playwright/Patchright dependencies.
- Playwright / Chromium: Browser runtime used by Scrapling dynamic and stealth fetchers. Installed under `.ms-playwright`.
- `data/search_keywords.csv` and `data/keyword_runs.csv`: Keyword and batch-control tracking for repeatable discovery tests.
- `reports/*.md` and `reports/*.csv`: Batch outputs, candidate queues, test results, and evidence summaries.
- `docs/request-solution-log.md`: Required task-end log for important requests, tool decisions, workflow changes, file-changing tasks, and future operating context.
- `.codex/config.toml` and `.codex/hooks/*.py`: Project-local Codex hooks for selected guardrails: destructive command blocking, request-log reminders, current-progress threshold warnings, script compile checks, capability inventory reminders, high-capability extraction scope warnings, and UTF-8 Markdown checks.

## Capability Setup

Use the project-local environment first:

```powershell
cd E:\AI\TestProject-v2
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:PLAYWRIGHT_BROWSERS_PATH='E:\AI\TestProject-v2\.ms-playwright'
.\.venv\Scripts\python -m playwright install chromium
.\.venv\Scripts\python scripts\utils\check_capability_inventory.py
```

When moving to another computer, run the inventory check first. If a task fails repeatedly and the existing tools are not enough, evaluate adding a new tool, skill, library, or language and record it in this section plus `docs/request-solution-log.md`.

## Current Operating Priority

- Market: Australia first.
- Customer focus: restaurant and hotel final customers first.
- Contact focus: key-person email first, key-person phone second, company-level contact paths after that.
- Tool goal: turn the proven Australia search, scoring, KP enrichment, CSV update, and reporting workflow into a repeatable local tool.

## Resume This Project

From PowerShell:

```powershell
cd E:\AI\TestProject-v2
git pull
codex "Read README.md, docs/current-progress.md, docs/request-solution-log.md, docs/guides/cli-operating-rules.md, docs/workflows/lead-enrichment-workflow.md, and docs/workflows/lead-collection-workflow.md first. Then continue the current Ron Group Australia restaurant/hotel lead toolization work. You may iterate automatically inside the approved task scope, but do not start a new business collection or enrichment iteration beyond that scope without explicit approval."
```

## Local Dashboard

Start the dashboard through the local server so the browser can read the default CSV files:

```powershell
cd E:\AI\TestProject-v2
.\scripts\utils\start_dashboard.ps1
```

Then use `http://localhost:8765/dashboard/`. The dashboard supports manual filling of missing company contact, form, key-person, and all linked contact fields, then exports canonical `leads.csv` and `contacts.csv` files with editor name, timestamp, and change notes. It does not collect leads, enrich contacts automatically, send emails, log in to platforms, or call AI APIs.

<!-- CODEx_END: project_index -->
