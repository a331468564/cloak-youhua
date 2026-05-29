# CLI Operating Rules

<!-- CODEx_START: task_context_rules -->
*Updated: 2026-05-11 00:00*

## Purpose

This file tells future Codex tasks which project files to read.

The goal is to reduce unnecessary context, avoid token waste, and prevent dashboard tasks from mixing with lead collection or enrichment tasks.

The main project goal remains collecting and enriching potential customer contact information for outreach.

When starting Codex from this project folder, treat `AGENTS.md` as the entry instruction file, then read this file before choosing task-specific context. For Codex hook, agent, config, startup, or CLI behavior work, also read `docs/codex-agent-usage.md` before editing files or running troubleshooting commands.

For project-level tasks, workflow changes, tool decisions, schema changes, backup/reporting changes, or unclear direction, read `docs/request-solution-log.md` first or after the task-specific context files.

Before finishing any task-oriented conversation, check whether `docs/request-solution-log.md` needs an entry or an update. Add one in the same turn if the conversation changed files, project rules, workflow decisions, data standards, tool behavior, or future operating context.

<!-- CODEx_END: task_context_rules -->

<!-- CODEx_START: request_log_autowrite_rule -->
*Updated: 2026-05-13 00:00*

## Request Log Autowrite Rule

Codex should treat `docs/request-solution-log.md` updates as a default part of finishing any task that changes project files, project rules, workflow decisions, data standards, tool behavior, or future operating context.

Default behavior:

- Write or update the request-log entry in the same turn as the change.
- Use the existing entry format with `Achievements` and `Issues / limits`. When encountering a blocker (debugging > 5 minutes), use the blocker taxonomy format `[MAJOR-SUBCATEGORY]` from the top of `docs/logs/changelog.md` and update the "Historical Blocker Index" table.
- Keep the entry concise and durable; do not record routine read-only checks, tiny lookups, or casual clarifications that do not affect future work.
- If a task spans several related changes in the same turn, prefer one concise entry over multiple fragmented entries.

Exceptions:

- Do not update the request log when the user explicitly says not to.
- Do not update the request log when the user explicitly limits the task to a specific file or file set that does not include `docs/request-solution-log.md`, such as "only modify `.codex/hooks/post_tool_hook.py`".
- If the user later asks why the log was not updated or asks for log coverage, explain the scope limit and offer to add the missing entry.

Hook policy:

- Codex hooks may remind or draft metadata, but they should not silently edit `docs/request-solution-log.md`.
- The assistant is responsible for the final request-log wording because it must reflect the user request, handling plan, result, achievements, issues, and follow-up.
- Runtime hook logs belong in `.codex/logs/*.jsonl`; durable project decisions belong in `docs/request-solution-log.md`.

<!-- CODEx_END: request_log_autowrite_rule -->

<!-- CODEx_START: alignment_and_clarification_rule -->
*Updated: 2026-05-09 16:28*

## Alignment and Clarification Rule

When a task affects project direction, tool access, lead quality standards, outreach readiness, account risk, or what "good enough" means, do not silently guess if the answer is unclear.

Ask the user a concise clarification question before proceeding when:

- The business goal or target customer definition is ambiguous.
- A tool may require account access, platform authorization, paid service, or risk to an existing account.
- The user asks to change quality thresholds, scoring rules, or outreach-readiness rules.
- A record could be saved in multiple ways and the choice affects later outreach.
- The available evidence is too weak to decide whether a company or person should be treated as a real lead/KP.

For routine CSV updates, official-source enrichment, backups, reports, and dashboard/export work, continue using reasonable assumptions and document them in `change_note`, `enrichment_notes`, or the batch report.

<!-- CODEx_END: alignment_and_clarification_rule -->

<!-- CODEx_START: format_preservation_rules -->
*Updated: 2026-05-13 00:00*

## Format Preservation Rules

Preserve the original format of user input and project content by default.

