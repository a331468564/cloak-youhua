export const meta = {
  name: 'verify-contacts',
  description: '验证当前直联数据的准确性',
  phases: [
    { title: 'Load', detail: '加载当前直联数据' },
    { title: 'Verify', detail: '验证每条直联' },
    { title: 'Report', detail: '生成验证报告' },
  ],
}

// ============================================
// Agent 角色定义
// ============================================

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

// ============================================
// 工作流执行
// ============================================

// Phase 1: 加载数据
phase('Load')

log('加载当前直联数据')

const loadData = await agent(
  CONTACT_VERIFIER + '\n\n' +
  '## 本次任务：加载直联数据\n\n' +
  '请执行以下操作：\n\n' +
  '1. 读取 `data/contacts.csv`\n' +
  '2. 筛选出有直联的记录（有邮箱或电话或 LinkedIn）\n' +
  '3. 统计各类直联数量\n' +
  '4. 按公司分组，列出所有直联\n\n' +
  '汇报：\n' +
  '- 总直联数\n' +
  '- 有邮箱的数量\n' +
  '- 有电话的数量\n' +
  '- 有 LinkedIn 的数量\n' +
  '- 需要验证的记录列表',
  { label: '加载数据', phase: 'Load' }
)

log('数据加载完成')

// Phase 2: 验证直联
phase('Verify')

log('开始验证直联')

const verification = await agent(
  CONTACT_VERIFIER + '\n\n' +
  '## 本次任务：验证直联准确性\n\n' +
  '基于加载的数据：\n' + loadData + '\n\n' +
  '请验证每条直联：\n\n' +
  '### 邮箱验证\n' +
  '1. 检查格式是否正确\n' +
  '2. 检查域名是否存在\n' +
  '3. 检查来源是否可靠\n\n' +
  '### 电话验证\n' +
  '1. 检查格式是否正确\n' +
  '2. 检查区号是否正确\n' +
  '3. 检查来源是否可靠\n\n' +
  '### LinkedIn 验证\n' +
  '1. 检查 URL 格式\n' +
  '2. 检查可访问性\n' +
  '3. 检查匹配度\n\n' +
  '汇报每条直联的验证结果：\n' +
  '- VERIFIED（已验证）\n' +
  '- UNVERIFIED（未验证）\n' +
  '- INVALID（无效）\n' +
  '- OUTDATED（过期）\n' +
  '- NEEDS_REVIEW（待审）',
  { label: '验证直联', phase: 'Verify' }
)

log('验证完成')

// Phase 3: 生成报告
phase('Report')

log('生成验证报告')

const report = await agent(
  CONTACT_VERIFIER + '\n\n' +
  '## 本次任务：生成验证报告\n\n' +
  '基于验证结果：\n' + verification + '\n\n' +
  '请生成验证报告：\n\n' +
  '1. 统计验证结果：\n' +
  '   - VERIFIED 数量\n' +
  '   - UNVERIFIED 数量\n' +
  '   - INVALID 数量\n' +
  '   - OUTDATED 数量\n' +
  '   - NEEDS_REVIEW 数量\n\n' +
  '2. 列出 INVALID 和 OUTDATED 的详情\n\n' +
  '3. 列出 NEEDS_REVIEW 的详情\n\n' +
  '4. 给出建议：\n' +
  '   - 哪些直联可以立即外联\n' +
  '   - 哪些需要进一步验证\n' +
  '   - 哪些应该标记为无效\n\n' +
  '5. 更新 docs/current-progress.md 中的直联统计',
  { label: '生成报告', phase: 'Report' }
)

// 返回汇总结果
return {
  loadData,
  verification,
  report,
  summary: '直联验证完成'
}
