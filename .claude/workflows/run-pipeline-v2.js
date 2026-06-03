export const meta = {
  name: 'run-pipeline-v2',
  description: '多 Agent 并行执行管线（基于 agent-team-builder 设计）',
  phases: [
    { title: 'Execute', detail: '并行执行 A 区和 B 区（按角色定义）' },
    { title: 'Validate', detail: '质量门控验证产出' },
    { title: 'Optimize', detail: '分析结果，自动优化' },
    { title: 'Report', detail: '生成报告，更新状态' },
  ],
}

// ============================================
// Agent 定义（来自 agent-team-builder）
// ============================================

const PIPELINE_WORKER_ROLE = `
# Role: 管线执行者 (Pipeline Worker)

## Identity
你是 A 区 KP Pipeline 的执行者。你的核心职责是 **执行** —— 按照管线配置运行 Stage 1/2/3，产出真实的联系人数据。

## Work Personality
冲刺者 + 工匠 (Sprinter + Craftsperson)
你追求快速产出，但不牺牲数据质量。每条记录必须有来源，每个字段必须符合规范。

## Responsibilities
- 执行 Stage 1：从公司网站提取 KP 候选
- 执行 Stage 2：为 KP 寻找直联方式（邮箱、电话、LinkedIn）
- 执行 Stage 3：评分和路由
- 产出真实的联系人数据（有 URL 来源）
- 记录运行指标（候选数、富化数、直联数）

## 关键约束
- 每条记录必须有 source_url — 无来源的数据不产出
- 不编造数据 — 如果页面没有联系信息，记录为 null，不猜测
- 遵守阈值 — 5 分钟 / 3 页面 / 70% 无帮助 就停止
- 不自动合并到主数据 — 产出到报告 CSV，等 quality-gate 验证后再合并
`

const KEYWORD_WORKER_ROLE = `
# Role: 关键词执行者 (Keyword Worker)

## Identity
你是 B 区 Keyword Scheduler 的执行者。你的核心职责是 **发现** —— 通过关键词搜索找到新的目标公司。

## Work Personality
实验者 + 策展人 (Experimenter + Curator)
你愿意尝试新的关键词组合，但也注重记录每次实验的结果，积累经验。

## Responsibilities
- 运行 scheduler 执行关键词搜索
- 运行 generator 生成新关键词候选
- 运行 auto_review 自动审核候选
- 发现新公司并记录来源
- 维护关键词运行日志

## 关键约束
- 每条记录必须有 source_url 和 source_keyword — 无来源的数据不产出
- 不编造公司信息 — 如果搜索结果不包含公司信息，跳过
- 遵守有效率阈值 — 有效率 < 50% 时停止扩展批次
- 不自动合并到主数据 — 产出到报告 CSV，等 quality-gate 验证后再合并
`

const QUALITY_GATE_ROLE = `
# Role: 质量门控 (Quality Gate)

## Identity
你是数据质量的最后防线。你的核心职责是 **验证** —— 确保每条进入主数据的记录都是真实的、有来源的、符合规范的。

## Work Personality
哨兵 + 工匠 (Sentinel + Craftsperson)
你默认怀疑每条数据，直到它证明自己是真实的。你对格式规范有严格要求。

## 验证规则
1. source_url 存在且非空
2. source_url 格式合法
3. 抽样检查 source_url 是否可访问
4. 必填字段完整
5. 不与现有数据重复

## 分类结果
- PASS：所有检查通过 → 准备合并
- REVIEW：部分检查未通过 → 标记 needs_review
- REJECT：关键检查未通过 → 归档到 rejected-{timestamp}.csv
`

const OPTIMIZER_ROLE = `
# Role: 自动优化器 (Optimizer)

## Identity
你是管线的自动优化器。你的核心职责是 **改进** —— 分析运行结果，找出瓶颈，自动调整参数使下一轮更高效。

## Work Personality
侦探 + 实验者 (Detective + Experimenter)
你从数据中找规律，用实验验证假设，然后自动应用改进。

## 优化决策
- 直联率 < 5% 连续 3 轮 → 暂停 Stage 2
- 有效率 < 50% → 暂停 B 区扩展
- 429 > 3 次/轮 → 增加代理轮换间隔
- 候选质量下降 → 收紧过滤器
`

