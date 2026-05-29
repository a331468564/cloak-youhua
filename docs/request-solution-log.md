<!-- DOC_META
lifecycle:  long-term
audience:   both
write_when: After each user request or solution change, append an entry
read_when:  When looking up historical requests/solutions
delete_when: Do not delete (old entries archived to archive/)
-->
# Request and Solution Log

<!-- CODEx_START: request_solution_log_rules -->
*Updated: 2026-05-26*

Purpose: keep a short, readable record of important user requests and the CLI/Codex handling approach.

Use this file for project-level requests, workflow changes, data-structure changes, tool decisions, file-changing tasks, and other tasks that future sessions should quickly understand.

For every task-oriented conversation, Codex should check before finishing whether the conversation changed files, project rules, workflow decisions, data standards, tool behavior, or future operating context. If yes, add or update a concise entry in this file in the same turn.

Do not record every tiny lookup, routine read-only check, or casual clarification that does not affect future work. Keep entries brief.

Entry format:

```text
## YYYY-MM-DD - Short Title

- User request:
- Handling plan:
- Files changed:
- Result:
- Achievements:
  - ...
- Issues / limits:
  - ...
- Follow-up:
```

For new entries, use `Achievements` and `Issues / limits` as short lists when the task produced concrete outputs, decisions, test results, defects, blockers, or limits. Keep them concise and review-oriented. If there are no meaningful issues, write `None found` rather than inventing one. Older entries do not need to be backfilled unless they are being edited for another reason.

<!-- CODEx_END: request_solution_log_rules -->

## Blocker Recording Rules

**When encountering a blocker (debugging > 5 minutes), follow this workflow:**

1. **Classify** — Identify the major category and technical subcategory from the taxonomy tables in `docs/logs/changelog.md`.
2. **Lookup** — Search the "Historical Blocker Index" table in changelog.md for the same tag. If a match exists, apply the recorded Fix / Best Practice directly.
3. **Solve and Record** — If no match (or the recorded fix does not apply), debug normally, then append a new entry using this format:

```markdown
`[MAJOR-SUBCATEGORY]` **Blocker Title**
- **Symptom:** What happened
- **Root Cause:** Why it happened
- **Fix:** How it was fixed
- **Best Practice:** How to avoid it next time (one sentence)
```

After recording, also add a row to the "Historical Blocker Index" table in changelog.md for quick lookup.

---

## Log Entry Locations

This file has been reorganized. Entries are now split by age:

- **Current entries (last 30 days):** [docs/logs/changelog.md](logs/changelog.md)
  - Contains all entries from 2026-04-18 onwards
  - New entries should be added here

- **Archived entries (older than 30 days):** [docs/logs/archive/request-solution-log-2026-04.md](logs/archive/request-solution-log-2026-04.md)
  - Contains entries from April 2026 and earlier
  - Currently empty (all existing entries are within the 30-day window)

---

## Archival Policy

Entries older than 30 days should be moved from `docs/logs/changelog.md` to the appropriate archive file under `docs/logs/archive/`. Archive files are named by month: `request-solution-log-YYYY-MM.md`.

When archiving:
1. Move entries with dates before the 30-day cutoff to the archive file for that month
2. Update this index file if the archive file names change
3. Keep the `docs/logs/changelog.md` file containing only the last 30 days of entries

---

<!-- CODEx_START: request_solution_index -->
*Updated: 2026-05-18 00:00*

All entries have been moved to [docs/logs/changelog.md](logs/changelog.md).

See the "Log Entry Locations" section above for full details.

<!-- CODEx_END: request_solution_index -->

### 2026-05-21 09:03 — 全局 request-solution-log 钩子

**User request:** 加一个全局 Claude hook，每 5 轮人机对话后自动更新 request-solution-log 文件。如果项目没有该文件则自动创建。按指定中文格式记录对话内容。

**Handling plan:**
1. 创建全局钩子脚本 `~/.claude/hooks/auto_request_solution_log.py`
2. 在 `~/.claude/settings.json` 注册 PostToolUse 钩子
3. 通过计数器文件 `.rslog_counter.json` 跟踪工具调用次数
4. 每 5 次工具调用触发：查找项目中文件名含 "request"+"solution" 的 .md 文件，找到则追加模板条目，找不到则自动创建
5. 测试验证触发逻辑和文件创建/追加功能

**Files changed:**
- `C:\Users\Administrator\.claude\hooks\auto_request_solution_log.py` (new)
- `C:\Users\Administrator\.claude\settings.json` — 注册全局 PostToolUse 钩子
- `docs/current-progress.md` — 钩子表更新为 6 个
- `docs/logs/changelog.md` — 追加变更记录

**Result:** 钩子已上线，每 5 次工具调用自动触发。文件查找改为按文件名匹配（含 "request"+"solution"），不再依赖硬编码路径。文件不存在时自动创建并写入 DOC_META 模板。

**Achievements:**
- 全局钩子对所有项目生效，无需逐项目配置
- 自动创建 + 自动追加模板，减少 agent 遗漏
- matcher 从 `""` 修正为 `"*"` 才能正确匹配所有工具调用

