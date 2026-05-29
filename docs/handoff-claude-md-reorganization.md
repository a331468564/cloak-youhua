<!-- DOC_META
lifecycle:  temporary
audience:   user
write_when: 交接文档，审核后可删除
read_when:  A 区 CC 审核时读取
delete_when: 审核完成后删除
-->
# Handoff: CLAUDE.md 精简重组方案

## 当前问题

CLAUDE.md 当前 360 行（15.2 KB），远超官方建议的 200 行上限。导致：

1. **关键规则被淹没** — 阻塞处理流程在第 360 行，agent 启动时读了但没执行（触发条件已从"5 分钟"改为"2–3 次尝试无进展"）
2. **上下文压力** — 每次会话启动就消耗 15 KB 上下文，留给实际工作的空间减少
3. **规则冲突风险** — CLAUDE.md 和 AGENTS.md 有重复内容（如数据安全规则），可能产生歧义

## 官方依据

Claude Code 官方文档（2026-05-28 查询）：

> "Target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."

> "If your CLAUDE.md is too long, Claude ignores half of it because important rules get lost in the noise."

> "If an entry is a multi-step procedure or only matters for one part of the codebase, move it to a skill or a path-scoped rule instead."

## 方案概要

### 精简 CLAUDE.md（360 行 → < 180 行）

**保留（每次启动必须知道）：**
- 入口规则（先读 AGENTS.md 再读 current-progress.md）
- 阻塞处理流程（从底部移到顶部，触发条件已改为"2–3 次尝试无进展"）
- 数据文件安全核心禁令（append-only、不能删除、不能覆盖）
- 关键提醒（精简到 8 条以内）
- 常用命令速查（A区 + B区）

**移除（移到 .claude/rules/ 按需加载）：**
- Rule 1-3b: 收集阈值、KP 搜索规则、多 KP 发现 → `extraction-rules.md`
- Rule 4-5: 去重、决策流程图 → `extraction-rules.md`
- Rule 6: 数据质量标准 → `extraction-rules.md`
- Rule 6b: CloakBrowser 配置 → `tool-config.md`
- Rule 7-8: 脚本用法、报告审核 → `extraction-rules.md`
- Rule 10: 运行报告生成 → `extraction-rules.md`
- Tools and Workflows → `kp-pipeline-rules.md` + `keyword-discovery-rules.md`
- File Structure → 不放 rules 里（agent 可以 ls 查看）
- Data Provenance & Recovery → `data-safety.md`

### 新建 .claude/rules/ 目录（3 个文件）+ skills（2 个）

**rules（被动约束，按需加载）：**

| 文件 | paths 匹配 | 内容 |
|------|-----------|------|
| `data-safety.md` | `data/**` | Rule 9 完整版 + 数据恢复 + 批次质量控制 |
| `extraction-rules.md` | `scripts/extraction/**`, `reports/**` | Rule 1-5, 6, 7, 8, 10 |
| `tool-config.md` | `scripts/**` | CloakBrowser 配置 + Dashboard |

**skills（多步流程，按需调用）：**

| 文件 | 触发方式 | 内容 | 状态 |
|------|---------|------|------|
| `skills/kp-discovery/SKILL.md` | `/kp-discovery` 或 agent 匹配 | KP 管线三阶段用法 | ✅ 已创建 |
| `skills/keyword-discovery/SKILL.md` | `/keyword-discovery` 或 agent 匹配 | 关键词调度器 + 发现脚本 | ✅ 已创建 |

### 阻塞处理流程加强

移到 CLAUDE.md 顶部（Entry Rule 之后），增加**主动触发点**：

- 遇到同一问题 2-3 次无进展 → 立即查表登记
- 工具返回非预期错误 → 立即查表登记
- 数据有效率 < 50% → 立即查表登记
- **阶段结束回顾** — 每个阶段任务完成后，检查是否有未登记的阻塞

## 实施计划（两步走）

### Step 1: B区架构整改（先做）

B区（关键词发现）目前只有一个 guide 文件，缺少 workflow 级别的规则和 CODEx 标记。需要仿照 A区结构补齐。

**新建 `docs/workflows/keyword-discovery-workflow.md`**，包含以下 CODEx 区块：

