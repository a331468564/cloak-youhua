<!-- DOC_META
lifecycle:  temporary
audience:   both
write_when: 触发条件见文档内"更新规则"一节
read_when:  每次新会话启动时必须读取
delete_when: 新会话读取后可覆盖
-->
# Current Progress

<!-- CODEx_START: current_progress -->
*Updated: 2026-05-30 (Run 25 完成 — Stage 2 直联富化，1 新直联，直联 74→75，边际收益持续下降)*

## 更新规则

**每次会话结束前，如果有以下任一情况，必须更新本文档：**

1. **管线运行完成** — 更新 AU 线索富化进度表、管线状态、运行指标
2. **数据量变化** — leads.csv 或 contacts.csv 行数变化超过 5 行
3. **新联系人确认** — 用户验证了 LinkedIn URL、确认了外联结果
4. **工具/流程变更** — 新脚本、新钩子、新配置上线
5. **方向调整** — 用户改变了优先级、市场、客户类型

**更新内容清单：**
- 顶部 `*Updated:*` 日期
- 数据快照表格（行数、富化进度）
- 管线状态（新运行结果）
- 下一步方向（已完成的划掉，新增的补上）
- 用户配合事项（已验证的标记完成）

**不要更新的情况：**
- 小修小改（修了个 typo、改了个路径）
- 管线跑了一轮但没有新发现
- 纯粹的文档规范化操作

**重要：两个任务互不干扰。** 做表单收集时只更新 A 区，做关键词拓展时只更新 B 区。不要混写。

---

## 数据快照（共享）

| 文件 | 行数 | 说明 |
|------|------|------|
| `data/leads.csv` | 348 | 主线索表（Run 24 含 AU- 前缀新线索） |
| `data/contacts.csv` | 168 | 联系人表（Run 24 Stage 2 更新 3 条直联） |
| `data/search_keywords.csv` | 624 | 搜索关键词定义，29 字段（V3 从 V2 同步） |
| `data/keyword_runs.csv` | 58 | 关键词运行记录，21 字段（V3 从 V2 同步） |

---

<!-- TASK_A_START: kp_pipeline -->
## A. KP 管线（表单收集）<!-- 做表单收集任务的 agent 读这一块 -->

> **定位：** 已知公司名 → 找联系人。读取 `docs/workflows/lead-collection-workflow.md`。

**AU 线索富化进度（344 条线索，~225 条 AU）：**

> **注意：** Run 19 新增 57 家 AU 公司（酒店/餐饮/承办），待 A 区表单收集补充联系信息。

| 指标 | 数量 | 说明 |
|------|------|------|
| 有 KP 姓名 | 80 | Run 24 实际 AU KP 数（含非 AU 共 91） |
| 有 KP 直联（邮箱+电话+LinkedIn） | 31 | Run 25 +1（Veriu Group Zed Sanjana 邮箱+电话） |
| KP 但无直联方式 | 49 | Run 25 -1（边际收益持续下降） |
| 完全无 KP | ~153 | 含新发现公司待富化 |

**公司联系路由覆盖（277 条线索）：**

| 类型 | 数量 | 说明 |
|------|------|------|
| 有公司邮箱 | 194 | Run 18 +4（Achefstouch/Elizabethandrews/Palmer 等） |
| 有公司电话 | 207 | Run 18 +3 |
| 有联系表单 URL | 148 | Run 18 +2（Australian Hotel/Palmer） |
| 有联系页 | 194 | Run 18 +2（Palmer/Millbrook） |
| 有公司 LinkedIn | 54 | Run 18 +12（Bentley/AVC/Crystalbrook/EVT/Meriton/Ovolo/Maybe/ALH/Signature/Gambaro/AHS/Bay13 等） |
| 有任何联系信息 | 265 | **12 条仍无任何联系信息**（3 AU + 9 非 AU） |

**联系人概况（168 条）：**

