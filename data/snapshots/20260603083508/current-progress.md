<!-- DOC_META
lifecycle:  temporary
audience:   both
write_when: 触发条件见文档内"更新规则"一节
read_when:  每次新会话启动时必须读取
delete_when: 新会话读取后可覆盖
-->
# Current Progress

<!-- CODEx_START: current_progress -->
*Updated: 2026-06-02 (A-Run 65 + B-Run 44: A区公司 493 不变，联系人 234 不变，可靠直联 90（重新审计：T1=27, T2 邮箱=36, T2 手机=27）。B区 179 关键词运行，0 新公司，市场已饱和)*

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
| `data/leads.csv` | 493 | 主线索表（A-Run 65 无变化） |
| `data/contacts.csv` | 234 | 联系人表（含 7 条 needs_review，14 条 pending_verification） |
| `data/search_keywords.csv` | 1460 | 搜索关键词定义，29 字段（B-Run 44 批量导入后） |
| `data/keyword_runs.csv` | 179 | 关键词运行记录，21 字段 |

---

<!-- TASK_A_START: kp_pipeline -->
## A. KP 管线（表单收集）<!-- 做表单收集任务的 agent 读这一块 -->

> **定位：** 已知公司名 → 找联系人。读取 `docs/workflows/lead-collection-workflow.md`。

**AU 线索富化进度（493 条线索，含 A 区 ~144 + B 区 ~344）：**

| 指标 | 数量 | 说明 |
|------|------|------|
| 有 KP 姓名 | ~101 | Run 36 +3（Stage 2 新发现 KP） |
| 有 KP 直联（邮箱+电话+LinkedIn） | 79 | Run 61 重新审计（T1 个人邮箱+手机 16，T2 单渠道 63） |
| KP 但无直联方式 | ~22 | 仅 LinkedIn 30 - 需手动验证 |
| 完全无 KP | ~170 | 含新发现公司待富化 |

**公司联系路由覆盖（493 条线索）：**

| 类型 | 数量 | 说明 |
|------|------|------|
| 有公司邮箱 | 201 | 含 key_contact_email |
| 有公司电话 | 213 | 含 key_contact_phone |
| 有联系表单 URL | 148 | company_contact_form_url |
| 有联系页 | 193 | company_contact_page |
| 有公司 LinkedIn | 54 | company_linkedin_url |
| 有任何联系信息 | 477 | **覆盖率 96.8%**（16 条仍无任何联系信息） |

**联系人概况（234 条，2026-06-02 再次审计）：**

| 类型 | 数量 | 说明 |
|------|------|------|
| **Tier 1（个人邮箱+手机）** | **27** | 最高质量，双渠道直联 |
| **Tier 2（邮箱 only）** | **36** | 单渠道邮箱 |
| **Tier 2（手机 only）** | **27** | 单渠道手机 |
| **Tier 3（仅 LinkedIn URL）** | **22** | 需手动验证 LinkedIn |
| **需审核（needs_review）** | **7** | 误报/存疑数据 |
| **待验证（pending_verification）** | **14** | Matthews 8 + Salter 5 + Catering 1 |
| **可靠直联（T1+T2）** | **90** | 真正可外联 |
| 有邮箱或电话 | 124 | 含公司通用邮箱/座机/1300 |
| 无任何联系信息 | 110 | |

> ⚠️ **2026-06-02 再次审计：** 按 contact_status 字段重新统计：T1（邮箱+手机）27、T2（邮箱 only）36、T2（手机 only）27、T3（LinkedIn only）22。可靠直联（T1+T2）= 90。直联率 52.9%（124/234 含公司通用邮箱）或 38.5%（90/234 仅个人渠道）。

**管线运行汇总（44 轮，2026-05-19 ~ 2026-06-02）：**

| 阶段 | 总轮次 | 总候选 | 总富化 | 总直联 | 平均直联率 |
|------|--------|--------|--------|--------|-----------|
| Stage 1 KP 发现 | 16 | ~6457 | — | — | — |
| Stage 2 直联富化 | 28 | ~560 | ~120 | ~35 | ~6% |
| Stage 3 验证门控 | 8 | ~2689 | — | — | — |

> 📋 完整运行记录：`E:\自动跑表单的成果和情况\run-log.md`

**最近 3 次运行：**
- **Run 59 (2026-06-02):** 报告生成。数据无变化。
- **Run 60 (2026-06-02):** 报告生成。数据无变化。
- **Run 61 (2026-06-02):** 报告生成。**公司 493 (+1)，邮箱 +2，电话不变。** 覆盖率 96.8%，直联率 32.9%。contacts 234 不变，可靠直联 79（重新审计）。
- **Run 65 (2026-06-02):** 报告生成。**数据无变化。** Stage 2 处理 10 候选，0 富化，0 直联。直联率 32.9%。contacts 再次审计：可靠直联 90（T1=27, T2=63）。