| CODEx 标记 | 内容 | 参考 A区 对标 |
|------------|------|--------------|
| `discovery_workflow` | 整体流程（关键词选择→搜索→过滤→入库→A区衔接） | `lead_discovery_workflow` |
| `discovery_quality_rules` | 每批质量标准（valid rate ≥ 50%，否则暂停） | `enrichment_threshold_rule` |
| `keyword_stopping_rules` | 关键词停止条件（3 次 0 线索→自动 Paused） | `enrichment_stopping_rules` |
| `batch_validation` | 批次验证（入库前去重、过滤、域名检查） | `entity_dedup_rule` |
| `discovery_to_enrichment_trigger` | 什么条件下提示 A区接手 | `b_to_a_auto_flow` |
| `keyword_health_metrics` | 关键词健康指标（发现质量分、可联系性分、有效率） | 无对标，新建 |

**同步调整：**
- `keyword-scheduler-guide.md` 保留为操作指南（命令、配置、架构图），规则迁移到新 workflow
- `current-progress.md` B区运行记录格式与 A区对齐（Run 编号、指标、下一步）
- 标记命名遵循 AGENTS.md 的 CODEx 标记治理规则（大类划分，不重复）

### Step 2: CLAUDE.md 精简 + 最佳实践对标（Step 1 完成后）

在 B区架构整改完成后，执行 CLAUDE.md 精简方案（见上方"方案概要"），同步更新：

- 阻塞触发条件统一为 "2–3 次尝试无进展"（已更新 AGENTS.md / CLAUDE.md / keyword-scheduler-guide.md）
- CLAUDE.md Rule 3/3b 的 "5 分钟" **保持不变**（这是 KP 搜索投入上限，不是阻塞检测。仅改阻塞检测触发条件为 "2–3 次尝试无进展"）
- Critical Reminders 精简到 8 条以内
- **CLAUDE.md 前 20 行**只放最常被违反的规则（数据安全 + 阻塞查表），不放入口说明
- ~~**KP 管线和关键词发现**改为 skills~~ ✅ 已完成（`skills/kp-discovery/SKILL.md`、`skills/keyword-discovery/SKILL.md`）
- **加 `PostToolUse` hook** 检测连续失败，自动注入阻塞查表提醒（作为 prompt 规则的强制触发层）
- **验证 `.claude/rules/` 的 `paths:` 机制**后再执行拆分
- **从 CLAUDE.md 移除**已迁移到 skills 的重复内容（Rule 1-8、Tools and Workflows 等）

## 今天新增的规则（需纳入 Step 2 迁移）

以下规则今天写入了项目文件，Step 2 精简时需要确保不丢失：

| 规则 | 位置 | 迁移目标 |
|------|------|----------|
| B→A Auto-Flow | `lead-collection-workflow.md` `b_to_a_auto_flow` | 保留原位 |
| Enrichment Threshold | `lead-collection-workflow.md` `enrichment_threshold_rule` | 保留原位 |
| CODEx 标记治理 | `AGENTS.md` Documentation Rules | 保留原位 |
| Blocker Handling（共享） | `AGENTS.md` Blocker Handling | 保留原位，A/B 区共用 |
| 阻塞触发条件 2–3 次 | AGENTS.md / CLAUDE.md / keyword-scheduler-guide.md | Step 2 统一迁移 |
| KP 管线三阶段流程 | `.claude/skills/kp-discovery/SKILL.md` | 已就位，Step 2 时从 CLAUDE.md 移除重复内容 |
| 关键词发现流程 + 过滤器 | `.claude/skills/keyword-discovery/SKILL.md` | 已就位，Step 2 时从 CLAUDE.md 移除重复内容 |
| 批次质量控制阈值 | 两个 skill 都有 | 有效率 < 50% 暂停，与 AGENTS.md Data Operation Rules 一致 |
| 阻塞处理流程 | 两个 skill 都有 | 引用 changelog.md 标签体系，与 AGENTS.md 一致 |
| 阶段结束回顾 | 两个 skill 都有 | 新增规则，确保阻塞不遗漏 |

## 当前状态

- Step 1（B区架构整改）：**skills 已创建，rules 和 workflow 待创建**
  - ✅ `.claude/skills/kp-discovery/SKILL.md` — 138 行，263 词，已生效（系统 skills 列表可见）
  - ✅ `.claude/skills/keyword-discovery/SKILL.md` — 148 行，297 词，已生效（系统 skills 列表可见）
  - ❌ `.claude/rules/` 目录尚未创建（3 个 rules 文件待建）
  - ❌ `docs/workflows/keyword-discovery-workflow.md` 尚未创建（B 区 CODEx 标记待补）
- Step 2（CLAUDE.md 精简）：方案已设计，等 Step 1 完成后执行
- 执行时会先备份现有 CLAUDE.md

## B 区审查发现（2026-05-28）

### 已修正

