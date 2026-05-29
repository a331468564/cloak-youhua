<!-- DOC_META
lifecycle:  temporary
audience:   user
write_when: V3 复制计划
read_when:  执行 V3 复制前读取
delete_when: V3 复制完成后删除
-->
# V3 复制计划：从 V2 1:1 复制 + 优化调整

*Created: 2026-05-28*

## 背景

V2 项目积累了完整的规则体系、工作流文档、钩子系统和数据管线。现在需要在 D 盘创建 V3 版本，先 1:1 复制 V2 的所有规范和代码，再按 handoff 文档的优化方案做结构调整。

**核心原则：** V3 启动时必须和 V2 规则完全一致，不能因为复制遗漏导致 agent 行为退化。

## V2 现状清单

### 指令文件（每次启动加载）

| 文件 | 行数 | 作用 |
|------|------|------|
| `CLAUDE.md` | 360 | 全局规则（入口、数据安全、工具配置、脚本用法） |
| `AGENTS.md` | ~167 | 操作规则（数据安全、文档规范、阻塞处理、标记治理、Blocker Handling） |
| `README.md` | 160 | 项目概述 |

### 工作流文档（CODEx 标记，按需读取）

| 文件 | 行数 | CODEx 区块数 | 覆盖 |
|------|------|-------------|------|
| `docs/workflows/lead-collection-workflow.md` | 338 | 10 | A区发现→收集→去重→阈值 |
| `docs/workflows/lead-enrichment-workflow.md` | 382 | 22 | A区富化→KP→LinkedIn→停止规则 |
| `docs/guides/cli-operating-rules.md` | 470 | 20+ | 任务分隔、CSV 操作、钩子配置 |
| `docs/guides/keyword-scheduler-guide.md` | 364 | 0 | B区操作指南（命令、配置、架构） |

### 钩子系统（强制执行层）

| 钩子 | 事件 | 作用 |
|------|------|------|
| `pre_bash_safety.py` | PreToolUse (Bash) | 拦截危险命令 |
| `post_bash_check.py` | PostToolUse (Bash) | 脚本运行后检查临时文件 |
| `post_blocker_detect.py` | PostToolUse (Bash) | 连续 2 次失败注入阻塞查表提醒 |
| `post_run_progress_check.py` | PostToolUse (Bash) | 管线运行后提醒更新进度 |
| `post_write_check.py` | PostToolUse (Write) | 新 .md 文件必须有 DOC_META |
| `stop_check.py` | Stop / SubagentStop | 未清理文件则阻止结束 |

**全局钩子（`~/.claude/hooks/`，不在项目内）：**

| 钩子 | 事件 | 作用 |
|------|------|------|
| `auto_request_solution_log.py` | PostToolUse (全局) | 每 10 次工具调用提醒追加 request-solution-log 条目 |

### 脚本（6,554 行）

| 模块 | 行数 | 功能 |
|------|------|------|
| `scripts/kp_pipeline/` | 1,466 | KP 管线三阶段（发现/富化/验证） |
| `scripts/keyword_scheduler/` | 1,313 | 关键词调度器（生成/执行/追踪/审核） |
| `scripts/extraction/` | 2,701 | 提取脚本（队列构建/候选提取/关键词发现） |
| `scripts/reports/` | 250 | Run 报告生成 |
| `scripts/analysis/` | 293 | Boss 报告 |
| `scripts/utils/` | 164+ | 能力检查、Dashboard 启动 |

### 配置

| 文件 | 行数 | 作用 |
|------|------|------|
| `config/workflow_rules.json` | 117 | 工作流阈值 |
| `config/kp_pipeline.json` | 74 | KP 管线阶段配置 |
| `config/keyword_scheduler.json` | 22 | 调度器配置 |
| `config/keyword_dimensions.json` | 103 | 关键词维度 + 查询模板 |

### 数据（空模板，不复制实际数据）

| 文件 | 字段数 | 说明 |
|------|--------|------|
| `data/leads.csv` | 53 | 主线索表（只复制 header） |
| `data/contacts.csv` | 21 | 联系人表（只复制 header） |
| `data/search_keywords.csv` | 29 | 关键词库（只复制 header） |
| `data/keyword_runs.csv` | 21 | 运行日志（只复制 header） |
| `data/kp_validation_log.csv` | 12 | 验证日志（只复制 header） |
| `data/outreach_log.csv` | 18 | 外联日志（只复制 header） |