| 类型 | 数量 | 说明 |
|------|------|------|
| 有邮箱（人名） | 39 | 可直接外联 |
| 有手机号 | 22 | 可直接外联 |
| 有公司邮箱 | 3 | 低价值，需转介 |
| **直联总数（人名邮箱+手机）** | **75** | **目标 100，差 25**（Run 25 +1：Veriu Group Zed Sanjana） |
| LinkedIn 直接 URL | 18 | 已确认的个人主页（Run 20 +9） |
| LinkedIn 搜索 URL | 8 | **需用户手动验证**（见下方清单） |

**管线运行记录：**
- Run 1 (2026-05-19): 处理 37 家，富化 8 家，直联 4 个（10.8%）。7 个待审候选全部通过。
- Run 2 (2026-05-20 上午): 处理 34 家，富化 6 家，直联 1 个（2.9%）。
- Run 3 (2026-05-20 下午): Stage 2 处理 34 家，富化 6 家，直联 1 个（2.9%）。
- Run 4 (2026-05-20 18:11): CloakBrowser 修复验证测试，Stage 2 处理 5 家，富化 2 家，直联 0 个。
- Run 5 (2026-05-20 22:24): 全量管线（Stage 1+2+3）。Stage 1 发现 415 候选人（40 家）。Stage 2 处理 34 家，富化 6 家，直联 1 个（2.9%）。Stage 3 自动批准 0，自动拒绝 417，人工审核 4 个。
- Run 6 (2026-05-21 14:38): 全量管线（Stage 1+2+3），limit 50。Stage 1 发现 385 候选人（50 家）。Stage 2 处理 34 家，富化 6 家，直联 1 个（2.9%）。Stage 3 自动批准 0，自动拒绝 387，人工审核 4 个。
- Run 7 (2026-05-22): 分步运行。Stage 1 (limit 40): 402 候选人（25 家公司）。Stage 2 (limit 34): 处理 34 家，富化 7 家，直联 2 个（5.9%）。Stage 2 结果未自动保存。手动检查联系页：Blank Creatives 手机 0438 745 304，Pleysier Perkins 座机 (03) 9533 6766。
- **Run 8 (2026-05-22 14:54): 表单收集批次。4 批 extraction（60 条线索），保存 43 家公司联系路由（95 个新字段）。覆盖：邮箱 84 家、电话 85 家、表单 93 家、联系页 108 家。剩余 10 条空状态（TLS/SSL 错误）。**
- **Run 9 (2026-05-25): 数据清理会话。重试 10 条空状态 → 全部有状态。填补 13 条联系路由空缺。清空 86+93 个废弃字段值。合并 2 对跨公司重复。删除 5 个死字段（53→48）。清理 request-solution-log.md（3409→108 行）。**
- **Run 10 (2026-05-25): 表单收集批次。25 个候选队列，2 批 extraction（25 家公司），514 个候选。新增 3 个 KP（EVT-Jane Hastings / Meriton-Harry Singh / Taverners-Kate Wilkie）。填补 8 家无联系路由线索。KP 47→50，contacts 154→157。**
- **Run 11 (2026-05-25): keyword-driven 管线测试。处理 10 家已有线索，未发现新公司。确认：keyword-driven 模式只做富化，不做发现。**
- **Run 12 (2026-05-26): 关键词发现 + 表单收集。20 Scale 关键词搜索 → 发现 26 家新 AU 公司入库（restaurant group / hotel / winery / brewery）。Extraction 3 批（26 家），296 候选。新增 2 个 KP（Global Hospitality-Nicholas Kalogeropoulos / Hurley Hotel-Jessica Bellwood）。16 家更新联系路由。leads 195→221，contacts 157→161。**
- **Run 13 (2026-05-26): 表单收集批次。106 候选队列，5 批 extraction（42 家公司），639 候选。填补 30 个联系路由字段。新增 1 个 KP（Tony Kelly-tony@tkrg.com.au）。21 条状态更新为"已找到联系路径"。AU 无联系路由：16→5。leads 277（不变），contacts 161→162。**
- **Run 14 (2026-05-26): 合并 Run 13 遗漏候选。从 5 个 form-batch 文件中提取 733 候选，保存 15 个新字段（9 KP 姓名、3 人名邮箱、3 KP LinkedIn）。277 条线索中有 251 条（91%）至少有 1 种联系信息。26 条仍无联系信息（11 条非 AU、15 条 AU）。**
- **Run 15 (2026-05-26): 表单收集批次。24 候选队列（build_form_kp_candidate_queue），3 批 extraction（24 家公司），453 候选。更新 16 家联系路由（+6 邮箱、+12 电话、+4 表单）。关键新增：Bentley 6 邮箱+3 电话+LinkedIn、AVC 3 邮箱（含 procurement@）、ALH/Gambaro 邮箱、Lancemore/Meriton/Ovolo/Taverners 电话。覆盖率 91%→94%（262/277）。AU 无联系：15→5。**
- **Run 16 (2026-05-26): 表单收集批次。105 候选 AU 队列（26 missing_kp_direct + 74 missing_kp + 5 missing_company_contact），4 批 extraction（105 家公司），1772 候选。56 条线索更新，219 个新字段。新增联系表单 +12、电话 +3、联系页 +17。AU KP 姓名 52→78，AU 有联系 147→157（97%）。新 KP 线索：Rosy Scatigna（Table For）、Jane Hastings（EVT）、Harry Singh（Meriton）。URL 编码值自动解码修复。**
- **Run 17 (2026-05-27): 表单收集批次。99 候选 AU 队列（55 missing_kp + 45 missing_form + 37 missing_kp_direct + 5 missing_company_contact），4 批 extraction（99 家公司），1736 候选。26 个字段更新，6 个新联系人（PHMG 2 人 / The Point 3 人 / Prancing Pony 1 人），9 个新公司 LinkedIn。contacts 162→168，AU 无联系 5→3。关键新增：Prancing Pony Corinna（邮箱+手机 0409134697）、procurement@ausvenueco.com.au、9 个公司 LinkedIn 页面。4 个 TLS 错误站点。**
- **Run 18 (2026-05-27): 表单收集批次。98 候选 AU 队列（53 missing_kp + 43 missing_form + 36 missing_kp_direct + 5 missing_company_contact），4 批 extraction（98 家公司），1602 候选。8 个字段更新（5 家公司），+12 公司 LinkedIn。边际收益递减：大部分 AU 线索已有联系路由。14 TLS 错误站点。KP 名称提取质量低（多为导航文本）。直联率触底。**
- **Run 20 (2026-05-28): 表单收集 + KP LinkedIn 富化。22 候选 AU 队列（18 missing_kp_direct + 3 missing_form + 3 missing_kp），2 批 extraction（22 家公司），453 候选。Google 搜索 10 个 KP 直联邮箱未果。9 个 KP LinkedIn URL 补全（Brent Savage / Nick Hildebrandt / Chris Lucas / Sven Almenning / Jane Hastings / Bill Gravanis / Rosy Scatigna / Stefano Catino / Justin Hemmes）。contacts 168（不变），LinkedIn 直接 URL 9→18。2 TLS 错误（Merivale / Taverners）。边际收益进一步递减：22 家公司级联系信息几乎全部已在 Run 13-18 覆盖。**
- **Run 21 (2026-05-29): 全阶段管线（Stage 1+2+3, limit 20）。** Stage 1 发现 331 候选人（20 家公司）。Stage 2 处理 20 家，富化 8 家，直联 4 个（20% 直联率，显著回升）。Stage 3 自动批准 0，自动拒绝 332，人工审核 7 个。关键新增：Ian Macklin（TM Design Group，邮箱+手机）、Jasimma（Blank Creatives，手机 0438 745 304）、Nyree Mackenzie（Mackenzie Design，手机 0499554947）、Miko Aspiras（Illoura Hospitality，邮箱）。leads 340→344，contacts 168→169。直联率从 2.9% 回升到 20%，说明剩余线索中仍有可挖掘的直联信息。
- **Run 22 (2026-05-29): Stage 2 富化 + 公司字段提升。** Stage 2 处理 20 家 KP-without-direct-contact 线索，富化 7 家，直联 4 个（20%）。公司字段提升 5 条（Chillie/360Shopfitters/TMDG/HCGroup/GreatIndoors）。修复管线自动保存逻辑（新增 `promote_company_contacts` + `save_enriched_results` 函数）。KP 直联 23→28，直联率 29.5%→35.9%。leads 340（不变），contacts 169（不变）。4 个 TLS 错误站点。
- **Run 23 (2026-05-29): Stage 1 KP 发现 + Stage 2 保存逻辑修复。** Stage 1 处理 20 家无 KP 线索，生成 359 候选人。从 role_context 片段提取 2 个新 KP（Greg Barclay-CEO / Mike Henshaw-Director），修复 2 个公司名前缀（"About Us"）。KP 89→91。Stage 2 处理 20 家 KP-without-direct-contact，富化 6 家，直联 3 个（15%）。**修复 Stage 2 保存逻辑**：新增 `save_stage2_results()` 函数，Stage 2 完成后自动更新 leads.csv key_contact_* 字段 + contacts.csv 追加/更新联系人。测试验证：leads 更新 2 条，contacts 更新 1 条。leads 340（不变），contacts 168（不变）。多个 TLS 错误站点。
- **Run 24 (2026-05-30): Stage 2 直联富化。** 处理 20 家 KP-without-direct-contact 线索，富化 6 家，直联 4 个（20% 直联率）。联系人更新 3 条：Jasimma@Blank Creatives（邮箱+手机）、Mark Brook@MYMYMY（邮箱+电话）、William Kuo@Alleyway Group（邮箱）。leads 更新 5 条（公司字段提升到 KP 字段）。leads 340→348，contacts 168（不变）。直联联系人 71→74。多个 TLS 错误站点（Pleysier Perkins / H&J Restaurants / Elements Dining 等）。
- **Run 25 (2026-05-30): Stage 2 直联富化。** 处理 20 家 KP-without-direct-contact 线索，富化 3 家，直联 1 个（5% 直联率）。Veriu Group Zed Sanjana 邮箱+电话直联。leads 更新 1 条，contacts 更新 1 条。leads 348（不变），contacts 168（不变）。直联联系人 74→75。多个 TLS 错误站点（Pleysier Perkins / Elements Dining / Speakeasy Group 等）。

