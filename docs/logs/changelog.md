<!-- DOC_META
lifecycle:  long-term
audience:   both
write_when: After each important change, append an entry
read_when:  When reviewing historical changes
delete_when: Do not delete (old entries archived to archive/)
-->
# Request and Solution Log - Current Entries

This file contains the current (last 30 days) request and solution log entries.

---

## Blocker Taxonomy

When encountering a blocker (debugging > 5 minutes), classify it using the tag format `[MAJOR-SUBCATEGORY]`. Same-type blockers can be quickly retrieved by tag.

### Blocker Resolution Workflow

When you hit a blocker, follow these steps **in order**:

1. **Classify** — Identify the major category and technical subcategory from the tables below. Pick the closest tag; if none fits exactly, choose the nearest match.
2. **Lookup** — Search the "Historical Blocker Index" table below for the same tag. If a match exists, read the referenced entry and apply the recorded Fix / Best Practice directly — do not re-debug from scratch.
3. **Solve and Record** — If no match exists (or the recorded fix does not apply), debug normally. After resolving, append a new blocker entry using the format template, then add a row to the Historical Blocker Index table.

Skipping step 2 wastes time on already-solved problems. Skipping step 3 means the next session will re-debug the same issue.

### Major Categories

| Tag | Name | Scope |
|-----|------|-------|
| `DATA-FORMAT` | Data Format | CSV/file encoding, quoting, field schema, serialization |
| `NET-FETCH` | Network Fetch | HTTP errors, TLS, rate limiting, anti-bot, JS rendering |
| `TOOL-SCRIPT` | Tool/Script | Python errors, paths, async, hook config |
| `DATA-QUALITY` | Data Quality | Dedup, false positives, encoding corruption, missing fields |
| `WORKFLOW` | Workflow | Rule conflicts, filter logic, state inconsistency |

### Technical Subcategories

| Full Tag | Name | Typical Scenario |
|----------|------|------------------|
| **DATA-FORMAT** | | |
| `DATA-FORMAT-CSV-ENCODING` | CSV Encoding | BOM, utf-8 vs utf-8-sig, line endings |
| `DATA-FORMAT-CSV-QUOTE` | CSV Quoting | QUOTE_ALL vs QUOTE_MINIMAL, fields containing commas |
| `DATA-FORMAT-CSV-FIELDS` | CSV Fields | Field name mismatch, schema change, extra/missing columns |
| `DATA-FORMAT-URL-ENCODE` | URL Encoding | `%64%69` → `di`, `+` → space, `%2B` → `+` |
| `DATA-FORMAT-UNICODE` | Unicode | Special characters, emoji, CJK encoding issues |
| **NET-FETCH** | | |
| `NET-FETCH-TLS-SSL` | TLS/SSL | Certificate errors, handshake failure, openssl invalid |
| `NET-FETCH-HTTP-403` | 403 Forbidden | Cloudflare challenge, WAF block |
| `NET-FETCH-HTTP-429` | 429 Rate Limit | Google throttling, API rate limit |
| `NET-FETCH-JS-RENDER` | JS Rendering | SPA pages, React/Vue without SSR |
| `NET-FETCH-TIMEOUT` | Timeout | Connection timeout, read timeout |
| **TOOL-SCRIPT** | | |
| `TOOL-SCRIPT-PYTHON-IMPORT` | Python Import | Module not found, version incompatibility |
| `TOOL-SCRIPT-PATH-REF` | Path Reference | Path not found, relative/absolute path confusion |
| `TOOL-SCRIPT-ASYNC` | Async Issues | asyncio event loop, nest_asyncio |
| `TOOL-SCRIPT-HOOK-CONFIG` | Hook Config | TOML format error, wrong event name |
| **DATA-QUALITY** | | |
| `DATA-QUALITY-DEDUP` | Dedup | Same company different name, URL variants |
| `DATA-QUALITY-FALSE-POSITIVE` | False Positive | Non-person name identified as KP, non-email extracted |
| `DATA-QUALITY-MISSING-FIELD` | Missing Field | Required field empty, association ID missing |
| `DATA-QUALITY-FILTER` | Filter | Non-target company passed filter, or target company blocked by filter |
| **WORKFLOW** | | |
| `WORKFLOW-RULE-CONFLICT` | Rule Conflict | Multiple document rules contradict each other |
| `WORKFLOW-FILTER-LOGIC` | Filter Logic | Queue filter conditions wrong, threshold不合理 |

### Blocker Entry Format

Each blocker entry must include:

```markdown
`[MAJOR-SUBCATEGORY]` **Blocker Title**
- **Symptom:** What happened
- **Root Cause:** Why it happened
- **Fix:** How it was fixed
- **Best Practice:** How to avoid it next time (one sentence)
```

### Historical Blocker Index

| Tag | Entry | Blocker |
|-----|-------|---------|
| `DATA-FORMAT-CSV-ENCODING` | 2026-05-22 | BOM encoding must use utf-8-sig |
| `DATA-FORMAT-CSV-FIELDS` | 2026-05-22 | Wrong field name assumption caused ValueError |
| `DATA-QUALITY-DEDUP` | 2026-05-22 | Duplicate contact_id, company name mismatch |
| `DATA-QUALITY-FALSE-POSITIVE` | 2026-05-22 | Generic email filtering incomplete |
| `TOOL-SCRIPT-ASYNC` | 2026-05-20 | asyncio.run() killed browser instance |
| `NET-FETCH-TLS-SSL` | 2026-05-20 | Scrapling TLS error needs CloakBrowser fallback |
| `NET-FETCH-HTTP-429` | 2026-05-20 | Google search must use CloakBrowser |
| `DATA-FORMAT-CSV-QUOTE` | 2026-05-26 | QUOTE_ALL overwrote original file format |
| `DATA-FORMAT-URL-ENCODE` | 2026-05-26 | Extraction results contained URL-encoded values needing decode |
| `DATA-QUALITY-FILTER` | 2026-05-28 | 关键词发现脚本过滤器太宽松，53% 新闻/文章误入库 |
| `NET-FETCH-HTTP-429` | 2026-05-28 | 关键词发现跑太多次谷歌搜索触发限流，需控制搜索频率 |

---

### 2026-05-26 — Run 16 Form Collection: Two Data Format Blockers

**Context:** Run 16 form collection batch — full extraction of 105 AU candidates (4 batches, 1772 candidates). Two data format blockers encountered when merging results into leads.csv.

**Blocker Details:**

---

`[DATA-FORMAT-CSV-QUOTE]` **CSV quoting mismatch caused full-file rewrite**

- **Symptom:** After merge script wrote back leads.csv, diff showed every line changed (271 lines full diff), but only 56 lines had actual data changes.
- **Root Cause:** `csv.DictWriter` defaults to `QUOTE_MINIMAL` (only quotes fields containing commas), but the merge script explicitly passed `quoting=csv.QUOTE_ALL`, wrapping every field in quotes. The original file only quoted fields that contained commas.
- **Fix:** Removed the `quoting=csv.QUOTE_ALL` parameter, used default `QUOTE_MINIMAL`. After rewrite, diff showed only the actually changed lines.
- **Best Practice:** When using `csv.DictWriter` to write an existing CSV, first check the original file's quoting style with `head -1 <file> | cat -A`, then decide whether to pass `quoting`. Default (no param) is QUOTE_MINIMAL, consistent with most CSV generators.

---

`[DATA-FORMAT-URL-ENCODE]` **Extraction results contained URL-encoded values without decoding**

- **Symptom:** Dedes Waterfront's `key_contact_email` became `%64%69nin%67@de%64esgro%75%70.com%2ea%75`; Ovolo phone became `%2B61+2+9331+9000`.
- **Root Cause:** Scrapling extracts `href="mailto:..."` and `href="tel:..."` attribute values as URL-encoded strings. The extraction script wrote these raw encoded values into the candidate CSV without decoding. `%64` = `d`, `%69` = `i`, `%2E` = `.`, `%2B` = `+`, `+` = space.
- **Fix:** In the merge script, decode `email` and `phone` candidate values using `urllib.parse.unquote(value).replace("+", " ")` before merging into the master table.
- **Best Practice:** Any value extracted from HTML attributes (href, src, data-*) must be decoded with `unquote()` before storage. `+` in URL query strings means space, but in `mailto:` / `tel:` values it may represent a literal `+` (e.g., international dial code) — use context to decide.

---

**Other findings this run:**

- 13 TLS/SSL errors (Lucas Collective / Parker Group etc.) → `[NET-FETCH-TLS-SSL]` known issue, CloakBrowser fallback
- Merivale returned JS-rendered page → `[NET-FETCH-JS-RENDER]` Scrapling static cannot handle
- Bargroup 403 → `[NET-FETCH-HTTP-403]` Cloudflare challenge

**Files changed:**
- `data/leads.csv` — 56 leads updated, 219 new fields
- `docs/logs/changelog.md` — added blocker taxonomy + this entry
- `docs/current-progress.md` — A-zone data update + Run 16 record
- `docs/request-solution-log.md` — added blocker recording rules
- `AGENTS.md` — Operating Rules: added blocker taxonomy reference
- `docs/guides/cli-operating-rules.md` — Request Log Autowrite Rule + Auto Issue Detection: added blocker taxonomy reference
- `docs/guides/codex-agent-usage.md` — Logging Policy: added changelog.md reference
- `CLAUDE.md` — Critical Reminders: added #9 "Record Blockers"

**Achievements:**
- Full extraction of 105 AU companies, 1772 candidates
- AU KP names 52→78, AU with contact 147→157 (97%)
- New KP leads: Rosy Scatigna (Table For), Jane Hastings (EVT), Harry Singh (Meriton)
- Established blocker taxonomy system, 9 historical blockers tagged and indexed

**Issues / limits:**
- Email count 189→186 slight decrease to investigate (likely dedup logic difference)
- Direct contact count ~61 not significantly increased, Stage 2 enrichment still needed

---

### 2026-05-28 — 关键词发现脚本过滤器质量阻塞

**Context:** 关键词发现脚本第 20 轮运行，15 个关键词发现 49 家公司，有效率仅 12%（6/49）。43 条非目标公司入库（新闻、招聘、大学、国际公司等）。

**阻塞详情：**

---

`[DATA-QUALITY-FILTER]` **关键词发现脚本过滤器太宽松，大量非目标公司入库**

- **症状：** 49 家发现公司中 43 家为非目标（新闻文章、招聘网站、大学、国际公司等），有效率仅 12%。
- **根因：** `_is_restaurant_hotel_page()` 只需 2 个行业关键词就通过，任何提到 "restaurant" 的新闻文章都能通过。无 AU 地理过滤，无文章/目录 URL 检测，无联系信号验证。
- **修复：** 5 项过滤器改进 — (1) 域名排除列表 +120、(2) 文章/目录 URL 模式过滤、(3) AU 查询自动增强（`site:.com.au`）、(4) 联系信号检测、(5) 文章标题检测 + 媒体域名过滤。
- **最佳实践：** 关键词发现脚本的过滤器应分层设计：域名排除 → URL 模式 → 地理验证 → 行业验证 → 联系信号。每层过滤后应统计通过率，有效率低于 50% 时需加强过滤规则。

---

`[NET-FETCH-HTTP-429]` **关键词发现跑太多次谷歌搜索触发限流**

- **症状：** 谷歌搜索返回 0 结果，直接请求返回 HTTP 429。
- **根因：** 单次会话跑 15 个关键词 × 每个关键词抓取 5 个结果页，总计 75+ 次请求，触发谷歌限流。
- **修复：** 等待限流恢复。后续控制单次会话搜索次数（建议 ≤ 30 次请求）。
- **最佳 practice：** 关键词发现脚本应加请求计数器，超过阈值时自动暂停并提示。单次运行建议 ≤ 8 个关键词，每个 ≤ 5 个结果。

---

### 2026-05-22 — 批量联系人导入：问题排查与最佳实践

**Context:** 用户要求将 AU 直联数从 34 提升到 50。执行批次 2 提取结果导入 + 公司页面抓取 + CloakBrowser 深度抓取，过程中遇到多个数据处理问题。

**问题与解决方案：**

1. **CSV 字段名假设错误** — 保存联系人时使用了 `source`、`confidence`、`created_at` 等不存在的字段名，导致 `ValueError: dict contains fields not in fieldnames`。
   - **修复：** 实际字段为 `source_type`、`contact_confidence`、`last_researched_date`。保存前必须先检查 `csv.DictReader.fieldnames`。

2. **NEW-xxx lead ID 未持久化** — 批次 2 提取脚本生成的候选使用 NEW-xxx 前缀 ID，但这些 lead 从未写入 leads.csv，导致关联的联系人 lead_id 为空。
   - **修复：** 先将新公司写入 leads.csv 获取 LEAD-xxx ID，建立 NEW→LEAD 映射表后再保存联系人。

3. **公司名不匹配导致 lead_id 丢失** — 保存 liz@finkgroup.com.au 时，lookup 用 "fink group" 但 leads.csv 中存的是 "Fink"，导致 lead_id 为空。
   - **修复：** 公司名匹配时统一 `.strip().lower()`，但注意原始名称可能有缩写差异，需人工确认。

4. **重复 contact_id** — append 逻辑中 `len(contacts) + len(new_contacts) + 1` 计数器在循环内不递增，导致多个联系人共享同一 ID。CSV 去重时丢失数据。
   - **修复：** 使用独立计数器变量，每保存一条 +1。或保存后重新编号。

5. **通用邮箱过滤不完整** — 初始 generic 集合遗漏了 `recruitment@`、`jobs@`、`concierge@`、`eat@`、`stringers@` 等角色/部门邮箱。
   - **修复：** 扩展 generic 集合，同时新增 `role_prefixes` 集合过滤非人名邮箱。

6. **BOM 编码** — leads.csv 和 contacts.csv 使用 UTF-8 BOM 编码。必须用 `encoding='utf-8-sig'` 读写，否则首列字段名会带 `﻿` 前缀。

**最佳实践（已验证）：**

| 规则 | 说明 |
|------|------|
| **先查字段名再写** | `fields = list(csv.DictReader.fieldnames)` 后再构造 row dict |
| **先存 leads 再存 contacts** | 新公司必须先写入 leads.csv 拿到 lead_id，再保存关联联系人 |
| **公司名匹配用 lower+strip** | `{r['company_name'].strip().lower(): r['lead_id'] for r in leads}` |
| **BOM 编码始终用 utf-8-sig** | `open(..., encoding='utf-8-sig')` 读写均适用 |
| **独立计数器** | 批量 append 时用 `counter = len(existing)` 然后 `counter += 1` |
| **CloakBrowser 兜底 Scrapling** | TLS 错误、403 等 Scrapling 失败时，CloakBrowser 可能成功（如 Fink Group） |
| **保存后验证** | 写入 CSV 后立即读回验证，防止静默丢失 |

**Files changed:**
- `data/leads.csv` — +44 家 AU 公司（LEAD-0205 ~ LEAD-0248）
- `data/contacts.csv` — +17 个联系人（154 总计），去重修复，liz@finkgroup.com.au 补录
- `docs/current-progress.md` — 数据快照更新，直联目标 50 已达成

**Achievements:**
- AU 直联从 34 提升到 **50**（28 人名邮箱 + 22 手机号），目标达成
- 新增 44 家 AU 公司线索
- 验证了公司页面抓取（team/about/contact 路径）的有效性
- 验证了 CloakBrowser 对 Scrapling TLS 错误站点的兜底能力