### 其他

| 目录/文件 | 说明 |
|-----------|------|
| `dashboard/` | 3 文件（index.html / app.js / style.css） |
| `docs/superpowers/` | 计划和设计文档（可选复制） |
| `docs/handoff-claude-md-reorganization.md` | 优化方案（必须复制） |
| `.gitignore` | Git 忽略规则 |
| `requirements.txt` | Python 依赖 |

## 复制步骤

### Phase 1: 基础结构（先做）

```
D:\TestProject-v3\
├── CLAUDE.md                    ← 从 V2 复制
├── AGENTS.md                    ← 从 V2 复制
├── README.md                    ← 从 V2 复制（可改项目名）
├── .gitignore                   ← 从 V2 复制
├── requirements.txt             ← 从 V2 复制
├── .claude/
│   ├── settings.json            ← 从 V2 复制（含 6 个项目级钩子配置）
│   ├── settings.local.json      ← 从 V2 复制（权限配置）
│   ├── hooks/
│   │   ├── pre_bash_safety.py
│   │   ├── post_bash_check.py
│   │   ├── post_blocker_detect.py
│   │   ├── post_run_progress_check.py
│   │   ├── post_write_check.py
│   │   └── stop_check.py
│   └── skills/
│       ├── kp-discovery/SKILL.md
│       └── keyword-discovery/SKILL.md
├── skills/
│   └── australia-lead-kp-research/SKILL.md
├── config/
│   ├── workflow_rules.json
│   ├── kp_pipeline.json
│   ├── keyword_scheduler.json
│   └── keyword_dimensions.json
└── data/
    ├── leads.csv                ← 只复制 header（53 字段）
    ├── contacts.csv             ← 只复制 header（21 字段）
    ├── search_keywords.csv      ← 只复制 header（29 字段）
    ├── keyword_runs.csv         ← 只复制 header（21 字段）
    ├── kp_validation_log.csv    ← 只复制 header（12 字段）
    └── outreach_log.csv         ← 只复制 header（18 字段）
```

### Phase 2: 文档体系

```
docs/
├── current-progress.md          ← 从 V2 复制，重置数据快照为 0
├── workflows/
│   ├── lead-collection-workflow.md    ← 10 个 CODEx 区块
│   └── lead-enrichment-workflow.md    ← 22 个 CODEx 区块
├── guides/
│   ├── cli-operating-rules.md         ← 20+ CODEx 区块
│   ├── keyword-scheduler-guide.md     ← 操作指南
│   ├── codex-agent-usage.md
│   ├── dashboard-guide.md
│   ├── iteration-setup.md
│   └── chinese-user-guide.md
├── architecture/
│   ├── lead-table-fields.md
│   └── project-overview.md
├── handoff-claude-md-reorganization.md  ← 优化方案
└── logs/
    ├── changelog.md
    └── archive/
```

### Phase 3: 脚本

```
scripts/
├── kp_pipeline/                 ← 7 文件，1,466 行
│   ├── __init__.py
│   ├── config.py
│   ├── metrics.py
│   ├── stage2_enrich.py
│   ├── stage3_validate.py
│   ├── cloak_fetcher.py
│   └── run_pipeline.py
├── keyword_scheduler/           ← 9 文件，1,313 行
│   ├── __init__.py
│   ├── config.py
│   ├── generator.py
│   ├── scheduler.py
│   ├── executor.py
│   ├── tracker.py
│   ├── auto_review.py
│   ├── import_suggestions.py
│   └── market_intel.py
├── extraction/                  ← 6 文件，2,701 行
│   ├── build_au_review_queue.py
│   ├── build_form_kp_candidate_queue.py
│   ├── extract_public_contact_candidates.py
│   ├── generate_kp_form_queries.py
│   ├── generate_kp_search_tasks.py
│   └── keyword_discovery.py
├── reports/
│   └── generate_run_report.py
├── analysis/
│   └── build_boss_report.py
├── utils/
│   ├── check_capability_inventory.py
│   ├── start_dashboard.ps1
│   └── ...
├── workflow_checker.py
└── quick_check.py
```

### Phase 4: Dashboard