**自动化门控指标：**
- direct_contact_rate > 10%: Run1 ✓ (10.8%) / Run2-6 ✗ (2.9%) / Run21-24 ✓ (20%) / Run25 ✗ (5%) — 剩余线索质量参差不齐
- false_positive_rate < 15%: 0%（7/7 人工审核通过）
- auto_approve_accuracy > 95%: 数据不足（Run5/6 自动批准 0 个）

**已发现问题：**
1. ~~Stage 1 队列路径不匹配~~ — **已修复**
2. ~~Stage 2 直联率已触底~~ — **Run 21-24 验证回升，Run 25 再次下降**：剩余 49 条线索质量参差不齐，直联率波动大（5%-20%）
3. ~~Google 搜索 429 限流~~ — **已解决**（CloakBrowser + Scrapling 联动）
4. **Swillhouse contact 页 403** — Cloudflare 挑战页，无法绕过
5. ~~管线不自动保存 Stage 2 富化结果~~ — **已修复**（Run 23：新增 `save_stage2_results()` 函数，更新 leads.csv key_contact_* + contacts.csv 追加/更新）
6. **44 条无 customer_type 的线索被队列过滤** — 需 `--include-review-needed` 标志
7. ~~废弃字段未迁移清理~~ — **已修复**（Run 9：清空 179 个废弃值，删除 5 死字段）
8. ~~跨公司重复入库~~ — **已修复**（Run 9：合并 2 对，新增 Entity-Level Dedup Rule）
9. ~~request-solution-log 空模板堆积~~ — **已修复**（3409→108 行，钩子已改为 interval=20 提醒模式）