Do not proactively evaluate whether another format is theoretically better. Do not spend extra reasoning on format optimization, presentation rewrites, or uncertain token savings.

Only adjust expression format when one of these triggers is clearly present:

- Context boundaries may be confused: the same input contains content with different permission levels or different purposes, such as a user task, external reference, project source text, error log, constraints, or expected output. In this case, use only minimal boundary labels to distinguish source and purpose. Do not rewrite the content. If headings, lists, code blocks, or quote blocks already make the boundaries clear, do not add XML labels.
- Repeated structure is obvious: many records share the same fields, repeated field names take meaningful space, compact representation preserves the field/value mapping, and no downstream consumer requires the original format or JSON. Do not compact small examples or unclear structures.
- Downstream machine parsing is clearly required: the user, script, API, database, test, automation flow, or existing project interface explicitly requires JSON, schema, CSV, YAML, fixed fields, or another strict structure.

These do not count as machine-parsing requirements:

- The content would merely look clearer in JSON or another structure.
- The content is complex.
- The agent prefers a more structured internal representation.
- The agent wants to organize its own reasoning.

When uncertain, keep the original format. When uncertain whether a format saves tokens, keep the original format. When uncertain whether downstream parsing is required, do not output strict structured formats. If Markdown is already clear enough, do not add another XML, JSON, YAML, or schema layer.

Project-specific applications:

- For `data/*.csv`, preserve schemas, field names, row counts, and current value style unless the user explicitly approves a migration or an existing script/interface requires a fixed format.
- For `docs/*.md`, preserve the existing Markdown structure and CODEx blocks. Do not rewrite whole sections only to make them look cleaner.
- For command output, error logs, hook logs, and diffs, summarize briefly by default. Read or show long details only when debugging or when the user explicitly asks.
- For Codex hooks, keep quiet-by-default behavior: no full event JSON, full diffs, full file contents, or long logs in stdout/stderr; runtime details belong in `.codex/logs/*.jsonl`.
- For reports and candidate records, use the existing project report/CSV conventions when scripts or prior workflow expect them. Do not switch to JSON only because it seems more structured.

<!-- CODEx_END: format_preservation_rules -->

<!-- CODEx_START: auto_issue_iteration_boundary -->
*Updated: 2026-05-12 12:10*

## Auto Issue Detection and Iteration Boundary

Codex may automatically identify problems during a task, record concise findings, and run bounded follow-up iterations inside the already approved task scope when the action does not change project direction, expand account risk, or lower/raise lead quality standards.

Allowed without extra approval:

- Note data quality issues, weak evidence, duplicate risk, missing fields, or low-yield query patterns.
- Record the issue in the relevant `change_note`, `enrichment_notes`, batch report, or `docs/request-solution-log.md` when it is important for future sessions. Blockers taking > 5 minutes to debug must use the `[MAJOR-SUBCATEGORY]` format from `docs/logs/changelog.md`.
- Propose the next iteration, including candidate leads, query patterns, review order, or report improvements.
- Within the approved task scope, retry failed commands, adjust scripts, refine ranking/deduplication, regenerate reports, rerun small verification tests, and update documentation/logs.
- If the same problem survives more than two serious attempts, evaluate whether a new tool, skill, library, runtime, or language is needed under the Capability Inventory Rules.

Not allowed without explicit user authorization:

- Start a new business collection/enrichment iteration that expands beyond the current approved task scope.
- Change target market, target customer priority, scoring thresholds, outreach-readiness rules, or source confidence rules.
- Use account-based, paid, login-only, automated social-platform, broad crawler, stealth/proxy/anti-bot, or otherwise risky tools.
- Make large CSV changes or schema changes outside the current approved task.

Practical rule: automatically record problems and keep iterating on implementation, testing, extraction quality, and documentation inside the approved task. Ask again before expanding the business scope, changing standards, using a newly risky access mode, or writing broad source-data changes.

