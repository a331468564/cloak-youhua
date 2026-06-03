<!-- DOC_META
lifecycle:  permanent
audience:   both
write_when: 团队设计研究完成时
read_when:  需要了解团队设计依据时
delete_when: 团队解散时
-->
# Agent 团队设计研究报告

*研究日期: 2026-06-02*

## 摘要

本报告记录了为 V3 项目设计 Agent 团队时的研究过程和发现。研究覆盖了 4 个权威来源，提取了质量门控、防幻觉、自动循环等关键最佳实践，并应用于团队设计。

## 来源列表

| # | 来源 | 类型 | 关键洞察 |
|---|------|------|----------|
| 1 | [Anthropic: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) | 官方工程博客 | 从简到繁、质量门控、ACI 设计、poka-yoke 防错 |
| 2 | [CrewAI Documentation](https://docs.crewai.com/concepts/crews) | 框架文档 | 顺序/层级执行、回调监控、检查点恢复、记忆系统 |
| 3 | [AIMultiple AI Agents Benchmark](https://aimultiple.com/ai-agents) | 行业基准测试 | 幻觉实例、ground truth 验证、human-in-the-loop |
| 4 | [LangChain: What is an Agent](https://www.langchain.com/blog/what-is-an-agent) | 技术博客 | Router→State Machine→Agent 谱系、持久化执行 |

## 关键发现

### 1. 质量门控模式（来自 Anthropic）

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **Prompt Chaining + Gate** | 分步处理，中间插入程序化检查 | 数据管线验证 |
| **Evaluator-Optimizer Loop** | 一个 LLM 生成，另一个循环评估 | 迭代优化 |
| **Parallelization + Voting** | 多次运行，投票阈值平衡误报/漏报 | 内容审核 |

**应用：** 在 quality-gate 中实现了 Prompt Chaining + Gate 模式，在 optimizer 中实现了 Evaluator-Optimizer Loop。

### 2. 防幻觉机制（来自 Anthropic + AIMultiple）

| 机制 | 说明 | 我们的应用 |
|------|------|-----------|
| **环境接地** | Agent 必须从环境获取 ground truth | 每条数据必须有 source_url |
| **ACI 防错设计** | 通过参数设计使模型更难犯错 | 强制 URL 格式验证 |
| **Human-in-the-loop** | 关键节点保留人工介入 | quality-gate 的 REVIEW 状态 |
| **Ground Truth 比对** | 与已知正确数据比对 | 去重检查 + 交叉验证 |

**应用：** 在 quality-gate 中实现了 5 级验证（存在→可访问→内容一致→交叉验证→confidence 分数）。

### 3. 自动循环最佳实践（来自 CrewAI + LangChain）

| 实践 | 说明 | 我们的应用 |
|------|------|-----------|
| **检查点恢复** | 任务完成后保存状态，中断后可恢复 | .session_state.json + checkpoint |
| **Step/Task Callback** | 每步/每任务完成后触发回调 | report-logger |
| **Memory 系统** | 短期/长期记忆，跨轮次积累经验 | optimization_history.json |
| **Durable Execution** | 持久化执行，处理中途错误 | 运行锁 + 状态文件 |
| **最大迭代次数** | 防止无限循环 | 退出条件 + 连续无产出计数器 |

**应用：** 在 orchestrator 中实现了检查点恢复机制和 Human-in-the-loop 节点。

### 4. 幻觉案例（来自 AIMultiple）

| Agent | 幻觉类型 | 教训 |
|-------|----------|------|
| Phidata | 链接指向不存在的页面 | 必须验证 URL 可访问 |
| Perplexity | 时间信息错误 | 必须验证时间戳准确性 |
| ChatGPT Search | 部分信息不满足查询要求 | 必须验证数据完整性 |

**应用：** 在 quality-gate 的幻觉检测中增加了时间戳验证和 URL 可访问性检查。

## 设计修正

基于研究发现，对原始团队设计做了以下修正：

### 修正 1: 增加 Evaluator-Optimizer 循环

```
原设计：pipeline-worker → quality-gate → optimizer（线性）
修正后：pipeline-worker → quality-gate → optimizer → quality-gate（循环）
                              ↑___________________________|
                               如果优化后仍有问题，循环验证
```

### 修正 2: 增强防幻觉机制

```
原设计：仅检查 source_url 是否存在
修正后：
  1. 检查 source_url 是否存在
  2. 抽样验证 source_url 是否可访问
  3. 验证 URL 内容与提取数据是否一致
  4. 与已有数据交叉验证
  5. 标记 confidence 分数
```

### 修正 3: 增加 Human-in-the-loop 节点

```
原设计：全自动，无人工介入
修正后：
  - quality-gate 的 REVIEW 状态 → 等待人工确认
  - optimizer 的重大配置变更 → 等待人工批准
  - 连续 3 轮无产出 → 暂停并通知用户
```

### 修正 4: 增加检查点恢复

```
原设计：仅 .session_state.json
修正后：
  - .session_state.json — 整体状态
  - .run_lock — 运行锁
  - .optimization_history.json — 优化历史
  - reports/checkpoint-{timestamp}.json — 每轮检查点
```

## 最终团队架构

```
┌─────────────────────────────────────────────────────────────┐
│                     用户启动 /loop 5m                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  orchestrator（检查锁 → 读状态 → 检查点恢复 → 决定任务）       │
└──────────┬──────────────────────────────┬───────────────────┘
           │                              │
    ┌──────▼──────┐               ┌───────▼───────┐
    │  pipeline-  │               │  keyword-     │
    │  worker     │               │  worker       │
    └──────┬──────┘               └───────┬───────┘
           │                              │
           └──────────┬───────────────────┘
                      │
              ┌───────▼───────┐
              │  quality-gate  │ ◄─── Ground Truth 验证
              │  (验证+入库)    │      5 级验证机制
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │   optimizer    │ ◄─── Evaluator-Optimizer 循环
              │  (分析+调参)   │      最多 3 次迭代
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │  quality-gate  │ ◄─── 验证优化方案
              │  (二次验证)     │
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │  report-logger │
              │  (报告+检查点)  │
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │  orchestrator  │
              │  (继续/暂停)   │
              └───────────────┘
```

## 结论

通过系统化研究，我们将 Agent 团队从"凭经验设计"升级为"基于权威最佳实践设计"。关键改进包括：

1. **质量门控**：从简单的 URL 存在检查升级为 5 级 Ground Truth 验证
2. **防幻觉**：增加了 ACI 防错设计和 Human-in-the-loop 节点
3. **自动循环**：增加了检查点恢复和 Evaluator-Optimizer 循环
4. **可靠性**：增加了运行锁、状态持久化、最大迭代次数保护

这些改进基于 Anthropic、CrewAI、AIMultiple 等权威来源的最佳实践，将显著提升团队的可靠性和数据质量。