**关键文件：**
- `scripts/kp_pipeline/run_pipeline.py` — 管线入口
- `scripts/kp_pipeline/stage2_enrich.py` — 富化逻辑
- `scripts/kp_pipeline/stage3_validate.py` — 评分和路由
- `config/kp_pipeline.json` — 阶段配置和阈值
- `reports/kp-pipeline/` — 运行报告
- `scripts/reports/generate_run_report.py` — Run 报告生成器（合并版，追加到 run-log.md）
- `D:\TestProject-v3\reports\run-log.md` — 合并运行记录（V3 待生成）

**A 区下一步：**
- ~~**恢复丢失线索**~~ ✅ 已完成（从 boss-report 导出恢复 56 条，277 条总计）
- ~~**Run 报告系统搭建**~~ ✅ 已完成（generate_run_report.py + run-log.md 合并版，Run 1-16 历史数据已补全）
- ~~**修复 Stage 2 保存逻辑**~~ ✅ 已完成（Run 23：新增 `save_stage2_results()` 函数）
- 扩大直联到 100（当前 75，差 25）— 继续跑 Stage 2 直联富化（剩余 49 条 KP 无直联线索，直联率 5%-20% 波动）
- 对新发现公司继续 KP 发现（91 有 KP / ~162 AU = 56%）
- ~~继续关键词发现（还有 400+ New 关键词未使用）~~ → Run 19 已验证 keyword_discovery.py，B 区待优化
- ~~12 条仍缺全部联系路由的线索需人工确认或标记低优先级~~ ✅ 大部分已填补（Run 13/14/17）
- **12 条仍无任何联系信息**（9 条非 AU + 3 条 AU）：
  - AU 问题站点：The Mulberry Group（SSL）、The Big Easy Group（404）、Vanillablue（404）
  - 非 AU（低优先级）：BMS London / Maguro Group / JOEY Restaurants / Miku Toronto / Ray-Ban / Book Club Bar / 4 家 NY 新开餐厅
