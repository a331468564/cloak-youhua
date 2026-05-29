<!-- DOC_META
lifecycle:  permanent
audience:   both
write_when: 创建演示文稿设计规范时
read_when:  需要了解演示文稿结构和内容设计时
delete_when: 演示文稿废弃时
-->
# Vibe Coding Agent 管理架构复盘 — 演示文稿设计

## 概述

为团队内部复盘会议制作一份 HTML 演示文稿，从 Vibe Coding 视角分析项目的 Agent 管理架构，总结做得好的规范和实践。

## 技术方案

- 单 HTML 文件，零外部依赖
- CSS `scroll-snap-type: y mandatory` 实现全屏逐页滑动
- 暗色科技风（#0f172a 深蓝黑背景，蓝紫渐变主色）
- 键盘 ↑↓ / 鼠标滚轮 / 触摸滑动翻页
- 右侧圆点导航 + 右下角页码计数器

## 幻灯片结构（12 页）

### 第 1 页 — 封面

- 大标题："Vibe Coding Agent 管理架构复盘"
- 副标题："Ron Group B2B Lead Research Project"
- 日期：2026-05-22
- 底部小字：团队内部分享

### 第 2 页 — 什么是 Vibe Coding

- 左侧：3 个核心特征卡片
  - 自然语言驱动：用 AGENTS.md 定义行为规则
  - 迭代式构建：Plan → Spec → Implement 循环
  - 人机协作：Hook 系统强制人类审核点
- 右侧：项目实践映射
  - AGENTS.md → 自然语言行为规范
  - Hook 系统 → 自动化守卫
  - current-progress.md → 滚动交接状态
- 关键信息：不是"让 AI 随便写代码"，而是用规范约束 AI 行为

### 第 3 页 — 整体架构总览

- 三层架构图（SVG 内联）：
  - 顶层：Claude Code + Codex（双 Agent 并行）
  - 中层：Hook 系统（安全 / 清理 / 文档 / 会话 4 道门）
  - 底层：数据层（leads.csv / contacts.csv / keywords.csv）+ 配置层（workflow_rules.json / kp_pipeline.json / keyword_scheduler.json）
- 标注：AGENTS.md 作为全局入口规则，被双 Agent 共享

### 第 4 页 — 双 Agent 并行架构

- 对比表格：

| 维度 | Claude Code | Codex |
|------|-------------|-------|
| 配置格式 | JSON (settings.json) | TOML (config.toml) |
| Hook 触发 | Python 直调 | PowerShell 包装 |
| 权限管理 | ~35 条通配符规则 | 内置安全 hook |
| 特有能力 | WebSearch, Agent 子任务 | 提取安全词检测 |

- 共享层标注：同一份 data/、同一套 AGENTS.md、同一套 workflow_rules.json
- 关键点：不是主从关系，是并行执行、共享数据

### 第 5 页 — Hook 闭环强制系统

- 闭环流程图：
  ```
  脚本运行 → 产物检测(post_bash) → 警告
       → agent 忽略 → Stop hook 拦截
       → 必须清理 → 通过
  ```
- 四个 Hook 职责卡片：
  - `pre_bash_safety.py`：拦截危险命令（rm -rf, git reset --hard 等）
  - `post_bash_check.py`：脚本运行后检查临时文件
  - `post_write_check.py`：新 .md 文件必须有 DOC_META
  - `stop_check.py`：有未清理文件或重会话未更新进度则阻止结束
- 额外：`auto_request_solution_log.py`（全局 hook，每 10 次工具调用提醒记录决策）
- 核心价值："AI 不能摆烂" — Hook 是行为约束的最后防线

### 第 6 页 — 任务区隔离（A区 / B区）

- 两个独立区块，各标注：
  - **A区（KP 管线）**：已知公司 → 找联系人
    - 入口：lead-collection-workflow.md
    - 脚本：scripts/kp_pipeline/
    - 配置：config/kp_pipeline.json
  - **B区（关键词调度）**：未知市场 → 发现公司
    - 入口：keyword-scheduler-guide.md
    - 脚本：scripts/keyword_scheduler/
    - 配置：config/keyword_scheduler.json + keyword_dimensions.json
- 中间分隔线标注"不混写"
- 共享层：data/、hooks/、AGENTS.md、workflow_rules.json

### 第 7 页 — 文档生命周期管理

三个机制并排展示：

1. **DOC_META 元数据**
   - 每个 .md 文件头部声明：lifecycle / audience / write_when / read_when / delete_when
   - 由 post_write_check.py hook 强制执行
   - 示例：
     ```html
     <!-- DOC_META
     lifecycle:  temporary
     audience:   both
     write_when: 管线运行完成后
     read_when:  每次新会话启动
     delete_when: 新会话读取后可覆盖
     -->
     ```

