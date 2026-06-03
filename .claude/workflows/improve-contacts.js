export const meta = {
  name: 'improve-contacts',
  description: '并行整改 B 区和测试 A 区，验证直联准确性，目标直联提升到 100',
  phases: [
    { title: 'Analyze', detail: '分析 B 区饱和原因和 A 区直联率低的原因' },
    { title: 'Fix B区', detail: '实施新搜索策略突破饱和' },
    { title: 'Improve A区', detail: '优化 Stage 2 提升直联率' },
    { title: 'Validate', detail: '验证产出，计算直联数' },
    { title: 'Verify', detail: '验证直联准确性' },
    { title: 'Optimize', detail: '分析结果，自动优化配置' },
    { title: 'Report', detail: '生成报告' },
  ],
}

// ============================================
// Agent 角色定义
// ============================================

const B_ZONE_FIXER = `
# Role: B 区突破专家

## Identity
你是 B 区关键词发现的突破专家。你的核心职责是 **打破饱和** —— 分析 B 区为什么有效率降到 0%，设计新的搜索策略，找到新的目标公司。

## 当前问题
- B-Run 31: 10 关键词，0 新公司，有效率 0%
- 累计覆盖: 458 家公司 / 444 域名
- Google 搜索策略已饱和，无新目标公司

## 你的任务
1. 分析 B 区饱和的根本原因
2. 设计新的搜索策略：
   - 新的关键词维度（如城市+行业、竞争对手+行业）
   - 新的搜索渠道（如 LinkedIn、行业协会目录、Google Maps）
   - 新的过滤规则（排除已知域名、排除非目标行业）
3. 实施新策略并测试
4. 汇报新发现的公司数

## 关键约束
- 每条记录必须有 source_url
- 有效率 < 50% 时停止扩展
- 不编造公司信息
`

const A_ZONE_IMPROVER = `
# Role: A 区直联提升专家

## Identity
你是 A 区 KP Pipeline 的优化专家。你的核心职责是 **提升直联率** —— 分析 Stage 2 为什么直联率降到 0%，找到改进方法，把直联数从 46 提升到 100。

## 当前问题
- 直联数: 46（目标 100，差 54）
- Stage 2 直联率: 0% 连续 4 轮
- 高优先级公司已被多轮处理，边际收益归零

## 你的任务
1. 分析 Stage 2 直联率 0% 的根本原因
2. 找到提升直联的方法：
   - 分析 Stage 3 人工审核候选（可能有漏网直联）
   - 验证推断邮箱（sam.hay@AVC、murray.graci@Crystalbrook）
   - 清理 Tier 4 存疑数据（提升数据质量）
   - 尝试新的 Stage 2 策略（如深度爬取、LinkedIn 搜索）
3. 实施改进并测试
4. 汇报新增直联数

## 关键约束
- 每条记录必须有 source_url
- 不编造数据
- 遵守阈值（5 分钟 / 3 页面 / 70% 无帮助）
`

const CONTACT_VERIFIER = `
# Role: 直联验证专家 (Contact Verifier)

## Identity
你是直联数据的验证专家。你的核心职责是 **验证** —— 检查每条直联是否真实、有效、可外联。

## Work Personality
哨兵 + 侦探 (Sentinel + Detective)
你默认怀疑每条直联，直到它证明自己是真实的。你追根溯源，找到证据。

## 验证方法

### 邮箱验证
1. 格式检查 — 是否符合邮箱格式
2. 域名检查 — 域名是否存在
3. MX 记录检查 — 域名是否有邮件服务器
4. 来源检查 — 邮箱来源是否可靠

### 电话验证
1. 格式检查 — 是否符合澳洲电话格式（+61 或 0 开头）
2. 区号检查 — 区号是否正确
3. 类型检查 — 是手机（04xx）还是座机（0x xxxx）
4. 来源检查 — 电话来源是否可靠

### LinkedIn 验证
1. URL 格式检查 — 是否是有效的 LinkedIn URL
2. 可访问性检查 — URL 是否可访问
3. 匹配度检查 — 联系人姓名是否与 LinkedIn 一致

## 验证结果分类
- VERIFIED：已验证有效
- UNVERIFIED：未验证但格式正确
- INVALID：格式错误或不存在
- OUTDATED：联系人已离职或公司已关闭
- NEEDS_REVIEW：不确定

## 关键约束
- 不编造验证结果
- 验证失败的标记为 INVALID，不删除
- 验证成功的标记为 VERIFIED
- 不确定的标记为 NEEDS_REVIEW
`

