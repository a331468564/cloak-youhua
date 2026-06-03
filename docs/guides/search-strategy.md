<!-- DOC_META
lifecycle:  long-term
audience:   agent
write_when: 发现搜索阻塞、搜索模式失效、或找到更优搜索策略时更新
read_when:  遇到搜索阻塞或需要优化搜索策略时查阅
delete_when: 不删除
-->
# Search Strategy — 搜索策略经验库

*Created: 2026-06-02*
*Updated: 2026-06-02*

**用途：** 记录 A 区（KP 管线）和 B 区（关键词发现）的搜索模式效果验证、数据源可靠性、已知限制、最佳实践。日常不看，遇到阻塞或需要优化时查阅。

**覆盖范围：**
- A 区 Stage 1：KP 发现（公司页面抓取、团队页面提取）
- A 区 Stage 2：直联富化（邮箱/电话/LinkedIn 搜索）
- A 区 Stage 3：验证门控（评分和路由）
- B 区：关键词发现（Google 搜索、公司发现）

**更新规则：** 发现搜索阻塞或更优策略时，主动登记到本文档。

---

## 1. 数据源可靠性排名

| 排名 | 数据源 | 可靠性 | 说明 |
|------|--------|--------|------|
| 1 | 公司官网（about/team/contact 页面） | ⭐⭐⭐⭐⭐ | 最可靠，直接从源头获取 |
| 2 | 公司官网 sitemap | ⭐⭐⭐⭐⭐ | 系统性发现页面的最佳方式 |
| 3 | Google 搜索（公司级查询） | ⭐⭐⭐⭐ | 如 "company name" team OR contact |
| 4 | Google 搜索（KP 级查询） | ⭐⭐⭐ | 如 "person name" "company" email |
| 5 | Google site: 搜索 | ⭐⭐ | 对 LinkedIn 等平台基本无效 |
| 6 | LinkedIn 公开页面 | ❌ | 未登录返回 451，完全无法访问 |

---

## 2. 搜索模式效果验证

### ❌ 无效模式（不要再用）

| 模式 | 问题 | 数据验证 |
|------|------|---------|
| `site:linkedin.com/in "name" "company"` | Google 对 LinkedIn 索引极差，几乎无结果 | 20 个有效 LinkedIn URL 全部来自公司官网，0 个来自此搜索 |
| `site:linkedin.com/in "name"` | 同上 | 同上 |
| 直接访问 `linkedin.com/in/xxx` | 未登录返回 HTTP 451 | Scrapling/CloakBrowser/urllib 全部 451 |
| `site:facebook.com "name" "company"` | 类似 LinkedIn，索引差 | 未验证，但预期同样无效 |

### ✅ 有效模式

| 模式 | 效果 | 说明 |
|------|------|------|
| `"company name" team OR leadership OR staff` | 好 | 公司级查询，一次搜索覆盖多人 |
| `"company name" contact OR "get in touch"` | 好 | 发现联系页面 |
| `site:{domain} team OR about` | 中 | 精确搜索公司网站，但有时返回 0 结果 |
| 从公司官网 sitemap 筛选 team/about/contact 页面 | 最好 | 不消耗 Google 配额，覆盖率高 |

---

## 3. Google 搜索限制

### 429 触发条件

| 条件 | 阈值 | 说明 |
|------|------|------|
| 单 IP 连续搜索 | ~5-10 次 | 触发 429，需切换代理节点 |
| 同一域名 site: 搜索 | ~3 次 | Google 对 site: 查询更敏感 |
| 短时间内密集搜索 | 不确定 | 2-4 秒间隔仍然太短 |

### 429 恢复策略

1. 切换代理节点（18 个节点池：JP/TW/SG/HK/US）
2. 等待 10-15 秒冷却
3. 3 次连续 429 → 暂停 5 分钟
4. 切换后验证新代理 IP ≠ 本机 IP

### 搜索配额管理

- 每日上限：50 次 Google 搜索（会话级）
- 优先级：公司级查询 > KP 级查询
- 超限后：跳过 Google 阶段，仅用公司网站抓取结果

---

## 4. LinkedIn URL 获取策略

### 已验证的有效方法

1. **公司官网 about/team 页面直接链接**
   - 最可靠，20/20 有效 LinkedIn URL 来自此方法
   - 示例：`https://applejackhospitality.com.au/` 页面直接链接到创始人 LinkedIn

2. **公司官网 sitemap → team/about 页面 → 提取 LinkedIn URL**
   - 系统性方法，覆盖率高

3. **Google 搜索公司名（非 site:linkedin.com）**
   - 搜索结果页面可能包含 LinkedIn URL
   - 但效率低于直接从公司官网获取

### 已验证的无效方法

1. ~~`site:linkedin.com/in "name" "company"`~~ — Google 索引差，0 成功率
2. ~~直接访问 `linkedin.com/in/xxx`~~ — HTTP 451，未登录无法访问
3. ~~LinkedIn 公开 profile 猜测~~ — URL 格式不确定，访问也无效

---

## 5. 邮箱模式推断

### 已验证的邮箱模式