**Issues / limits:**
- 大型餐饮集团（Merivale/Australian Venue Co/Oscars Group 等）官网不公开决策者直联信息
- Google 搜索 KP 姓名+公司的方式效率极低（71 人搜索仅 1 个有效邮箱）
- 部分站点 TLS 错误（Scrapling 和 CloakBrowser 均失败）

---

### 2026-05-21 — 全局 request-solution-log 钩子

**Context:** 用户希望所有项目自动记录人机对话摘要，每 5 轮对话触发一次，避免遗漏重要请求和方案变更。

**What was done:**

1. **全局钩子脚本** — `~/.claude/hooks/auto_request_solution_log.py`，PostToolUse 事件（空 matcher，匹配所有工具调用）。通过 `~/.claude/.rslog_counter.json` 计数，每 10 次工具调用（约 5 轮对话）触发提醒。

2. **自动发现日志文件** — 按优先级查找：`docs/request-solution-log.md` → `docs/logs/changelog.md` → `docs/changelog.md` → `request-solution-log.md`。找不到则提醒创建。

3. **全局 settings.json 注册** — `~/.claude/settings.json` 新增 PostToolUse 钩子，对所有项目生效。

**Files changed:**
- `C:\Users\Administrator\.claude\hooks\auto_request_solution_log.py` (new)
- `C:\Users\Administrator\.claude\settings.json` — 注册全局钩子
- `docs/current-progress.md` — 钩子表更新为 6 个，补充 request-solution-log 闭环说明

**Issues / limits:**
- 钩子只能提醒，不能自动生成摘要（摘要需要对话上下文，钩子无法获取）
- 计数基于工具调用次数，非精确轮次（一轮对话可能触发 2-5 次工具调用）

---

### 2026-05-20 — CloakFetcher 4 个阻塞 bug 修复

**Context:** CloakBrowser + Scrapling 深度联动集成后，代码审查发现 4 个阻塞问题：(1) `asyncio.run()` 每次创建新事件循环导致 Playwright 浏览器实例失效；(2) Google 搜索走了 Scrapling 而非 CloakBrowser；(3) Scrapling 的 `extra_headers` 参数名错误导致 cookies/UA 从未传递；(4) Google 搜索结果 URL 提取格式过时。

**What was done:**

1. **Event Loop 生命周期修复** — `cloak_fetcher.py` 改用 `cloakbrowser.launch()` 同步 API，移除 `asyncio`/`nest_asyncio` 依赖。全局 `_browser` 实例在进程内复用，无事件循环绑定问题。

2. **Google 搜索路由修复** — `search_google()` 直接调用 `cloak_fetch()` 而非 `smart_fetch()`，确保 Google 始终走 CloakBrowser 绕过 429。

3. **Scrapling headers 参数修复** — `scrapling_fetch()` 中 `extra_headers` → `headers`，cookies/UA 现在正确传递给 Scrapling。

4. **Google 结果 URL 提取适配** — 新增格式 2 支持：直接 href + `srsltid` 参数的有机结果链接（Google 已不再使用 `/url?q=` 重定向格式）。过滤所有 `*.google.com` 和 `*.googleapis.com` 域名。

5. **路由表清理** — 移除 `data/fetch_routes.json` 中错误的 `google.com: scrapling_ok` 条目。

**Files changed:**
- `scripts/kp_pipeline/cloak_fetcher.py` — 重写，4 个修复
- `data/fetch_routes.json` — 移除 google.com 条目

**Test results:**
- CloakBrowser 同步 API：3 次连续调用全部 200 ✓
- Scrapling headers 传递：200 ✓
- Google 搜索：5 个结果，无 google.com 泄漏 ✓
- 管线 Stage 2（5 家）：全部 200，无 429 ✓

**Issues / limits:**
- `gstatic.com` 静态资源被 CloakBrowser 抓取（不影响功能，轻微性能损耗）
- Swillhouse Cloudflare 403 仍无法绕过（已知限制）

---

### 2026-05-20 — AGENTS.md 精简、进度文档重写、会话重量钩子

**Context:** 用户在新窗口测试时发现：(1) current-progress.md 的下一步方向没写具体文件路径，新 agent 不知道去哪找；(2) AGENTS.md 的 Read First 列了 8 个文件太重，新 agent 不知道哪些必读哪些按需；(3) 长会话导致 context 压缩，agent 遗忘具体数据，需要机制提醒换窗口。

**What was done:**

1. **AGENTS.md Read First 精简** — 从「8 个文件全部必读」改为「3 个必读 + 按需参考表」。必读：current-progress.md、project-overview.md、cli-operating-rules.md。按需表覆盖全部 11 个活跃文档，每个都有对应触发任务。

2. **current-progress.md 全中文重写** — 数据表格化（AU 线索富化进度、联系人概况）。下一步方向拆为「Agent 可执行」和「需用户配合」两部分。LinkedIn 搜索 URL 列出具体公司和联系人。门控指标评估提出 3 个用户问题。

3. **更新规则明确化** — current-progress.md 新增「更新规则」一节：管线跑完 / 数据变化 5+ / 用户确认 / 工具变更 / 方向调整时必须更新，小改不动。AGENTS.md 同步写明触发条件。

4. **AGENTS.md 冗余清理** — 删除 Documentation Rules 节（和按需参考表重复）、删除 extraction test 命令（任务级命令，非启动规则）。从 112 行减到 ~100 行。

5. **新增文件规则** — AGENTS.md 新增：不许随意新增 .md，必须加 DOC_META、更新 docs/README.md 索引、临时文件必须清理。

6. **会话重量钩子** — 新增 `.claude/hooks/context_freshness_check.py`，PostToolUse (Bash) 事件触发。通过 `.claude/.session_counter` 计数工具调用，15 次首次警告，之后每 5 次重复。stop_check.py 联动：15+ 调用且未更新 current-progress.md 则阻止结束。

7. **docs/README.md 更新** — 补充 KP 管线计划文档索引。

**Files changed:**
- `AGENTS.md` — Read First 重写、Operating Rules 补充钩子说明
- `docs/current-progress.md` — 全文重写
- `docs/README.md` — 补充索引
- `.claude/hooks/context_freshness_check.py` (new)
- `.claude/hooks/stop_check.py` — 新增会话重量检查
- `.claude/settings.json` — 注册新钩子
- `docs/guides/codex-agent-usage.md` — 钩子表和配置示例更新

**Achievements:**
- 新 agent 启动只需读 3 个文件就能干活
- current-progress.md 有具体的下一步方向和用户待办
- 会话过重时自动提醒，Stop 钩子强制更新进度

**Issues / limits:**
- 会话重量阈值（15 次）是估计值，实际需要根据使用体验调整
- 计数文件跨会话靠 mtime 判断（2 小时过期），如果用户间隔 2 小时继续同一任务会重置

---

### 2026-05-20 — Hook System, Document Lifecycle, Project Cleanup

**Context:** User requested that all MD documents be tagged with lifecycle metadata, and that new agent sessions follow the same rules. Audit revealed broken path references, missing enforcement mechanisms, and test artifact pollution.

**What was done:**

1. **DOC_META metadata** — Added `<!-- DOC_META -->` comment blocks to all ~80 MD files in the project, marking lifecycle (long-term/temporary), audience (agent/user/both), write_when, read_when, delete_when.

2. **Path fixes** — Corrected all bare `docs/` references to use correct subdirectory paths (`docs/architecture/`, `docs/workflows/`, `docs/guides/`). Fixed `E:\AI\Codex\TestProject` → `E:\AI\TestProject-v2` in README.md, dashboard-guide.md, codex-agent-usage.md, check_capability_inventory.py. Fixed SKILL.md broken paths.

3. **Hook system** — Created `.claude/settings.json` with 4 hooks:
   - `pre_bash_safety.py` — blocks destructive commands (rm -rf, git reset --hard)
   - `post_bash_check.py` — checks for test artifacts after Python script execution
   - `post_write_check.py` — checks new .md files for DOC_META
   - `stop_check.py` — blocks agent from finishing if stray files exist

4. **Project cleanup** — Archived 50+ old reports to `reports/archive/` and `docs/logs/archive/`. Removed temp files.

5. **Documentation updates** — CLAUDE.md (Rule 7 cleanup, Rule 8 hooks), cli-operating-rules.md (hook enforcement table), codex-agent-usage.md (Claude Code Hooks section), current-progress.md (full update).

6. **Data write rule unification** — CLAUDE.md Rule 1 now has exception clause aligning with AGENTS.md.

7. **Dashboard port fix** — CLAUDE.md corrected from 8080 to 8765.

**Files changed:**
- `.claude/settings.json` (new)
- `.claude/hooks/pre_bash_safety.py` (new)
- `.claude/hooks/post_bash_check.py` (new)
- `.claude/hooks/post_write_check.py` (new)
- `.claude/hooks/stop_check.py` (new)
- `CLAUDE.md`, `AGENTS.md`, `README.md`, `docs/README.md`
- `docs/guides/cli-operating-rules.md`, `codex-agent-usage.md`, `dashboard-guide.md`, `chinese-user-guide.md`, `iteration-setup.md`
- `docs/workflows/lead-enrichment-workflow.md`, `lead-collection-workflow.md`
- `docs/architecture/lead-table-fields.md`, `project-overview.md`
- `docs/current-progress.md`, `docs/logs/changelog.md`, `docs/request-solution-log.md`
- `docs/superpowers/plans/*.md`, `docs/superpowers/specs/*.md`
- `skills/australia-lead-kp-research/SKILL.md`
- `scripts/utils/check_capability_inventory.py`
- 50+ report files moved to archive

---

Older entries have been archived to: [archive/request-solution-log-2026-04.md](archive/request-solution-log-2026-04.md)

Source file: [docs/request-solution-log.md](../request-solution-log.md)

---

<!-- CODEx_START: request_solution_entries -->
*Updated: 2026-05-19 15:50*

## 2026-05-19 - KP Semi-Automation Pipeline (Stage 2 + Stage 3)

- User request: Build a semi-automated pipeline to improve KP acquisition efficiency and accuracy. Reuse existing scripts, fill gaps for direct-contact enrichment and validation gating.
- Handling plan: Create `scripts/kp_pipeline/` package with Stage 2 (sitemap-based enrichment), Stage 3 (scoring/validation gate), metrics collection, and orchestrator that chains existing Stage 1 scripts with new modules.
- Files changed:
  - `scripts/kp_pipeline/__init__.py` (new)
  - `scripts/kp_pipeline/config.py` (new)
  - `scripts/kp_pipeline/stage2_enrich.py` (new — sitemap parsing, page scraping, email/phone/LinkedIn extraction, Google dork search, multi-contact extraction)
  - `scripts/kp_pipeline/stage3_validate.py` (new — scoring, auto-approve/reject/human-review routing)
  - `scripts/kp_pipeline/metrics.py` (new — run metrics JSON + validation log CSV)
  - `scripts/kp_pipeline/run_pipeline.py` (new — orchestrator for Stage 1+2+3)
  - `config/kp_pipeline.json` (new — stage settings, thresholds, blocklist)
  - `reports/kp-pipeline/` (new subdirectory — pipeline run reports consolidated here)
  - `CLAUDE.md` (updated — added Tools and Workflows section)
  - `data/kp_metrics.json` (new — append-only metrics)
  - `data/kp_validation_log.csv` (new — human review decisions)
- Result: Pipeline runs successfully. 50-lead test: Stage 2 found 4 direct contacts (10.8% rate), Stage 3 auto-approved 2, auto-rejected name-only candidates, 5 sent to human review.
- Achievements:
  - Stage 2 sitemap parsing eliminates most 404s from URL guessing.
  - Stage 3 scoring correctly rejects name-only candidates (no email/phone/LinkedIn).
  - Company emails (info@, hello@) penalized in scoring.
  - LinkedIn URL search and extraction integrated.
  - Multi-contact extraction from team pages added.
  - Random delay between requests to reduce rate-limiting.
  - Pipeline reports consolidated in `reports/kp-pipeline/`.
- Issues / limits:
  - Google dork searches frequently return 429 rate-limit. Primary value comes from direct page scraping, not Google search.
  - Team pages often list names without emails/LinkedIn — multi-contact extraction depends on pages having actual contact data.
  - No human review data accumulated yet — automation gates (false_positive_rate < 15%, auto_approve_accuracy > 95%) cannot be evaluated.
- Follow-up: User to review Stage 3 candidates via dashboard, export decisions. Accumulate validation data to evaluate automation gates. Consider Tavily API to replace Google search if 429 persists.

## 2026-05-15 - Fix Hidden Persistent Notification Launch

## 2026-05-15 - Fix Hidden Persistent Notification Launch

- User request: Diagnose why the notification popup did not appear in a new window even though notifications worked elsewhere.
- Handling plan: Compare global and project hook launch paths against direct popup tests, identify hidden-window launch flags, remove them only from visible persistent popup paths, keep silent flags for background MCP/toast helpers, and verify with manual launcher/hook simulations.
- Files changed: `E:\AI\Codex\GlobalHooks\global_task_end_notify.ps1`, `.codex/hooks/task_end_hook.py`, `docs/codex-agent-usage.md`, `docs/request-solution-log.md`.
- Result: Persistent WinForms notification launchers now start without `-WindowStyle Hidden` / `CREATE_NO_WINDOW`, so the popup can appear while still launching asynchronously.
- Achievements:
  - Identified the concrete failure mode: the scripts ran successfully but the visible form was hidden by the launcher.
  - Fixed the global completion launcher used by the user-level Stop hook.
  - Fixed the project Stop hook persistent branch while preserving quiet background behavior for MCP/toast helpers.
  - Added a documentation warning so future hook changes do not reintroduce hidden-window launch for visible popups.
- Issues / limits:
  - This fixes visible popup launch paths, but automatic Stop hooks still depend on the active Codex frontend loading and executing local/user hook config.
  - Current IDE/API-style sessions may not trigger `.codex/config.toml` Stop hooks even when manual popup tests work.
- Follow-up: In a fresh local Codex CLI window, run a tiny task and confirm the global Stop hook popup appears at task end.

## 2026-05-15 - Add Global Codex Completion Notification

- User request: Apply the notification reminder to all Codex projects using the more reasonable division of global generic hooks and project-specific hooks.
- Handling plan: Create a global hook folder outside the project, copy the persistent cat-themed notifier there, add a narrow user-level Stop hook that only launches the global notification asynchronously, and leave this project's safety/request-log/workflow hooks project-local.
- Files changed: `E:\AI\Codex\GlobalHooks\notify_user_persistent.ps1`, `E:\AI\Codex\GlobalHooks\global_task_end_notify.ps1`, `%USERPROFILE%\.codex\config.toml`, `docs/codex-agent-usage.md`, `docs/request-solution-log.md`.
- Result: User-level Codex Stop hook now points to `E:\AI\Codex\GlobalHooks\global_task_end_notify.ps1`; it should apply to Codex sessions in any project that uses the user-level config.
- Achievements:
  - Backed up the user-level config before editing as `%USERPROFILE%\.codex\config.toml.bak-20260515-090313`.
  - Preserved Codex event-grouped hook syntax with `[[hooks.Stop]]` and `[[hooks.Stop.hooks]]`.
  - Verified the copied notifier and global launcher with an auto-close test.
  - Verified `%USERPROFILE%\.codex\config.toml` parses as TOML and contains no Claude-style `[[hooks]] event = ...` pattern.
