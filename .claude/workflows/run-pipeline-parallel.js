export const meta = {
  name: 'run-pipeline-parallel',
  description: 'A 区 KP 管线并行执行（4 Agent）',
  phases: [
    { title: 'Stage 1', detail: 'KP 发现' },
    { title: 'Stage 2', detail: '直联富化' },
    { title: 'Stage 3', detail: '验证门控' },
    { title: 'Report', detail: '生成报告' },
  ],
}

// 并行执行 4 个 Agent，每个跑一批管线
const results = await parallel([
  // Agent 1: Stage 1 KP 发现（公司 1-10）
  () => agent(
    'Run A区 KP pipeline Stage 1 only. Execute: python -m scripts.kp_pipeline.run_pipeline --stage 1 --limit 10. Report the number of candidates found.',
    { label: 'A区-Stage1-批次1', phase: 'Stage 1' }
  ),
  // Agent 2: Stage 1 KP 发现（公司 11-20）
  () => agent(
    'Run A区 KP pipeline Stage 1 only. Execute: python -m scripts.kp_pipeline.run_pipeline --stage 1 --limit 10 --offset 10. Report the number of candidates found.',
    { label: 'A区-Stage1-批次2', phase: 'Stage 1' }
  ),
  // Agent 3: Stage 2 直联富化
  () => agent(
    'Run A区 KP pipeline Stage 2 only. Execute: python -m scripts.kp_pipeline.run_pipeline --stage 2 --limit 10. Report the number of contacts enriched and direct contacts found.',
    { label: 'A区-Stage2', phase: 'Stage 2' }
  ),
  // Agent 4: Stage 3 验证门控
  () => agent(
    'Run A区 KP pipeline Stage 3 only. Execute: python -m scripts.kp_pipeline.run_pipeline --stage 3 --limit 10. Report the number of candidates validated and auto-approved/rejected.',
    { label: 'A区-Stage3', phase: 'Stage 3' }
  ),
])

// 汇总结果
const summary = results.map((r, i) => `Agent ${i+1}: ${r || 'completed'}`).join('\n')

// 生成报告
log('生成 Run 报告...')
await agent(
  'Generate the run report. Execute: python scripts/reports/generate_run_report.py --auto-stats --auto-timing. Report the key metrics.',
  { label: '生成报告', phase: 'Report' }
)

return { summary, results }