const OPTIMIZER_ROLE = `
# Role: 自动优化器 (Optimizer)

## Identity
你是管线的自动优化器。你的核心职责是 **改进** —— 分析运行结果，找出瓶颈，自动调整参数使下一轮更高效。

## Work Personality
侦探 + 实验者 (Detective + Experimenter)
你从数据中找规律，用实验验证假设，然后自动应用改进。

## 你的任务
1. 分析 A 区和 B 区的运行结果
2. 识别瓶颈和低效环节
3. 自动调整配置参数：
   - config/kp_pipeline.json（A 区配置）
   - config/keyword_scheduler.json（B 区配置）
   - 过滤器规则
4. 记录优化历史

## 优化决策规则
- 直联率 < 5% 连续 3 轮 → 暂停 Stage 2
- 有效率 < 50% → 暂停 B 区扩展
- 429 > 3 次/轮 → 增加代理轮换间隔
- 候选质量下降 → 收紧过滤器

## 关键约束
- 不删除已有配置，只添加或调整
- 记录每次优化（写入优化历史）
- 优化幅度有限（单次调整不超过 20%）
`

// ============================================
// 工作流执行
// ============================================

// Phase 1: 分析问题
phase('Analyze')

log('启动 B 区突破专家和 A 区提升专家（并行分析）')

const [bAnalysis, aAnalysis] = await parallel([
  () => agent(
    B_ZONE_FIXER + '\n\n' +
    '## 本次任务：分析 B 区饱和原因\n\n' +
    '请执行以下分析：\n\n' +
    '1. 读取 `data/search_keywords.csv`，分析关键词分布\n' +
    '2. 读取 `data/keyword_runs.csv`，分析历史有效率趋势\n' +
    '3. 读取 `docs/current-progress.md`，了解 B 区当前状态\n' +
    '4. 分析饱和的根本原因\n' +
    '5. 提出 3-5 个新的搜索策略\n\n' +
    '汇报分析结果和建议。',
    { label: 'B区分析', phase: 'Analyze' }
  ),
  () => agent(
    A_ZONE_IMPROVER + '\n\n' +
    '## 本次任务：分析 A 区直联率低的原因\n\n' +
    '请执行以下分析：\n\n' +
    '1. 读取 `data/contacts.csv`，分析当前直联分布\n' +
    '2. 读取 `docs/current-progress.md`，了解 A 区当前状态\n' +
    '3. 分析 Stage 2 直联率 0% 的根本原因\n' +
    '4. 找到可以提升直联的方法：\n' +
    '   - Stage 3 人工审核候选\n' +
    '   - 推断邮箱验证\n' +
    '   - Tier 4 数据清理\n' +
    '5. 提出具体的改进方案\n\n' +
    '汇报分析结果和建议。',
    { label: 'A区分析', phase: 'Analyze' }
  ),
])

log('分析完成')

// Phase 2: 实施改进
phase('Fix B区 + Improve A区')

log('启动 B 区新策略和 A 区改进（并行实施）')

const [bResult, aResult] = await parallel([
  () => agent(
    B_ZONE_FIXER + '\n\n' +
    '## 本次任务：实施 B 区新搜索策略\n\n' +
    '基于分析结果：\n' + bAnalysis + '\n\n' +
    '请实施新的搜索策略：\n\n' +
    '1. 选择 1-2 个最有潜力的新策略\n' +
    '2. 生成新的关键词（使用 generator）\n' +
    '3. 运行 scheduler 测试新关键词\n' +
    '4. 汇报新发现的公司数\n\n' +
    '执行命令：\n' +
    '```\n' +
    'python -m scripts.keyword_scheduler.generator --max 20\n' +
    'python -m scripts.keyword_scheduler.scheduler --limit 10\n' +
    '```\n\n' +
    '汇报执行结果。',
    { label: 'B区实施', phase: 'Fix B区 + Improve A区' }
  ),
  () => agent(
    A_ZONE_IMPROVER + '\n\n' +
    '## 本次任务：实施 A 区直联提升方案\n\n' +
    '基于分析结果：\n' + aAnalysis + '\n\n' +
    '请实施改进方案：\n\n' +
    '1. 验证推断邮箱（如有）\n' +
    '2. 清理 Tier 4 存疑数据（如有）\n' +
    '3. 审核 Stage 3 人工审核候选\n' +
    '4. 尝试新的 Stage 2 策略（如深度爬取）\n' +
    '5. 汇报新增直联数\n\n' +
    '执行命令：\n' +
    '```\n' +
    'python -m scripts.kp_pipeline.run_pipeline --stage 2 --limit 10\n' +
    '```\n\n' +
    '汇报执行结果。',
    { label: 'A区实施', phase: 'Fix B区 + Improve A区' }
  ),
])