Once the user explicitly approves a high-capability extraction mode, Codex may use it only within the approved scope. The approval should state or imply the target domains/URLs, batch size, allowed tool mode, output files, review boundary, account owner/authorization, rate limit, cooldown, and ban-risk stop conditions. If the run encounters account warnings, forced verification, temporary blocks, rate-limit errors, unexpected payment/access-control barriers, credential requests, or data the user is not authorized to access, stop and ask again before continuing.

Ban prevention is the main operational risk boundary for approved authenticated, proxy, stealth, CAPTCHA-handling, paid-source, or platform-account runs. Do not optimize for maximum scraping volume; optimize for small, reviewable batches and account survival.

<!-- CODEx_END: auto_issue_iteration_boundary -->

<!-- CODEx_START: documentation_revision_standard -->
*Updated: 2026-05-12 12:45*

## Documentation Revision Standard

When Codex discovers a project rule problem, workflow ambiguity, documentation issue, encoding issue, repeated data-quality issue, or tool limitation, record it in the most relevant active Markdown file so future sessions can treat the fix as the current standard.

Use this placement rule:

- Project direction, workflow boundaries, tool access, and revision standards: `docs/cli-operating-rules.md`.
- Codex hook setup, hook command format, and hook troubleshooting details: `docs/codex-agent-usage.md`.
- Current status, immediate next work, and resume context: `docs/current-progress.md`.
- Important user requests and the Codex handling/result: `docs/request-solution-log.md`.
- Dashboard usage or local browser/CSV behavior: `docs/dashboard-guide.md`.
- Collection rules and query/batch behavior: `docs/lead-collection-workflow.md`.
- Keyword scheduler operations and keyword-driven discovery: `docs/guides/keyword-scheduler-guide.md`.
- Enrichment, contact confidence, KP, and outreach-readiness rules: `docs/lead-enrichment-workflow.md`.
- Field definitions, canonical values, and CSV registration rules: `docs/lead-table-fields.md`.

Do not leave important findings only in chat. If the finding affects future operation, add a concise note to the corresponding Markdown file and add a short entry to `docs/request-solution-log.md` when the request or fix changes project behavior.

For Chinese Markdown files on Windows, preserve UTF-8 readability. If PowerShell displays mojibake, verify with `Get-Content -Raw -Encoding UTF8` before assuming the file content is corrupted.

<!-- CODEx_END: documentation_revision_standard -->

<!-- CODEx_START: csv_operations_rules -->
*Updated: 2026-05-22*

## CSV 数据操作规范

批量导入联系人或线索时，遵循以下规则避免数据丢失：

**字段名验证（必须）：**
- 写入前先检查：`fields = list(csv.DictReader(open(file, encoding='utf-8-sig')).fieldnames)`
- 不要假设字段名。leads.csv 和 contacts.csv 的字段名可能与脚本输出不同
- 常见错误：`source` → 实际是 `source_type`；`confidence` → 实际是 `contact_confidence`；`created_at` → 实际是 `last_researched_date`

**编码：**
- 所有 `data/*.csv` 使用 UTF-8 BOM 编码
- 读写均用 `encoding='utf-8-sig'`
- 不指定编码会导致首列字段名带 `﻿` 前缀，匹配失败

**导入顺序：**
1. 先将新公司写入 `data/leads.csv`，获取 `LEAD-xxx` ID
2. 建立旧 ID → 新 ID 映射表（如 `NEW-xxx → LEAD-xxx`）
3. 再保存联系人到 `data/contacts.csv`，使用映射后的 lead_id
4. 写入后立即读回验证，防止静默丢失

**ID 生成：**
- 使用独立计数器，不要在循环内用 `len(contacts) + i` 计算
- 示例：`counter = len(existing_contacts)` 然后每条 `counter += 1`
- 批量写入后检查是否有重复 contact_id

**公司名匹配：**
- 统一用 `.strip().lower()` 比较
- 注意缩写差异（如 "Fink" vs "Fink Group"），必要时人工确认
- 匹配失败时 lead_id 为空，联系人将无法关联到 AU 线索