- ~~**Run 20 后边际收益已触底**~~ Run 21-24 验证回升（20%），Run 25 再次下降（5%）：剩余线索质量参差不齐
- 继续跑 Stage 2（当前 75 直联，目标 100，差 25，剩余 49 条候选）

**A 区待用户处理：**
- **审核 Run 21 的 7 个人工审核候选：**
  - Ian Macklin（TM Design Group）：imacklin@tmdg.com.au / +61 417 147 110，score 75
  - Jasimma（Blank Creatives）：hello@blankcreatives.com.au / 0438 745 304，score 75
  - Nyree Mackenzie（Mackenzie Design）：create@nyreemackenzie.com / 0499554947，score 75
  - Miko Aspiras（Illoura Hospitality）：enquiry@illourahospitality.com.au，score 65
  - Kiera Hamilton（JLW Fitout）：info@jlwinteriors.com.au / 1300 559 477，score 45
  - Alex Jarrold（Jarrold & Bailie）：info@jarroldandbailie.au，score 45
  - Mark Brook（MYMYMY）：hello@mymymy.com.au / 02 6176 3438，score 45
- 手动验证 8 个 LinkedIn 搜索 URL
- **手动验证 Run 20 新增的 9 个 KP LinkedIn URL**（确认人名/公司匹配）：
  - Chris Lucas → https://au.linkedin.com/in/christopher-lucas-1aa8a3133
  - Sven Almenning → https://au.linkedin.com/in/sven-almenning
  - Jane Hastings → https://au.linkedin.com/in/jane-hastings-77144940
  - Bill Gravanis → https://au.linkedin.com/in/bill-gravanis-a4059121
  - Rosy Scatigna → https://au.linkedin.com/in/rosy-scatigna-a2355192
  - Stefano Catino → https://au.linkedin.com/in/stefano-catino-005a05298
  - Brent Savage → https://au.linkedin.com/in/brent-savage-062464235
  - Nick Hildebrandt → https://au.linkedin.com/in/nick-hildebrandt-303182215
  - Justin Hemmes → https://au.linkedin.com/in/justin-hemmes-84778298
