<!-- DOC_META
lifecycle:  temporary
audience:   both
write_when: 触发条件见文档内"更新规则"一节
read_when:  每次新会话启动时必须读取
delete_when: 新会话读取后可覆盖
-->
# Current Progress

<!-- CODEx_START: current_progress -->
*Updated: 2026-06-03 (A-Run 71: 报告生成，542 公司/234 联系人/93 直联，覆盖率 97.0%。B-Run 69: 报告生成，179 关键词运行，124 有效结果但 0 新公司。可靠直联 93，距目标 100 差 7。候选池持续饱和，需新搜索渠道或手动验证 LinkedIn。)*

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
| `data/leads.csv` | 542 | 主线索表（B 区区域城市搜索 +49，15 条已标记 needs_review：10 条 eater.com 媒体 URL + 5 对重复 website） |
| `data/contacts.csv` | 234 | 联系人表（含 9 条 needs_review，pending_verification 已清零） |
| `data/search_keywords.csv` | 1712 | 搜索关键词定义，29 字段（B-Run 60 生成器新增 252） |
| `data/keyword_runs.csv` | 179 | 关键词运行记录，21 字段 |

---

<!-- TASK_A_START: kp_pipeline -->
## A. KP 管线（表单收集）<!-- 做表单收集任务的 agent 读这一块 -->

> **定位：** 已知公司名 → 找联系人。读取 `docs/workflows/lead-collection-workflow.md`。

**AU 线索富化进度（502 条线索，含 A 区 ~144 + B 区 ~358）：**

| 指标 | 数量 | 说明 |
|------|------|------|
| 有 KP 姓名 | ~101 | Run 36 +3（Stage 2 新发现 KP） |
| 有 KP 直联（邮箱+电话+LinkedIn） | 79 | Run 61 重新审计（T1 个人邮箱+手机 16，T2 单渠道 63） |
| KP 但无直联方式 | ~22 | 仅 LinkedIn 30 - 需手动验证 |
| 完全无 KP | ~170 | 含新发现公司待富化 |

**公司联系路由覆盖（502 条线索）：**

| 类型 | 数量 | 说明 |
|------|------|------|
| 有公司邮箱 | 333 | 含 key_contact_email（A-Run 70 +7） |
| 有公司电话 | 333 | 含 key_contact_phone（A-Run 70 +7） |
| 有联系表单 URL | 148 | company_contact_form_url |
| 有联系页 | 193 | company_contact_page |
| 有公司 LinkedIn | 54 | company_linkedin_url |
| 有任何联系信息 | 486 | **覆盖率 96.8%**（16 条仍无任何联系信息） |

**联系人概况（234 条，2026-06-03 A-Run 70 后）：**

| 类型 | 数量 | 说明 |
|------|------|------|
| **已找到直联** | **59** | 有邮箱或电话的联系人（54 有直接联系方式） |
| **已识别联系人** | **155** | 已确认身份但未找到直联方式 |
| **需审核（needs_review）** | **9** | 误报/存疑数据（含多姓名邮箱推断误报） |
| **需人工确认** | **7** | 待手动查找联系方式 |
| **待验证（pending_verification）** | **4** | 待验证数据 |
| **可靠直联（有邮箱+电话）** | **93** | 有邮箱或电话，可外联 |
| 有邮箱 | 65 | 含公司通用邮箱 |
| 有电话 | 55 | 含座机/1300 |
| 有 LinkedIn | 36 | 含 Matthews 8 条已验证 |
| 无任何联系信息 | 107 | |

> **2026-06-03 A-Run 67 数据质量清理：** Stage 2 跑 10 家公司，0 富化（候选池饱和）。随后进行数据质量清理：(1) 7 条升级为直联（Chef Rob Bellamy 手机、Guy/Mark/Corinna/Nicholas/Peter/Tony 邮箱）；(2) 14 条 pending_verification 全部处理（Matthews 8→已识别联系人、Salter 5→需人工确认、Catering 1→需人工确认）；(3) 17 条 empty status 全部填充；(4) Frank Tucker 手机字段含 LinkedIn URL 已修正；(5) 2 条多姓名误报移入 needs_review。已找到直联 52→59（+7），可靠直联 90→89（Frank Tucker 修正 -1）。