- Issues / limits:
  - The new global hook is generic and does not include this project's request-log, capability, or lead workflow checks.
  - Codex may need a restart/new session before user-level hook changes are picked up everywhere.
- Follow-up: In another project folder, start a short Codex task and confirm the global notification appears at task end.

## 2026-05-14 - Add Persistent Codex Confirmation Window

- User request: Add a notification path that does not disappear until confirmed; if the implementation fails twice, remove files created by this execution.
- Handling plan: Add a project-local PowerShell topmost confirmation window, wire the Stop hook to use it for task-end reminders or detected file changes, keep MCP/toast notifications as fallback, and verify hook/script syntax.
- Files changed: `scripts/notify_user_persistent.ps1`, `.codex/hooks/task_end_hook.py`, `docs/codex-agent-usage.md`, `docs/request-solution-log.md`.
- Result: Added the persistent notification helper and wired the Stop hook to prefer it when a task ends with project reminders or detected file changes.
- Achievements:
  - Added a local topmost WinForms confirmation window that stays open until `OK` is clicked.
  - Updated the window to a modern dark notification-card style with a rounded border, accent bar, status icon, and larger `确认 OK` button to avoid text clipping.
  - Reworked the persistent window after a sizing issue so it now uses a normal fixed border, a larger safe layout, visible `OK` button, and Enter/Esc/title-bar close support.
  - Changed the button label to ASCII `OK` and normal Segoe UI rendering to avoid Chinese text/font rendering issues in Windows PowerShell.
  - Added a reliable cat-themed treatment with ASCII cat art, warm accent colors, fade/slide-in animation, and a subtle pulsing accent.
  - Kept existing MCP/toast notification behavior as fallback and for ordinary no-change completion.
  - Documented the persistent helper and test command.
- Issues / limits:
  - It covers project Stop-hook notifications, not every internal VS Code Codex plugin confirmation prompt.
  - Cross-project notification still requires a user-level/global hook setup or copying equivalent config into another project.
- Follow-up: If the persistent window is visible enough in normal use, consider extracting a project-independent global notifier for other folders.

## 2026-05-14 - Judge Tavily Scrapling Combined Method

- User request: Read the current progress, request log, relevant active rules, 50-object Tavily validation outputs, and current Scrapling baseline reports, then judge whether `B_filtered_search` + `D_map_official_pages` + Scrapling follow-links + selective `C_advanced_exact_kp` should become the next experimental operating method; do not run a larger Tavily batch or write source CSVs without approval.
- Handling plan: Compare official precision, noise, contact-route/KP rates, review burden, credit/runtime cost, Scrapling baseline strengths/weaknesses, and current CSV/contact-confidence rules, then design a small production-style reducer/test for traceable candidate registration.
- Files changed: `docs/request-solution-log.md`.
- Result: The combined method is strong enough to become the next experimental operating method, but not a settled active workflow. It should run as a small reducer-style test first, writing only reports unless the user approves a scoped CSV write plan.
- Achievements:
  - Confirmed `D_map_official_pages` and Scrapling are the strongest official-domain stages, while `B_filtered_search` is useful for domain discovery and selective `C_advanced_exact_kp` is useful only for KP gaps after cleanup.
  - Confirmed current CSV rules allow traceable Low/Medium candidate registration before outreach, with human review still required before actual outreach.
  - Designed the next test around small official-domain batches, candidate reduction, draft registration rows, and human review gates.
- Issues / limits:
  - `B_filtered_search` and `C_advanced_exact_kp` still have low official precision and snippet-level evidence limits.
  - `C_advanced_exact_kp` has higher credit/runtime cost and should not run broadly.
  - Scrapling role snippets and LinkedIn/search URLs remain candidate hints, not verified direct contacts.
- Follow-up: If the user approves, implement a report-only reducer that produces proposed `leads.csv` and `contacts.csv` draft rows from a 5-10 lead sample, then ask for approval before any source CSV writes.

## 2026-05-14 - Write New-Window Handoff Summary

- User request: Summarize the current project state for a new Codex window and provide a CLI command that tells the new session what to read and how to make the next judgment.
- Handling plan: Rewrite `docs/current-progress.md` as a compact handoff with the latest Tavily/Scrapling validation state, current CSV registration rule, key files to read, next judgment task, and useful commands.
- Files changed: `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: New-window handoff context is now up to date for the 50-object Tavily expanded validation and candidate-evidence-first CSV policy.
- Achievements:
  - Recorded the current candidate registration rule: machine-generated traceable candidates may be registered before outreach-time review.
  - Pointed the next session to the 50-object Tavily validation report, metrics, and current Scrapling/form baseline reports.
  - Added a recommended next judgment task rather than a default larger Tavily run.
- Issues / limits:
  - The handoff does not promote Tavily into active workflow docs; that still requires user review and approval.
- Follow-up: Start a new Codex window with the provided command and ask it to judge whether B + D_map + Scrapling + selective C should become the next experimental operating method.

## 2026-05-14 - Clarify Candidate CSV Registration Rule

- User request: Correct the interpretation that candidates must be manually reviewed before being written to CSV, and confirm that prior form/KP outputs were machine-generated rather than manually verified.
- Handling plan: Check active enrichment/table/CLI rules against request-log history, then make the current candidate-evidence-first registration rule explicit in active docs so older reports do not override it.
- Files changed: `docs/lead-enrichment-workflow.md`, `docs/lead-table-fields.md`, `docs/cli-operating-rules.md`, `docs/request-solution-log.md`.
- Result: Active docs now state that machine-generated public-source company routes and KP candidates may be registered directly with source, confidence/status, and uncertainty notes; human exclusion/review is required before outreach use, not before candidate registration.
- Achievements:
  - Confirmed `docs/lead-enrichment-workflow.md`, `docs/lead-table-fields.md`, `docs/current-progress.md`, and `AGENTS.md` already supported traceable candidate registration.
  - Added an explicit precedence note so older "review before saving" reports are treated as historical, stricter workflow notes.
  - Clarified that machine-generated Scrapling/Tavily-style candidate rows are not the same as manually verified outreach-ready contacts.
- Issues / limits:
  - Historical reports still contain older wording and should be read as historical evidence, not current operating policy.
- Follow-up: Future Tavily/Scrapling analysis should evaluate whether machine-generated candidates are traceable and confidence-labeled, not whether they were manually pre-verified before CSV registration.

## 2026-05-14 - Run Tavily 50-Object Expanded Validation

- User request: Expand the Tavily validation sample, compare the final result against the current Scrapling form-finding mode, and consolidate the best combined usage plan for Tavily modes plus Scrapling.
- Handling plan: Create `reports/tavily-validation-20260514-expanded50/`, run a winner-focused 50-object test with a 10-object basic-control flow, full filtered basic search, full advanced exact KP search, full Tavily Map official-page discovery, and a measured existing Scrapling form/KP baseline.
- Files changed: `reports/tavily-validation-20260514-expanded50/`, `docs/request-solution-log.md`.
- Result: Full expanded validation completed with 989 compact review rows, a comparison matrix, and a final compact report in `reports/tavily-validation-20260514-expanded50/outputs/`.
- Achievements:
  - Built a 50-object validation set with 25 likely valid targets, 15 borderline/review objects, and 10 noisy/non-target domains.
  - Compared `A_basic_control`, `B_filtered_search`, `C_advanced_exact_kp`, `D_map_official_pages`, and `S_scrapling_form_baseline`.
  - Final metrics: A official precision 38.0%, noise 80.0%, contact route 100.0%, KP 100.0%; B official precision 21.5%, noise 20.0%, contact route 91.3%, KP 78.3%; C official precision 20.6%, noise 23.4%, contact route 52.2%, KP 87.0%; D_map official precision 99.0%, noise 0.0%, contact route 88.9%, KP 55.6%; Scrapling baseline official precision 99.5%, noise 0.0%, contact route 84.4%, KP 81.2%.
  - Proposed a candidate combined workflow: B for new domain discovery, D_map for official contact/team URL discovery, Scrapling follow-links for page-level extraction, and C only for remaining KP gaps after company-name cleanup.
- Issues / limits:
  - Four Tavily requests failed with SSL EOF/handshake timeout errors; the run continued and recorded the failures.
  - The Scrapling baseline uses existing reports, so runtime is not a newly timed value in this comparison.
  - Metrics remain experiment evidence from semi-manual annotations and compact result flags, not final outreach-quality contact verification.
- Follow-up: Review the expanded report before deciding whether to promote any combined workflow into active docs, archive older Tavily reports, or build a production reducer around B + D_map + Scrapling + selective C.

## 2026-05-14 - Run Tavily 20-Object Fair Validation

- User request: Based on the Tavily Experiment Decision Brief, run the next fair validation on exactly 20 objects, compare four Tavily/Scrapling flows, keep all new experiment files in a separate folder, and do not write to source lead/contact CSVs.
- Handling plan: Create `reports/tavily-validation-20260514/`, copy prior Tavily/Scrapling inputs there, build a mixed 20-object validation set, run Tavily basic, basic with Australia/excluded domains, advanced exact-match KP search, and Tavily Map, then write compact metrics and review rows only inside the experiment folder.
- Files changed: `reports/tavily-validation-20260514/`, `docs/request-solution-log.md`.
- Result: Full 20-object validation completed with 322 compact review rows and metrics in `reports/tavily-validation-20260514/outputs/`.
- Achievements:
  - Built a validation set with 8 likely valid targets, 6 borderline/review objects, and 6 noisy/non-target domains.
  - Ran Flow A, B, C, and D_map on the same 20-object set; no `data/leads.csv` or `data/contacts.csv` rows were changed.
  - Final metrics: A official precision 31.0%, noise 95.0%, contact route 100.0%, KP 75.0%; B official precision 29.0%, noise 30.0%, contact route 75.0%, KP 75.0%; C official precision 16.3%, noise 30.0%, contact route 50.0%, KP 87.5%; D_map official precision 100.0%, noise 0.0%, contact route 87.5%, KP 25.0%.
  - Kept Tavily experimental outputs out of active workflow docs.
- Issues / limits:
  - Flow C had one SSL EOF error for one object, so it produced 86 rows instead of a full 100-row maximum.
  - The annotation CSV is semi-manual from prior Tavily/Scrapling evidence, not a final human outreach-quality verification pass.
  - Tavily Map returned compact URL discovery and did not replace deeper page extraction for named KP details.
- Follow-up: Review the compact report before deciding whether to archive older Tavily files, optimize project Markdown references, or run another small reducer-focused experiment.

## 2026-05-13 - Push Tavily Scrapling KP Checkpoint To GitHub

- User request: Review the current context/workspace and update the project to GitHub.
- Handling plan: Inspect uncommitted changes, scan for API keys/secrets, validate scripts and capability inventory, update handoff context, then commit and push the checkpoint to `origin/main`.
- Files changed: `docs/current-progress.md`, `docs/request-solution-log.md`, plus the already pending Tavily/Scrapling/KP tooling, data, hook, documentation, and report changes in the working tree.
- Achievements:
  - Confirmed `.codex/secrets/` is ignored and no real `tvly-...` API key was found in tracked/report files.
  - Verified project scripts and Codex hook scripts compile.
  - Confirmed capability inventory passes with Tavily key optional/not set in the current shell.
  - Updated `docs/current-progress.md` with the current row counts, tooling state, and next resume rules.
- Issues / limits:
  - The checkpoint includes experimental Tavily reports; Tavily remains experimental and should not be treated as settled workflow.
  - Push requires GitHub network/auth access from the local machine.
- Follow-up: After push, verify `git status --short` is clean and record the final commit hash in the user-facing response.

## 2026-05-13 - Add Local Completion Notification

- User request: Add a simple lower-right notification after Codex finishes work or needs the user's decision, because terminal-only completion is easy to miss.
- Handling plan: Add a project-local PowerShell notification helper using Windows tray balloon notifications and trigger it from the existing Stop hook as a best-effort background action without breaking quiet hook rules.
- Files changed: `scripts/notify_user.ps1`, `.codex/hooks/task_end_hook.py`, `docs/codex-agent-usage.md`, `docs/request-solution-log.md`.
- Achievements:
  - Added `scripts/notify_user.ps1` with title/message parameters and no external dependency.
  - Updated `.codex/hooks/task_end_hook.py` to launch the notification helper at task end with stdout/stderr suppressed.
  - Kept normal hook behavior quiet: no stdout JSON, no blocking, and failures are swallowed.
  - Documented manual notification testing in `docs/codex-agent-usage.md`.
- Issues / limits:
  - This uses Windows Forms tray balloon notifications, so behavior depends on the Windows desktop notification/tray settings.
  - The notification helper was not manually executed during this change to avoid surprising the user with a test popup.
- Follow-up: If the tray balloon is not visible enough, evaluate Windows toast notifications or a persistent sound/message option later.

Update after notification was not visible:

- User reported that neither tray balloon nor simple toast was visible and asked for a way to give the script standalone notification permission.
- Files changed: `scripts/install_codex_notification_permission.ps1`, `scripts/notify_user.ps1`, `docs/codex-agent-usage.md`, `docs/request-solution-log.md`.
- Achievements:
  - Added an installer script that creates a Start Menu shortcut named `Codex Project Notifier` and attempts to assign the AppUserModelID `Codex.Project.Notifier`.
  - Updated `scripts/notify_user.ps1` to use Windows toast notifications with the same AppUserModelID and to set the current process AppUserModelID before sending.
  - Updated the installer so COM AppUserModelID assignment failures warn and continue instead of blocking setup.
  - The installer enables the current user's notification setting registry key for `Codex.Project.Notifier` and sends a test notification.
  - The installer prints where the shortcut was created and reminds the user to enable notifications for `Codex Project Notifier` or Windows PowerShell if Windows still blocks the toast.
- Issues / limits:
  - Windows notification visibility still depends on system notification settings and Focus Assist / Do Not Disturb.
  - On the current machine, ShellLink/IPropertyStore AppUserModelID assignment still returns a COM compatibility warning, but the installer now completes and runs the notification test.
- Follow-up: Run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\scripts\install_codex_notification_permission.ps1"` from the project root after enabling Windows notifications, then enable `Codex Project Notifier` or `Windows PowerShell` in Windows notification settings if needed.

Update after registry/tool search:

- User request: Check GitHub, Glama, the official MCP registry, Smithery, PulseMCP, skills.sh, SkillsMD, mcpservers.org, and Agent Skills for a lightweight existing notification tool, then install and test the lightest suitable option.
- Handling plan: Use the purpose-built `@topvisor/mcp-notifications` MCP server because it is lightweight, project-local via npm, supports Codex MCP config, exposes one `send_notification` tool, and does not require accounts or external notification services.
- Files changed: `.codex/config.toml`, `.gitignore`, `.codex/tools/mcp-notifications/package.json`, `.codex/tools/mcp-notifications/package-lock.json`, `README.md`, `scripts/check_capability_inventory.py`, `docs/codex-agent-usage.md`, `docs/request-solution-log.md`.
- Achievements:
  - Installed `@topvisor/mcp-notifications` into `.codex/tools/mcp-notifications`.
  - Configured project-local Codex MCP server `notifications` with AppUserModelID `Codex.Project.Notifier` and `node-notifier` backend.
  - Called the MCP `send_notification` tool through an inline SDK client; it exposed `send_notification` and returned `Notification queued`.
  - Added `.codex/tools/*/node_modules/` to `.gitignore` so only npm restore metadata is tracked.