log('实施完成')

// Phase 3: 验证产出
phase('Validate')

log('启动质量验证')

const validation = await agent(
  '# Role: 质量验证\n\n' +
  '请验证以下产出：\n\n' +
  '### B 区结果\n' + bResult + '\n\n' +
  '### A 区结果\n' + aResult + '\n\n' +
  '验证内容：\n' +
  '1. 新增公司是否有 source_url\n' +
  '2. 新增直联是否有 source_url\n' +
  '3. 数据是否与现有记录重复\n' +
  '4. 计算当前直联总数\n\n' +
  '汇报验证结果和当前直联数。',
  { label: '质量验证', phase: 'Validate' }
)

log('验证完成')

// Phase 4: 验证直联准确性
phase('Verify')

log('启动直联验证专家')

const verification = await agent(
  CONTACT_VERIFIER + '\n\n' +
  '## 本次任务：验证直联准确性\n\n' +
  '基于以下验证结果：\n' + validation + '\n\n' +
  '请验证当前所有直联：\n\n' +
  '1. 读取 `data/contacts.csv`\n' +
  '2. 筛选出有直联的记录（有邮箱或电话或 LinkedIn）\n' +
  '3. 验证每条直联：\n' +
  '   - 邮箱：格式、域名、来源\n' +
  '   - 电话：格式、区号、来源\n' +
  '   - LinkedIn：URL、可访问性、匹配度\n' +
  '4. 分类结果：\n' +
  '   - VERIFIED：已验证有效\n' +
  '   - UNVERIFIED：未验证但格式正确\n' +
  '   - INVALID：格式错误或不存在\n' +
  '   - OUTDATED：联系人已离职\n' +
  '   - NEEDS_REVIEW：不确定\n\n' +
  '汇报：\n' +
  '- VERIFIED 数量\n' +
  '- UNVERIFIED 数量\n' +
  '- INVALID 数量\n' +
  '- OUTDATED 数量\n' +
  '- NEEDS_REVIEW 数量\n' +
  '- 可立即外联的直联列表',
  { label: '直联验证', phase: 'Verify' }
)

log('直联验证完成')

// Phase 5: 自动优化
phase('Optimize')

log('启动 Optimizer 分析结果')

const optimization = await agent(
  OPTIMIZER_ROLE + '\n\n' +
  '## 本次任务：分析运行结果并优化配置\n\n' +
  '基于以下运行结果：\n\n' +
  '### B 区结果\n' + bResult + '\n\n' +
  '### A 区结果\n' + aResult + '\n\n' +
  '### 验证结果\n' + validation + '\n\n' +
  '请执行以下优化：\n\n' +
  '1. 分析运行结果，识别瓶颈\n' +
  '2. 检查当前配置：\n' +
  '   - config/kp_pipeline.json\n' +
  '   - config/keyword_scheduler.json\n' +
  '3. 自动调整配置参数（如有必要）\n' +
  '4. 记录优化历史到 .optimization_history.json\n\n' +
  '汇报优化结果：\n' +
  '- 是否需要优化\n' +
  '- 优化了哪些参数\n' +
  '- 优化前后对比\n' +
  '- 下一轮注意事项',
  { label: 'Optimizer', phase: 'Optimize' }
)

log('优化完成')

// Phase 5: 生成报告
phase('Report')

log('生成报告')

const report = await agent(
  '# Role: 报告生成\n\n' +
  '请生成改进报告：\n\n' +
  '1. 执行命令生成报告：\n' +
  '   - python scripts/reports/generate_run_report.py --auto-stats --auto-timing\n' +
  '   - python scripts/reports/generate_keyword_report.py --auto-timing\n\n' +
  '2. 更新 docs/current-progress.md\n\n' +
  '3. 汇报：\n' +
  '   - B 区新发现公司数\n' +
  '   - A 区新增直联数\n' +
  '   - 当前直联总数\n' +
  '   - 距离目标 100 还差多少\n' +
  '   - 优化建议\n' +
  '   - 下一步建议',
  { label: '报告生成', phase: 'Report' }
)

// 返回汇总结果
return {
  bAnalysis,
  aAnalysis,
  bResult,
  aResult,
  validation,
  verification,
  optimization,
  report,
  summary: 'B 区整改 + A 区测试 + 直联验证完成，目标直联 60'
}
