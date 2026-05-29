<!-- DOC_META
lifecycle:  long-term
audience:   both
write_when: 项目规则、工作流、工具配置变更时更新
read_when:  每次会话启动时读取（AGENTS.md 之后）
delete_when: 不删除
-->
# Project Instructions

## Entry Rule

**Before any task, read `AGENTS.md` first.** It defines the operating rules, task-specific context file lists, documentation rules, and safety boundaries. Follow its "Read First" section before acting.

**Then read `docs/current-progress.md`.** It contains the latest project status, data snapshot, what has been done, what needs to be done next, and what the user needs to do. Without it you will be working blind.

## Project Overview
This is a B2B lead research project for Australian restaurant/hotel industry. The goal is to collect contact information for key decision makers to support supplier outreach.

## Core Workflow Rules

### Rule 1: Company Information Collection Threshold

**STOP collecting company info when ANY of these conditions are met:**
- Found contact page URL
- Found at least 1 email address
- Found at least 1 phone number
- Found LinkedIn company page
- Searched 3 pages with no new discoveries

**DO NOT continue searching if:**
- All above items are already in `data/leads.csv`
- The lead already has `contact_research_status` = "已找到联系路径"

### Rule 2: Key Person (KP) Search Trigger

**Start searching for KP ONLY when:**
- Company info is complete (email, phone, or contact page found)
- No key person identified yet
- Company has team/about page (indicates larger organization)

**DO NOT search for KP if:**
- Lead already has `key_contact_name` in `data/leads.csv`
- Lead already has contact in `data/contacts.csv`
- Company is sole proprietor (contact_person field already filled)

### Rule 3: KP Search Investment Limits

**STOP searching for KP when ANY of these conditions are met:**
- Time spent > 5 minutes on single lead
- Pages searched > 3 with no new findings
- Ratio of unhelpful pages > 70%
- Found KP name but cannot verify contact method

**ABANDON KP search and mark as "低优先级" if:**
- All above limits reached
- No LinkedIn profile found after 2 search attempts
- Company appears to have no public team page

### Rule 3b: Multi-KP Discovery (重要)

**每家公司尽可能找到多个KP和对接人：**
- 不要只找一个KP就停止
- 团队/About页面上的所有决策者都应记录
- 每个KP都需要尝试找到：邮箱、电话、LinkedIn、社交媒体
- LinkedIn 个人URL如果找不到，至少生成搜索URL供人工审核

**KP优先级：**
1. 直联邮箱（firstname.lastname@domain）→ 高价值
2. 直联手机（04xx）→ 高价值
3. LinkedIn 个人主页URL → 中价值
4. LinkedIn 搜索URL（供人工确认）→ 低价值但有用
5. 公司邮箱（info@, hello@）→ 低价值，但仍需记录
6. 公司电话（1300/1800）→ 低价值

**LinkedIn处理规则：**
- 找到个人URL → 直接保存到 contacts.linkedin_url
- 找不到个人URL → 生成搜索URL保存，标记为"待人工确认"
- 不要尝试自动登录LinkedIn或抓取个人页面内容

### Rule 4: Duplicate Prevention

**BEFORE any extraction, check existing data:**
1. Load `data/contacts.csv` - check contact names, emails, phones
2. Load `data/leads.csv` - check contact_person, email_address, phone_number, key_contact_*
3. Skip any candidate that already exists

**Use `--skip-existing` flag (default: true) when running extraction scripts**

### Rule 5: Decision Flowchart

```
START
  │
  ▼
[Load existing data from data/]
  │
  ▼
[Company Info Collection]
  │
  ├─► Found email/phone/contact page?
  │     ├─ YES → Mark "已找到联系路径" → Check KP
  │     └─ NO → Continue search (max 3 pages)
  │              └─ No result → Mark "需人工确认" → NEXT LEAD
  │
  ▼
[Check Key Person]
  │
  ├─► Already have KP in contacts.csv?
  │     ├─ YES → Skip, NEXT LEAD
  │     └─ NO → Start KP search
  │
  ▼
[KP Search]
  │
  ├─► Found KP name?
  │     ├─ YES → Try to find contact (email/phone/LinkedIn)
  │     │        ├─ Found → Save to contacts.csv → NEXT LEAD
  │     │        └─ Not found (5min/3pages) → Mark "已识别联系人" → NEXT LEAD
  │     └─ NO → Continue search (max 5 minutes)
  │              └─ Timeout → Mark "低优先级" → NEXT LEAD
  │
  ▼
[NEXT LEAD]
```

### Rule 6: Data Quality Standards

**Email classification:**
- `info@`, `admin@`, `contact@` → company_email (low value)
- `sales@`, `procurement@`, `accounts@` → department_email (medium value)
- `firstname.lastname@` → person_email (high value)
- `firstname@` → person_email (medium value, verify)

**Phone classification:**
- 1300/1800 numbers → company_phone (low value)
- Landline (02/03/07/08) → company_phone (medium value)
- Mobile (04xx) → person_phone (high value)