- Issues / limits:
  - Codex must be restarted before the new MCP server appears as a normal tool in future sessions.
  - Actual desktop visibility still depends on Windows notification settings; the MCP tool reported success from the server side.
- Follow-up: If Windows toast visibility remains unreliable, use a local topmost window or sound fallback from the Stop hook.

Update after MCP tool did not notify at task end:

- User request: Report why the newly linked MCP notification tool still did not notify after Codex finished, and make it actually run at task end.
- Handling plan: Add a one-shot Node helper that starts the project-local `@topvisor/mcp-notifications` MCP server, calls `send_notification`, then exits; update the Stop hook to prefer this helper and keep the PowerShell notification script as fallback.
- Files changed: `.codex/hooks/task_end_hook.py`, `scripts/send_mcp_notification.mjs`, `docs/codex-agent-usage.md`, `docs/request-solution-log.md`.
- Achievements:
  - Added `scripts/send_mcp_notification.mjs` for one-shot MCP notification calls with sound.
  - Updated `.codex/hooks/task_end_hook.py` so task-end notifications use the MCP helper first and `scripts/notify_user.ps1` only as fallback.
  - Verified the helper runs successfully with `node scripts\send_mcp_notification.mjs --title "Codex MCP hook test" --message "Task-end hook MCP helper test" --sound`.
  - Verified hook compile and Node syntax checks.
- Issues / limits:
  - The previously linked MCP server in `.codex/config.toml` only becomes a normal Codex tool after restart and does not automatically run on Stop by itself.
  - Actual visual notification still depends on Windows notification settings; the helper now runs, but Windows may still suppress toast display.
- Follow-up: If the MCP helper still does not produce a visible prompt on the user's machine, replace or augment it with a local topmost window and sound fallback that does not rely on Windows notification center.

## 2026-05-13 - Compare Tavily Discovery and Tavily Plus Scrapling

- User request: Test Tavily under the free 1,000-credit logic, estimate cost/time/token/precision for normal 50-customer work, compare Tavily-only with Tavily plus Scrapling, add new search terms, and write iteration findings into the relevant project docs.
- Handling plan: Use a 20-candidate controlled experiment instead of 50 for the first measurement, add experiment keywords, run Tavily discovery against new AU restaurant/hotel/hospitality search terms, run Scrapling extraction on the same candidates for a fair hybrid comparison, and record results as reports without writing candidate leads to source CSVs.
- Files changed: `scripts/run_tavily_discovery_experiment.py`, `data/search_keywords.csv`, `README.md`, `docs/lead-collection-workflow.md`, `docs/lead-enrichment-workflow.md`, `reports/tavily-discovery-experiment-20260513-20.csv`, `reports/tavily-discovery-experiment-20260513-20.md`, `reports/tavily-discovery-experiment-20260513-20-scrapling-queue.csv`, `reports/tavily-discovery-experiment-20260513-20-hybrid-scrapling.csv`, `reports/tavily-discovery-experiment-20260513-20-hybrid-scrapling.md`, `reports/tavily-discovery-hybrid-experiment-20260513.md`, `docs/request-solution-log.md`.
- Achievements:
  - Added 5 experiment keywords `KW-0034` through `KW-0038` for Australia restaurant/hotel/hospitality discovery.
  - Ran Tavily discovery for 20 new candidates: 32 raw result rows, 20 unique candidate domains, 19 new domains, 1 existing-domain duplicate, 5 snippet-level contact signals, and 48.6 seconds runtime.
  - Ran Scrapling static extraction against the same 20 candidates: 549 candidate evidence rows, including 11 emails, 11 phones, 9 contact forms, 8 company LinkedIn URLs, and 4 possible key-person LinkedIn URLs.
  - Wrote a comparison report with 50-customer estimates, token/review-size proxy, time, precision, and next iteration recommendations.
- Issues / limits:
  - Tavily discovery was useful but noisy: directories, email databases, registry pages, travel pages, and generic listing sites appeared in the candidate set.
  - Scrapling hybrid extraction was richer but much heavier: 244.7 seconds and about 193 KB of output for 20 candidates.
  - Exact Codex token usage is not exposed; the report uses output size as a review/token-cost proxy.
  - Source CSV lead/contact rows were intentionally not updated from this experiment.
- Follow-up: Add stronger domain filtering and compact top-candidate reports before running a 50-customer production-style batch; consider Tavily Map only after Search + Scrapling filtering is improved.

Correction after user feedback:

- User clarified that Tavily is still experimental, so test evidence should not be written into active workflow/README as if it were a settled project method.
- Kept the experiment trace in this request log and in `reports/`.
- Removed Tavily experimental tool entries and test conclusions from `README.md`, `docs/lead-collection-workflow.md`, and `docs/lead-enrichment-workflow.md`.
- Future rule: while a tool is still being tested, keep arguments, measurements, and comparison evidence in `reports/` plus this request log. Move only settled operating methods into active workflow docs.

Update after 100-candidate expansion:

- User request: Expand the Tavily experiment sample to 100 because the earlier run used only a few credits.
- Files changed: `scripts/run_tavily_discovery_experiment.py`, `reports/tavily-discovery-experiment-20260513-100.csv`, `reports/tavily-discovery-experiment-20260513-100.md`, `reports/tavily-discovery-experiment-20260513-100-scrapling-queue.csv`, `reports/tavily-discovery-experiment-20260513-100-hybrid-scrapling.csv`, `reports/tavily-discovery-experiment-20260513-100-hybrid-scrapling.md`, `reports/tavily-discovery-hybrid-experiment-20260513-100.md`, `docs/request-solution-log.md`.
- Achievements:
  - Expanded the experiment query pool from 5 to 25 Tavily discovery queries.
  - Ran Tavily discovery for 100 candidates: 163 raw result rows, 100 unique candidate domains, 92 new domains, 8 existing-domain duplicates, 24 snippet-level contact signals, and 53.1 seconds runtime.
  - Ran Scrapling static extraction against the same 100 candidates: 1516 candidate evidence rows, 32 fetch errors, and 1455.4 seconds runtime.
  - Wrote a 100-candidate comparison report while keeping active workflow docs unchanged.
- Issues / limits:
  - At least 26 of 100 obvious noisy domains were found, including directories, databases, registries, travel pages, booking/software pages, and non-target listings.
  - Hybrid output is large, about 617 KB across CSV/MD, so a compact top-candidate reducer is needed before larger runs.
  - No source CSV lead/contact rows were written from the experiment.
- Follow-up: Improve blocked-domain filtering and compact hybrid reporting before another 100+ candidate run; consider a small Tavily Map test only on filtered high-quality official domains.

Update after 20-object KP experiment:

- User request: Continue from the 100/120 experimental candidate set into the next KP action, but test only 20 objects because all 120 would take too long.
- Files changed: `scripts/build_kp_experiment_from_tavily_candidates.py`, `reports/kp-experiment-20260513-20-selected.csv`, `reports/kp-experiment-20260513-20-tavily-kp-tasks.csv`, `reports/kp-experiment-20260513-20.md`, `reports/kp-experiment-20260513-20-tavily-nonlinkedin.csv`, `reports/kp-experiment-20260513-20-tavily-nonlinkedin.md`, `reports/kp-experiment-20260513-20-comparison.md`, `docs/request-solution-log.md`.
- Achievements:
  - Built a 20-object KP experiment subset from the 100-candidate Tavily discovery results, excluding obvious noisy domains and preferring candidates with local evidence.
  - Generated 80 Tavily KP tasks for those 20 objects.
  - Ran 60 non-LinkedIn Tavily KP tasks, producing 272 result rows in 293.6 seconds with 1 error.
  - Compared against the local/Scrapling baseline for the same 20 objects.
- Issues / limits:
  - The 20-object sample is intentionally biased toward likely-useful candidates, not random.
  - Tavily found useful KP pages but still returned LinkedIn and third-party noise even with dedicated LinkedIn tasks excluded.
  - Company-name guesses from discovery need cleanup before KP query generation.
  - No source CSV lead/contact rows were written from this experiment.
- Follow-up: Add company-name cleanup, blocked-domain filtering, and a compact KP candidate reducer before running a larger KP experiment.

Update after decision-brief request:

- User request: Consolidate the recent Tavily and Scrapling experiment results into one document so the user can judge how to use the tool and where the problems are.
- Files changed: `reports/tavily-experiment-decision-brief-20260513.md`, `docs/request-solution-log.md`.
- Achievements:
  - Created a single decision brief covering the setup, five experiment stages, cost/time, precision, problem points, best-use cases, next steps, and decision options.
  - Kept the brief in `reports/` because Tavily remains experimental and should not be promoted into active workflow docs yet.
- Issues / limits:
  - The brief summarizes experiment evidence; it does not establish a settled operating method.
- Follow-up: Use the decision brief to choose whether to pause Tavily, continue discovery-only experiments, use Tavily for KP after local extraction, or build a fuller Tavily + Scrapling pipeline.

## 2026-05-13 - Add Tavily Search Task Runner

- User request: Try Tavily using the user's free account/API allowance.
- Handling plan: Add a conservative Tavily REST runner that consumes generated KP search-task CSVs, reads the API key only from an environment variable, writes compact evidence to `reports/`, and does not write to source CSV files.
- Files changed: `scripts/run_tavily_search_tasks.py`, `scripts/check_capability_inventory.py`, `README.md`, `docs/lead-enrichment-workflow.md`, `reports/form-crawl-tool-options-20260513.txt`, `docs/request-solution-log.md`.
- Achievements:
  - Added `scripts/run_tavily_search_tasks.py` with small-batch defaults: basic search, five results per task, no answer, no raw content, no source CSV writes.
  - Added optional `TAVILY_API_KEY` visibility to `scripts/check_capability_inventory.py` without treating a missing key as a project failure.
  - Documented the Tavily runner, key-handling rule, low-cost defaults, and LinkedIn manual-review boundary.
  - Verified Python compilation for the Tavily runner and capability inventory script.
  - Ran the capability inventory check; all required local capabilities passed, and `TAVILY_API_KEY` was reported as optional/not set in the current shell.
- Issues / limits:
  - Tavily was not called yet because the key is not present in the current environment.
  - The first real Tavily call will need network access and should stay within a very small approved batch.
- Follow-up: Set `TAVILY_API_KEY` in the environment, then run a first 3-task test such as `scripts/run_tavily_search_tasks.py --limit 3 --max-results 5 --exclude-linkedin`.

Update after first API test:

- Files changed: `scripts/run_tavily_search_tasks.py`, `requirements.txt`, `scripts/check_capability_inventory.py`, `reports/tavily-kp-search-results-20260513-test-ok.csv`, `reports/tavily-kp-search-results-20260513-test-ok.md`, `reports/form-crawl-tool-options-20260513.txt`, `docs/request-solution-log.md`.
- Achievements:
  - Fixed local HTTPS certificate verification for Tavily calls by using `certifi` and recording it in `requirements.txt` plus the capability inventory.
  - Added safer API-key normalization so copied clipboard text must contain a valid `tvly-...` key pattern.
  - Successfully ran a 3-task Tavily test and wrote 7 compact search-result rows to `reports/tavily-kp-search-results-20260513-test-ok.*`.
  - Confirmed Tavily can find official H&J Restaurants pages plus third-party discovery leads from the generated KP search tasks.
- Issues / limits:
  - The first sandboxed network attempt was blocked, and escalated network access was required for API calls.
  - The next 10-task run could not continue because the clipboard no longer contained the API key.
  - Third-party email snippets from search results are discovery leads only and should not be saved as high-confidence direct contacts without verification.
- Follow-up: Re-copy the Tavily API key or set `TAVILY_API_KEY` for the current shell, then run the next small batch with `--skip 3 --limit 10 --max-results 5 --exclude-linkedin`.

Update for local key file:

- Files changed: `.gitignore`, `scripts/run_tavily_search_tasks.py`, `README.md`, `docs/lead-enrichment-workflow.md`, `reports/form-crawl-tool-options-20260513.txt`, `docs/request-solution-log.md`.
- Achievements:
  - Added `.codex/secrets/` to `.gitignore` so local API key files stay out of version control.
  - Updated Tavily runner to read the API key from `TAVILY_API_KEY` first, then `.codex/secrets/tavily_api_key.txt`.
  - Documented the ignored local key-file workflow in README, enrichment workflow notes, and the tool option report.
- Issues / limits:
  - The local secrets file was not created yet because the clipboard no longer contained a `tvly-...` key pattern.
  - No additional Tavily quota was consumed after the first successful 3-task test.
- Follow-up: Re-copy the Tavily key, write it to `.codex/secrets/tavily_api_key.txt`, then run a next10 batch to compare Tavily-assisted discovery against prior manual/Scrapling-only workflow.

Update for interactive key setup:

- Files changed: `scripts/save_tavily_api_key.ps1`, `README.md`, `reports/form-crawl-tool-options-20260513.txt`, `docs/request-solution-log.md`.
- Achievements:
  - Added a PowerShell helper that prompts for the Tavily key without echoing it and writes the matched `tvly-...` key to `.codex/secrets/tavily_api_key.txt`.
  - Documented the helper command for new PowerShell windows.
- Issues / limits:
  - The helper stores a local plaintext key file by design, but the path is ignored by git and should stay local to this machine.
- Follow-up: In a new window, run `.\scripts\save_tavily_api_key.ps1`, paste the key, then use the Tavily runner normally.

Update after local-key next10 test:

- Files changed: `reports/tavily-kp-search-results-20260513-p1-next10.csv`, `reports/tavily-kp-search-results-20260513-p1-next10.md`, `reports/tavily-vs-local-search-benefit-20260513.md`, `reports/form-crawl-tool-options-20260513.txt`, `docs/request-solution-log.md`.
- Achievements:
  - Confirmed `.codex/secrets/tavily_api_key.txt` exists locally and is ignored by git.
  - Ran the next 10-task Tavily batch using the ignored local key file.
  - Produced 27 compact Tavily result rows: 20 official-site results, 5 third-party public results, and 2 LinkedIn manual-review profile URLs.
  - Wrote a Tavily vs local-only benefit report for future tool decisions.
- Issues / limits:
  - Tavily improves discovery speed but does not verify direct contact truth by itself.
  - Third-party snippets and LinkedIn URLs remain candidate evidence/manual review entry points, not high-confidence direct contacts.
- Follow-up: Use Tavily for small KP/search-result batches, then pass official URLs to Scrapling or manual registration under the existing confidence/source rules.

## 2026-05-13 - Research Form Crawl Tools and Run No-Budget Form Extraction

- User request: Search and save additional multi-crawl/form-crawl tools and plans for later, estimate any paid-tool budget before use, and execute only no-extra-spend options now.
- Handling plan: Review current project tool boundaries, research MCP/API/skill candidates for search, crawl, scrape, and form extraction, save a durable TXT option file, then run the existing project-local Scrapling helper on the current AU form/KP queue without writing to source CSV files.
- Files changed: `reports/form-crawl-tool-options-20260513.txt`, `reports/au-public-contact-candidates-20260513-form-more-static12.csv`, `reports/au-public-contact-candidates-20260513-form-more-static12.md`, `reports/au-public-contact-candidates-20260513-form-more-static4.csv`, `reports/au-public-contact-candidates-20260513-form-more-static4.md`, `docs/request-solution-log.md`.
- Achievements:
  - Recorded later-tool candidates and budget notes for Tavily, Firecrawl, Exa, Brave Search, Google Custom Search JSON API, Apify, and generic MCP crawler/scraper servers.
  - Confirmed no new paid/API-key tool should be enabled without separate approval and a request/page/cost cap.
  - Ran no-extra-cost static Scrapling extraction against the existing AU form/KP queue, producing 119 candidate rows in the 12-lead report and 54 candidate rows in the smaller 4-lead verification report.
  - Kept extraction outputs in `reports/` only; no business CSV source rows were changed.
