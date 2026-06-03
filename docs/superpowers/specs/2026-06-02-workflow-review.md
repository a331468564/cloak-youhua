<!-- DOC_META
lifecycle:  temporary
audience:   both
write_when: 工作流审查时
read_when:  需要审查工作流与权威研究的对比时
delete_when: 审查完成后可删除
-->
# 工作流审查报告

*审查日期: 2026-06-02*

## 当前工作流

**文件**: `.claude/workflows/improve-contacts.js`

**目标**: 并行整改 B 区和测试 A 区，验证直联准确性，目标直联提升到 100

**Agent 数量**: 6 个

## 工作流结构

```
Phase 1: Analyze（并行）
  ├─ B 区突破专家：分析饱和原因
  └─ A 区提升专家：分析直联率低原因

Phase 2: Fix + Improve（并行）
  ├─ B 区：实施新搜索策略
  └─ A 区：实施直联提升方案

Phase 3: Validate
  └─ Quality Gate：验证产出

Phase 4: Verify
  └─ Contact Verifier：验证直联准确性

Phase 5: Optimize
  └─ Optimizer：分析结果，自动调参

Phase 6: Report
  └─ Report Logger：生成报告
```

## Agent 角色定义

| Agent | 角色 | 性格 | 任务 |
|-------|------|------|------|
| **B 区突破专家** | 实验者 + 策展人 | 探索新策略 | 突破饱和瓶颈 |
| **A 区提升专家** | 冲刺者 + 工匠 | 快速产出 | 提升直联率 |
| **Quality Gate** | 哨兵 + 工匠 | 严谨验证 | 验证数据质量 |
| **Contact Verifier** | 哨兵 + 侦探 | 怀疑一切 | 验证直联准确性 |
| **Optimizer** | 侦探 + 实验者 | 分析优化 | 自动调参 |
| **Report Logger** | 策展人 + 导师 | 清晰记录 | 生成报告 |

## 权威研究来源