**通用邮箱过滤：**
- generic 集合应包含：`info, hello, admin, contact, enquiry, enquiries, sales, office, reception, reservations, events, functions, bookings, careers, media, marketing, accounts, feedback, support, help, team, general, hr, press, partnerships, private, groups, catering, noreply, no-reply, donotreply, webmaster, postmaster`
- role_prefixes 集合应包含：`concierge, recruitment, jobs, eat, stringers, main, inbound, tenders, suppliers, stay, book, connect, collab, groundcontrol, chef, projects`
- 编码邮箱（如 `h1587-fb@accor.com`）：前缀含连续数字的跳过

<!-- CODEx_END: csv_operations_rules -->

<!-- CODEx_START: schema_migration_rule -->
*Updated: 2026-05-25*

## Schema 迁移规范

重命名或废弃 CSV 字段时，必须完成迁移闭环：

1. **写迁移脚本** — 一次性脚本把旧字段值搬到新字段，清空旧字段
2. **验证无数据丢失** — 迁移后检查：新字段有值的行数 ≥ 旧字段原行数，不存在「旧字段有值、新字段无值」的孤儿行
3. **保留列头** — 清空旧字段的值，但保留 CSV 列头，避免已有脚本因列数变化报错
4. **更新 fallback 代码** — 所有读取旧字段的地方，确认新字段已有数据后再移除 fallback

不要依赖「文档标注 deprecated」代替实际迁移。不写迁移脚本，旧字段就会被新代码继续写入，重复数据越积越多。

<!-- CODEx_END: schema_migration_rule -->

<!-- CODEx_START: context_checkpoint_rules -->
*Updated: 2026-05-12 12:45*

## Context Checkpoint Rules

Codex usually cannot rely on a stable exact "context left" number from the CLI. When an exact context budget is visible, update progress and notify the user once the remaining context is around 80% or lower after meaningful work has started. If the remaining context approaches a low level, update progress immediately before continuing.

When the exact budget is not visible, estimate conservatively from:

- Many large Markdown/CSV/script reads in one session.
- Long diffs, long command output, or many report files opened.
- Multiple implementation/test/documentation loops in one conversation.
- Any sign that a context compaction or account/session handoff may happen soon.

Checkpoint action:

- Rewrite `docs/current-progress.md` as the latest compact handoff state.
- Add or update `docs/request-solution-log.md` when project behavior, workflow, tools, standards, source data, or handoff context changed.
- Tell the user that a checkpoint was written and what the next step is.

`docs/current-progress.md` is a rolling handoff file, not an append-only history. After a new session has read the current handoff and durable decisions have been preserved in `docs/request-solution-log.md` or the relevant active rule/workflow docs, stale progress details may be deleted or condensed. Each update should replace old progress with the current state, immediate next plan, and only the reports/files still needed for continuation.

Do not update `docs/current-progress.md` for every routine task or early small iteration. For ordinary task work that changes files, tools, workflow behavior, or future operating context, add the durable record to `docs/request-solution-log.md` only. Update `docs/current-progress.md` only when there is a real checkpoint need, such as account/session handoff, context-budget risk, a completed meaningful stage, a major data/tool milestone, or a new immediate next plan that future sessions need to resume without rereading chat.

<!-- CODEx_END: context_checkpoint_rules -->

<!-- CODEx_START: capability_inventory_rules -->
*Updated: 2026-05-12 11:10*

## Capability Inventory Rules

New tools should be installed into the project directory or another non-C: drive location when technically possible. Use a global C: drive install only when a core runtime requires it or when the user explicitly approves it.

For Python tools, prefer:

- project-local `.venv`
- `requirements.txt`
- project-local browser/runtime caches such as `.ms-playwright`

When adding a tool, script, skill, library, runtime, browser, or computer language, update the project capability inventory:

