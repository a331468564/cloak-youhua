<!-- DOC_META
lifecycle:  temporary
audience:   both
write_when: 触发条件见文档内"更新规则"一节
read_when:  每次新会话启动时必须读取
delete_when: 新会话读取后可覆盖
-->
# Current Progress

<!-- CODEx_START: current_progress -->
*Updated: 2026-06-01 (Run 27 完成 — Stage 1 KP 发现（定向），+32 联系人，AU KP 80→96，直联 +1)*

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
| `data/leads.csv` | 381 | 主线索表（B-Run 22 新增 33 家 AU 公司） |
| `data/contacts.csv` | 201 | 联系人表（Run 27 Stage 1 新增 32 条） |
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
| 有 KP 姓名 | 96 | Run 27 +16（定向 Stage 1，32 新联系人） |
| 有 KP 直联（邮箱+电话+LinkedIn） | 32 | Run 27 +1（Rob Wilkes @ Taste Hospitality 邮箱+电话） |
| KP 但无直联方式 | 64 | Run 27 新增 15 个无直联 KP |
| 完全无 KP | ~170 | 含新发现公司待富化（仍有 60+ 未处理） |

**公司联系路由覆盖（277 条线索）：**

| 类型 | 数量 | 说明 |
|------|------|------|
| 有公司邮箱 | 194 | Run 18 +4（Achefstouch/Elizabethandrews/Palmer 等） |
| 有公司电话 | 207 | Run 18 +3 |
| 有联系表单 URL | 148 | Run 18 +2（Australian Hotel/Palmer） |
| 有联系页 | 194 | Run 18 +2（Palmer/Millbrook） |
| 有公司 LinkedIn | 54 | Run 18 +12（Bentley/AVC/Crystalbrook/EVT/Meriton/Ovolo/Maybe/ALH/Signature/Gambaro/AHS/Bay13 等） |
| 有任何联系信息 | 265 | **12 条仍无任何联系信息**（3 AU + 9 非 AU） |

**联系人概况（201 条）：**

| 类型 | 数量 | 说明 |
|------|------|------|
| 有邮箱（人名） | 40 | 可直接外联 |
| 有手机号 | 23 | 可直接外联 |
| 有公司邮箱 | 3 | 低价值，需转介 |
| **直联总数（人名邮箱+手机）** | **77** | **目标 100，差 23**（Run 27 +1：Rob Wilkes） |
| LinkedIn 直接 URL | 18 | 已确认的个人主页（Run 20 +9） |
| LinkedIn 搜索 URL | 8 | **需用户手动验证**（见下方清单） |

**管线运行汇总（27 轮，2026-05-19 ~ 2026-06-01）：**

| 阶段 | 总轮次 | 总候选 | 总富化 | 总直联 | 平均直联率 |
|------|--------|--------|--------|--------|-----------|
| Stage 1 KP 发现 | 7 | ~2700 | — | — | — |
| Stage 2 直联富化 | 20 | ~400 | ~90 | ~30 | ~10% |
| Stage 3 验证门控 | 3 | ~1100 | — | — | — |

> 📋 完整运行记录：`E:\自动跑表单的成果和情况\run-log.md`

**最近 3 次运行：**
- **Run 25 (2026-05-30):** Stage 2 富化 3 家，直联 1 个（5%）。Veriu Group Zed Sanjana。leads 348，contacts 168。
- **Run 26 (2026-06-01):** Stage 2 富化 3 家，直联 0 个（0%）。leads 381，contacts 169。**⚠️ Stage 2 触底，建议暂停。**
- **Run 27 (2026-06-01):** Stage 1 定向 KP 发现，80 家公司，+32 联系人。AU KP 80→96，contacts 169→201，直联 76→77（Rob Wilkes）。关键新增：La Vie/Trilogy/Reilly/GM Hotels/Matthews 等。

**自动化门控指标：**
- direct_contact_rate > 10%: Run1 ✓ (10.8%) / Run2-6 ✗ (2.9%) / Run21-24 ✓ (20%) / Run25-26 ✗ (0%-5%) / Run27 ✓ (Stage 1 定向，+1 直联) — **Stage 2 直联已触底，Stage 1 定向提取仍有收益**
- false_positive_rate < 15%: 0%（7/7 人工审核通过）
- auto_approve_accuracy > 95%: 数据不足（Run5/6 自动批准 0 个）