| # | 来源 | 类型 | 关键洞察 |
|---|------|------|----------|
| 1 | [Anthropic: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | 官方工程博客 | 从简到繁、质量门控、ACI 设计、poka-yoke 防错 |
| 2 | [CrewAI Documentation](https://docs.crewai.com/concepts/crews) | 框架文档 | 顺序/层级执行、回调监控、检查点恢复、记忆系统 |
| 3 | [AIMultiple AI Agents Benchmark](https://aimultiple.com/ai-agents) | 行业基准测试 | 幻觉实例、ground truth 验证、human-in-the-loop |
| 4 | [LangChain: What is an Agent](https://www.langchain.com/blog/what-is-an-agent) | 技术博客 | Router→State Machine→Agent 谱系、持久化执行 |

## 对比分析

### 已实现的

| 研究发现 | 实现方式 | 状态 |
|---------|---------|------|
| **Anthropic: Prompt Chaining + Gate** | Phase 3 (Validate) + Phase 4 (Verify) | ✅ 已实现 |
| **Anthropic: Parallelization + Voting** | parallel() 调用 A 区和 B 区 | ✅ 已实现 |
| **Anthropic: Environment Grounding** | Agent 读取 data 文件 | ✅ 已实现 |
| **Anthropic: Human-in-the-loop** | NEEDS_REVIEW 状态 | ✅ 已实现 |
| **AIMultiple: Ground Truth Comparison** | Validate + Verify phases | ✅ 已实现 |

### 部分实现的

| 研究发现 | 当前状态 | 差距 |
|---------|---------|------|
| **Anthropic: Evaluator-Optimizer Loop** | Phase 5 (Optimize) | 缺少循环回 Validate |
| **CrewAI: Step/Task Callback** | Report phase | 仅报告，未回调 |
| **CrewAI: Memory System** | 读取 optimization_history.json | 未写入记忆 |

### 缺失的

| 研究发现 | 要求 | 影响 |
|---------|------|------|
| **Anthropic: ACI Error-Proofing** | 通过参数设计使模型更难犯错 | Agent 可能犯可预防的错误 |
| **CrewAI: Checkpoint Recovery** | 中断后可从断点继续 | 中断需重新开始 |
| **LangChain: Durable Execution** | 处理中途错误 | 错误导致整个流程失败 |

## 关键差距详解

### 1. Evaluator-Optimizer 循环缺失

**研究要求**:
```
pipeline-worker → quality-gate → optimizer → quality-gate（循环）
                                          ↑___________________________|
                                           如果优化后仍有问题，循环验证
```

**当前实现**:
```
Phase 3: Validate → Phase 5: Optimize → Phase 6: Report（单向）
```

**影响**: 可能应用无效优化，因为没有验证优化是否有效。

### 2. ACI 防错设计缺失

**研究要求**:
- 通过参数设计使模型更难犯错
- 明确禁止的行为
- 强制验证步骤

**当前实现**:
- Agent prompt 中有"关键约束"
- 但没有系统化的防错机制

**影响**: Agent 可能犯可预防的错误（如编造数据、跳过验证）。

### 3. 检查点恢复缺失

**研究要求**:
- 每个 Phase 完成后保存检查点
- 如果中断，从最近检查点恢复

**当前实现**:
- 无检查点机制
- 中断需重新开始

**影响**: 长时间运行的工作流如果中断，会丢失所有进度。

### 4. 持久化执行缺失

**研究要求**:
- 每个 Agent 执行失败时，记录错误并继续
- 不因单个 Agent 失败而终止整个流程

**当前实现**:
- 如果一个 Agent 失败，整个流程可能失败

**影响**: 单点故障导致整个流程失败。

## 确认的修正方案

> 以下方案已逐项与用户确认，可直接用于实施。

### 修正 1: Evaluator-Optimizer 循环 ✅

**决定**: 加，最多循环 3 次。

**实现逻辑**:
```
Phase 5: Optimize
  ├─ Optimizer：分析结果，调整配置
  ├─ Quality Gate：验证优化结果
  ├─ 如果验证失败 → 重新优化（最多 3 次）
  └─ 如果 3 次仍失败 → 标记 OPTIMIZATION_FAILED，记录失败原因，继续
```

```javascript
// Phase 5: 优化（带循环）
let optimizationResult
for (let attempt = 1; attempt <= 3; attempt++) {
  optimizationResult = await agent(OPTIMIZER_ROLE + '...')
  const verifyResult = await agent(QUALITY_GATE_ROLE + '...')
  if (!verifyResult.includes('INVALID')) break
  log(`优化验证失败，第 ${attempt} 次重试`)
}
if (optimizationResult.includes('INVALID')) {
  log('优化 3 次仍失败，标记 OPTIMIZATION_FAILED')
}
```

### 修正 2: ACI 防错设计 ✅

**决定**: 加，内容已按用户反馈调整。

**关键调整**:
- B 区有效率阈值：使用采样窗口（至少 10 个关键词），而非逐条判断
- 电话验证：接受国际格式，不强制澳洲格式
- Optimizer 大范围修改：标记 NEEDS_APPROVAL，不阻塞工作流，积攒到 Report 阶段统一审批
- 所有标记必须有闭环处理动作

#### B 区突破专家 — 防错约束

```
### 禁止行为
- 不编造公司名/域名/URL
- 不重复使用已饱和的关键词

### 强制步骤
- 每条新公司必须附 source_url
- 检查域名是否已在 data/leads.csv 中（去重）

### 错误处理
- 有效率 < 50%（采样窗口 ≥ 10 个关键词）→ 自动切换搜索策略维度
- 记录切换原因到 docs/logs/changelog.md
- 连续 2 次策略切换仍无效 → 标记 SATURATED，报告给人工
```

#### A 区提升专家 — 防错约束

```
### 禁止行为
- 不编造邮箱/电话/LinkedIn
- 不猜测联系人信息

### 强制步骤
- 每条直联必须有 source_url
- 验证邮箱格式后再写入

### 错误处理
- Stage 2 连续 0% → 标记 STAGE2_STALLED，切换到 Stage 3 审核或推断邮箱验证
- 数据质量存疑 → 标记 NEEDS_REVIEW，不删除
```

#### Quality Gate（质量验证）— 防错约束

```
### 禁止行为
- 不放过缺少 source_url 的记录
- 不忽略重复数据

### 强制步骤
- 逐条检查 source_url 存在性
- 计算重复率

### 错误处理
- 重复率 > 20% → 标记 HIGH_DUPLICATE，自动去重并报告数量
- 缺少来源的记录 → 标记 MISSING_SOURCE，写入 needs_review，不写入 leads/contacts
```

#### Contact Verifier（直联验证）— 防错约束

```
### 禁止行为
- 不假设未验证的邮箱是有效的
- 不跳过格式检查

### 强制步骤
- 邮箱必须通过格式+域名检查
- 电话验证接受国际格式（不强制澳洲格式）
  - 澳洲号码标记 AU_PHONE
  - 非澳洲号码标记 INTL_PHONE

### 错误处理
- 格式错误 → 标记 INVALID，保留在 contacts.csv 但不删除
- 无法确认 → 标记 NEEDS_REVIEW，保留在 contacts.csv，下一轮人工审核
```

#### Optimizer（自动优化器）— 防错约束

```
### 禁止行为
- 不删除已有配置，只添加或调整
- 不在无人工审批的情况下做大范围修改（> 20% 或影响多个配置项）

### 强制步骤
- 记录每次优化到 .optimization_history.json
- 优化前先读当前配置

### 错误处理
- 小调整（≤ 20%）→ 自动执行
- 大范围修改（> 20%）→ 标记 NEEDS_APPROVAL，记录修改计划，不阻塞工作流
- 优化后验证失败 → 标记 OPTIMIZATION_FAILED，回滚配置到优化前版本
- 连续 3 次验证失败 → 暂停自动优化，报告给人工

### 人工审批处理
- NEEDS_APPROVAL 修改计划积攒到 Report 阶段统一展示
- 用户在报告中看到待审批列表，统一决定是否批准
- 批准后由 Optimizer 应用修改
```

#### Report Logger（报告生成）— 防错约束

```
### 禁止行为
- 不编造数据
- 不遗漏异常情况

### 强制步骤
- 报告必须包含数据来源统计
- 异常必须列入"问题"章节
- 必须汇总所有待审批项（NEEDS_APPROVAL）

### 错误处理
- 数据不完整 → 标记 INCOMPLETE_DATA，列出缺失项
```

#### 标记闭环处理总表

| 标记 | 触发条件 | 后续动作 |
|------|---------|---------|
| `LOW_EFFICIENCY` | 最近 10 关键词有效率 < 50% | 自动切换搜索策略维度，记录切换原因，继续执行 |
| `SATURATED` | 连续 2 次策略切换仍无效 | 暂停 B 区扩展，报告给人工，等待决策 |
| `STAGE2_STALLED` | Stage 2 连续 0% | 暂停 Stage 2，切换到 Stage 3 审核或推断邮箱验证 |
| `HIGH_DUPLICATE` | 重复率 > 20% | 自动去重，报告去重数量 |
| `MISSING_SOURCE` | 缺少 source_url | 标记 needs_review，不写入 leads/contacts |
| `INVALID` | 格式错误或不存在 | 保留在 contacts.csv 但标记 INVALID，不删除 |
| `NEEDS_REVIEW` | 无法确认 | 保留在 contacts.csv，下一轮人工审核 |
| `OPTIMIZATION_FAILED` | 优化后验证失败（3 次） | 回滚配置到优化前版本，记录失败原因，暂停自动优化 |
| `NEEDS_APPROVAL` | 大范围修改（> 20%） | 积攒到 Report 阶段统一展示，不阻塞工作流 |
| `INTL_PHONE` | 非澳洲电话号码 | 标记为国际号码，方便分类外联 |
| `AU_PHONE` | 澳洲电话号码 | 标记为澳洲号码 |
| `INCOMPLETE_DATA` | 报告数据不完整 | 标记缺失项，下一轮补充 |

### 修正 3: 检查点恢复 ✅

**决定**: 加。

**设计约束**: 人工审批部分（如 NEEDS_APPROVAL）不阻塞工作流，全部积攒到 Report 阶段统一处理。

**实现逻辑**:
- 每个 Phase 完成后保存检查点到 `.claude/checkpoints/` 目录
- 检查点内容：Phase 名称、执行结果、时间戳
- 启动时检查是否有检查点，有则跳过已完成的 Phase

```javascript
// 每个 Phase 完成后保存检查点
phase('Analyze')
// ... 执行分析 ...
saveCheckpoint('analyze', { bAnalysis, aAnalysis })

phase('Fix B区 + Improve A区')
// ... 执行改进 ...
saveCheckpoint('fix-improve', { bResult, aResult })

// 启动时检查是否有检查点
const checkpoint = loadCheckpoint()
if (checkpoint) {
  // 从检查点恢复，跳过已完成的 Phase
  resumeFromCheckpoint(checkpoint)
}
```

### 修正 4: 持久化执行（容错）✅

**决定**: 加。

**实现逻辑**:
- 每个 Agent 调用包裹 try/catch
- 失败时记录错误到 `docs/logs/workflow-errors.log`，返回 `{ error: message, status: 'FAILED' }`
- 后续 Phase 收到 FAILED 结果时，跳过依赖该结果的步骤，继续执行其他部分
- 最终报告中标记哪些 Phase 失败

```javascript
// 每个 Agent 执行时捕获错误
try {
  const result = await agent(prompt)
  return result
} catch (error) {
  log(`Agent 执行失败: ${error.message}`)
  // 记录错误但继续执行
  return { error: error.message, status: 'FAILED' }
}
```

## 修正后的工作流结构

```
Phase 1: Analyze（并行，容错）
  ├─ B 区突破专家：分析饱和原因
  └─ A 区提升专家：分析直联率低原因
  └─ 检查点: analyze-checkpoint.json
  └─ 失败处理: 记录错误，继续执行

Phase 2: Fix + Improve（并行，容错）
  ├─ B 区：实施新搜索策略（自动切换策略，连续 2 次无效才报告人工）
  └─ A 区：实施直联提升方案
  └─ 检查点: fix-improve-checkpoint.json
  └─ 失败处理: 记录错误，继续执行

Phase 3: Validate（容错）
  └─ Quality Gate：验证产出（检查 source_url、去重、计算重复率）
  └─ 检查点: validate-checkpoint.json
  └─ 失败处理: 记录错误，继续执行

Phase 4: Verify（容错）
  └─ Contact Verifier：验证直联准确性（接受国际电话格式）
  └─ 检查点: verify-checkpoint.json
  └─ 失败处理: 记录错误，继续执行

Phase 5: Optimize（循环，最多 3 次，容错）
  ├─ Optimizer：分析结果，自动调参
  │   ├─ 小调整（≤ 20%）→ 自动执行
  │   └─ 大范围修改（> 20%）→ 标记 NEEDS_APPROVAL，不阻塞
  ├─ Quality Gate：验证优化结果
  └─ 如果验证失败 → 重新优化（最多 3 次）
  └─ 检查点: optimize-checkpoint.json
  └─ 失败处理: 记录错误，继续执行

Phase 6: Report（汇总所有待处理项）
  └─ Report Logger：生成报告
  └─ 汇总 NEEDS_APPROVAL 待审批列表
  └─ 汇总 NEEDS_REVIEW 待审核列表
  └─ 汇总 INCOMPLETE_DATA 缺失项
  └─ 检查点: report-checkpoint.json

人工审批（Report 之后）
  └─ 用户查看报告中的待审批列表
  └─ 统一决定是否批准大范围修改
  └─ 批准后由 Optimizer 应用修改
```

## 总结

| 维度 | 当前状态 | 修正后状态 | 确认决定 |
|------|---------|-----------|---------|
| **质量门控** | ✅ 已实现 | ✅ 保持 | — |
| **并行执行** | ✅ 已实现 | ✅ 保持 | — |
| **防幻觉** | ✅ 已实现 | ✅ 增强 | ACI 防错约束加入所有 Agent |
| **Human-in-the-loop** | ✅ 已实现 | ✅ 保持 | — |
| **Evaluator-Optimizer 循环** | ❌ 缺失 | ✅ 新增 | 最多循环 3 次 |
| **ACI 防错设计** | ❌ 缺失 | ✅ 新增 | 采样窗口、国际电话、标记闭环 |
| **检查点恢复** | ❌ 缺失 | ✅ 新增 | 人工审批不阻塞工作流 |
| **持久化执行** | ❌ 缺失 | ✅ 新增 | Agent 失败不中断流程 |

**关键设计决策**:
1. 人工审批（NEEDS_APPROVAL）不阻塞工作流，积攒到 Report 阶段统一展示
2. B 区 LOW_EFFICIENCY 自动切换策略，连续 2 次无效才报告人工
3. 电话验证接受国际格式，澳洲/非澳洲分别标记
4. 所有标记都有对应的闭环处理动作（见标记闭环处理总表）

**结论**: 当前工作流已实现 50% 的权威研究最佳实践。修正后可达到 90% 以上。
