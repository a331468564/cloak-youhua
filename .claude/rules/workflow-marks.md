---
paths:
  - ".claude/workflows/**"
  - ".claude/agents/**"
---

# Workflow 标记闭环处理

所有 Agent 在执行中遇到以下情况时，必须使用对应标记。每个标记都有明确的后续动作，不允许只标记不处理。

## 标记总表

| 标记 | 触发条件 | 后续动作 |
|------|---------|---------|
| `LOW_EFFICIENCY` | 最近 10 关键词有效率 < 50% | 自动切换搜索策略维度，记录切换原因到 changelog，继续执行 |
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

## 使用规则

1. **必须闭环** — 每个标记必须有对应的后续动作，不允许只标记不处理
2. **不阻塞** — NEEDS_APPROVAL 等标记不阻塞工作流，积攒到 Report 阶段统一处理
3. **记录原因** — 标记时必须记录触发原因（如切换了哪个策略、回滚了哪个配置）
4. **报告汇总** — Report 阶段必须汇总所有标记，生成待处理列表