**活跃问题：**
1. **Stage 2 直联率已触底** — Run 25-26 连续低直联率（5%/0%），建议暂停 Stage 2，改用 Stage 1 定向提取新 KP
2. **Stage 1 队列重复处理** — 标准队列按优先级排序，高优先级公司被反复处理。Run 27 改用定向队列（跳过已处理公司）解决
3. **Swillhouse contact 页 403** — Cloudflare 挑战页，无法绕过
4. **44 条无 customer_type 的线索被队列过滤** — 需 `--include-review-needed` 标志（Run 27 已包含）

**关键文件：**
- `scripts/kp_pipeline/run_pipeline.py` — 管线入口
- `scripts/kp_pipeline/stage2_enrich.py` — 富化逻辑
- `scripts/kp_pipeline/stage3_validate.py` — 评分和路由
- `config/kp_pipeline.json` — 阶段配置和阈值
- `reports/kp-pipeline/` — 单次运行报告
- `scripts/reports/generate_run_report.py` — Run 报告生成器
- `E:\自动跑表单的成果和情况\run-log.md` — 完整 A 区运行记录（26 轮）

**A 区下一步：**
- ~~Stage 2 直联富化~~ ⚠️ **暂停**（Run 25-26 直联率 0%-5%，边际收益触底）
- ~~**对 B-Run 22 新发现的 33 家公司跑 Stage 1 KP 发现**~~ ✅ Run 27 完成（+32 联系人，AU KP 80→96）
- **优先级 1：继续 Stage 1 定向提取** — 仍有 60+ 家未处理 AU Final Customer 公司
- **优先级 2：对新 KP 跑 Stage 2 直联富化** — 96 个 AU KP 中 64 个无直联，新 KP 直联率预期高于老候选
- **优先级 3：审核 Run 21 的 7 个待审候选** — 审核通过可直接增加直联数（当前 77，目标 100，差 23）
- **12 条仍无任何联系信息**（9 条非 AU + 3 条 AU）：
  - AU 问题站点：The Mulberry Group（SSL）、The Big Easy Group（404）、Vanillablue（404）
  - 非 AU（低优先级）：BMS London / Maguro Group / JOEY Restaurants / Miku Toronto / Ray-Ban / Book Club Bar / 4 家 NY 新开餐厅

**A 区待用户处理：**
- **🔴 审核 7 个人工审核候选**（审核通过可直接增加直联数，详见 contacts.csv）：Ian Macklin / Jasimma / Nyree Mackenzie / Miko Aspiras / Kiera Hamilton / Alex Jarrold / Mark Brook
- 手动验证 8 个 LinkedIn 搜索 URL + 9 个 Run 20 新增 KP LinkedIn URL（详见 contacts.csv LinkedIn 字段）
- 评估自动化门控指标（是否启用自动批准）
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
- ✅ 域名缓存：B区跳过已访问域名（2.1x 提速），A区复用 cookies/UA，缓存存 E:/cache/domain_cache.json（5000 条上限 + 30 天过期）

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

**B 区运行汇总（4 轮，2026-05-28 ~ 2026-05-30）：**

| 轮次 | 关键词 | 新公司 | 有效率 | 关键成果 |
|------|--------|--------|--------|----------|
| Run 19 | 38 | 57 | — | 首次关键词发现，277→334 |
| Run 20 | 15 | 6 | 12% | 过滤器优化（5 项改进） |
| B-Run 21 | 20 | 8 | 88% | 验证过滤器效果 |
| B-Run 22 | 15 | 33 | 82% | 短场地关键词 + AU 增强修复 |

> 📋 完整运行记录：`E:\自动跑表单的成果和情况\run-log.md`

**最近 2 次运行：**
- **B-Run 21 (2026-05-30):** 20 个短场地关键词，发现 8 家新 AU 公司，**有效率 88%**。过滤器优化验证成功。
- **B-Run 22 (2026-05-30):** 15 个短场地关键词，发现 33 家新 AU 公司（348→381），**有效率 82%**。修复短查询 AU 增强逻辑。

**B 区下一步：**
- **对新发现的 33 家公司跑 A 区表单收集**（补充联系信息）
- 用 market_intel 分析历史数据，优化关键词库
- 对 58 条 review 状态的关键词做二次人工筛选（可选）
- **继续优化关键词库：** 将长关键词（>5 词）替换为更短的变体，提高生产力
- **清理低效关键词：** 暂停 0 结果的长关键词（procurement team / supplier registration 等）
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
