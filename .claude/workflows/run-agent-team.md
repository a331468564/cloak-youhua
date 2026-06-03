<!-- DOC_META
lifecycle:  permanent
audience:   agent
write_when: 团队初始化时创建
read_when:  需要运行团队工作流时
delete_when: 团队解散时
-->
# Run Agent Team Workflow

运行 V3 Agent 团队执行一轮完整的管线任务。

## 触发方式

```
/workflow run-agent-team
```

## 工作流步骤

### Step 1: 初始化检查
```
Agent: orchestrator
任务: 检查运行锁和会话状态
产出: 是否可以运行、本轮任务类型
```

### Step 2: 执行管线
```
如果 A 区可运行：
  Agent: pipeline-worker
  任务: 执行 Stage 1+2+3
  产出: 候选联系人数据

如果 B 区可运行：
  Agent: keyword-worker
  任务: 运行 scheduler
  产出: 新发现公司
```

### Step 3: 质量验证
```
Agent: quality-gate
任务: 验证所有产出数据
产出: 验证结果（PASS/REVIEW/REJECT）
动作: PASS 的数据合并到主文件
```

### Step 4: 自动优化
```
Agent: optimizer
任务: 分析运行结果，决定是否调参
产出: 优化结果（如有）
```

### Step 5: 记录报告
```
Agent: report-logger
任务: 生成报告，更新状态
产出: 运行报告、更新后的状态文件
```

### Step 6: 决策
```
Agent: orchestrator
任务: 判断是否继续下一轮
产出: 建议（继续/暂停/人工检查）
```

## 状态文件

- `.session_state.json` — 会话状态
- `.run_lock` — 运行锁
- `.optimization_history.json` — 优化历史

## 输出

- `reports/` — 运行报告
- `data/leads.csv` — 更新后的线索
- `data/contacts.csv` — 更新后的联系人
- `docs/current-progress.md` — 更新后的进度