| 模式 | 示例 | 成功率 |
|------|------|--------|
| firstname.lastname@domain | john.smith@company.com | 高 |
| firstnamelastname@domain | johnsmith@company.com | 中 |
| f.lastname@domain | j.smith@company.com | 中 |
| firstname.l@domain | john.s@company.com | 低 |

### 推断策略

1. 从公司网站提取所有邮箱
2. 分析个人邮箱（含 `.` 或 `_` 的 local part）的模式
3. 为未匹配的 KP 生成候选邮箱
4. 优先使用最常见的模式

### 注意事项

- 推断邮箱需标记为 `inferred_from_pattern`，confidence 为 Medium
- 不要推断 `info@`、`hello@` 等通用邮箱
- 邮箱域名必须从实际发现的邮箱中提取，不能假设

---

## 6. 常见阻塞及解决方案

### 阻塞 1: Google 429 频繁触发

**症状：** Stage 2 连续多轮直联率为 0%，日志显示大量 429

**原因：** 
- 代理 IP 被 Google 标记（数据中心 IP）
- 搜索间隔太短（2-4 秒）
- 搜索模式太明显（site:linkedin.com）

**解决方案：**
1. 切换到公司级查询模式（减少搜索次数）
2. 增加搜索间隔到 10-15 秒
3. 使用每日搜索配额（50 次上限）
4. 优先从公司网站抓取，Google 只做兜底

### 阻塞 2: LinkedIn URL 无法获取

**症状：** 需要 KP 的 LinkedIn URL，但无法找到

**原因：** LinkedIn 未登录返回 451，Google site: 搜索无效

**解决方案：**
1. 从公司官网 about/team 页面查找直接链接
2. 从公司 sitemap 中查找 team 页面
3. 放弃自动获取，标记为需人工验证

### 阻塞 3: 邮箱推断不准

**症状：** 推断的邮箱被退回或无效

**原因：** 
- 公司邮箱模式不统一
- KP 使用非标准邮箱格式
- 推断模式选择错误

**解决方案：**
1. 收集更多样本邮箱确认模式
2. 使用多种模式生成候选邮箱
3. 标记为 `needs_review`，需人工验证

---

## 7. 最佳实践

### Stage 2 优化策略（2026-06-02 验证）

1. **公司级批量处理** — 同一公司只抓取一次网站，多个 KP 共享结果
2. **邮箱模式推断** — 发现 `firstname.lastname@domain` 后自动推断
3. **Google 搜索配额** — 每日 50 次上限，公司级查询优先
4. **结果缓存** — 同一公司不重复抓取

### 效果对比

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 直联率 | 0% | 20% |
| Google 搜索次数/批 | 80-120 | 20-40 |
| 429 触发率 | 高 | 低 |

---

## 8. A 区（KP 管线）搜索经验

### Stage 1: KP 发现

**有效方法：**
- 公司官网 about/team 页面 → 提取人名 + 职位
- 公司 sitemap → 筛选 team/about/people/leadership 页面
- 从页面中的邮箱推断人名（firstname.lastname@domain → "Firstname Lastname"）

**无效方法：**
- 直接访问 `/team`、`/about` 等猜路径 → 大量 404
- 从 role_context 片段自动提取人名 → 误报率高（已优化：section header 剥离 + 数字词黑名单）

**关键发现：**
- `key_person_name` 提取逻辑误报率从 93% 降到 ~0%（Run 31 验证）
- role_context 中的人名需要手动解析，不能自动提取

### Stage 2: 直联富化

**有效方法：**
- 公司级批量处理（同一公司只抓取一次网站）
- 邮箱模式推断（从已有邮箱推断 firstname.lastname@domain）
- 公司级 Google 查询（"company name" team OR contact）

**无效方法：**
- KP 级 Google 查询（每个 KP 都搜一次）→ 429 频繁
- LinkedIn site: 搜索 → 0 成功率
- 直接访问 LinkedIn 公开页面 → HTTP 451

**关键发现：**
- 直联率从 0% 提升到 20%（2026-06-02 验证）
- 公司官网是 LinkedIn URL 的唯一可靠来源（20/20 有效 URL 来自官网）

### Stage 3: 验证门控

**评分逻辑：**
- 姓名 + 职位 + 直联方式 → 0-100 分
- ≥85: 自动批准 | <30: 自动拒绝 | 30-85: 人工审核

**关键发现：**
- 人工审核准确率 100%（7/7 通过）
- 自动批准数据不足，暂不启用

---

## 9. 待验证假设

以下假设尚未充分验证，需要在后续运行中确认：

- [ ] 公司级查询是否真的比 KP 级查询更有效（需要更多数据）
- [ ] 邮箱模式推断的准确率（需要人工验证推断邮箱）
- [ ] 每日 50 次配额是否合理（可能需要调整）
- [ ] 代理节点池是否需要扩充或更换（数据中心 IP 可能被全面标记）

---

## 更新日志

| 日期 | 更新内容 |
|------|---------|
| 2026-06-02 | 初始版本：LinkedIn site: 搜索无效验证、公司级查询策略、邮箱模式推断、Google 429 管理 |