- 评估自动化门控指标（是否启用自动批准）
- **37 条 KP 无直联线索中，大量仅靠联系表单（Trader House / Speakeasy / Merivale 等），需评估是否值得手动外联**
<!-- TASK_A_END: kp_pipeline -->

---

<!-- TASK_B_START: keyword_scheduler -->
## B. Keyword Scheduler（关键词拓展）<!-- 做关键词拓展任务的 agent 读这一块 -->

> **定位：** 未知市场 → 发现新公司。读取 `docs/guides/keyword-scheduler-guide.md`。

**模块状态：** 已完成，可直接使用。

**已完成：**
- ✅ 核心模块：scheduler.py / keyword_discovery.py / tracker.py / config.py
- ✅ 生成器：generator.py（7 维度 × 15 模板，含自动去重）
- ✅ 市场分析：market_intel.py（效果排名 + 候选评分）
- ✅ 导入工具：import_suggestions.py（列不一致自动重写）
- ✅ 测试：11 个单元测试全部通过
- ✅ KP Pipeline 集成：`--keyword-driven` 标志
- ✅ 操作指南：docs/guides/keyword-scheduler-guide.md
- ✅ 任务分离规范：cli-operating-rules.md 新增独立上下文
- ✅ 关键词拓展：38 → 116 → 486 → 624（+138 人工审核导入），覆盖 62 个客户类型
- ✅ 维度扩展：customer_type +25, role +10, geo +13, trigger_event +10
- ✅ 生成器去重：load_existing_patterns() 含占位符展开
- ✅ import_suggestions 字段修复：_KEYWORDS_FIELDNAMES 补齐 5 列
- ✅ scheduler 排序修复：New 状态 +3.0 boost + 随机 jitter，解决新关键词永远选不到的问题
- ✅ generator round-robin 修复：customer_type 均匀分配，不再集中在第一个类型
- ✅ 自动审核：auto_review.py（score >= 0.6 自动通过，< 0.4 自动拒绝，中间需人工）
- ✅ 反馈循环修复：scheduler 解析提取结果 → tracker 自动回写 discovery_quality_score / contactability_score
- ✅ 自动状态调整：3 次运行 0 线索 → 自动 Paused，效果好 → 自动 Active

**关键命令：**
```bash
# 日常采集
python -m scripts.keyword_scheduler.scheduler --dry-run
python -m scripts.keyword_scheduler.scheduler --limit 10

# 生成新关键词
python -m scripts.keyword_scheduler.generator --dry-run --max 50
python -m scripts.keyword_scheduler.generator --max 100

# 自动审核（半自动，替代人工逐行审核）
python -m scripts.keyword_scheduler.auto_review --dry-run
python -m scripts.keyword_scheduler.auto_review

# 导入审核后的关键词
python -m scripts.keyword_scheduler.import_suggestions

# 市场分析
python -c "from scripts.keyword_scheduler.market_intel import generate_market_report; ..."

# 与 KP Pipeline 联动
python -m scripts.kp_pipeline.run_pipeline --stage all --limit 10 --keyword-driven
```

**关键文件：**
- `scripts/keyword_scheduler/` — 模块目录
- `config/keyword_scheduler.json` — 调度器配置
- `config/keyword_dimensions.json` — 维度值 + 查询模板
- `data/search_keywords.csv` — 关键词主库
- `data/keyword_runs.csv` — 运行日志
- `reports/suggested_keywords.csv` — 生成的候选（需审核）
- `docs/guides/keyword-scheduler-guide.md` — 操作指南