**管线运行汇总（45 轮，2026-05-19 ~ 2026-06-03）：**

| 阶段 | 总轮次 | 总候选 | 总富化 | 总直联 | 平均直联率 |
|------|--------|--------|--------|--------|-----------|
| Stage 1 KP 发现 | 16 | ~6457 | — | — | — |
| Stage 2 直联富化 | 29 | ~570 | ~120 | ~35 | ~6% |
| Stage 3 验证门控 | 8 | ~2689 | — | — | — |

> 📋 完整运行记录：`E:\自动跑表单的成果和情况\run-log.md`

**最近 3 次运行：**
- **Run 68 (2026-06-03):** Stage 2 标准运行。**跑 10 家公司，0 富化，0 直联。** 连续多轮零直联，候选池已确认饱和。
- **Run 69 (2026-06-03):** KP 级搜索策略测试。**测试 5 个 Tier 3 高管（Frank Tucker、Brent Savage、Nick Hildebrandt、Stefano Catino、Rosy Scatigna），0 直联。** 验证了行业特性：酒店餐饮高管不公开个人联系方式。新增 `stage2_kp_level_search.py` 脚本。
- **Run 70 (2026-06-03):** Stage 2 标式运行。**跑 10 家公司，0 富化，0 直联。** 候选池持续饱和，Stage 2 已无可用候选。
- **Run 71 (2026-06-03):** 报告生成运行。**542 公司/234 联系人/93 可靠直联，覆盖率 97.0%，直联率 32.9%。** 数据量不变（+41 邮箱/+35 电话为 A-Run 71 报告统计差异，实际 contacts.csv 行数不变）。

**自动化门控指标：**
- direct_contact_rate > 10%: Run1 ✓ (10.8%) / Run2-6 ✗ (2.9%) / Run21-24 ✓ (20%) / Run25-26 ✗ (0%-5%) / Run27 ✓ (Stage 1 定向，+1 直联) / Run28 ✗ (0%) / Run29 ✓ (Stage 1 定向，+1 直联) / Run30 ✗ (Stage 1 定向，0 直联，候选质量低) / Run31 ✗ (Stage 1 定向，0 直联，+2 联系人) / Run32 ✗ (Stage 2 直联 0%，人工审核 -1 直联) / Run33 ✗ (Stage 1+2 全跑，0 直联) / Run35 ✓ (Stage 2 直联 10%，+2 推断邮箱) / Run36 ✗ (7.5%，+3 直联) / Run38 ✗ (0%，趋势未持续) / Run45 ✗ (0%，连续两轮零直联) / Run50 ✗ (0%，连续三轮零直联) / Run52 ✗ (0%，连续四轮零直联) / Run55 ✗ (0%，+1 电话但无可靠直联) / Run56 ✗ (报告生成，+27 公司/+19 邮箱/+15 电话，可靠直联 46 不变) / Run57 ✗ (报告生成，+3 公司/+20 邮箱/+16 电话，可靠直联 46 不变) / Run58 ✗ (Stage 2 直联率 10%，但 1 条为误报已标记 needs_review) / Run61 ✗ (报告生成，+1 公司/+2 邮箱，可靠直联 79 重新审计) / Run67 ✗ (Stage 2 跑 10 家公司 0 富化，数据清理 +7 直联，pending_verification 清零，空状态清零) / Run68 ✗ (Stage 2 跑 10 家公司 0 富化 0 直联，候选池确认饱和) / Run69 ✗ (KP 级搜索测试 5 高管 0 直联，行业特性验证) / **Run70 ✗ (Stage 2 跑 10 家公司 0 富化 0 直联，候选池持续饱和) / Run71 ✗ (报告生成，542 公司/234 联系人/93 直联，覆盖率 97.0%，数据量不变)**
- false_positive_rate < 15%: 0%（7/7 人工审核通过）
- auto_approve_accuracy > 95%: 数据不足（Run5/6 自动批准 0 个）