**Confidence levels:**
- High: Verified person contact (name + title + direct contact)
- Medium: Likely person contact (name + role match)
- Low: Company/department contact only

### Rule 6b: CloakBrowser + Scrapling 联动配置

**用于绕过 Google 429、Cloudflare 等反爬：**

```python
# CloakBrowser — 始终用于 Google 搜索
from scripts.kp_pipeline.cloak_fetcher import cloak_fetch, search_google, smart_fetch, close_browser

# Google 搜索（始终用 CloakBrowser，不走 Scrapling）
results = search_google("company name director", max_results=5)

# 智能抓取（Scrapling 优先，CloakBrowser 兜底 + cookie 传递）
text, html, status, error, tool = smart_fetch(url, timeout=15)

# 直接用 CloakBrowser（绕过 Scrapling 无法处理的站点）
text, html, cookies, ua, status, error = cloak_fetch(url, timeout=30)

# 用完关闭浏览器
close_browser()
```

**已知限制：**
- Cloudflare 挑战页（如 Swillhouse）即使 CloakBrowser 也返回 403
- LinkedIn 搜索页需要登录，无法绕过
- `gstatic.com` 静态资源会被 CloakBrowser 抓取（不影响功能）
- Scrapling TLS 错误的站点（如 Fink Group）可用 CloakBrowser 兜底
- 大型餐饮集团官网通常不公开决策者直联信息，公司页面抓取对小型公司更有效

**关键约束：**
- Google 搜索**必须**用 `search_google()` 或 `cloak_fetch()`，不能用 `smart_fetch()`（会被 429）
- CloakBrowser 使用同步 `launch()` API，不要用 `asyncio.run()` 或 `nest_asyncio`
- Scrapling 传 cookies/UA 用 `headers` 参数，不是 `extra_headers`

### Rule 7: Script Usage

**Standard extraction command:**
```bash
python scripts/extraction/extract_public_contact_candidates.py \
  --input reports/round1-queue.csv \
  --skip 0 \
  --limit 10 \
  --follow-links 3 \
  --fetcher static \
  --skip-existing \
  --output-prefix "round-N-"
```

**Always use `--skip-existing` to avoid duplicate work**

### Rule 8: Report Review Priority

**Review candidates in this order:**
1. `key_person_name` (score 85-89) - Verify before saving
2. `email` with person patterns (score 100-114) - Classify and save
3. `phone` with mobile pattern (score 90-94) - Verify and save
4. `contact_form` (score 88) - Verify it's actual contact form
5. `team_link` / `contact_link` (score 68-76) - Manual review for KP

**DO NOT save without review:**
- LinkedIn URLs (need person/company fit verification)
- Role context snippets (need name/title confirmation)
- Company emails (need department classification)

### Rule 9: Data File Safety

**Master data files are append-only:**
- `data/leads.csv` and `data/contacts.csv` — only append new qualified records, never delete or overwrite existing ones
- Before writing: backup original → dry-run → generate merge report → confirm record count only increases
- Filtered-out data must be written to `reports/rejected-{timestamp}.csv`, never silently deleted
- Unverifiable data: mark `needs_review`, do not delete

**Dedup and cleaning scope:**
- Only operate on new data; never scan the full master table and delete historical records
- Dedup compares new data against existing data; existing records are never modified

**Country detection:**
- Do not use domain suffix as the sole country indicator
- Many Australian companies use `.com`, `.net.au`, `.io` — not just `.com.au`

**Batch quality control:**
- Define qualification criteria before running search tasks
- Track valid rate per batch (qualified / total)
- If valid rate < 50%: pause batch expansion, optimize keywords/filtering, report valid rate and suggestions

**Must pause for user confirmation:**
- Delete or overwrite existing records in master tables
- `git checkout` / `restore` / `reset` / `reset --hard` on data files
- Master table record count decreases
- Switch task zones (A ↔ B)
- Valid rate < 50% but batch would continue

### Rule 10: Run Report Generation

**每轮任务跑完后必须生成报告（表单收集、KP 富化、关键词发现等）：**
- 脚本：`scripts/reports/generate_run_report.py`
- 输出目录：`D:\TestProject-v3\reports\`
- 报告内容：进度快照、亮点、问题（可选）、系统优化（可选）
- 用 `--title` 区分任务类型，`--task` 描述本次具体任务
- 报告仅用于人类观察，agent 不需要回读
- 使用 `--auto-stats` 自动从 CSV 读取跑后统计

## Tools and Workflows

### Dashboard (线索补全台)

Local review/edit tool for leads and contacts.

```bash
# Start local server (required for CSV loading)
cd D:\TestProject-v3 && python -m http.server 8765
# Open: http://localhost:8765/dashboard/
```

- Loads `data/leads.csv` and `data/contacts.csv` automatically
- Filter by country, missing fields, search
- Edit company info, key person, contacts
- Export updated CSV

### KP Pipeline (半自动化管线)

Three-stage pipeline for key person discovery and enrichment.

```bash
# Run all stages
python -m scripts.kp_pipeline.run_pipeline --limit 50 --stage all