**B 区运行记录：**
- **Run 19 (2026-05-28): 关键词发现。** 用 keyword_discovery.py 跑 38 个关键词（pub group / catering company / hotel group / event venue 等），发现 57 家新 AU 公司入库（277→334）。有效公司：酒店集团（Grand Hotel / Oaks / Trilogy / Hunter / Marlow / Song / Laundy / Yarra）、餐饮集团（The Pub Group / PubCo / Laundy / Welcome Hospitality）、餐饮承办（Darwin Catering / Australian Catering / EatFirst / Bespoke Catering / The Catering Dept 等）。清理了大量误入库的非目标公司（招聘中介、设备供应商、招标平台、Ghost Kitchen 文章等）。更新了 keyword_discovery.py 的域名排除列表。
- **Run 20 (2026-05-28): 关键词发现 + 过滤器优化。** 跑 15 个面向实际场地的关键词，发现 49 家公司，但有效率仅 12%（6/49）。根因分析：53% 新闻/文章、14% 学生公寓、12% 行业协会、7% 招聘、14% 教育/政府。清理 43 条非目标，保留 6 家 AU 公司（Mimosa Wines / The Winery Surry Hills / Southern Cross Motel / Australian Motel / Salter Brothers / Regional Motel Partners）。对关键词发现脚本做了 5 项过滤器优化：(1) 域名排除列表扩展 +120、(2) 文章/目录 URL 模式过滤、(3) AU 查询自动增强（`site:.com.au`）、(4) 联系信号检测（页面必须有邮箱/电话/联系页链接）、(5) 文章标题检测 + 媒体/专业服务域名过滤。谷歌 429 限流，优化效果待下次验证。
- **B-Run 21 (2026-05-30): 关键词发现过滤器验证。** 跑 20 个短场地关键词（restaurant group / hotel group / pub group / catering / event venue），发现 8 家新 AU 公司（340→348）。**有效率 88%（7/8）**，验证了 Run 20 过滤器优化效果。有效公司：Umberto Group / Aurora Hotel Group / Lillywhite Hotel Group / MALONEY HOTELS / The Grace Hotel / Commune Group / RG Restaurants。修复 2 个过滤器漏洞：(1) 添加 boothby.com.au 等 5 个媒体域名到排除列表，(2) 增强文章标题检测（问题式标题 "how does/what/why" 等模式）。关键词生产力 20%（4/20 关键词有结果），Melbourne 搜索效果最好。

**B 区下一步：**
- ~~用 generator 批量生成新关键词候选~~ ✅ 已完成（+370 新关键词导入）
- ~~scheduler 排序调整~~ ✅ 已完成（New +3.0 boost + jitter 随机轮换）
- ~~generator round-robin 修复~~ ✅ 已完成（customer_type 均匀分配）
- ~~自动审核 + 反馈循环~~ ✅ 已完成（auto_review.py + tracker 自动回写分数）
- ~~人工审核 suggested_keywords 并导入~~ ✅ 已完成（593 条审核：503 approved / 32 rejected / 58 review，+138 新关键词入库，486→624）
- ~~新关键词发现流程~~ ✅ Run 19 验证（keyword_discovery.py + CloakBrowser Google 搜索）
- ~~**优化关键词质量：**~~ ✅ Run 20 完成过滤器优化（5 项改进），有效率从 12% 预期提升到 50%+，待谷歌 429 恢复后验证
- ~~**验证过滤器效果：**~~ ✅ B-Run 21 验证有效率 88%（Run 20 的 12%→88%），过滤器优化成功
- 对新发现的 8 家公司跑 A 区表单收集（补充联系信息）
- 用 market_intel 分析历史数据，优化关键词库
- 对 58 条 review 状态的关键词做二次人工筛选（可选）
- **优化关键词生产力：** 当前仅 20% 关键词有结果，需测试更多关键词变体
- **优化关键词模式：** 当前长关键词（>5 词）加 site:.com.au 后 Google 返回 0 结果，需生成更短的发现型关键词
<!-- TASK_B_END: keyword_scheduler -->