**活跃问题：**
1. ~~**⚠️ Run 36 直联数据失实**~~ ✅ **已修正** — 2026-06-02 重新审计
2. **Stage 2 直联率零** — Run 38~70 连续 0%，候选池已饱和，KP 级搜索策略测试也无效（行业特性：酒店餐饮高管不公开个人联系方式）
3. ~~**需审核数据 21 条**~~ ✅ **已清理** — pending_verification 14→0，needs_review 7→9（+2 多姓名误报）
4. **Stage 1 队列重复处理** — 标准队列按优先级排序，高优先级公司被反复处理。Run 27 改用定向队列解决
5. ~~**Stage 1 候选质量低**~~ ✅ **已优化**
6. **Swillhouse contact 页 403** — Cloudflare 挑战页，无法绕过
7. **Google 429 频繁** — 代理轮换后恢复
8. **Stage 1 结果未自动合并** — Stage 1 产出 350+ 候选（Run 38），仅存报告 CSV，未自动合并
9. ~~**推断邮箱需验证**~~ ✅ **已验证**
10. ~~**Run 36 Stage 3 人工审核 12 候选**~~ ✅ **已处理**
11. ~~**⚠️ Run 60 邮箱推断误报**~~ ✅ **已标记 needs_review**
12. **Frank Tucker 手机字段修正** — C-0012 手机字段含 LinkedIn URL，已修正为 linkedin_url
13. **多姓名邮箱推断误报** — CT-0224 (AVC) 和 CT-0225 (Crystalbrook) 为邮箱推断 bug 产生的多姓名混合体，已标记 needs_review

**关键文件：**
- `scripts/kp_pipeline/run_pipeline.py` — 管线入口
- `scripts/kp_pipeline/stage2_enrich.py` — 富化逻辑
- `scripts/kp_pipeline/stage3_validate.py` — 评分和路由
- `config/kp_pipeline.json` — 阶段配置和阈值
- `reports/kp-pipeline/` — 单次运行报告
- `scripts/reports/generate_run_report.py` — Run 报告生成器
- `E:\自动跑表单的成果和情况\run-log.md` — 完整 A 区运行记录（26 轮）

**A 区下一步：**
- ~~**优先级 0：修复邮箱推断 bug**~~ ✅ **已修复并验证**
- ~~**优先级 1：审核 Stage 3 人工审核候选**~~ ✅ **已完成** — 14 条全部处理
- ~~**优先级 2：评估外联策略**~~ ✅ **已完成** — T1 外联列表已生成
- ~~**优先级 2.5：数据质量清理**~~ ✅ **已完成** — A-Run 67：已找到直联 +7，pending_verification 清零，empty status 清零，Frank Tucker 修正
- **优先级 3：对 B-Run 32-35 新发现的 20 家公司跑 A 区表单收集** — 这些公司刚被 B 区发现，尚未进行联系人富化
- **优先级 4：B 区需引入新搜索渠道** — Google 搜索边际收益接近零，需引入 LinkedIn Sales Navigator、Google Maps API、行业展会参展商列表、州级商会官网直接爬取
- **优先级 5：B 区测试剩余 venue-type 关键词** — speakeasy / heritage pub / distillery cellar door / waterfront restaurant 尚未测试
- ~~Stage 2 直联富化~~ ❌ **已确认饱和** — Run 67~69 连续 0%，KP 级搜索策略测试也无效，候选池耗尽
- **12 条仍无任何联系信息**（9 条非 AU + 3 条 AU）：
  - AU 问题站点：The Mulberry Group（SSL）、The Big Easy Group（404）、Vanillablue（404）
  - 非 AU（低优先级）：BMS London / Maguro Group / JOEY Restaurants / Miku Toronto / Ray-Ban / Book Club Bar / 4 家 NY 新开餐厅