**自动化门控指标：**
- direct_contact_rate > 10%: Run1 ✓ (10.8%) / Run2-6 ✗ (2.9%) / Run21-24 ✓ (20%) / Run25-26 ✗ (0%-5%) / Run27 ✓ (Stage 1 定向，+1 直联) / Run28 ✗ (0%) / Run29 ✓ (Stage 1 定向，+1 直联) / Run30 ✗ (Stage 1 定向，0 直联，候选质量低) / Run31 ✗ (Stage 1 定向，0 直联，+2 联系人) / Run32 ✗ (Stage 2 直联 0%，人工审核 -1 直联) / Run33 ✗ (Stage 1+2 全跑，0 直联) / Run35 ✓ (Stage 2 直联 10%，+2 推断邮箱) / Run36 ✗ (7.5%，+3 直联) / Run38 ✗ (0%，趋势未持续) / Run45 ✗ (0%，连续两轮零直联) / Run50 ✗ (0%，连续三轮零直联) / Run52 ✗ (0%，连续四轮零直联) / Run55 ✗ (0%，+1 电话但无可靠直联) / Run56 ✗ (报告生成，+27 公司/+19 邮箱/+15 电话，可靠直联 46 不变) / Run57 ✗ (报告生成，+3 公司/+20 邮箱/+16 电话，可靠直联 46 不变) / Run58 ✗ (Stage 2 直联率 10%，但 1 条为误报已标记 needs_review) / **Run61 ✗ (报告生成，+1 公司/+2 邮箱，可靠直联 79 重新审计)**
- false_positive_rate < 15%: 0%（7/7 人工审核通过）
- auto_approve_accuracy > 95%: 数据不足（Run5/6 自动批准 0 个）

**活跃问题：**
1. ~~**⚠️ Run 36 直联数据失实**~~ ✅ **已修正** — 2026-06-02 重新审计：可靠直联（T1 个人邮箱+手机 16 + T2 单渠道 63）= 79。之前 46 遗漏了 30 条仅手机联系人
2. **Stage 2 直联率接近零** — Run 38 + Run 45 + Run 50 + Run 52 连续 0%（四轮），Run 55 +1 电话但无可靠直联，Stage 2 边际收益已接近零
3. **需审核数据 21 条** — needs_review 7 条 + pending_verification 14 条（Matthews 8 + Salter 5 + Catering 1）
4. **Stage 1 队列重复处理** — 标准队列按优先级排序，高优先级公司被反复处理。Run 27 改用定向队列解决
5. ~~**Stage 1 候选质量低**~~ ✅ **已优化** — key_person_name 提取逻辑改进完成（误报率 93%→~0%）
6. **Swillhouse contact 页 403** — Cloudflare 挑战页，无法绕过
7. **Google 429 频繁** — Run 28/33/38 期间触发多次 429，代理轮换后恢复
8. **Stage 1 结果未自动合并** — Stage 1 产出 350+ 候选（Run 38），仅存报告 CSV，未自动合并
9. ~~**推断邮箱需验证**~~ ✅ **已验证** — sam.hay@AVC 和 murray.graci@Crystalbrook 均为混合体（非真实邮箱），已清空
10. **Run 36 Stage 3 人工审核 12 候选** — 多数为误报名称，实际需审核：Shayne Lucas State @ Meriton、David Strom @ Tenfold、Peter Inglese @ Riverstone、Jared Stringer @ The Lane
11. **⚠️ Run 60 邮箱推断误报** — `extract_email_pattern()` 未按域名过滤，导致 Yahoo 域名邮箱被误认为公司邮箱模式。CT-0237 (saif.konstantakos@yahooinc.com) 已标记 needs_review

**关键文件：**
- `scripts/kp_pipeline/run_pipeline.py` — 管线入口
- `scripts/kp_pipeline/stage2_enrich.py` — 富化逻辑
- `scripts/kp_pipeline/stage3_validate.py` — 评分和路由
- `config/kp_pipeline.json` — 阶段配置和阈值
- `reports/kp-pipeline/` — 单次运行报告
- `scripts/reports/generate_run_report.py` — Run 报告生成器
- `E:\自动跑表单的成果和情况\run-log.md` — 完整 A 区运行记录（26 轮）