---

## Hook 系统（共享）

`.claude/settings.json` — 8 个钩子强制执行文档生命周期和清理规则：

| 钩子 | 事件 | 范围 | 作用 |
|------|------|------|------|
| `pre_bash_safety.py` | PreToolUse (Bash) | 项目 | 拦截危险命令 |
| `post_bash_check.py` | PostToolUse (Bash) | 项目 | 脚本运行后检查临时文件 |
| `post_blocker_detect.py` | PostToolUse (Bash) | 项目 | 连续 2 次失败自动注入阻塞查表提醒 |
| `post_run_progress_check.py` | PostToolUse (Bash) | 项目 | 管线运行后提醒更新进度 |
| `post_write_check.py` | PostToolUse (Write) | 项目 | 新 .md 文件必须有 DOC_META |
| `stop_check.py` | Stop / SubagentStop | 项目 | 有未清理文件或重会话未更新进度则阻止结束 |
| `daily_snapshot.py` | SessionStart | 项目 | 每日首次启动自动提交 data/ 快照 |
| `auto_request_solution_log.py` | PostToolUse (全部) | **全局** | 每 10 次工具调用提醒追加 request-solution-log 条目 |

闭环：脚本运行 → 产物警告 → agent 忽略 → Stop 钩子拦截 → agent 必须清理 → 通过。

## 工具备注（共享）

- Tavily 已暂停，当前使用 Scrapling/form 提取。
- **CloakBrowser + Scrapling 深度联动**（`scripts/kp_pipeline/cloak_fetcher.py`）：
  - 域名路由记忆：`data/fetch_routes.json` 记住每个域名哪个工具可用
  - Cookie 传递：CloakBrowser 探路拿 cookies/UA → 传给 Scrapling
  - 智能降级：Scrapling 失败 → CloakBrowser 兜底 → cookies 回传 Scrapling
  - Google 搜索始终用 CloakBrowser（绕过 429）
- 线索看板：`.\scripts\utils\start_dashboard.ps1` 然后打开 `http://localhost:8765/dashboard/`。

## 常用命令（共享）

```powershell
cd E:\AI\TestProject-v2
git status --short
.\.venv\Scripts\python scripts\utils\check_capability_inventory.py
```

看板：
```powershell
.\scripts\utils\start_dashboard.ps1
```

**A 区命令（表单收集）：**
```powershell
python -m scripts.kp_pipeline.run_pipeline --stage all --limit 40
```

**Run 报告生成（每轮任务跑完后必须执行）：**
```powershell
python scripts/reports/generate_run_report.py --input run_data.json --auto-stats
```
输出目录：`E:\自动跑表单的成果和情况\`

**B 区命令（关键词拓展）：**
```powershell
python -m scripts.keyword_scheduler.scheduler --dry-run
python -m scripts.keyword_scheduler.scheduler --limit 10
python -m scripts.keyword_scheduler.generator --dry-run --max 50
```

## 守则（共享）

- 不做大范围源数据改动，除非有明确计划。
- 不使用 Tavily，除非重新批准。
- 工作流/工具变更记录到 `docs/logs/changelog.md`。
- 钩子强制清理 — 有未清理文件会阻止会话结束。
- **A 区和 B 区独立更新，不混写。**

## 自动化

- `/full-auto-pipeline` — 运行一次完整管线（表单收集→KP富化→关键词发现→报告）
- `/loop 30m /full-auto-pipeline` — 每 30 分钟自动运行管线
- 每日快照：`daily_snapshot.py` 钩子在会话启动时自动 commit data/
- 权限：VSCode 扩展已配置 `bypassPermissions`，管线运行无需人工确认
- 安全兜底：`pre_bash_safety.py` 拦截破坏性命令，`stop_check.py` 拦截未清理退出

<!-- CODEx_END: current_progress -->
