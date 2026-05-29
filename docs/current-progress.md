<!-- DOC_META
lifecycle:  temporary
audience:   both
write_when: 触发条件见文档内"更新规则"一节
read_when:  每次新会话启动时必须读取
delete_when: 新会话读取后可覆盖
-->
# Current Progress

<!-- CODEx_START: current_progress -->
*Updated: 2026-05-29 (V3 Step 1+2 完成 — B区架构整改 + CLAUDE.md 精简)*

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
| `data/leads.csv` | 0 | 主线索表，53 字段（V3 初始化，待填充） |
| `data/contacts.csv` | 0 | 联系人表，21 字段（V3 初始化，待填充） |
| `data/search_keywords.csv` | 0 | 搜索关键词定义，29 字段（V3 初始化，待填充） |
| `data/keyword_runs.csv` | 0 | 关键词运行记录，21 字段（V3 初始化，待填充） |

---

<!-- TASK_A_START: kp_pipeline -->
## A. KP 管线（表单收集）<!-- 做表单收集任务的 agent 读这一块 -->

> **定位：** 已知公司名 → 找联系人。读取 `docs/workflows/lead-collection-workflow.md`。

**AU 线索富化进度（V3 初始化，待填充）：**

| 指标 | 数量 | 说明 |
|------|------|------|
| 有 KP 姓名 | 0 | 待首次管线运行 |
| 有 KP 直联（邮箱+电话+LinkedIn） | 0 | 待首次管线运行 |
| KP 但无直联方式 | 0 | 待首次管线运行 |
| 完全无 KP | 0 | 待首次管线运行 |

**公司联系路由覆盖（V3 初始化，待填充）：**

| 类型 | 数量 | 说明 |
|------|------|------|
| 有公司邮箱 | 0 | 待首次表单收集 |
| 有公司电话 | 0 | 待首次表单收集 |
| 有联系表单 URL | 0 | 待首次表单收集 |
| 有联系页 | 0 | 待首次表单收集 |
| 有公司 LinkedIn | 0 | 待首次表单收集 |
| 有任何联系信息 | 0 | 待首次表单收集 |

**联系人概况（V3 初始化，待填充）：**

| 类型 | 数量 | 说明 |
|------|------|------|
| 有邮箱（人名） | 0 | 待首次管线运行 |
| 有手机号 | 0 | 待首次管线运行 |
| 有公司邮箱 | 0 | 待首次管线运行 |
| **直联总数（人名邮箱+手机）** | **0** | **目标 100** |
| LinkedIn 直接 URL | 0 | 待首次管线运行 |
| LinkedIn 搜索 URL | 0 | 待首次管线运行 |

**管线运行记录：** （V3 尚无运行记录）

**自动化门控指标：** （V3 尚无数据）

**关键文件：**
- `scripts/kp_pipeline/run_pipeline.py` — 管线入口
- `scripts/kp_pipeline/stage2_enrich.py` — 富化逻辑
- `scripts/kp_pipeline/stage3_validate.py` — 评分和路由
- `config/kp_pipeline.json` — 阶段配置和阈值
- `reports/kp-pipeline/` — 运行报告
- `scripts/reports/generate_run_report.py` — Run 报告生成器

**A 区下一步：**
- 导入或发现首批 AU 线索入库
- 运行 KP 管线 Stage 1 发现关键联系人
- 运行表单收集补充公司联系路由
<!-- TASK_A_END: kp_pipeline -->

---

<!-- TASK_B_START: keyword_scheduler -->
## B. Keyword Scheduler（关键词拓展）<!-- 做关键词拓展任务的 agent 读这一块 -->

> **定位：** 未知市场 → 发现新公司。读取 `docs/guides/keyword-scheduler-guide.md`。

**模块状态：** 已完成，可直接使用（从 V2 复制，代码完整）。