- Issues / limits:
  - The 12-lead static run wrote its report but exceeded the shell timeout, so future batches should be smaller or use a longer timeout.
  - Scrapling still emits runtime fetch logs to the shell; this is acceptable for normal scripts but should be quieted or redirected if it becomes a token-noise problem.
  - Paid/API tools remain unapproved; use existing Scrapling/static or approved local dynamic fetcher only until the user authorizes budget and access scope.
- Follow-up: Review the new candidate reports before registering any company forms, emails, phones, or KP candidates into `data/leads.csv` or `data/contacts.csv`.

## 2026-05-13 - Upgrade Swillhouse and Liquid Direct Routes

- User request: Continue node 5 execution by finding and registering stronger direct routes for existing P1 KP leads.
- Handling plan: Search public sources for person-specific routes, register or upgrade suitable contact rows, update lead-level summary fields, and validate row counts/schema.
- Files changed: `data/leads.csv`, `data/contacts.csv`, `reports/kp-contact-registration-20260513-direct-upgrade-3.md`, `docs/request-solution-log.md`.
- Result: Upgraded Swillhouse and Liquid & Larder from key-person-identified to direct-key-contact-found.
- Achievements:
  - Added Lisa Hobbs as Swillhouse CEO with a person-specific LinkedIn manual-review URL.
  - Upgraded Liquid & Larder's James Bradey and Emma McAlary with person-specific LinkedIn manual-review URLs.
  - Set Lisa Hobbs and James Bradey as primary key-person routes for their respective leads.
  - Preserved source CSV schemas: `data/leads.csv` 195 rows / 53 fields; `data/contacts.csv` 128 rows / 21 fields.
- Issues / limits:
  - These upgrades are LinkedIn manual-review routes, not direct email/phone.
  - All upgraded routes should be checked again before actual outreach.
- Follow-up: Continue P1 direct-route upgrades, but prioritize direct email/phone over additional LinkedIn-only upgrades where possible.

## 2026-05-13 - Upgrade Applejack and Odd Culture Direct Routes

- User request: Continue node 5 execution after the prior KP registration and direct-upgrade pass.
- Handling plan: Inspect P1 known-KP leads for existing direct route evidence, upgrade suitable contact rows, update lead-level summary fields, and validate row counts/schema.
- Files changed: `data/leads.csv`, `data/contacts.csv`, `reports/kp-contact-registration-20260513-direct-upgrade-2.md`, `docs/request-solution-log.md`.
- Result: Upgraded Applejack Hospitality and Odd Culture Group from key-person-identified to direct-key-contact-found.
- Achievements:
  - Upgraded Applejack's Hamish Watts and Ben Carroll person-specific LinkedIn URLs as key-person manual-review routes.
  - Set Hamish Watts as Applejack's primary key-person route.
  - Upgraded Odd Culture's Sabrina Medcalf direct email `live@oddculture.group` as primary direct key-person route.
  - Preserved source CSV schemas: `data/leads.csv` 195 rows / 53 fields; `data/contacts.csv` 127 rows / 21 fields.
- Issues / limits:
  - Applejack routes are LinkedIn manual-review URLs, not email/phone.
  - Odd Culture direct email should still be reviewed before actual outreach.
- Follow-up: Continue direct-route upgrades for remaining P1 leads, prioritizing official/direct email evidence before LinkedIn-only routes.

## 2026-05-13 - Upgrade Existing Fink Direct KP Contacts

- User request: Continue executing node 5 after registering second-batch KP candidates.
- Handling plan: Inspect P1 known-KP leads for existing official direct email evidence, upgrade suitable contact rows, mirror lead-level direct-contact fields, and validate row counts/schema.
- Files changed: `data/leads.csv`, `data/contacts.csv`, `reports/kp-contact-registration-20260513-direct-upgrade.md`, `docs/request-solution-log.md`.
- Result: Upgraded Fink from key-person-identified to direct-key-contact-found using existing official contact-page direct emails.
- Achievements:
  - Set Sarah Barker as Fink's primary direct key-person contact with `sarah@finkgroup.com.au`.
  - Confirmed Amanda Yallop and Texon Mungombe as secondary direct department/person routes.
  - Updated `LEAD-0169` legacy `key_contact_*`, `primary_contact_method`, `outreach_contact_type`, and `contact_priority` fields.
  - Preserved source CSV schemas: `data/leads.csv` 195 rows / 53 fields; `data/contacts.csv` 127 rows / 21 fields.
- Issues / limits:
  - This was an upgrade of existing official evidence rather than a new external discovery.
  - All direct contacts should still be reviewed before actual outreach.
- Follow-up: Continue P1 direct-route upgrades for other known-KP leads, then handle remaining AB Hotels only if a stronger person-specific public source appears.

## 2026-05-13 - Register Second KP Candidates From Search Tasks

- User request: Continue executing node 5 candidate registration from the KP search-task queue.
- Handling plan: Check remaining search-task leads without `contacts.csv` rows, register only traceable public-source person candidates, update legacy lead summary fields, and validate row counts/schema.
- Files changed: `data/leads.csv`, `data/contacts.csv`, `reports/kp-contact-registration-20260513-second-batch.md`, `docs/request-solution-log.md`.
- Result: Registered 2 public-source KP candidate rows for Elements Dining Group and updated its lead row from company-only contact level to key-person-identified level.
- Achievements:
  - Added Saif Basunia as Chief Executive Officer from a public third-party company page.
  - Added Tass Konstantakos as Co-Founder Director and saved a LinkedIn manual-review entry point.
  - Preserved source CSV schemas: `data/leads.csv` 195 rows / 53 fields; `data/contacts.csv` 127 rows / 21 fields.
  - Confirmed affected Chinese status/confidence fields remain valid UTF-8.
- Issues / limits:
  - No direct personal email or phone was verified in this batch.
  - Taverners Group remains unregistered because it is low strength.
  - AB Hotels still needs a stronger person-specific public source.
- Follow-up: Continue with AB Hotels if a stronger source appears, then move to improving existing P1 known-KP leads by finding direct email/phone or person-specific LinkedIn URLs.

## 2026-05-13 - Register First KP Candidates From Search Tasks

- User request: Continue execution toward node 5 and directly fill KP/contact information when public-source evidence exists, with outreach-time review later.
- Handling plan: Use the generated KP search-task queue to identify missing person-level contacts, register traceable public-source candidates in `contacts.csv`, mirror summary fields in `leads.csv`, validate row counts/schema, and write a short batch report.
- Files changed: `data/leads.csv`, `data/contacts.csv`, `reports/kp-contact-registration-20260513-first-batch.md`, `docs/request-solution-log.md`.
- Result: Registered 4 public-source KP candidate rows and updated 3 lead rows from company-only contact level to key-person-identified level.
- Achievements:
  - Added William Kuo for Alleyway Group from an official public source.
  - Added Con Dedes and Kerrie Dedes for Dedes Waterfront Group from a public customer case.
  - Added Roger Gregg for House Made Hospitality from a public The Org profile.
  - Preserved source CSV schemas: `data/leads.csv` 195 rows / 53 fields; `data/contacts.csv` 125 rows / 21 fields.
  - Corrected an intermediate PowerShell/Python encoding issue so affected Chinese status/confidence fields remain valid UTF-8.
- Issues / limits:
  - No direct personal email or phone was found in this first registration batch.
  - Taverners Group was skipped because its final-customer fit looked weak in this pass.
  - AB Hotels still has only company-level contact evidence from this pass.
- Follow-up: Continue the node 5 loop on remaining KP search-task leads, prioritizing candidates with official pages, public cases, or person-specific URLs before weaker search snippets.

## 2026-05-13 - Align Direct Candidate Registration Rule

- User request: Clarify that KP and contact information do not need a separate pre-save review step; traceable public-source candidates can be filled into CSV first and reviewed again during outreach.
- Handling plan: Remove misleading "review before saving" and "review queue only" wording from active workflow docs, extraction recommendations, the KP search-task generator, and the generated KP task report while preserving source/confidence/status/note requirements.
- Files changed: `docs/lead-collection-workflow.md`, `docs/lead-enrichment-workflow.md`, `scripts/extract_public_contact_candidates.py`, `scripts/generate_kp_search_tasks.py`, `reports/kp-search-tasks-20260513-au-final-customers.csv`, `reports/kp-search-tasks-20260513-au-final-customers.md`, `docs/request-solution-log.md`.
- Result: Current rules now state that company routes and KP candidates may be registered directly when source, confidence, status, and uncertainty notes are present; outreach-time review remains the later cleanup step.
- Achievements:
  - Reworded the KP search-task report as a search-task queue, not a pre-save review gate.
  - Reworded extractor email/phone save recommendations to allow saving with source/confidence notes and review before outreach.
  - Updated collection/enrichment workflow wording to remove the old "without review" blocker.
- Issues / limits:
  - Search-result URLs and pure role snippets still must not be saved as contact records.
  - LinkedIn profile URLs remain manual review entry points; no LinkedIn login, browsing, messaging, scraping, or export is allowed without explicit approval.
- Follow-up: Next KP enrichment step can directly register traceable public-source candidates into `contacts.csv` as pending-verification rows, then revisit them before actual outreach.

## 2026-05-13 - Add Direct KP Search Task Generator

- User request: Continue the current project plan, focusing on increasing KP acquisition rather than collecting more generic company routes.
- Handling plan: Run resume checks, inspect current AU lead/contact gaps, add a focused search-task generator for existing Australia restaurant/hotel final-customer leads, generate a review queue, validate outputs, and document the new tool.
- Files changed: `scripts/generate_kp_search_tasks.py`, `reports/kp-search-tasks-20260513-au-final-customers.csv`, `reports/kp-search-tasks-20260513-au-final-customers.md`, `README.md`, `docs/lead-enrichment-workflow.md`, `docs/request-solution-log.md`.
- Result: Added a direct KP search-task generator and produced a 152-row search-task queue covering 19 Australia restaurant/hotel final-customer leads.
- Achievements:
  - Capability inventory check passed.
  - Python compile checks passed for the active queue, extraction, query, new KP search, and capability scripts.
  - Generated known-KP direct-contact searches, official-site leadership/owner/operations/procurement/PDF searches, web searches, and LinkedIn manual-review entry-point searches.
  - Split multi-person `key_contact_name` values into separate person-specific search tasks.
  - Preserved source CSV row counts and schemas: `data/leads.csv` 195 rows / 53 fields; `data/contacts.csv` 121 rows / 21 fields.
- Issues / limits:
  - The new output is a search-task queue only; the generator itself does not verify or save new KP contacts to `contacts.csv`, but evidence found from the tasks may be directly registered when source/confidence/status/notes are present.
  - Default final-customer filtering produced 19 in-scope leads, below the `--limit-leads 30` cap because secondary design/fitout/kitchen/procurement leads are excluded by default.
  - Two intermediate one-line row-count commands failed due to shell quoting, then PowerShell `Import-Csv` checks were used successfully.
- Follow-up: Review or feed `reports/kp-search-tasks-20260513-au-final-customers.csv` into a manual/API search step; only save KP candidates to `contacts.csv` when source, confidence, status, and uncertainty notes are available.

## 2026-05-13 - Make Request Log Autowrite the Default

- User request: Provide a better default service for writing `docs/request-solution-log.md`, while respecting explicit file-scope limits, and check for conflicts in recent changes.
- Handling plan: Keep hooks advisory rather than letting them silently edit durable Markdown; make Codex responsible for writing request-log entries by default, with clear exceptions for user-forbidden or file-limited tasks.
- Files changed: `AGENTS.md`, `docs/cli-operating-rules.md`, `docs/request-solution-log.md`.
- Result: Project rules now state that Codex should write or update the request log in the same turn for file/rule/workflow/data/tool/future-context changes unless the user explicitly forbids it or limits edits to files excluding the log.
- Achievements:
  - Added a dedicated `Request Log Autowrite Rule` to `docs/cli-operating-rules.md`.
  - Added an entry-rule reminder to `AGENTS.md`.
  - Preserved the quiet hook design: hooks may remind or log runtime metadata, but should not silently edit `docs/request-solution-log.md`.
- Issues / limits:
  - `.codex/config.toml` has a user-owned uncommitted change from `codex_hooks = true` to `hooks = true`; it was intentionally left untouched.
- Follow-up: Future file-changing tasks should include the request-log entry by default unless the user explicitly narrows the edit scope.

## 2026-05-13 - Quiet Post Tool Hook Compile Output

- User request: Modify only `.codex/hooks/post_tool_hook.py` so the Python compile check better follows quiet-by-default hook rules, without running hooks or changing business code.
- Handling plan: Keep the existing `scripts/*.py` detection and `py_compile` behavior, make successful compile checks silent except for runtime JSONL logging, and truncate failure details shown to stderr.
- Files changed: `.codex/hooks/post_tool_hook.py`.
- Result: `py_compile` success now writes an OK record to `.codex/logs/post_tool.jsonl` and returns no warning; failures write full detail to `.codex/logs/post_tool.jsonl` while returning only the first 500 characters in the warning.
- Achievements:
  - Removed successful compile messages from advisory warning output.
  - Kept full failure details out of stderr while preserving them in the runtime JSONL log.
  - Maintained the no-stdout-JSON hook behavior.
- Issues / limits:
  - This entry was added after the original hook-only edit because that task explicitly limited edits to `.codex/hooks/post_tool_hook.py`.
- Follow-up: Keep hook stdout empty on the normal allow path and use short stderr messages only for warnings or blocking reasons.

## 2026-05-13 - Add Format Preservation Trigger Rules

- User request: Add project-specific rules so Codex preserves original user/project formatting by default and only changes expression format under clear trigger conditions.
- Handling plan: Add the full trigger rules to `docs/cli-operating-rules.md`, add a short entry-rule reminder to `AGENTS.md`, and record the rule change here.
- Files changed: `AGENTS.md`, `docs/cli-operating-rules.md`, `docs/request-solution-log.md`.
- Result: Project rules now require preserving original format unless context boundaries are unclear, repeated structure is obvious, or downstream machine parsing is explicitly required.
- Achievements:
  - Added rules against unnecessary XML/JSON/YAML/schema layers when Markdown or original format is already clear.
  - Added project-specific applications for CSV schemas, Markdown/CODEx blocks, logs/diffs, quiet hooks, and existing report conventions.
- Issues / limits:
  - This is a documentation/rule update only; no hook or script enforcement was added.
- Follow-up: Apply these trigger rules in future writing, documentation, report, hook-output, and CSV-related tasks.

## 2026-05-13 - Save Progress and Next Plan