- `README.md` Project Tools / Capability Setup
- `requirements.txt` or the relevant setup file
- `scripts/utils/check_capability_inventory.py` when the tool can be checked automatically
- `docs/request-solution-log.md` for the user request, handling plan, result, and follow-up

When a problem survives more than two serious attempts with the existing capabilities, stop treating it as only an execution issue. Evaluate whether the project needs a new tool, skill, library, runtime, or language. If yes, propose or add the capability, then record why it was added and how future sessions should check for it.

When moving this project to another computer, run `scripts/utils/check_capability_inventory.py` from the project-local Python environment before continuing operational work.

<!-- CODEx_END: capability_inventory_rules -->

<!-- CODEx_START: codex_hook_config_rules -->
*Updated: 2026-05-12 17:30*

## Codex Hook Config Rules

Before modifying `.codex/config.toml` or user-level Codex hook config, confirm the active Codex version's supported TOML structure and compare against `docs/codex-agent-usage.md`.

Do not copy Claude Code hook array syntax into Codex:

```toml
[[hooks]]
event = "PreToolUse"
command = "..."
```

Codex hook config should use event-grouped tables plus nested hook entries, for example:

```toml
[[hooks.PreToolUse]]
matcher = "^(Bash|PowerShell|shell_command)$"

[[hooks.PreToolUse.hooks]]
type = "command"
command = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "& .\.venv\Scripts\python.exe .\.codex\hooks\safety_hook.py"'
```

If Codex startup reports `invalid type: sequence, expected struct HooksToml in hooks`, check for forbidden Claude-style patterns:

```powershell
Select-String -Path .\.codex\config.toml -Pattern '\[\[hooks\]\]|event\s*='
```

Correct result: no output. Fix any matches before continuing normal CLI work.

<!-- CODEx_END: codex_hook_config_rules -->

<!-- CODEx_START: confirmed_business_priorities -->
*Updated: 2026-05-09 17:25*

## Confirmed Business Priorities

For the current Australia lead workflow, prioritize key-person discovery over raw lead volume or general contact forms.

First-stage outreach should focus on restaurant and hotel final customers rather than fit-out, design, procurement, or supplier/partner companies.

Public search results, public The Org pages, and public LinkedIn-visible evidence may be saved as Low or Medium confidence key-person candidates when the source is recorded and the uncertainty is documented.

The strongest contact standard is a key person with at least an email address, preferably with phone as well. Company email, company phone, and company contact forms are secondary because general inboxes are less likely to receive useful replies, especially for larger companies.

<!-- CODEx_END: confirmed_business_priorities -->

<!-- CODEx_START: simplification_rule -->
*Updated: 2026-05-11 17:00*

## Simplification Rule

Do not add more dashboard complexity, review segmentation, or classification layers unless the user explicitly requests them.

For the current toolization stage, focus on:

- Search query generation.
- Official company contact forms.
- Form/KP discovery.
- Lightweight CSV update helpers.
- Batch report generation.

Keep outputs simple enough to review quickly. Treat complex final-customer/supplier segmentation as auxiliary evidence, not the main workflow.

<!-- CODEx_END: simplification_rule -->

<!-- CODEx_START: report_precedence_rule -->
*Updated: 2026-05-09 18:06*

## Report Precedence Rule

Historical reports in `reports/`, `exports/`, and dated batch reports under `docs/` are evidence of what happened in earlier runs.

They do not override current active rules in:

- `README.md`
- `docs/project-overview.md`
- `docs/lead-collection-workflow.md`
- `docs/lead-enrichment-workflow.md`
- `docs/lead-table-fields.md`
- `docs/cli-operating-rules.md`
- active project skills

If a historical report recommends an old next action that conflicts with the current Australia-first, restaurant/hotel final-customer, KP-first direction, follow the current active docs or ask the user before changing direction.

This also applies to CSV registration policy. Older reports or request-log entries that say "review before saving" describe the earlier stricter workflow. The current rule is candidate-evidence-first registration: machine-generated public-source company routes and KP candidates may be saved to `data/leads.csv` or `data/contacts.csv` with source, confidence/status, and uncertainty notes, then excluded or upgraded during outreach-time human review.