```
dashboard/
├── index.html
├── app.js
└── style.css
```

## 复制后必须验证

复制完成后，新会话启动时检查：

1. **入口规则** — agent 是否先读 AGENTS.md 再读 current-progress.md
2. **钩子系统** — 7 个钩子是否全部触发（试一个危险命令、一个脚本、一个 Write）
3. **CODEx 标记** — agent 做 A区任务时能否找到 `lead-collection-workflow.md` 的 10 个区块
4. **阻塞检测** — 连续 2 次失败后是否注入查表提醒
5. **数据安全** — agent 是否遵守 append-only 规则
6. **标记治理** — agent 是否遵守"不新增不必要标记"规则
7. **Skills 加载** — `/kp-discovery` 和 `/keyword-discovery` 是否出现在 skills 列表中
8. **全局钩子** — `auto_request_solution_log.py`（`~/.claude/hooks/`）在新环境下是否触发
9. **数据字段** — `leads.csv` header 确认有 53 个字段

## V3 优化调整（复制验证后执行）

按 `docs/handoff-claude-md-reorganization.md` 的两步计划：

### Step 1: B区架构整改

| 任务 | 状态 | 说明 |
|------|------|------|
| `skills/kp-discovery/SKILL.md` | ✅ 已完成 | 138 行，KP 管线三阶段 |
| `skills/keyword-discovery/SKILL.md` | ✅ 已完成 | 148 行，关键词发现流程 + 过滤器 |
| `.claude/rules/`（3 个文件） | ❌ 未开始 | data-safety / extraction-rules / tool-config |
| `docs/workflows/keyword-discovery-workflow.md` | ❌ 未开始 | 6 个 CODEx 区块 |
| `blocker_handling` 共享规则 | ✅ 已完成 | 在 AGENTS.md，A/B 区共用 |
| `post_blocker_detect.py` hook | ✅ 已完成 | 连续 2 次失败自动注入提醒 |

### Step 2: CLAUDE.md 精简

- 360 行 → < 180 行
- 前 20 行放最常被违反的规则（数据安全 + 阻塞查表）
- Rule 1-10 移到 `.claude/rules/`（3 个文件：data-safety / extraction-rules / tool-config）
- ~~KP 管线和关键词发现改为 `skills/`~~ ✅ 已完成
- ~~加 PostToolUse hook 阻塞检测~~ ✅ 已完成
- Rule 3/3b "5 分钟"保持不变（KP 搜索投入上限）
- 验证 `.claude/rules/` 的 `paths:` 机制后再拆分
- 从 CLAUDE.md 移除已迁移到 skills 的重复内容

## 复制命令参考

```powershell
# 创建 V3 目录
mkdir D:\TestProject-v3
cd D:\TestProject-v3

# 复制整个项目（排除 data 实际内容、reports、.venv、node_modules）
robocopy E:\AI\TestProject-v2 D:\TestProject-v3 /E /XD .venv node_modules __pycache__ exports /XF *.bak

# 清空数据文件只保留 header
python -c "
import csv, os
for f in ['data/leads.csv','data/contacts.csv','data/search_keywords.csv',
          'data/keyword_runs.csv','data/kp_validation_log.csv','data/outreach_log.csv']:
    if os.path.exists(f):
        with open(f, encoding='utf-8-sig') as fh:
            header = next(csv.reader(fh))
        with open(f, 'w', encoding='utf-8-sig', newline='') as fh:
            csv.writer(fh).writerow(header)
        print(f'Cleared: {f}')
"

# 清空 reports 目录
Remove-Item -Recurse -Force reports\*
mkdir reports

# 初始化 git
git init
git add .
git commit -m "V3 initial: 1:1 replicate V2 rules and structure"
```

## 风险

| 风险 | 缓解 |
|------|------|
| 复制遗漏导致 agent 行为退化 | 复制后验证清单（9 项检查） |
| data 文件 header 不完整 | 复制后对比 V2 header 字段数 |
| 钩子脚本路径依赖 | `settings.json` 用 `${CLAUDE_PROJECT_DIR}` 变量，不硬编码 |
| V3 和 V2 的 .claude/projects 路径不同 | 需确认 memory 路径是否需要调整 |
| handoff 中的优化可能影响 V3 稳定性 | 先 1:1 验证通过，再逐步优化 |