**Issues / limits:**
- 钩子只能追加模板，实际内容需 agent 根据对话上下文填充
- 计数基于工具调用次数，非精确人机轮次（一轮可能 2-5 次调用）

**Follow-up:**
- 下个会话验证钩子在新窗口中的自动触发效果
- 观察是否需要调整触发频率（当前 5 次）

## 2026-05-26 - 表单收集 Run 15

**User request:** 做表单收集任务

**Handling plan:** 读取 AGENTS.md + current-progress.md A 区 + lead-collection-workflow.md → 构建候选队列 → 3 批 extraction → 保存到 leads.csv

**Files changed:**
- `data/leads.csv` — 更新 16 家公司联系路由（+6 邮箱、+12 电话、+4 表单）
- `docs/current-progress.md` — 更新 A 区数据和 Run 15 记录

**Result:** 24 候选队列，453 候选提取。覆盖率 91%→94%（262/277）。AU 无联系：15→5。

**Achievements:**
- Bentley Restaurant Group: 6 邮箱 + 3 电话 + LinkedIn
- Australian Venue Co.: 3 邮箱（含 procurement@）+ 表单 + LinkedIn
- ALH Group / Gambaro Group: 新增邮箱
- Lancemore / Meriton / Ovolo / Taverners: 新增电话

**Issues / limits:**
- 剩余 5 条 AU 无联系线索为硬骨头（SSL/404/无公开联系页）
- 剩余 10 条非 AU 线索为低优先级

## 2026-05-28 - keyword_discovery.py 过滤器优化

**User request:** 优化关键词发现质量，避免非目标公司入库

**Handling plan:** 分析 Run 20 的 43 条非目标记录根因 → 优化 keyword_discovery.py 的 5 层过滤逻辑

**Files changed:**
- `scripts/extraction/keyword_discovery.py` — 5 项过滤器优化
- `data/leads.csv` — 清理 43 条非目标，保留 6 家 AU 公司
- `reports/rejected-keyword-discovery-20260528155730.csv` — 被拒记录存档
- `docs/current-progress.md` — 更新 B 区 Run 20 记录

**Result:** 有效率 12%（6/49），清理后 leads.csv 334→340

**Achievements:**
- 根因分析：53% 新闻/文章、14% 学生公寓、12% 行业协会、7% 招聘、14% 教育/政府
- 5 项过滤器改进：域名排除列表扩展 +120、文章/目录 URL 模式过滤、AU 查询自动增强（`site:.com.au`）、联系信号检测、文章标题检测
- 保留 6 家目标公司：Mimosa Wines / The Winery Surry Hills / Southern Cross Motel / Australian Motel / Salter Brothers / Regional Motel Partners

**Issues / limits:**
- 谷歌 429 限流，优化效果待下次验证
- 长关键词（>5 词）加 `site:.com.au` 后返回 0 结果，需生成更短的发现型关键词
- 域名排除列表需持续维护（新发现的非目标域名需手动添加）

**Follow-up:**
- 等谷歌 429 恢复后重跑验证有效率
- 考虑为关键词发现脚本生成专用短关键词（区别于调度器的长关键词）

## 2026-05-29 - Claude Code IDE API 400 修复

**User request:** 排查项目 IDE 里的 Claude Code 报错 `API Error: 400 messages[1].role must be either 'user' or 'assistant', but got 'system'`，终端手动清理 `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_MODEL` 后可正常输出，但 IDE Claude Code 仍不可用。

**Handling plan:** 对比终端和 IDE 的环境变量来源，检查 VS Code 用户设置、项目 `.vscode/settings.json`、用户级 `.claude/settings.json` 和 Windows HKCU 环境变量。

**Files changed:**
- `C:\Users\Administrator\AppData\Roaming\Code\User\settings.json` - 从 `claudeCode.environmentVariables` 移除第三方 `ANTHROPIC_*` 中转和模型覆盖，仅保留非必要流量/遥测关闭项。
- `C:\Users\Administrator\.claude\settings.json` - 清空用户级 `env` 中的默认 mimo 模型覆盖。
- Windows HKCU Environment - 移除 `ANTHROPIC_BASE_URL`、`ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_MODEL` 及默认模型覆盖项。

**Result:** 配置回读验证通过；VS Code 用户设置和 Claude 用户设置已不包含第三方 Anthropic 覆盖项，HKCU 仅剩 `ANTHROPIC_API_KEY`。需要重启 VS Code / Reload Window 后 IDE Claude Code 才会使用新环境。

**Achievements:**
- 定位根因是 IDE panel 继承了持久化中转配置，不是项目 `.claude` hook 脚本语法问题。
- 修复了 VS Code Claude Code 插件层和 Windows 用户环境变量层的冲突配置。

**Issues / limits:**
- 已运行的 VS Code/Claude Code 进程可能仍缓存旧环境，必须重启窗口或退出 VS Code 后重新打开。
- `ANTHROPIC_API_KEY` 仍保留，因为用户验证可工作的终端命令未清除此项；如后续官方登录仍异常，再单独移除或轮换。
