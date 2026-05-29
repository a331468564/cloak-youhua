<!-- DOC_META
lifecycle:  long-term
audience:   both
write_when: 项目规则、工作流、工具配置变更时更新
read_when:  每次会话启动时读取（AGENTS.md 之后）
delete_when: 不删除
-->
# Project Instructions

## Data Safety — NEVER VIOLATE

`data/leads.csv` and `data/contacts.csv` are **append-only**. Never delete or overwrite existing records.

- Before writing: backup → dry-run → merge report → confirm record count only increases.
- Filtered-out data → `reports/rejected-{timestamp}.csv`, never silently deleted.
- Unverifiable data → mark `needs_review`, do not delete.
- Valid rate < 50% → pause batch expansion, report and optimize.
- Detailed rules in `.claude/rules/data-safety.md` (auto-loaded when accessing `data/`).

## Blocker Handling — Same issue 2–3 times, STOP

When a blocker is hit (same issue, 2–3 attempts with no progress), stop debugging:

1. **Classify** — Tag with `[CATEGORY-SUBCATEGORY]` from `docs/logs/changelog.md`.
2. **Lookup** — Check "Historical Blocker Index" in changelog. If match exists, apply recorded fix.
3. **Solve and Record** — If no match, solve, then append entry with Symptom / Root Cause / Fix / Best Practice.

Common tags: `NET-FETCH-HTTP-429`, `NET-FETCH-HTTP-403`, `NET-FETCH-TLS`, `DATA-QUALITY-FILTER`, `DATA-QUALITY-DEDUP`, `TOOL-SCRIPT-ERROR`

Shared rule — see AGENTS.md Blocker Handling for full table. A区 and B区 agent 启动时读 AGENTS.md 即可。

## Entry Rule

**Before any task, read `AGENTS.md` first.** It defines operating rules, task-specific context file lists, documentation rules, and safety boundaries. Follow its "Read First" section.

**Then read `docs/current-progress.md`.** It contains the latest project status, data snapshot, what has been done, and what needs to be done next.

## Project Overview

B2B lead research for Australian restaurant/hotel industry. Two task zones:
- **A区 (KP 管线):** Known company → find contacts. Read `docs/workflows/lead-collection-workflow.md`.
- **B区 (关键词发现):** Unknown market → discover companies. Read `docs/workflows/keyword-discovery-workflow.md`.

## Critical Reminders

1. **ALWAYS check existing data before extraction** — load `data/leads.csv` and `data/contacts.csv` first.
2. **STOP when thresholds reached** — 5 min / 3 pages / 70% unhelpful for KP search.
3. **Mark status accurately** — `已找到联系路径` / `需人工确认` / `低优先级`.
4. **ALWAYS clean up test artifacts** — `git status` after scripts, delete `temp_*` / `test_*` / `debug_*`.
5. **Hooks are active** — `.claude/settings.json` enforces destructive command blocking, post-script artifact check, DOC_META check on new docs, pre-exit stray file check.
6. **A区 and B区 independent** — do not mix updates.
7. **Run report after every batch** — A区用 `generate_run_report.py --auto-stats --auto-timing`，B区用 `generate_keyword_report.py --auto-timing`，汇总用 `generate_summary.py`
8. **输出使用中文** — 所有对用户的文字回复、状态更新、任务说明使用中文。代码注释、变量名、commit message、技术术语保持英文。

## Commands Quick Reference

```bash
# A区 — KP 管线（表单收集）
python -m scripts.kp_pipeline.run_pipeline --stage all --limit 40

# B区 — 关键词调度器
python -m scripts.keyword_scheduler.scheduler --limit 10
python -m scripts.keyword_scheduler.generator --dry-run --max 50

# Run 报告（A区）
python scripts/reports/generate_run_report.py --auto-stats --auto-timing

# Run 报告（B区）
python scripts/reports/generate_keyword_report.py --auto-timing

# 汇总仪表盘
python scripts/reports/generate_summary.py

# 看板
.\scripts\utils\start_dashboard.ps1
```

## Detailed Rules (auto-loaded by path)

| Rule File | paths | Content |
|-----------|-------|---------|
| `.claude/rules/data-safety.md` | `data/**` | Append-only, dedup, batch quality, recovery |
| `.claude/rules/extraction-rules.md` | `scripts/extraction/**`, `reports/**` | Collection thresholds, KP rules, decision flowchart, data quality |
| `.claude/rules/tool-config.md` | `scripts/**` | CloakBrowser config, KP pipeline, dashboard |

## Skills (invoke with /command)

| Skill | Trigger | Content |
|-------|---------|---------|
| `/kp-discovery` | KP pipeline tasks | KP 三阶段流程 + 阻塞处理 |
| `/keyword-discovery` | Keyword discovery tasks | 关键词调度器 + 发现脚本 + 过滤器 |

## Proxy Rotation (CloakBrowser 专用)

CloakBrowser 使用独立代理实例（端口 7898），支持多 IP 自动轮换 + 仿人浏览行为。

- **配置目录：** `config/proxy-rotation/`（独立管理，含 mihomo 配置和使用说明）
- **设计文档：** `docs/superpowers/specs/2026-05-29-stealth-proxy-rotation-design.md`
- **使用说明：** `config/proxy-rotation/README.md`
- **触发场景：** `search_google()` / `cloak_fetch()` 访问 Google 时自动生效
- **不影响：** 系统其他软件的代理流量（主 Clash Verge Rev 端口 7897 不变）