**A 区待用户处理：**
- **审核 Craig Shearer @ Kickon Group** — Stage 3 人工审核候选（分数 75，邮箱 j@kickongroup.com）
- **T1 外联测试** — 12 条双渠道联系人已准备就绪，见 `reports/t1-outreach-list-20260602.md`
- **手动验证 Matthews Hospitality 8 条 LinkedIn** — 已升级为"已识别联系人"，需手动访问获取邮箱/电话
- **手动验证 29 个 Tier 3 LinkedIn URL** — 24 个直接个人页面（高管/创始人），手动访问可获取邮箱/电话，是提升直联数的最现实路径
- **需人工确认 7 条** — Salter Brothers 5 条 board 成员 + Catering Group 1 条 + 其他 1 条，需手动查找联系方式
- 64 条 KP 无直联线索中，大量仅靠联系表单，需评估是否值得手动外联
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

**B 区运行汇总（15 轮，2026-05-28 ~ 2026-06-03）：**

| 轮次 | 关键词 | 新公司 | 有效率 | 关键成果 |
|------|--------|--------|--------|----------|
| Run 19 | 38 | 57 | — | 首次关键词发现，277→334 |
| Run 20 | 15 | 6 | 12% | 过滤器优化（5 项改进） |
| B-Run 21 | 20 | 8 | 88% | 验证过滤器效果 |
| B-Run 22 | 15 | 33 | 82% | 短场地关键词 + AU 增强修复 |
| B-Run 23 | 11 | 14 | 86% | 首次用 keyword_discovery.py 直接运行，venue-type 关键词 |
| B-Run 24 | 5 | 1 | 20% | FF&E supplier 关键词过于细分，有效率触底 |
| B-Run 25 | 10 | 33 | 90% | 供应商类关键词（家具/设备/布草/IT），暂停 FF&E 后改回宽泛词 |
| B-Run 26 | 40 | 3 | ~60% | venue-type 关键词（restaurant/hotel/pub group owner），代理 HK 节点修复 |
| B-Run 27 | 25 | 13 | 69% | venue-type 关键词（restaurant/pub group owner），修复 dry-run 缓存 bug + Scrapling cookies bug |
| B-Run 28 | 5 | 2 | 40% | 优化选择（跳过 0% 关键词），市场分析对比有效率，新增 2 家但质量存疑 |
| B-Run 29 | 10 | 8 | 27% | venue-type 关键词（motel/restaurant/hotel management），新增 3 家非目标已清理 |
| B-Run 30 | 5 | 0 | N/A | 过滤器优化 + 非目标标记，0 新公司（全部重复/排除） |
| B-Run 31 | 10 | 0 | 0% | 市场分析 + 89 关键词导入 + 测试运行，B 区确认饱和 |
| B-Run 32 | 3 | 10 | 100% | **突破：** 放宽 venue 过滤器（4+ 文本信号无需 URL），wine bar 关键词 |
| B-Run 33 | 3 | 7 | 100% | rooftop bar + boutique hotel 关键词，继续突破 |
| B-Run 34 | 3 | 2 | 67% | cocktail bar + speakeasy 关键词 |
| B-Run 35 | 3 | 1 | 33% | microbrewery 关键词，边际收益递减 |
| B-Run 39 | 179 | 0 | 75.8% | 大批量运行（supplier/fitout/venue 关键词），124 有效结果但均为已知公司，0 新公司 |
| B-Run 44 | 179 | 0 | 100% | 大批量运行（supplier/fitout/venue 关键词），全部为已知公司，市场确认饱和 |
| B-Run 60 | 252 | 0 | — | 关键词报告生成，1712 关键词，200 条 suggested_keywords 待审核 |
| B-Run 61 | 20+ | **49** | — | **突破：区域城市搜索策略**，Hobart(9)/Adelaide Hills(8)/Fremantle(6)/Cairns(4)/Bunbury(4) 等 20+ 区域城市关键词，493→542 |