2. **CODEx 块标记**
   - `<!-- CODEx_START: block_name -->` / `<!-- CODEx_END: block_name -->`
   - Agent 选择性读取相关区块，节省 token
   - lead-collection-workflow.md 有 7 个块，cli-operating-rules.md 有 12 个块

3. **任务上下文列表**
   - 每种任务类型有预定义的文件读取列表
   - Lead collection: 6 文件 / Keyword scheduler: 7 文件 / Dashboard: 2 文件
   - 最化 token 浪费

### 第 8 页 — 渐进式自动化门控

- 三阶段漏斗图：
  ```
  Stage 1: KP 发现 → 产出候选人
       ↓
  Stage 2: 直联富化 → 产出联系方式
       ↓
  Stage 3: 验证门控 → auto_approve / auto_reject / human_review
  ```
- Stage 3 评分算法：
  - 基准 50 分
  - 直联 + 高置信度：+35
  - 直联 + 中置信度：+25
  - LinkedIn 仅：+15
  - 公司邮箱：-10
  - >= 85 自动批准 / < 30 自动拒绝 / 中间人工审核
- 三个自动化门槛：
  1. direct_contact_rate > 10%（Run 1: 10.8% ✓, 后续: 2.9% ✗）
  2. false_positive_rate < 15%（0% ✓）
  3. auto_approve_accuracy > 95%（数据不足）
- 核心理念：渐进式信任，数据说话

### 第 9 页 — 数据治理体系

- 邮件分类三级：
  - `person_high`：firstname.lastname@domain → 直联
  - `department_medium`：sales@ / procurement@ → 部门级
  - `company_low`：info@ / hello@ / admin@ → 公司级
- 电话分类三级：
  - `person_high`：04xx 手机
  - `company_medium`：02/03/07/08 座机
  - `company_low`：1300/1800
- 去重规则：email 精确 / phone 精确 / name 模糊
- 候选优先注册：先保存带置信度的候选，人工审核在外联前而非保存前

### 第 10 页 — 做得好的 8 个规范

8 个亮点卡片，每个一句：

1. **Hook 闭环强制** — 脚本产物必须清理，Stop hook 是最后防线
2. **任务区隔离** — A/B 区独立，不混写，文档各自维护
3. **文档生命周期** — DOC_META + CODEx 块标记，按需读取
4. **渐进式门控** — 数据达标才解锁自动化，不盲目信任
5. **候选优先注册** — 降低阻塞，批量发现不卡在逐条验证
6. **域名路由记忆** — Scrapling/CloakBrowser 自动选择最优工具
7. **子进程隔离** — Keyword scheduler 调用已有脚本，不耦合
8. **双语文档** — 中英混合，匹配澳洲华人商业场景

### 第 11 页 — 数据快照

- 关键指标大数字卡片：
  - 253 leads（138 AU）
  - 155 contacts
  - 486 keywords（62 客户类型）
  - 7 轮管线运行
- 直联进度条：58 / 100（目标 100）
- 管线效率趋势：Run 1: 10.8% → Run 2-7: 2.9%-5.9%（触底）

### 第 12 页 — 改进方向

- 3 个已知问题 + 改进思路：
  1. Stage 2 直联率触底（2.9%）→ 需要新策略（LinkedIn 深挖、行业数据库）
  2. 管线不自动保存结果 → run_pipeline.py 需要写回 CSV 逻辑
  3. 8 个 LinkedIn 搜索 URL 待人工验证
- 底部下一步行动项

## 视觉规范

### 颜色

- 背景：#0f172a（深蓝黑）
- 卡片背景：#1e293b（深灰蓝）
- 主色渐变：#6366f1 → #8b5cf6（蓝紫）
- 文字：#e2e8f0（浅灰）
- 次要文字：#94a3b8（中灰）
- 高亮/强调：#22d3ee（青色）
- 成功：#34d399（绿色）
- 警告：#fbbf24（黄色）

### 字体

- 标题：system-ui, -apple-system, sans-serif
- 正文：system-ui, -apple-system, sans-serif
- 代码/架构图：'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace

### 布局

- 每页 100vh，flex 居中
- 内容区最大宽度 1200px，左右 padding 40px
- 卡片圆角 12px，轻微阴影
- 页面间距由 scroll-snap 控制

## 输出

- 单文件：`reports/vibe-coding-presentation.html`
- 可直接浏览器打开，无需服务器
- 可单文件分享（邮件/即时通讯）

## 不包含

- 不引入外部 CSS/JS 框架
- 不使用 CDN 依赖
- 不需要构建步骤
- 不做响应式适配（演示用 16:9 屏幕）