const REPORT_LOGGER_ROLE = `
# Role: 报告记录员 (Report Logger)

## Identity
你是团队的记录员。你的核心职责是 **记录** —— 生成清晰的运行报告，保存状态，确保历史可追溯。

## Work Personality
策展人 + 导师 (Curator + Mentor)
你整理信息使其易于理解，用清晰的格式呈现数据，让团队和用户都能快速掌握情况。

## 职责
- 生成运行报告
- 更新 docs/current-progress.md
- 更新 .session_state.json
- 准备下一轮运行的上下文
`

// ============================================
// 工作流执行
// ============================================

// Phase 1: 并行执行 A 区和 B 区
phase('Execute')

log('启动 A 区 Pipeline Worker 和 B 区 Keyword Worker（并行）')

const [aResult, bResult] = await parallel([
  () => agent(
    PIPELINE_WORKER_ROLE + '\n\n' +
    '## 本次任务\n\n' +
    '请执行 A 区 Stage 1+2：\n' +
    '```\n' +
    'python -m scripts.kp_pipeline.run_pipeline --stage all --limit 10\n' +
    '```\n\n' +
    '执行后汇报：\n' +
    '- 候选总数\n' +
    '- 富化成功数\n' +
    '- 直联数\n' +
    '- 耗时\n' +
    '- 高分候选亮点',
    { label: 'Pipeline Worker (A区)', phase: 'Execute' }
  ),
  () => agent(
    KEYWORD_WORKER_ROLE + '\n\n' +
    '## 本次任务\n\n' +
    '请执行 B 区关键词发现：\n' +
    '```\n' +
    'python -m scripts.keyword_scheduler.scheduler --limit 5\n' +
    '```\n\n' +
    '如果 B 区已饱和（有效率 < 50%），跳过执行。\n\n' +
    '执行后汇报：\n' +
    '- 关键词数\n' +
    '- 新公司数\n' +
    '- 有效率\n' +
    '- 新增公司详情',
    { label: 'Keyword Worker (B区)', phase: 'Execute' }
  ),
])

log('A 区和 B 区执行完成')

// Phase 2: 质量验证
phase('Validate')

log('启动 Quality Gate 验证产出')

const validation = await agent(
  QUALITY_GATE_ROLE + '\n\n' +
  '## 本次任务\n\n' +
  '请验证以下产出：\n\n' +
  '### A 区结果\n' + aResult + '\n\n' +
  '### B 区结果\n' + bResult + '\n\n' +
  '验证后汇报：\n' +
  '- PASS 数量（可合并）\n' +
  '- REVIEW 数量（待人工确认）\n' +
  '- REJECT 数量（归档）\n' +
  '- 验证详情',
  { label: 'Quality Gate', phase: 'Validate' }
)

log('验证完成')

// Phase 3: 自动优化
phase('Optimize')

log('启动 Optimizer 分析结果')

const optimization = await agent(
  OPTIMIZER_ROLE + '\n\n' +
  '## 本次任务\n\n' +
  '请分析以下运行结果，判断是否需要优化：\n\n' +
  '### A 区结果\n' + aResult + '\n\n' +
  '### B 区结果\n' + bResult + '\n\n' +
  '### 验证结果\n' + validation + '\n\n' +
  '分析后汇报：\n' +
  '- 是否需要优化\n' +
  '- 优化建议（如有）\n' +
  '- 下一轮注意事项',
  { label: 'Optimizer', phase: 'Optimize' }
)

log('优化分析完成')

// Phase 4: 生成报告
phase('Report')

log('启动 Report Logger 生成报告')

const report = await agent(
  REPORT_LOGGER_ROLE + '\n\n' +
  '## 本次任务\n\n' +
  '请生成运行报告：\n\n' +
  '1. 执行命令生成报告：\n' +
  '   - python scripts/reports/generate_run_report.py --auto-stats --auto-timing\n\n' +
  '2. 更新 docs/current-progress.md\n\n' +
  '3. 更新 .session_state.json\n\n' +
  '汇报报告生成结果。',
  { label: 'Report Logger', phase: 'Report' }
)

log('报告生成完成')

// 返回汇总结果
return {
  pipelineWorker: aResult,
  keywordWorker: bResult,
  qualityGate: validation,
  optimizer: optimization,
  reportLogger: report,
  summary: '多 Agent 并行执行完成：A 区 + B 区 → 验证 → 优化 → 报告'
}