> 📋 完整运行记录：`E:\自动跑表单的成果和情况\run-log.md`

**最近 3 次运行：**
- **B-Run 44 (2026-06-02):** 大批量运行 179 个关键词（supplier/fitout/venue 类），有效率 100%，但全部为已知公司，**0 新公司**。市场确认饱和。
- **B-Run 60 (2026-06-03):** 关键词报告生成。1712 关键词（+252 生成器新增），suggested_keywords.csv 200 条待审核（153 pending / 44 rejected / 3 approved）。0 新公司，B 区搜索持续饱和。
- **B-Run 61 (2026-06-03):** **区域城市搜索突破！** 20+ 区域城市关键词（Hobart/Adelaide Hills/Fremantle/Cairns/Bunbury/Geelong/Ballarat/Bendigo/Wollongong/Townsville/Launceston/Gold Coast），**+49 家新公司**（493→542）。最佳表现：Hobart 9 家、Adelaide Hills 8 家、Fremantle 6 家。新鲜度/奖项/协会/细分菜系搜索无效（0 新公司）。
- **B-Run 69 (2026-06-03):** 报告生成运行。179 关键词，124 有效结果，有效率 75.8%，**0 新公司**。supplier/fitout/venue 类关键词产出大量结果但均为已知公司，市场已饱和。

**配置变更（优化器 2026-06-03）：**
- `keyword_scheduler.json` max_keywords_per_run: 0 → **5**（区域城市策略已验证，重新启用 B 区）
- `keyword_scheduler.json` template_expansions.[city]: 新增 10 个区域城市（Fremantle/Cairns/Townsville/Geelong/Ballarat/Bendigo/Wollongong/Bunbury/Launceston/Adelaide Hills）
- `leads.csv` 数据质量：10 条 eater.com 媒体 URL + 5 对重复 website 已标记 needs_review
- 详细记录：`.optimization_history.json` 第 7 条

**B 区下一步：**
- **继续区域城市搜索（最高优先级）** — 覆盖更多区域城市：Sunshine Coast / Toowoomba / Mandurah / Geraldton / Albany / Rockhampton / Mackay / Bundaberg / Hervey Bay / Mildura / Shepparton / Wagga Wagga / Orange / Tamworth / Coffs Harbour / Port Macquarie 等
- **测试区域城市 + venue 细分组合** — 如 "Thai restaurant Hobart contact" / "wine bar Bendigo contact" / "boutique hotel Fremantle contact"
- **测试区域城市 + 细分客户类型** — 如 "catering company Ballarat contact" / "restaurant owner Cairns email"
- **处理 15 条 needs_review 数据** — 10 条 eater.com 媒体 URL（建议移除）+ 5 对重复 website（建议合并）
- **对新发现的 49 家公司跑 A 区表单收集** — 这些公司尚未进行联系人富化
- ~~B 区已确认饱和~~ ❌ **已突破** — 区域城市搜索策略有效
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

## 备注（共享）

- **Tavily 已暂停**，当前使用 Scrapling/form 提取。重新启用需用户批准。
- 命令见 CLAUDE.md "Commands Quick Reference"，守则见 AGENTS.md "Operating Rules"。

## 自动化

- `/full-auto-pipeline` — 运行一次完整管线（表单收集→KP富化→关键词发现→报告）
- `/loop 30m /full-auto-pipeline` — 每 30 分钟自动运行管线
- 每日快照：`daily_snapshot.py` 钩子在会话启动时自动 commit data/
- 权限：VSCode 扩展已配置 `bypassPermissions`，管线运行无需人工确认
- 安全兜底：`pre_bash_safety.py` 拦截破坏性命令，`stop_check.py` 拦截未清理退出

<!-- CODEx_END: current_progress -->