**A 区下一步：**
- ~~**优先级 0：修复邮箱推断 bug**~~ ✅ **已修复并验证** — `extract_email_pattern()` 新增 `target_domain` 参数，代码正确。Stage 2 跑 5 家公司均未触发邮箱推断（网站无公开邮箱），bug 修复有效但需有邮箱的公司实测
- ~~**优先级 1：审核 Stage 3 人工审核候选**~~ ✅ **已完成** — 14 条全部验证通过，3 条数据修正（姓名补全 2 + 职位更正 1）
- ~~**优先级 2：评估外联策略**~~ ✅ **已完成** — T1 外联列表已生成：`reports/t1-outreach-list-20260602.md`（12 条双渠道联系人）
- **优先级 3：对 B-Run 32-35 新发现的 20 家公司跑 A 区表单收集** — 这些公司刚被 B 区发现，尚未进行联系人富化
- **优先级 4：B 区需引入新搜索渠道** — Google 搜索边际收益接近零，需引入 LinkedIn Sales Navigator、Google Maps API、行业展会参展商列表、州级商会官网直接爬取
- **优先级 5：B 区测试剩余 venue-type 关键词** — speakeasy / heritage pub / distillery cellar door / waterfront restaurant 尚未测试
- ~~清理 Tier 4 存疑数据~~ ✅ **已完成** — 6 条误报/重复已标记 needs_review
- ~~验证推断邮箱~~ ✅ **已完成** — sam.hay@AVC 和 murray.graci@Crystalbrook 均为混合体，已清空
- ~~Stage 2 直联富化~~ ⚠️ Run 58 回归 10% 但为误报，边际收益接近零
- ~~Stage 1 定向提取~~ ⚠️ 收益递减
- **12 条仍无任何联系信息**（9 条非 AU + 3 条 AU）：
  - AU 问题站点：The Mulberry Group（SSL）、The Big Easy Group（404）、Vanillablue（404）
  - 非 AU（低优先级）：BMS London / Maguro Group / JOEY Restaurants / Miku Toronto / Ray-Ban / Book Club Bar / 4 家 NY 新开餐厅

**A 区待用户处理：**
- ~~**审核 Stage 3 人工审核候选**~~ ✅ **已完成** — 14 条全部验证通过，3 条数据修正。Matthews 8 条 LinkedIn URL 有效，需手动访问获取联系方式
- **审核 Craig Shearer @ Kickon Group** — Stage 3 人工审核候选（分数 75，邮箱 j@kickongroup.com）
- **T1 外联测试** — 12 条双渠道联系人已准备就绪，见 `reports/t1-outreach-list-20260602.md`
- ~~决定 Tier 4 存疑数据处理方式~~ ✅ **已完成** — 6 条已标记 needs_review
- ~~验证推断邮箱~~ ✅ **已完成** — sam.hay@AVC 和 murray.graci@Crystalbrook 均为混合体，已清空
- 手动验证 24 个 LinkedIn URL（Tier 3，需确认是否为正确的人）
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

**B 区运行汇总（13 轮，2026-05-28 ~ 2026-06-02）：**

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

> 📋 完整运行记录：`E:\自动跑表单的成果和情况\run-log.md`

**最近 3 次运行：**
- **B-Run 32~35 (2026-06-02):** **突破饱和！** 根因分析发现 `_is_restaurant_hotel_page()` 过滤器要求 URL 含 venue 信号（≥2 个），但很多 venue 用品牌名做域名（如 zigis.com.au、marionwine.com.au）。**修复：** (1) 放宽文本信号要求：4+ 文本信号无需 URL 检查，2+ 文本信号 + 1 URL 信号通过；(2) 扩展 venue_url_signals 和 venue_text_signals 列表；(3) 新增 association_name 维度（+13 个商会/协会）。**结果：** wine bar 关键词 10 新公司，rooftop bar + boutique hotel 7 新公司，cocktail bar + speakeasy 2 新公司，microbrewery 1 新公司。**总计 20 新公司，461→488 域名。**
- **B-Run 39 (2026-06-02):** 大批量运行 179 个关键词（supplier/fitout/venue 类），有效率 75.8%，124 个有效搜索结果但全部为已知公司，**0 新公司**。关键词覆盖 restaurant group / hotel procurement / restaurant fitout / hospitality interior design / commercial kitchen 等，搜索结果质量高但市场已饱和。
- **B-Run 30 (2026-06-02):** 关键词报告生成，124 关键词汇总，有效率 75.8%，0 新公司。无管线执行。
- **B-Run 44 (2026-06-02):** 大批量运行 179 个关键词（supplier/fitout/venue 类），有效率 100%，但全部为已知公司，**0 新公司**。市场确认饱和。

**B 区下一步：**
- **继续 venue-type 关键词** — 还有 speakeasy / heritage pub / distillery cellar door / waterfront restaurant 等未测试
- **测试 association 关键词** — 新增的商会/协会关键词（AHA state chapters、CCIWA、Business SA 等）需测试
- **对新发现公司跑 A 区表单收集** — 20 家新公司待联系信息富化
- **评估误报** — AU-0587 (visitcanberra.com.au) 和 AU-0603 (adventuresnsunsets.com) 可能是目录/媒体网站，需检查
- **keyword_discovery.py 需接入 tracker**（当前直接运行不会更新 keyword_runs.csv）
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