- **Rule 3 "5 分钟"不应改为"2–3 次"** — Rule 3 的 "5 分钟 / 3 页" 是 KP 搜索投入上限（控制单个线索的搜索成本），不是阻塞检测。已修正 Step 2 描述，Rule 3 保持不变。

### 待闭环

1. **Step 1 执行者未指定** — B 区架构整改由谁做？当前 B 区工作由关键词发现会话负责，但 handoff 给了 A 区 CC。需明确分工。

2. ~~**`blocker_handling` 标记重复**~~ **已解决** — `blocker_handling` 已从 `lead-collection-workflow.md` 移到 `AGENTS.md` 作为共享规则，Step 1 表格已移除该行。A/B 区 agent 启动时读 AGENTS.md 即可获取阻塞处理规则，无需各自定义。

3. **`.claude/rules/` 的 `paths:` 未验证** — 建议 Step 2 之前先做小测试：创建 `.claude/rules/test.md` 加 `paths:` 前言，确认新会话能按需加载。

4. **`keyword_health_metrics` 无 A 区对标** — B 区独立指标，需确认不会和 `kp_metrics.json` 产生数据冲突。

## 最佳实践对标缺口（2026-05-28 多源研究）

### 缺口 1: 阻塞流程需要 hook 强制执行

**来源：** Claude 官方 hooks 文档 — "CLAUDE.md instructions shape Claude's behavior but are not a hard enforcement layer. To block an action regardless of what Claude decides, use a PreToolUse hook instead."

**现状：** 阻塞处理写在 AGENTS.md / CLAUDE.md 里，靠 agent 自觉执行。本次会话已证明 agent 不一定执行。

**建议：** 加 `PostToolUse` hook，检测到连续失败（同一工具连续报错 2-3 次）时，自动注入 `additionalContext` 提醒执行阻塞查表。不替代 CLAUDE.md 里的规则，而是作为**强制触发层**。

### 缺口 2: 关键规则应放 CLAUDE.md 最前 20 行

**来源：** "Lost in the Middle" (Liu et al., TACL 2023) — LLM 对上下文中间的指令遵循率呈 U 型曲线，开头和结尾最强，中间最弱。

**现状：** 方案说"阻塞流程移到 Entry Rule 之后"，但 Entry Rule 本身占了 5 行，阻塞流程可能不在前 20 行。

**建议：** CLAUDE.md 前 20 行只放最常被违反的规则（数据安全核心禁令 + 阻塞查表），入口说明和项目概述放后面。

### 缺口 3: 多步流程应放 skills 不是 rules — ✅ 已解决

**来源：** Claude 官方 — "If an entry is a multi-step procedure or only matters for one part of the codebase, move it to a skill or a path-scoped rule instead." Skills 适合多步流程，rules 适合被动约束。

**现状：** ✅ 已创建两个 skill：
- `.claude/skills/kp-discovery/SKILL.md` — KP 管线三阶段（138 行，263 词）
- `.claude/skills/keyword-discovery/SKILL.md` — 关键词发现流程（148 行，297 词）

`docs/workflows/` 下的 workflow 文件保留为人类参考，skills 里放 agent 可执行的步骤。

### 缺口 4: DOC_META 用 HTML 注释节省 token

**来源：** Claude 官方 — HTML 注释（`<!-- ... -->`）在注入上下文前被剥离，零 token 成本。

**现状：** 每个 .md 文件的 DOC_META 块消耗 token。

**建议：** DOC_META 保持 `<!-- DOC_META ... -->` 格式（当前已是），确认所有文件都用 HTML 注释而非纯文本。

### 缺口 5: 缺少具体验证步骤

**现状：** 风险部分提到 `.claude/rules/` 的 `paths:` 需要验证，但没有具体步骤。

**建议：** Step 2 之前加验证步骤：
1. 创建 `.claude/rules/test-paths.md`（带 `paths: ["scripts/test/**"]`）
2. 新开会话，读取 `scripts/test/` 下文件
3. 检查 agent 是否自动加载了 test-paths.md 的规则
4. 可选：用 `InstructionsLoaded` hook 审计加载时机

## 风险

- `.claude/rules/` 的 `paths:` 机制需要验证是否在当前 Claude Code 版本生效
- 拆分后需要确保没有规则丢失
- AGENTS.md 可能也需要同步调整（减少重复）
- Step 1 新建 workflow 后，需确认 agent 能通过 AGENTS.md 的 task context 找到新文件
- hook 强制执行阻塞查表需要测试，避免过度触发干扰正常工作