# Run single stage
python -m scripts.kp_pipeline.run_pipeline --stage 2 --limit 20
```

**Stage 1 (KP 发现):** Reuses existing scripts to extract KP candidates from web.
**Stage 2 (直联富化):** Takes leads with KP name but missing direct contact → scrapes sitemap + company pages → finds email/phone.
**Stage 3 (验证门控):** Scores candidates → auto-approve (≥85) / auto-reject (<30) / human review (30-85).

Metrics stored in `data/kp_metrics.json`, validation log in `data/kp_validation_log.csv`.

### Extraction Scripts

```bash
# Build candidate queue
python scripts/extraction/build_form_kp_candidate_queue.py

# Run extraction with dedup
python scripts/extraction/extract_public_contact_candidates.py \
  --input reports/queue.csv --skip 0 --limit 10 \
  --follow-links 3 --fetcher static --skip-existing
```

## File Structure

```
data/
  leads.csv              # Master lead list (DO NOT modify directly)
  contacts.csv           # Verified contacts (review before adding)
  kp_metrics.json        # Pipeline run metrics (append-only)
  kp_validation_log.csv  # Human review decisions
  keyword_runs.csv       # Search keyword tracking
  search_keywords.csv    # Keyword definitions

dashboard/
  index.html             # 线索补全台 (start http server to use)
  app.js                 # Dashboard logic
  style.css              # Dashboard styles

reports/
  kp-pipeline-run-*.md   # Pipeline run reports
  round*-*.csv           # Extraction candidates (review before saving)
  round*-*.md            # Human-readable reports

scripts/
  kp_pipeline/           # KP enrichment pipeline
    config.py            # Load config from config/kp_pipeline.json
    stage2_enrich.py     # Direct contact enrichment (sitemap + scrape)
    stage3_validate.py   # Validation gate (score/route)
    metrics.py           # Metrics collection
    run_pipeline.py      # Pipeline orchestrator
  extraction/            # Data extraction scripts
  search/                # Search keyword generation
  workflow_checker.py    # Threshold enforcement and duplicate check

config/
  kp_pipeline.json       # Pipeline stage settings and thresholds
  workflow_rules.json    # Existing workflow thresholds
```

### Data Provenance & Recovery

When data is lost or corrupted, check the recovery sources below. The "recovery source" column lists files that contain a snapshot or superset of the data.

| Master File | Written By | Flows To | Recovery Source |
|---|---|---|---|
| `data/leads.csv` | extraction scripts, keyword_discovery.py, manual edits | contacts.csv (via lead_id), dashboard, reports | git history |
| `data/contacts.csv` | extraction scripts, KP pipeline, manual edits | dashboard, reports | git history |
| `data/search_keywords.csv` | import_suggestions.py, manual edits | scheduler, generator | git history |
| `data/keyword_runs.csv` | tracker.py | scheduler, market_intel | git history |
| `data/kp_metrics.json` | metrics.py | pipeline reports | git history |
| `data/kp_validation_log.csv` | stage3_validate.py | pipeline reports | git history |

**Recovery checklist:**
1. Check `git log` and `git show` for committed versions
2. Check `reports/` for extraction results and merge records
3. Check `data/*.bak.*` for pre-operation backups
4. Check `data/contacts.csv` for cross-references via lead_id

## Critical Reminders

1. **Master data files are append-only** — See Rule 9. Exception: machine-generated public-source company routes and KP candidates may be appended to `data/leads.csv` or `data/contacts.csv` with source, confidence/status, and uncertainty notes (per AGENTS.md Operating Rules). Never delete or overwrite existing records without user confirmation.
2. **ALWAYS check existing data before extraction**
3. **STOP when thresholds are reached - don't over-invest**
4. **Mark status accurately for next agent**
5. **Document why you skipped or abandoned a lead**
6. **Use dashboard for human review, not raw CSV editing**
7. **ALWAYS clean up test artifacts after running scripts** — Run `git status` after every script execution. Delete temp files (`temp_*`, `test_*`, `debug_*`). Remove test-generated CSV/MD from project root. Report "task complete" only after confirming no stray files remain.
8. **Hooks are active** — `.claude/settings.json` enforces: (a) destructive command blocking, (b) post-script artifact check, (c) DOC_META check on new .md files, (d) pre-exit stray file check. If Stop hook blocks you, clean up stray files before trying again.
9. **Record Blockers** — Any blocker where the same issue is attempted 2–3 times with no progress must be handled in order: **(1) Classify** the blocker using the `[MAJOR-SUBCATEGORY]` tag from `docs/logs/changelog.md`; **(2) Lookup** the "Historical Blocker Index" table — if a matching tag exists, apply the recorded Fix directly instead of re-debugging; **(3) Solve and Record** — if no match, debug normally, then append a new entry with Symptom / Root Cause / Fix / Best Practice and update the index table.