**已完成（V2 已验证）：**
- ✅ 核心模块：scheduler.py / executor.py / tracker.py / config.py
- ✅ 生成器：generator.py（7 维度 × 15 模板，含自动去重）
- ✅ 市场分析：market_intel.py（效果排名 + 候选评分）
- ✅ 导入工具：import_suggestions.py（列不一致自动重写）
- ✅ KP Pipeline 集成：`--keyword-driven` 标志
- ✅ 操作指南：docs/guides/keyword-scheduler-guide.md
- ✅ 自动审核：auto_review.py（score >= 0.6 自动通过，< 0.4 自动拒绝，中间需人工）
- ✅ 反馈循环：scheduler 解析提取结果 → tracker 自动回写分数
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

**B 区运行记录：** （V3 尚无运行记录）

**B 区下一步：**
- 生成首批关键词候选（generator）
- 导入种子关键词到 search_keywords.csv
- 运行 scheduler 做首次关键词发现
<!-- TASK_B_END: keyword_scheduler -->

---

## Hook 系统（共享）

`.claude/settings.json` — 7 个钩子强制执行文档生命周期和清理规则：

| 钩子 | 事件 | 范围 | 作用 |
|------|------|------|------|
| `pre_bash_safety.py` | PreToolUse (Bash) | 项目 | 拦截危险命令 |
| `post_bash_check.py` | PostToolUse (Bash) | 项目 | 脚本运行后检查临时文件 |
| `post_blocker_detect.py` | PostToolUse (Bash) | 项目 | 连续 2 次失败自动注入阻塞查表提醒 |
| `context_freshness_check.py` | PostToolUse (Bash) | 项目 | 会话超过 15 次工具调用时提醒更新进度并开新窗口 |
| `post_write_check.py` | PostToolUse (Write) | 项目 | 新 .md 文件必须有 DOC_META |
| `stop_check.py` | Stop / SubagentStop | 项目 | 有未清理文件或重会话未更新进度则阻止结束 |
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
cd D:\TestProject-v3
git status --short
python scripts\utils\check_capability_inventory.py
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
输出目录：`D:\TestProject-v3\reports\`

**B 区命令（关键词拓展）：**
```powershell
python -m scripts.keyword_scheduler.scheduler --dry-run
python -m scripts.keyword_scheduler.scheduler --limit 10
python -m scripts.keyword_scheduler.generator --dry-run --max 50
```

## V3 结构建设进度

**Step 1 (B区架构整改):** ✅ 完成
- ✅ `.claude/rules/data-safety.md` — 79 行，`paths: data/**`
- ✅ `.claude/rules/extraction-rules.md` — 146 行，`paths: scripts/extraction/**, reports/**`
- ✅ `.claude/rules/tool-config.md` — 65 行，`paths: scripts/**`
- ✅ `docs/workflows/keyword-discovery-workflow.md` — 218 行，6 CODEx 区块
- ✅ Skills: kp-discovery (138行) + keyword-discovery (148行) + spec-checker (195行)

**Step 2 (CLAUDE.md 精简):** ✅ 完成
- ✅ CLAUDE.md 360→84 行（含命令速查），前 20 行放数据安全+阻塞查表
- ✅ AGENTS.md 已添加 DOC_META
- ✅ spec-checker 验证通过

**V3 vs V2 结构差异：**

| 项目 | V2 | V3 |
|------|----|----|
| CLAUDE.md | 360 行，Rule 1-10 全部内联 | 84 行，规则迁移到 `.claude/rules/` |
| .claude/rules/ | 不存在 | 3 个文件（paths 按需加载） |
| keyword-discovery-workflow.md | 不存在 | 218 行，6 CODEx 区块 |
| Skills | 2 个 (kp/keyword) | 3 个 (+spec-checker) |
| 数据 | 340 leads / 168 contacts / 624 keywords | 全部 0 行 |
| Git | 有历史 | 5 commits |

## 守则（共享）

- 不做大范围源数据改动，除非有明确计划。
- 不使用 Tavily，除非重新批准。
- 工作流/工具变更记录到 `docs/logs/changelog.md`。
- 钩子强制清理 — 有未清理文件会阻止会话结束。
- **A 区和 B 区独立更新，不混写。**

<!-- CODEx_END: current_progress -->