<!-- CODEx_END: report_precedence_rule -->

<!-- CODEx_START: lead_collection_context -->
*Updated: 2026-05-08 12:05*

## Lead Collection Tasks（表单收集）

For form-based lead collection tasks（已知公司名，找联系人），read only:

- `README.md`
- `docs/project-overview.md`
- `docs/lead-collection-workflow.md`
- `docs/lead-table-fields.md`
- `data/search_keywords.csv`
- `data/leads.csv`

Do not read dashboard documentation unless the user asks about the dashboard.
Do not read keyword scheduler documentation unless the task is about keyword-driven discovery.

<!-- CODEx_END: lead_collection_context -->

<!-- CODEx_START: keyword_scheduler_context -->
*Updated: 2026-05-21 16:30*

## Keyword Scheduler Tasks（关键词拓展）

For keyword-driven discovery tasks（未知市场发现公司），read only:

- `README.md`
- `docs/guides/keyword-scheduler-guide.md`
- `config/keyword_scheduler.json`
- `config/keyword_dimensions.json`
- `data/search_keywords.csv`
- `data/keyword_runs.csv`

适用场景：
- 生成新关键词候选（generator.py）
- 执行关键词驱动搜索（scheduler.py）
- 分析关键词效果和市场段（market_intel.py）
- 导入审核后的关键词（import_suggestions.py）
- 与 KP Pipeline 联动（--keyword-driven）

Do not read KP Pipeline documentation unless the task also involves Stage 2/3 enrichment.
Do not mix keyword scheduler operations with form-based collection in the same task.

<!-- CODEx_END: keyword_scheduler_context -->

<!-- CODEx_START: lead_enrichment_context -->
*Updated: 2026-05-08 12:05*

## Lead Enrichment Tasks

For lead enrichment tasks, read only:

- `README.md`
- `docs/lead-enrichment-workflow.md`
- `docs/lead-table-fields.md`
- `data/leads.csv`

Do not read dashboard documentation for enrichment tasks.

<!-- CODEx_END: lead_enrichment_context -->

<!-- CODEx_START: dashboard_context -->
*Updated: 2026-05-08 12:05*

## Dashboard Tasks

For dashboard tasks, read only:

- `README.md`
- `docs/dashboard-guide.md`
- `dashboard/index.html`
- `dashboard/app.js`
- `dashboard/style.css`

Do not treat dashboard work as the main project goal. The dashboard is only a read-only support tool for reviewing CSV data.

<!-- CODEx_END: dashboard_context -->

<!-- CODEx_START: backup_iteration_context -->
*Updated: 2026-05-08 12:05*

## Backup or Iteration Tasks

For backup or iteration tasks, read only:

- `README.md`
- `docs/iteration-setup.md`
- `docs/request-solution-log.md`

Do not read old backup files unless the user explicitly asks to restore or compare backups.

<!-- CODEx_END: backup_iteration_context -->

<!-- CODEx_START: separation_rules -->
*Updated: 2026-05-21 16:30*

## Separation Rules

- Do not read `docs/dashboard-guide.md` unless the task is about the dashboard.
- Do not mix dashboard instructions with lead collection instructions.
- Do not mix dashboard instructions with lead enrichment instructions.
- Do not read old backup files unless explicitly requested.
- Do not treat dashboard work as lead collection.
- Do not treat dashboard work as lead enrichment.
- For collection tasks, focus on finding relevant companies.
- For enrichment tasks, focus on finding usable contact methods.
- For dashboard tasks, focus on read-only review and display.
- **Do not mix keyword scheduler tasks with form-based collection tasks.** They are independent workflows with different data sources and outputs.
- For keyword scheduler tasks, focus on keyword selection, template expansion, and search execution.
- For form-based collection tasks, focus on company name search and contact page extraction.

<!-- CODEx_END: separation_rules -->
