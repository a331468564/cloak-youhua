<!-- DOC_META
lifecycle:  permanent
audience:   both
write_when: 团队初始化时创建
read_when:  需要了解团队结构时
delete_when: 团队解散时
-->
# V3 Agent 团队

## 团队成员

| Agent | 文件 | 职责 |
|-------|------|------|
| **orchestrator** | `orchestrator.md` | 调度器 — 管理循环、协调其他 Agent |
| **pipeline-worker** | `pipeline-worker.md` | A 区执行者 — 运行 KP Pipeline |
| **keyword-worker** | `keyword-worker.md` | B 区执行者 — 运行 Keyword Scheduler |
| **quality-gate** | `quality-gate.md` | 质量门控 — 验证数据、拦截幻觉 |
| **optimizer** | `optimizer.md` | 自动优化器 — 分析结果、调参 |
| **report-logger** | `report-logger.md` | 报告记录员 — 生成报告、保存状态 |

## 协作流程

```
用户启动
    │
    ▼
orchestrator（读取状态、创建锁）
    │
    ├──→ pipeline-worker（A 区执行）  ←─┐ 并行
    │                                    │
    ├──→ keyword-worker（B 区执行）  ←─┘
    │
    ▼
quality-gate（验证所有产出）
    │
    ├── PASS → 合并到 data/
    ├── REVIEW → 等待人工确认
    └── REJECT → 归档
    │
    ▼
optimizer（分析结果、自动调参）
    │
    ▼
report-logger（生成报告、保存状态）
    │
    ▼
orchestrator（释放锁、汇报结果）
```

## 使用方式

### 单次运行
```
/agent orchestrator 跑一轮完整管线
```

### 自动循环
```
/loop 30m /agent orchestrator 运行管线
```

### 查看状态
```
/agent orchestrator 检查当前状态
```

## 防幻觉机制

- **数据锚定**：每条记录必须有 source_url
- **质量门控**：quality-gate 验证后才入库
- **严格模式**：无来源数据直接拒绝

## 运行锁机制

- `.run_lock` 文件防止重复执行
- 锁过期时间 10 分钟
- 上一轮未完成时自动跳过

## 状态文件

- `.session_state.json` — 会话状态
- `.run_lock` — 运行锁（临时）
- `.optimization_history.json` — 优化历史