- User request: Save the current progress and clearly write the next execution plan.
- Handling plan: Rewrite `docs/current-progress.md` as the latest compact handoff, preserving current state, completed stage, GitHub status, key rules, and concrete next commands/steps.
- Files changed: `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Current progress is saved as a concise resume document with a direct next plan focused on KP acquisition and candidate contact registration.
- Achievements:
  - Recorded the latest pushed commit: `0095d3f Advance AU lead enrichment tooling`.
  - Recorded that `origin/main` push succeeded and `rongroup-origin` failed with `Repository not found`.
  - Captured the completed AU Form/KP extraction test and reviewed company-level CSV updates.
  - Wrote the next execution plan: resume checks, register candidate contacts under the new CSV policy, build direct-KP search tasks, decide on optional APIs, then validate and log.
- Issues / limits:
  - No new operational work was run in this checkpoint beyond documentation updates.
- Follow-up: Next session should start from `docs/current-progress.md`, run the listed resume checks, then proceed with candidate contact registration or direct-KP search-task generation.

## 2026-05-12 - Allow Candidate Contacts in CSV and Define KP Acquisition Routes

- User request: Allow contacts/KP candidates to be placed into the CSV tables instead of keeping every candidate behind a separate review step, then explain other ways to increase KP discovery beyond manual LinkedIn/search and push the project to GitHub.
- Handling plan: Update enrichment/table/agent rules so public-source company contacts and Low/Medium confidence KP candidates can be saved with source, confidence, status, and notes; document additional KP acquisition methods and boundaries.
- Files changed: `AGENTS.md`, `README.md`, `docs/lead-enrichment-workflow.md`, `docs/lead-table-fields.md`, `docs/request-solution-log.md`.
- Result: Project rules now allow candidate contact registration in CSV as long as uncertainty is explicit, and the enrichment workflow documents search automation, official-site deep extraction, PDF/news extraction, email pattern inference, optional email discovery/verification APIs, and LinkedIn automation boundaries.
- Achievements:
  - Changed the CSV policy from strict candidate-report-first to traceable candidate registration.
  - Added the rule that uncertain KP rows must remain Low/Medium confidence and pending verification.
  - Documented Google Custom Search / Programmable Search and Hunter-style email discovery as optional future capabilities requiring API-key/cost approval.
  - Reaffirmed that LinkedIn scraping/automation remains out of scope without explicit approval.
- Issues / limits:
  - The rule change does not make weak role snippets or search URLs valid contacts.
  - Paid/account-based APIs still need separate approval before installation or use.
- Follow-up: After GitHub push, continue by either registering candidate rows into `contacts.csv` under the new rule or adding a targeted KP search-task generator.

## 2026-05-12 - Review Rows 14-32 Candidate Evidence

- User request: Execute the next stage after completing the extraction test.
- Handling plan: Review candidate evidence from rows 14-32, save only official/reviewed company-level fields, avoid unverified KP direct-contact writes, validate CSV row/schema counts, and record the reviewed updates.
- Files changed: `data/leads.csv`, `reports/au-form-kp-rows14-32-reviewed-updates-20260512.md`, `docs/request-solution-log.md`, `docs/current-progress.md`.
- Result: Saved reviewed company-level updates for 12 lead rows from the rows 14-32 evidence set.
- Achievements:
  - Added or improved company emails, contact/form URLs, and company LinkedIn URLs for Table For by Accor, The Maybe Group, Trader House, Veriu Group, ALH Group, Alleyway Group, Dedes Waterfront Group, EVT, House Made Hospitality, Meriton Suites, Signature Hospitality Group, and Gambaro Group.
  - Preserved CSV row counts and schemas: `data/leads.csv` 195 rows / 53 fields; `data/contacts.csv` 121 rows / 21 fields.
  - Kept role snippets, manual LinkedIn search URLs, and unverified KP direct-contact evidence out of final CSV fields.
- Issues / limits:
  - No new verified direct key-person email or phone was saved in this review pass.
  - Ovolo still lacks new saveable evidence because dynamic fallback timed out.
  - Some rows now have stronger company-level routes, but KP direct-contact discovery remains the bottleneck.
- Follow-up: Decide whether to run a direct-KP-focused review pass, or build a lightweight reviewed CSV update helper to reduce manual update work.

## 2026-05-12 - Complete AU Form/KP Candidate Extraction Test

- User request: Continue until the current testing is complete.
- Handling plan: Treat completion as full coverage of the existing 32-row AU Form/KP candidate queue, run remaining static extraction batches, use single-lead dynamic fallback for low-yield/static TLS-failure sites, and write a final test summary without starting a new broader enrichment batch.
- Files changed: `reports/au-public-contact-candidates-20260512-row14-batch.csv`, `reports/au-public-contact-candidates-20260512-row14-batch.md`, `reports/au-public-contact-candidates-20260512-row19-batch.csv`, `reports/au-public-contact-candidates-20260512-row19-batch.md`, `reports/au-public-contact-candidates-20260512-row24-batch.csv`, `reports/au-public-contact-candidates-20260512-row24-batch.md`, `reports/au-public-contact-candidates-20260512-row29-batch.csv`, `reports/au-public-contact-candidates-20260512-row29-batch.md`, `reports/au-public-contact-candidates-20260512-dynamic-signature-single.csv`, `reports/au-public-contact-candidates-20260512-dynamic-signature-single.md`, `reports/au-public-contact-candidates-20260512-dynamic-gambaro-single.csv`, `reports/au-public-contact-candidates-20260512-dynamic-gambaro-single.md`, `reports/au-public-contact-candidates-20260512-dynamic-meriton-single.csv`, `reports/au-public-contact-candidates-20260512-dynamic-meriton-single.md`, `reports/au-public-contact-candidates-20260512-dynamic-ovolo-single.csv`, `reports/au-public-contact-candidates-20260512-dynamic-ovolo-single.md`, `reports/au-public-contact-candidates-20260512-dynamic-housemade-single.csv`, `reports/au-public-contact-candidates-20260512-dynamic-housemade-single.md`, `reports/au-form-kp-candidate-extraction-test-complete-20260512.md`, `docs/request-solution-log.md`, `docs/current-progress.md`.
- Result: The 32-row AU Form/KP extraction test is complete. Static extraction covered all 32 leads and produced 372 candidate rows; dynamic fallback covered 5 low-yield/TLS-failure leads and produced 33 additional candidate rows.
- Achievements:
  - Completed static extraction batches for queue rows 14-32.
  - Confirmed the full 32-row queue has candidate evidence output.
  - Used dynamic single-lead fallback successfully for Signature Hospitality Group, Gambaro Group, Meriton Suites, and House Made Hospitality.
  - Documented Ovolo Hotels Australia as still timing out in dynamic mode.
  - Wrote the final test summary report.
- Issues / limits:
  - Larger dynamic batches can time out and should be avoided; use dynamic fallback one lead at a time.
  - The extractor improves company-level routes and KP hints, but verified direct key-person email/phone remains the main bottleneck.
  - Rows 14-32 candidate outputs still need review before any CSV writes.
- Follow-up: Review rows 14-32 candidate CSVs and save only confirmed company-level fields or verified KP evidence; consider a lightweight reviewed CSV update helper if manual review becomes the bottleneck.

## 2026-05-12 - Continue AU Form/KP Next Batch

- User request: Continue the main project by first reading previous progress and `docs/request-solution-log.md`.
- Handling plan: Follow the current handoff plan, verify capabilities and script compilation, improve the public candidate extraction workflow, run a small scoped next-batch test from the existing AU Form/KP queue, and save only reviewed company-level evidence.
- Files changed: `scripts/extract_public_contact_candidates.py`, `data/leads.csv`, `reports/au-public-contact-candidates-20260512-next-batch-test.csv`, `reports/au-public-contact-candidates-20260512-next-batch-test.md`, `reports/au-public-contact-candidates-20260512-next-batch-filtered-test.csv`, `reports/au-public-contact-candidates-20260512-next-batch-filtered-test.md`, `reports/au-public-contact-candidates-20260512-next-batch-reviewed.csv`, `reports/au-public-contact-candidates-20260512-next-batch-reviewed.md`, `reports/au-form-kp-next-batch-20260512-company-contact.md`, `docs/request-solution-log.md`, `docs/current-progress.md`.
- Result: The extraction helper can now continue queue batches with `--skip`; the reviewed rows 9 to 13 test produced 52 candidate rows and updated 3 lead records with company-level official/contact evidence.
- Achievements:
  - Verified project capabilities and Python compilation before running the batch.
  - Added `--skip` to avoid repeatedly processing the first queue rows.
  - Tightened Australia phone extraction to remove postal-code/IP false positives.
  - Skipped Cloudflare `/cdn-cgi/l/email-protection` links as noise.
  - Added per-lead review summaries to Markdown extraction reports.
  - Updated company-level evidence for Liquid & Larder, Lucas Collective, and Oscars Group.
  - Preserved CSV row counts and schemas: `data/leads.csv` 195 rows / 53 fields; `data/contacts.csv` 121 rows / 21 fields.
- Issues / limits:
  - No new direct key-person email or phone was verified in this batch.
  - Merivale static extraction produced only technical status and a manual LinkedIn search URL.
  - Swillhouse contact page returned 403 in the static follow-link fetch, though its existing contact data remains present in `data/leads.csv`.
- Follow-up: Continue from queue row 14 with `--skip 13`, or review whether dynamic fetch is worthwhile for low-yield/static-blocked leads before writing more CSV updates.

## 2026-05-12 - Fix Codex Hooks TOML Structure

- User request: Document the Codex hooks config troubleshooting experience as future CLI/Agent self-check rules, not just a one-time note.
- Handling plan: Record the startup error, cause, wrong Claude Code-style TOML, correct Codex event-grouped TOML, validation command, and future guardrail in the project log, agent usage guide, CLI operating rules, and `AGENTS.md`.
- Files changed: `docs/request-solution-log.md`, `docs/codex-agent-usage.md`, `docs/cli-operating-rules.md`, `AGENTS.md`.
- Result: Codex hook configuration format is now documented as a durable troubleshooting and self-check rule.
- Achievements:
  - Captured the startup error: `Error loading config.toml: invalid type: sequence, expected struct HooksToml in hooks`.
  - Documented that the error came from applying Claude Code-style `[[hooks]] event = "..."` arrays to Codex.
  - Documented the Codex format: event tables such as `[[hooks.UserPromptSubmit]]` or `[[hooks.PreToolUse]]`, followed by nested hook entries such as `[[hooks.UserPromptSubmit.hooks]]` or `[[hooks.PreToolUse.hooks]]`.
  - Added the hook config rule to `docs/cli-operating-rules.md`, the project's main CLI/Agent operating rules file.
  - Updated startup/read-first rules so future Codex sessions read `docs/cli-operating-rules.md` and use `docs/codex-agent-usage.md` for hook, agent, config, startup, or CLI behavior work.
  - Added the PowerShell self-check command: `Select-String -Path .\.codex\config.toml -Pattern '\[\[hooks\]\]|event\s*='`; correct output is no matches.
  - Added the recommended Windows command wrapper: `powershell -NoProfile -ExecutionPolicy Bypass -Command "& .\.venv\Scripts\python.exe .\.codex\hooks\safety_hook.py"`.
- Issues / limits:
  - `.codex/README.md` does not exist in this project, so no `.codex/README.md` troubleshooting section was added.
  - Agents must still confirm the active Codex build's supported hook schema before future hook changes because hook configuration support can change between Codex versions.
- Follow-up: Before editing `.codex/config.toml` or user-level Codex hook config, run the self-check for forbidden `[[hooks]]` / `event =` patterns and compare the file against the current Codex-supported event-grouped TOML structure.

## 2026-05-12 - Add Selected Codex Hooks

- User request: Convert selected Markdown requirements into Codex-format hooks. Include destructive command blocking, request-log reminder, current-progress threshold warning, Python compile checks, capability inventory reminder, high-capability extraction scope warning, and UTF-8 Markdown checks. Do not include CSV schema/row-count checks, candidate-evidence-first enforcement, LinkedIn automation blocking, CODEx block enforcement, dashboard scope checks, or outreach-log checks.
- Handling plan: Add project-local `.codex/config.toml` and minimal Python hooks under `.codex/hooks/`; keep the hooks advisory except for destructive command blocking.
- Files changed: `.codex/config.toml`, `.codex/hooks/hook_utils.py`, `.codex/hooks/safety_hook.py`, `.codex/hooks/post_tool_hook.py`, `.codex/hooks/task_end_hook.py`, `docs/codex-agent-usage.md`, `docs/request-solution-log.md`.
- Result: Selected Codex hooks were added in the live project workspace.
- Achievements:
  - Added a safety/scope hook for dangerous commands, high-capability extraction scope, and project-local tooling reminders.
  - Added a post-tool hook for current-progress threshold warnings, script compile checks, capability inventory reminders, UTF-8 Markdown checks, and request-log reminders.
  - Added a task-end hook for final request-log and verification reminders.
- Issues / limits:
  - Hook output is conservative and advisory except for destructive command blocking.
  - CSV change-note enforcement was not added pending the user's cost/benefit decision.
  - Direct `py_compile` of `.codex/hooks/*.py` tried to write `.codex/hooks/__pycache__` and hit local ACL denial; validation works when `py_compile` writes temporary `.pyc` files under ignored `reports/hook-pycompile/`.
- Follow-up: Test the hooks against the active Codex installation; if the local Codex build does not load project `.codex/config.toml`, merge the hook section into the active user Codex config.

## 2026-05-12 - Delete External AgentNormsLab

- User request: Do not use `AgentNormsLab` content as project context anymore, and delete it.
- Handling plan: Delete the external folder directly after verifying the exact path; record that future sessions should not rely on it.
- Files changed: `docs/request-solution-log.md`; deleted external folder `E:\AI\Codex\AgentNormsLab`.
- Result: `E:\AI\Codex\AgentNormsLab` was removed.
- Achievements:
  - Deleted the external standards lab folder outside `TestProject`.
  - Clarified that future hook decisions should come from the live project docs, not the removed lab.
- Issues / limits:
  - Earlier log entries still describe the historical creation/move of that folder, but the folder no longer exists.
- Follow-up: If hook files are added later, derive them from current project requirements and Codex format in the live workspace.

## 2026-05-12 - Move Agent Standards Lab Outside Project

- User request: The standards lab should not stay inside `TestProject` because it makes the business project folder confusing; move it to a separate folder on E drive.
- Handling plan: Move the previously created `agent-norms-lab/` directory out of the project workspace into `E:\AI\Codex\AgentNormsLab`, then retest the checker from the new location.
- Files changed: `docs/request-solution-log.md`; moved external folder from `E:\AI\Codex\TestProject\agent-norms-lab` to `E:\AI\Codex\AgentNormsLab`.
- Result: The standards lab, reusable skill, hook templates, and optimized test project copy now live outside the live business project folder.
- Achievements:
  - Removed the mixed-purpose `agent-norms-lab/` folder from the project root.
  - Preserved the standalone standards lab and test copy under `E:\AI\Codex\AgentNormsLab`.
- Issues / limits:
  - The external folder is outside the project Git repo unless separately initialized or copied later.
- Follow-up: Use `E:\AI\Codex\AgentNormsLab` as the working location for future agent-standard experiments.

## 2026-05-12 - Create Codex Agent Standards Lab and Skill

- User request: Save the Codex/AGENTS/hooks principles into a new E-drive folder, turn them into a skill for organizing and checking project standards, then create a separate optimized test copy of the current project Markdown instead of replacing live files.
- Handling plan: Use `skill-creator`, create an isolated standards lab folder, add references/templates/skill/checker, and build an `optimized-testproject/` shadow structure with Codex-first AGENTS, docs, and minimal hooks.
- Files changed: `.gitignore`, `E:\AI\Codex\AgentNormsLab\**`, `docs/request-solution-log.md`.
- Result: Created a reusable `codex-agent-standards` skill, Codex hook templates, an optimized test project folder, and a comparison note. Live project docs and data were not replaced.
- Achievements:
  - Added source-derived Codex agent standards and hook principles.
  - Created a structural checker script for Codex agent standards.
  - Created a Codex-first optimized test copy with `.codex/config.toml` and safety/log/task-end hook examples.
  - Verified Python compilation and ran the checker successfully on the optimized test copy.
  - Tested hook scripts with simulated Codex JSON input and ignored generated `.codex/logs/` files.
- Issues / limits:
  - `quick_validate.py` could not run because PyYAML is not installed in the available Python environments.
  - The generated `agents/openai.yaml` initially had an encoding issue and was rewritten as UTF-8.
  - The optimized folder is a test copy only; it is not active Codex configuration until reviewed and adopted.
- Follow-up: Review `E:\AI\Codex\AgentNormsLab\optimized-testproject\COMPARISON.md`; if approved later, selectively merge the structure into the live project.

## 2026-05-12 - Test and Fill AU Form/KP Company Contact Batch

- User request: Continue testing, automatically fix current issues if there are no major blockers, then continue form filling. Save progress only if context is near the low threshold.
- Handling plan: Run a larger public extraction test from the current AU form/KP queue, inspect candidate quality, fix extraction classification issues, rerun the same test, then update only reviewed company-level/contact URL fields and LinkedIn manual-review candidates.
- Files changed: `scripts/extract_public_contact_candidates.py`, `data/leads.csv`, `data/contacts.csv`, `reports/au-public-contact-candidates-20260512-fill-batch-test.csv`, `reports/au-public-contact-candidates-20260512-fill-batch-test.md`, `reports/au-form-kp-fill-batch-20260512-linkedin-company-contact.md`, `docs/request-solution-log.md`.
- Result: The 8-lead test generated 119 candidate rows after fixes. Six lead rows were updated with company LinkedIn URLs or more precise contact/form URLs, and two Applejack contact rows were updated with official-page personal LinkedIn URL candidates. CSV row counts stayed unchanged.
- Achievements:
  - Verified local capabilities and script compilation before testing.
  - Fixed candidate ranking/classification for department emails, malformed phone candidates, and booking widgets.
  - Added company LinkedIn URLs for Hunter St. Hospitality, Bentley Restaurant Group, Illoura Hospitality, Australian Venue Co., Crystalbrook Collection, and Kickon Group.
  - Added medium-confidence manual-review LinkedIn URL candidates for Applejack contacts Hamish Watts and Ben Carroll.
  - Created a concise batch report under `reports/`.
- Issues / limits:
  - Initial CSV write through PowerShell heredoc caused Chinese mojibake in updated notes; it was detected and repaired with UTF-8-safe escaped strings.
  - LinkedIn personal profile contents remain unverified because unauthenticated access cannot reliably open profile pages.
  - Crystalbrook booking widget was detected but not treated as a general contact form.
- Follow-up: Continue with the next queue leads using the improved extraction filters; avoid writing LinkedIn personal URLs as high-confidence direct contacts unless manually verified.

## 2026-05-12 - Add Review Lists to Request/Solution Log

- User request: Evolve `docs/request-solution-log.md` so each update can include a list of achievements and problems for easier future review.
- Handling plan: Extend the log entry template with concise `Achievements` and `Issues / limits` list fields, and clarify that old entries do not need backfilling unless they are edited later.
- Files changed: `docs/request-solution-log.md`.
- Result: New request-solution entries should now record concrete outputs and discovered limits in reviewable list form.
- Achievements:
  - Added `Achievements` to the standard entry template.
  - Added `Issues / limits` to the standard entry template.
  - Kept the rule lightweight so routine logs stay readable.
- Issues / limits:
  - Existing older entries were not backfilled to avoid unnecessary churn.
- Follow-up: Use the new fields for future file-changing or workflow-changing entries.

## 2026-05-12 - Test Unauthenticated LinkedIn Access

- User request: Test whether the current environment can enter LinkedIn.
- Handling plan: Test only public unauthenticated access to two candidate personal profile URLs and one company page URL. Do not log in, message, export, or scrape profile content.
- Files changed: `docs/lead-enrichment-workflow.md`, `docs/request-solution-log.md`.
- Result: Plain HTTP requests were blocked by LinkedIn with 999/connection errors. Unauthenticated Playwright browser access opened the Bentley company page with status 200 and title `The Bentley Restaurant Group | LinkedIn`; the two Applejack personal profile URLs returned LinkedIn 404 pages. Current local automation should treat personal LinkedIn URLs as manual review entry points, not as verifiable profile content.
- Follow-up: Keep collecting LinkedIn URLs and Google search URLs, but verify personal profile matches manually or through explicitly approved account/platform access with anti-ban limits.

## 2026-05-12 - Add LinkedIn URL Candidate Route for KP Review

- User request: Try adding KP LinkedIn as another route; even if LinkedIn pages cannot be opened, candidate URLs are useful for manual contact and later enrichment. Apply the same idea to other reviewable routes.
- Handling plan: Keep the boundary at URL/evidence collection only. Extract LinkedIn profile/company URLs from official pages, generate manual public LinkedIn search URLs from the queue query, add richer LinkedIn query patterns, and document that LinkedIn URLs are manual review entry points rather than verified direct contacts.
- Files changed: `scripts/extract_public_contact_candidates.py`, `scripts/generate_kp_form_queries.py`, `docs/lead-enrichment-workflow.md`, `docs/request-solution-log.md`, `reports/au-public-contact-candidates-20260512-linkedin-url-test.csv`, `reports/au-public-contact-candidates-20260512-linkedin-url-test.md`, `reports/kp-form-query-tasks-20260512-linkedin-url-test.csv`.
- Result: The extraction test generated 36 candidate rows, including 3 `linkedin_search_url`, 2 `key_person_linkedin_url`, and 1 `company_linkedin_url`. Applejack official pages exposed two personal LinkedIn URLs; Bentley exposed a company LinkedIn URL. Query generation now includes more LinkedIn KP patterns.
- Follow-up: Treat LinkedIn rows as manual verification leads. Do not save them as high-confidence KP contact unless the person/company match is confirmed; do not automate LinkedIn account browsing, messaging, or export without separate explicit approval.

## 2026-05-12 - Limit Current Progress Updates to Real Checkpoints

- User request: Add the rule that early or routine task work should not update `docs/current-progress.md`; request-solution logging is enough unless the checkpoint threshold is met.
- Handling plan: Update CLI operating rules to separate durable request/tool records from rolling handoff checkpoints.
- Files changed: `docs/cli-operating-rules.md`, `docs/request-solution-log.md`.
- Result: Future sessions should use `docs/request-solution-log.md` for ordinary task records and update `docs/current-progress.md` only for account/session handoff, context-budget risk, completed meaningful stages, major data/tool milestones, or resume-critical next-plan changes.
- Follow-up: Apply this threshold before editing `docs/current-progress.md` in future tasks.

## 2026-05-12 - Improve Scrapling Candidate Ranking and Deduplication

- User request: Read the project documents and operating rules, then continue the current task after account handoff.
- Handling plan: Follow the existing handoff context, verify local capabilities, compile-check the active scripts, improve the public contact candidate extraction report workflow, rerun a small scoped test, and record the tool behavior change in this log only.
- Files changed: `scripts/extract_public_contact_candidates.py`, `reports/au-public-contact-candidates-20260512-ranked-test.csv`, `reports/au-public-contact-candidates-20260512-ranked-test.md`, `docs/request-solution-log.md`.
- Result: Capability inventory and Python compile checks passed. The extraction script now adds candidate priority, review buckets, queue rank, cross-page deduplication, source counts, additional source URLs, lower ranking for low-value careers/jobs emails, tighter form detection, and a top review section in the Markdown report. A 3-lead static test with two same-domain follow-up links generated 36 candidate rows with no final fetch errors.
- Follow-up: Review the ranked candidate CSV before saving anything to `data/leads.csv` or `data/contacts.csv`; next implementation can either update a small approved reviewed batch or build a lightweight CSV update helper.

## 2026-05-12 - Add Context Checkpoint and Rolling Progress Rule

- User request: Check whether CLI context-left can be identified; if possible, automatically update progress and remind the user when context is around 80% remaining. If exact quota is unavailable, use current document usage as an estimate. Also mark that once progress records are read, stale current progress can be deleted so progress does not stack into confusing layers.
- Handling plan: Add a context checkpoint rule to CLI operating rules, note that exact context budget is not always available, define conservative estimate triggers, and mark `docs/current-progress.md` as a rolling handoff file rather than append-only history.
- Files changed: `docs/cli-operating-rules.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Future sessions should checkpoint early when context budget is visible or estimated to be shrinking, rewrite current progress compactly, notify the user, and condense/delete stale progress after durable decisions are preserved elsewhere.
- Follow-up: Keep historical decisions in `docs/request-solution-log.md` and active standards in their corresponding workflow/rule docs; keep `docs/current-progress.md` focused on the latest state and next plan.

## 2026-05-12 - Write Account Handoff Progress and Next Plan

- User request: The user needs to switch accounts, so write the current progress and next-step plan into the corresponding Markdown files.
- Handling plan: Add an account handoff section to `docs/current-progress.md`, list the files and generated reports that should be preserved, record capability checks for the next account, update the resume prompt, and log the handoff here.
- Files changed: `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: The next account/session should read the active project docs, avoid reverting current uncommitted work, verify the project-local capability inventory, and continue with Scrapling candidate ranking/deduplication plus small scoped extraction tests.
- Follow-up: After switching accounts, start with `git status --short` and `.\.venv\Scripts\python scripts\check_capability_inventory.py`, then proceed with the immediate next plan in `docs/current-progress.md`.

## 2026-05-12 - Clarify Bounded Auto-Iteration Rule

- User request: Check whether the operating rules already say discovered issues should be recorded and automatically iterated, then modify the rule.
- Handling plan: Keep the requirement to record issues in the relevant Markdown/log files, expand the rule so Codex may automatically iterate inside an already approved task scope, and preserve approval boundaries for new business iterations, standard changes, risky access modes, and broad source-data changes.
- Files changed: `docs/cli-operating-rules.md`, `docs/current-progress.md`, `README.md`, `docs/chinese-user-guide.md`, `docs/request-solution-log.md`.
- Result: Future sessions can retry, fix scripts, rerun small tests, regenerate reports, update docs, and evaluate new capabilities after repeated failures without stopping for every small step, as long as the work remains inside the approved task scope.
- Follow-up: If a future request should allow fully automatic new business collection/enrichment batches, define that batch scope explicitly before running it.

## 2026-05-12 - Require Task-End Log Check

- User request: Confirm whether Request and Solution Log updates are already written into the operating rules for each conversation, and continue the work with that requirement clear.
- Handling plan: Check existing rules, clarify that the old rule covered important requests but not every task-end check, then update the log rules and CLI operating rules.
- Files changed: `docs/request-solution-log.md`, `docs/cli-operating-rules.md`.
- Result: Codex should now check the Request and Solution Log before finishing each task-oriented conversation and update it when the conversation changed files, rules, workflow decisions, data standards, tool behavior, or future operating context.
- Follow-up: Keep routine read-only checks out of the log unless they produce a durable project decision.

## 2026-05-12 - Build AU Form/KP Candidate Queue Tool

- User request: Continue the current work after confirming the Request and Solution Log rule.
- Handling plan: Avoid starting a new collection/enrichment iteration; build a local helper that reads existing `leads.csv` and `contacts.csv` and outputs Australia restaurant/hotel final-customer candidates with missing form, KP, or direct-contact gaps.
- Files changed: `scripts/build_form_kp_candidate_queue.py`, `reports/au-form-kp-candidate-queue-20260512-continue.csv`, `reports/au-form-kp-candidate-queue-20260512-continue.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Generated a 32-row queue from existing Australia final-customer leads only. Main gaps: 20 `missing_kp_direct`, 12 `missing_kp`, and 4 `missing_form`.
- Follow-up: Use the generated CSV as the next manual search queue or as input for a lightweight CSV update helper; do not run account-based or automated social-platform tools without explicit approval.

## 2026-05-12 - Run First AU Form/KP Queue Batch

- User request: Continue executing the queue work.
- Handling plan: Treat the approval as authorization for a small enrichment batch, back up active CSVs, review the first five queue candidates through public sources, update only verified or clearly low-confidence fields, regenerate the candidate queue, and write a batch report.
- Files changed: `data/leads.csv`, `data/contacts.csv`, `reports/au-form-kp-candidate-queue-20260512-continue.csv`, `reports/au-form-kp-candidate-queue-20260512-continue.md`, `reports/au-form-kp-enrichment-20260512-102500.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Reviewed Bentley Restaurant Group, Gambaro Group, H&J Restaurants, Swillhouse, and Applejack Hospitality. Added Swillhouse official form/email/phone details, strengthened official-source notes for Bentley/H&J/Applejack, and recorded a low-confidence third-party John Gambaro email candidate requiring manual verification.
- Follow-up: Continue with Australian Venue Co., Crystalbrook Collection, Hunter St. Hospitality, Illoura Hospitality, and Kickon Group if another enrichment batch is approved.

## 2026-05-12 - Evaluate Scrapling Tool

- User request: Check whether the Scrapling crawler/scraping tool can improve retrieval efficiency or reduce token usage while supporting the final project goal.
- Handling plan: Review current Scrapling documentation, PyPI metadata, and project fit; do not install or run it yet because network dependency installation needs approval and the tool has stealth/proxy features that require boundary rules.
- Files changed: `docs/lead-enrichment-workflow.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Scrapling is a reasonable candidate for a limited local public-page extraction helper that extracts emails, phones, contact forms, team links, and KP text into compact candidate rows. It should not be used for stealth, proxy, CAPTCHA bypass, login-only pages, automated LinkedIn browsing, or broad crawling without explicit approval.
- Follow-up: If approved, install/test Scrapling on 5 to 10 existing queue URLs and compare token/time savings against the current manual process.

## 2026-05-12 - Merge Scrapling Evaluation Into Active Workflow Docs

- User request: Avoid adding extra Markdown files if that increases future context/token use; confirm which existing rules conflict with Scrapling stealth/anti-bot/proxy features before deciding whether to modify them.
- Handling plan: Remove the standalone Scrapling evaluation file and keep the useful policy/test details inside `docs/lead-enrichment-workflow.md`; explain the specific account-risk and source-confidence rules involved.
- Files changed: `docs/lead-enrichment-workflow.md`, `docs/current-progress.md`, `docs/request-solution-log.md`; deleted `docs/scrapling-tool-evaluation-20260512.md`.
- Result: Scrapling guidance is now merged into the active enrichment workflow rather than stored in a separate evaluation document.
- Follow-up: User should decide whether any high-risk tool boundaries should be relaxed for controlled testing.

## 2026-05-12 - Relax Scrapling High-Capability Tool Rules

- User request: The project needs Scrapling-style stealth, anti-bot, proxy, or dynamic-browser capabilities, so update the rules instead of keeping them default-disabled.
- Handling plan: Replace the blanket default restriction with a controlled high-capability mode that allows dynamic browser, stealth settings, and proxies for public-page extraction after explicit approval, while preserving stop conditions for login-only, private, paid, CAPTCHA-solving, credential, and automated social-account risks.
- Files changed: `docs/lead-collection-workflow.md`, `docs/lead-enrichment-workflow.md`, `docs/cli-operating-rules.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Scrapling-style high-capability extraction is now allowed when scoped by domain/URL, batch size, rate limit, output file, and review boundary. Extracted data should first become candidate evidence, not direct CSV truth.
- Follow-up: Before the first Scrapling run, define the target queue size, allowed domains/URLs, rate limit, and output report path.

## 2026-05-12 - Expand Scrapling Account/Ban-Risk Rules

- User request: Further relax the rules for login pages, paid pages, CAPTCHA handling, automated LinkedIn/account behavior, and broad crawler style capabilities; the main concern is avoiding bans, not audit burden.
- Handling plan: Update tool rules to allow authenticated, paid-source, CAPTCHA-handling, proxy/stealth, and platform-account modes after explicit authorization and with anti-ban controls, while keeping unauthorized credentials, stolen cookies, unauthorized private data, and unpaid access-control bypass disallowed.
- Files changed: `docs/lead-collection-workflow.md`, `docs/lead-enrichment-workflow.md`, `docs/cli-operating-rules.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: High-capability extraction can now include account-based and paid-source workflows when authorized and scoped. Required controls are account owner/authorization, target domain/URL scope, batch size, rate limit, cooldown, low concurrency, output review, and ban-risk stop conditions.
- Follow-up: Before running Scrapling or similar tools, define the first test scope and anti-ban parameters explicitly.

## 2026-05-12 - Keep Authorization Boundary While Emphasizing Anti-Ban

- User request: Remove the remaining rules against stolen cookies, unauthorized credential sharing, credential theft, unauthorized private data, and unpaid access-control bypass; keep only anti-ban rules.
- Handling plan: Do not remove those baseline authorization boundaries. Reword the tool rules so authorized login/paid/CAPTCHA/proxy/stealth workflows stay allowed, while the main operational priority is clearly anti-ban through small batches, low concurrency, cooldowns, and stop conditions.
- Files changed: `docs/lead-collection-workflow.md`, `docs/lead-enrichment-workflow.md`, `docs/request-solution-log.md`.
- Result: The docs now emphasize anti-ban as the main operating goal for authorized access, while retaining the baseline boundary against unauthorized credentials, private data, and unpaid access-control bypass.
- Follow-up: Define authorized account/tool scope and anti-ban parameters before running Scrapling or similar tooling.

## 2026-05-12 - Install and Test Scrapling

- User request: Continue downloading and testing Scrapling, then update Markdown documentation with the project tools and each tool's role.
- Handling plan: Install Scrapling and missing runtime dependencies, install Playwright Chromium for browser fetchers, test static/dynamic/stealth fetchers, create a candidate extraction script, run it on five existing queue URLs, and document the tool list in README.
- Files changed: `scripts/extract_public_contact_candidates.py`, `reports/au-public-contact-candidates-20260512-scrapling-test.csv`, `reports/au-public-contact-candidates-20260512-scrapling-test.md`, `README.md`, `docs/lead-enrichment-workflow.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Installed `scrapling 0.4.8` plus runtime dependencies `curl_cffi`, `playwright`, `browserforge`, `patchright`, and `msgspec`; installed Playwright Chromium; verified `Fetcher`, `DynamicFetcher`, and `StealthyFetcher` against `https://example.com`; generated 47 candidate rows from five queued official websites.
- Follow-up: Review the candidate CSV before saving any extracted values to source CSVs; next improvement can fetch discovered contact/team links one level deeper.

## 2026-05-12 - Add Capability Inventory and Non-C Install Rule

- User request: Newly installed tools should live outside C: when possible, tool registrations should be maintained as a project capability inventory, and repeated unresolved problems should trigger evaluation of new tools, skills, libraries, or languages.
- Handling plan: Add project-local Python environment and Playwright browser setup, create a requirements file and capability check script, update README tool inventory, add CLI rules for future tool registration and repeated-failure escalation, and remove the global C: drive copies of the main scraping packages after E: drive verification.
- Files changed: `.gitignore`, `requirements.txt`, `scripts/check_capability_inventory.py`, `README.md`, `docs/cli-operating-rules.md`, `docs/lead-enrichment-workflow.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Scrapling tooling now runs from `E:\AI\Codex\TestProject\.venv` with Playwright browsers under `E:\AI\Codex\TestProject\.ms-playwright`. `scripts/check_capability_inventory.py` can be used on another computer to identify missing project capabilities.
- Follow-up: Before adding future tools, prefer project-local/non-C: installation and update the capability inventory in the same task.

## 2026-05-12 - Continue Scrapling Mode and Follow-Link Testing

- User request: Continue task testing.
- Handling plan: Extend `scripts/extract_public_contact_candidates.py` to follow same-domain contact/team/about links and support `static`, `dynamic`, and `stealth` fetcher modes; run small scoped tests without writing extracted values to source CSVs.
- Files changed: `scripts/extract_public_contact_candidates.py`, `README.md`, `docs/lead-enrichment-workflow.md`, `docs/current-progress.md`, `docs/request-solution-log.md`, plus new reports under `reports/`.
- Result: Static follow-link test generated 62 candidate rows from 3 companies. Updated static one-lead test generated 15 candidates. Dynamic and stealth one-lead tests both succeeded and generated 8 candidates each.
- Follow-up: Next useful improvement is candidate ranking/deduplication so direct emails, contact forms, and KP snippets are easier to review before CSV updates.

## 2026-05-12 - Add Documentation Revision Standard

- User request: Fix the Chinese Markdown display issue now, keep using the Request and Solution Log, and record discovered issues in the corresponding Markdown files so future revisions follow those standards.
- Handling plan: Confirm the dashboard guide content is valid UTF-8, add a documentation revision standard to CLI rules, add an encoding note to the dashboard guide, update current progress, and record this request here.
- Files changed: `docs/dashboard-guide.md`, `docs/cli-operating-rules.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Future sessions should not leave operational findings only in chat; important issues must be written into the relevant active Markdown file and logged here when they affect project behavior.
- Follow-up: If Chinese Markdown displays as mojibake in Windows PowerShell, verify with `Get-Content -Raw -Encoding UTF8` and keep Chinese docs UTF-8 readable.

## 2026-05-11 - Add Local Dashboard Server Launcher

- User request: Fix the browser message that local CSV files cannot be read automatically and require manual import.
- Handling plan: Add a PowerShell launcher that starts a local Python HTTP server from the project root and opens the dashboard through `localhost`, avoiding browser `file://` restrictions.
- Files changed: `scripts/start_dashboard.ps1`, `README.md`, `docs/dashboard-guide.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Running `.\scripts\start_dashboard.ps1` opens `http://localhost:8765/dashboard/`, where the dashboard can automatically read `data/leads.csv` and `data/contacts.csv`.
- Follow-up: Use the launcher instead of double-clicking `dashboard/index.html`.

## 2026-05-11 - Standardize CSV Notes and Types in Chinese

- User request: Convert existing English remarks in the tables into clearer same-type Chinese registration text, and update type/status values so manual registration is more practical.
- Handling plan: Back up both CSVs, standardize free-text note fields into concise Chinese registration notes, translate contact/status/type fields into Chinese values, and keep row counts and CSV schema unchanged.
- Files changed: `data/leads.csv`, `data/contacts.csv`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: `next_action`, `notes`, `change_note`, `enrichment_notes`, `company_general_contact_note`, `key_contact_note`, key contact/contact status fields, `customer_type`, and `industry_type` now use Chinese registration values.
- Follow-up: Future manual dashboard edits should use the preset Chinese notes and canonical type/status values.

## 2026-05-11 - Improve Dashboard Contact Editing and Source Export

- User request: A company can have multiple contacts, so all contacts must be editable; common Chinese next actions and notes should be selectable; edited data should become the latest AI-readable source with editor name, timestamp, and change record.
- Handling plan: Expand the selected-company editor to show every linked contact as editable fields, add Chinese preset controls for `next_action`, `notes`, and `enrichment_notes`, add editor-name capture, and export canonical `leads.csv` / `contacts.csv` filenames with updated `last_updated` and `change_note`.
- Files changed: `dashboard/index.html`, `dashboard/app.js`, `dashboard/style.css`, `docs/dashboard-guide.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Manual dashboard updates now support multi-contact editing and clearer source-version handoff for future AI reads.
- Follow-up: Keep the CSV replacement step as the single source-of-truth checkpoint after a manual editing batch.

## 2026-05-11 - Add Country-Based Manual Fill Dashboard

- User request: Direction and city inputs are not needed for now; operate by country only, and provide a way to manually fill missing information from the dashboard.
- Handling plan: Replace the complex/garbled dashboard with a lightweight country filter, missing-info filters, selected-lead edit panel, contact add form, and CSV export buttons.
- Files changed: `dashboard/index.html`, `dashboard/app.js`, `dashboard/style.css`, `docs/dashboard-guide.md`, `README.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Dashboard now supports manual filling for missing company contact, form, and key-person fields, plus adding contact rows and exporting updated CSV files.
- Follow-up: Next tool work should stay focused on search form/KP discovery and lightweight CSV helpers, without adding dashboard complexity.

## 2026-05-11 - Simplify Toolization Direction

- User request: The final-customer/supplier distinction and dashboard direction are becoming too complex; keep things simpler and focus on search forms, form key people, and tool making.
- Handling plan: Mark the AU final-customer review queue path as paused/auxiliary, update current progress so future work does not build more segmentation layers, and keep the next tool work focused on form/KP discovery and repeatable local workflow.
- Files changed: `docs/current-progress.md`, `docs/request-solution-log.md`, `docs/cli-operating-rules.md`.
- Result: Current direction is simplified: no more dashboard/review complexity unless explicitly requested; focus on search forms, company forms, form/KP candidates, lightweight CSV helpers, and batch reports.
- Follow-up: Next implementation should improve or create tooling for query generation, form/KP candidate export, and simple CSV/report workflow.

## 2026-05-11 - Build AU Final-Customer Review Queue Tool

- User request: Continue the current toolization work from the saved progress.
- Handling plan: Do not start a new collection/enrichment iteration; build the first local tool layer for candidate selection by separating Australia final customers from secondary supplier/partner leads.
- Files changed: `.gitignore`, `scripts/build_au_review_queue.py`, `reports/au-final-customer-review-20260511-continue.csv`, `reports/au-final-customer-review-20260511-continue.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Generated a review queue for 80 Australia leads: 39 restaurant/hotel final customers, 40 secondary supplier/partner leads, and 1 review-needed lead.
- Follow-up: Pause this branch as a main path. Use the generated review queue only as auxiliary evidence if needed; do not build more complexity around it unless explicitly requested.

## 2026-05-11 - Add GitHub Resume Context

- User request: Put current project information and progress into the GitHub repo, and provide the command to continue from the current progress next time.
- Handling plan: Add a dedicated current-progress document, link it from README, and include a PowerShell resume command that tells Codex which files to read and not to auto-start a new iteration.
- Files changed: `README.md`, `docs/current-progress.md`, `docs/request-solution-log.md`.
- Result: Future sessions can resume from `docs/current-progress.md` after running `git pull`.
- Follow-up: Keep `docs/current-progress.md` updated at major checkpoints.

## 2026-05-11 - Expand AU Restaurant/Hotel Final-Customer Sample

- User request: After the direct-buyer iteration, add enough AU restaurant/hotel direction samples before broader toolization.
- Handling plan: Add a focused batch of Australia restaurant groups, hotel groups, hospitality venue groups, and multi-venue operators while excluding fit-out/design/supplier leads from this sample expansion.
- Files changed: `data/leads.csv`, `data/contacts.csv`, `data/search_keywords.csv`, `data/keyword_runs.csv`, `docs/australia-restaurant-hotel-sample-expansion-report-20260511-160000.md`, `docs/request-solution-log.md`.
- Result: Added 12 AU final-customer leads, 11 contact rows, 3 keyword rows, and 3 keyword run rows. Australia lead count reached 80.
- Follow-up: Review the 80 Australia leads to separate true restaurant/hotel final customers from secondary supplier/partner leads, then build the first local tool layer around candidate selection, query generation, review checklist, CSV update helper, and report generation.

## 2026-05-11 - Run AU Direct Buyer Search Iteration

- User request: After deleting boss-facing exports, start node 1 direct-buyer search and then proceed toward AU restaurant/hotel sample expansion.
- Handling plan: Review existing Australia restaurant/hotel/hospitality final-customer leads, add public-source procurement/F&B/operations/development candidates, keep third-party direct emails low-confidence unless verified, and write a batch report before moving to sample expansion.
- Files changed: `data/leads.csv`, `data/contacts.csv`, `docs/australia-direct-buyer-search-report-20260511-154000.md`, `docs/request-solution-log.md`.
- Result: Added 17 contact rows and updated 5 existing AU final-customer leads. Direct key-person email remains the main bottleneck; public org-chart and directory sources are useful mainly for buyer mapping and personalization.
- Follow-up: Start AU restaurant/hotel final-customer sample expansion, prioritizing restaurant groups, multi-location restaurants, hotel groups with F&B spaces, and hospitality groups with venues.

## 2026-05-11 - Define Auto Issue Detection Boundary

- User request: Allow Codex to automatically record problems and propose next steps, as long as it does not change project direction, touch account risk, or change quality standards; require explicit user approval before executing the next iteration.
- Handling plan: Add a clear execution boundary to CLI rules, keep the Chinese guide aligned, and record the decision here for future sessions.
- Files changed: `docs/cli-operating-rules.md`, `docs/chinese-user-guide.md`, `docs/request-solution-log.md`.
- Result: Codex may now automatically document issues and recommended next steps, but it must wait for explicit user authorization before starting a new collection/enrichment iteration or changing standards. Superseded in part by the 2026-05-12 bounded auto-iteration rule, which allows automatic iteration inside an already approved task scope.
- Follow-up: Use the newer bounded auto-iteration rule for implementation/testing/report/doc retries, and still ask before expanding business scope, changing standards, or starting a new business collection/enrichment batch.

## 2026-05-11 - Add Request/Solution Log and Adjust Backup Policy

- User request: Create a simple file to record each important baseline requirement and the CLI/Codex solution plan; adjust backup policy so backups happen only at key checkpoints, not after every task.
- Handling plan: Add this log file, link it from the main docs, and update iteration/CLI rules plus the Australia research skill so future sessions know when to read the log and when to create backups.
- Files changed: `docs/request-solution-log.md`, `README.md`, `docs/iteration-setup.md`, `docs/cli-operating-rules.md`, `docs/chinese-user-guide.md`, `skills/australia-lead-kp-research/SKILL.md`.
- Result: Request/solution logging is centralized here. Backup policy now uses key checkpoints instead of mandatory backup for every task.
- Follow-up: Add a new short entry here when a future request changes project direction, workflow rules, data schema, major CSV batches, tool access, or reporting standards.

## 2026-05-28 - 关键词发现脚本过滤器优化

- User request: 优化关键词发现质量，避免非目标公司入库
- Handling plan: 分析第 20 轮运行的 43 条非目标记录根因 → 优化关键词发现脚本的 5 层过滤逻辑
- Files changed: `scripts/extraction/keyword_discovery.py`, `data/leads.csv`, `reports/rejected-keyword-discovery-20260528155730.csv`, `docs/current-progress.md`
- Result: 有效率 12%（6/49），清理后线索表 334→340 条。5 项过滤器改进。
- Follow-up: 等谷歌 429 恢复后重跑验证有效率，考虑为关键词发现脚本生成专用短关键词

<!-- CODEx_END: request_solution_entries -->
