<!-- DOC_META
lifecycle:  permanent
audience:   both
write_when: 团队初始化时创建
read_when:  调用 /orchestrator 时
delete_when: 团队解散时
-->
---
name: orchestrator
description: 执行型调度器 — 读取状态、并行分配任务、验证产出、生成报告。当需要运行完整管线时调用。
---

# Orchestrator — 执行型调度器

执行 V3 管线的完整流程：读取状态 → 并行分配任务 → 验证产出 → 生成报告。

## 触发方式

```
/orchestrator
```

## 执行流程

当用户调用 `/orchestrator` 时，按以下步骤执行：

### 第 1 步：读取状态（30 秒内完成）

```
读取以下文件：
  - .session_state.json — 上次运行结果
  - docs/current-progress.md — 当前进度
  - reports/ 目录下最近的报告 — 最近运行情况
  - .run_lock — 是否有任务在运行
```

### 第 2 步：检查运行锁

```
如果 .run_lock 存在且未过期：
  → 输出"上一轮仍在运行，跳过"
  → 结束

如果 .run_lock 不存在或已过期：
  → 创建 .run_lock（过期时间 10 分钟后）
  → 继续执行
```

### 第 3 步：并行分配任务

同时启动两个 Agent：

**Agent 1: pipeline-worker（A 区）**
```
执行命令：
python -m scripts.kp_pipeline.run_pipeline --stage all --limit 10

产出：
- 候选联系人列表（带来源 URL）
- reports/kp-pipeline/stage1-{timestamp}.csv
- reports/kp-pipeline/stage2-{timestamp}.csv
```

**Agent 2: keyword-worker（B 区）**
```
执行命令：
python -m scripts.keyword_scheduler.scheduler --limit 5

产出：
- 新发现的公司列表（带搜索来源）
- reports/keyword-run-{timestamp}.csv
```

### 第 4 步：收集产出

```
等待两个 Agent 完成：
  - pipeline-worker 返回候选数据
  - keyword-worker 返回新公司
  - 汇总所有产出
```

### 第 5 步：验证产出

调用 quality-gate 验证所有产出：

```
对每条记录验证：
  1. source_url 是否存在且非空
  2. source_url 格式是否合法
  3. 抽样检查 source_url 是否可访问
  4. 检查必填字段是否完整
  5. 检查是否与现有数据重复

分类结果：
  - PASS → 合并到 data/leads.csv 或 data/contacts.csv
  - REVIEW → 标记 needs_review，等待人工确认
  - REJECT → 归档到 reports/rejected-{timestamp}.csv
```

### 第 6 步：分析优化

调用 optimizer 分析运行结果：

```
分析指标：
  - A 区：直联率、候选质量、富化成功率
  - B 区：有效率、新公司数、关键词命中率

如果有优化方案：
  - 执行优化（修改配置文件）
  - 记录优化历史

如果无需优化：
  - 跳过
```

### 第 7 步：生成报告

调用 report-logger：

```
执行命令：
  - A 区：python scripts/reports/generate_run_report.py --auto-stats --auto-timing
  - B 区：python scripts/reports/generate_keyword_report.py --auto-timing

更新文件：
  - docs/current-progress.md — 更新进度
  - .session_state.json — 更新状态
  - reports/checkpoint-{timestamp}.json — 保存检查点
```

### 第 8 步：释放锁

```
删除 .run_lock
```

### 第 9 步：汇报结果

向用户汇报：

```
本轮运行摘要：
- A 区：X 候选，Y 富化，Z 直联
- B 区：X 关键词，Y 新公司，有效率 Z%
- 验证：X 通过，Y 待审，Z 拒绝
- 优化：X（如有）
- 下一步：XXX
```

## 退出条件

满足任一条件时，暂停循环（但本轮必须执行完）：

| 条件 | 阈值 | 说明 |
|------|------|------|
| A 区直联率 | < 5% 连续 3 轮 | Stage 2 效率过低 |
| B 区有效率 | < 50% | 关键词质量下降 |
| 运行时间 | > 5 分钟 | 单轮超时 |
| 新增直联 | = 0 连续 3 轮 | 无新产出 |
| Google 429 | > 3 次 | 代理问题 |

## Human-in-the-loop 节点

| 节点 | 触发条件 | 动作 |
|------|----------|------|
| REVIEW 数据 | quality-gate 标记 REVIEW | 等待人工确认 |
| 重大配置变更 | optimizer 要求修改阈值 > 20% | 等待人工批准 |
| 连续无产出 | 连续 3 轮无新数据 | 暂停并通知用户 |

## 自动循环

如果需要自动循环运行，使用：

```
/loop 5m /orchestrator
```

这会每 5 分钟检查一次，如果有锁就跳过，没有锁就执行一轮。

## 状态文件

- `.session_state.json` — 会话状态
- `.run_lock` — 运行锁（临时）
- `.optimization_history.json` — 优化历史
- `reports/checkpoint-{timestamp}.json` — 检查点
