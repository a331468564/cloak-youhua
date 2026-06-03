export const meta = {
  name: 'run-pipeline',
  description: '并行执行 A 区和 B 区管线，验证产出，生成报告',
  phases: [
    { title: 'Execute', detail: '并行执行 A 区和 B 区' },
    { title: 'Validate', detail: '验证产出数据' },
    { title: 'Report', detail: '生成报告和更新状态' },
  ],
}

// Phase 1: 并行执行 A 区和 B 区
phase('Execute')

const [aResult, bResult] = await parallel([
  () => agent(
    '你是 pipeline-worker。请执行 A 区 Stage 1+2：\n\n' +
    '执行命令：python -m scripts.kp_pipeline.run_pipeline --stage all --limit 10\n\n' +
    '注意：\n' +
    '- 产出到报告 CSV\n' +
    '- 记录运行结果（候选数、富化数、直联数、耗时）\n' +
    '- 不要只分析，要实际执行脚本\n\n' +
    '完成后汇报结果。',
    { label: 'A区 Pipeline', phase: 'Execute' }
  ),
  () => agent(
    '你是 keyword-worker。请执行 B 区关键词发现：\n\n' +
    '执行命令：python -m scripts.keyword_scheduler.scheduler --limit 5\n\n' +
    '注意：\n' +
    '- 如果 B 区已饱和（有效率 < 50%），跳过执行\n' +
    '- 产出到报告 CSV\n' +
    '- 记录运行结果（关键词数、新公司数、有效率）\n\n' +
    '完成后汇报结果。',
    { label: 'B区 Keywords', phase: 'Execute' }
  ),
])

log('A 区和 B 区执行完成')

// Phase 2: 验证产出
phase('Validate')

const validation = await agent(
  '你是 quality-gate。请验证以下产出：\n\n' +
  'A 区结果：\n' + aResult + '\n\n' +
  'B 区结果：\n' + bResult + '\n\n' +
  '验证规则：\n' +
  '1. 每条记录必须有 source_url\n' +
  '2. 无来源的数据标记 needs_review\n' +
  '3. 有来源的数据可以合并到主文件\n\n' +
  '汇报验证结果（通过/待审/拒绝数量）。',
  { label: '质量验证', phase: 'Validate' }
)

log('验证完成：' + validation)

// Phase 3: 生成报告
phase('Report')

const report = await agent(
  '你是 report-logger。请生成运行报告：\n\n' +
  '执行命令：\n' +
  '- python scripts/reports/generate_run_report.py --auto-stats --auto-timing\n\n' +
  '更新文件：\n' +
  '- docs/current-progress.md\n' +
  '- .session_state.json\n\n' +
  '汇报报告生成结果。',
  { label: '生成报告', phase: 'Report' }
)

log('报告生成完成')

return {
  aResult,
  bResult,
  validation,
  report,
}
