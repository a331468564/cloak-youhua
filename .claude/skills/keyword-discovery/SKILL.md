---
name: keyword-discovery
description: Use when discovering new AU restaurant/hotel companies via keyword search, running the keyword scheduler, or generating new keywords. Triggers on keywords like "keyword discovery", "新公司", "关键词", "scheduler", "发现新线索".
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - Agent
  - TodoWrite
  - AskUserQuestion
---

# Keyword Discovery（关键词驱动新公司发现）

## Overview

用谷歌搜索关键词，从搜索结果中提取 AU 餐饮/酒店公司，去重后写入 `data/leads.csv`。发现后自动衔接 KP 管线（kp-discovery）。

**核心原则：** 有效率低于 50% 时必须暂停优化过滤，不能继续扩大批次。

## When to Use

- 用户说"做关键词拓展"、"发现新公司"、"跑 scheduler"
- `data/search_keywords.csv` 有 New/Active 状态的关键词未使用
- 需要扩充线索库（当前线索不够做表单收集）

**不要用在：** 已知公司找联系人（用 kp-discovery）、纯数据清理

## 前置条件

1. 读取 `AGENTS.md` 的操作规则
2. 读取 `docs/current-progress.md` B 区
3. 读取 `docs/guides/keyword-scheduler-guide.md`

## 域名缓存

B区使用域名缓存（`E:/cache/domain_cache.json`）跳过已访问域名，A区复用缓存的 cookies/UA。

- 搜索前自动检查缓存，已访问域名直接跳过
- 搜索后自动标记域名有效/无效
- 缓存清理：5000 条上限 + 30 天过期
- 清理命令：`from scripts.utils.domain_cache import force_cleanup; force_cleanup()`

## 两种模式

### 模式 A：调度器采集（从关键词库选词）

```bash
# 预览合格关键词
python -m scripts.keyword_scheduler.scheduler --dry-run

# 执行采集（默认 top 5）
python -m scripts.keyword_scheduler.scheduler --limit 10
```

**合格条件：** 状态 Active/Testing/New + 冷却期已过 + 按优先级排序

### 模式 B：关键词发现（直接搜索新公司）

```bash
# 预览
python scripts/extraction/keyword_discovery.py --limit 5 --dry-run

# 执行
python scripts/extraction/keyword_discovery.py --limit 10 --max-results 8

# 指定关键词 ID
python scripts/extraction/keyword_discovery.py --keywords "KW-0487,KW-0470" --max-results 5
```

## 过滤器层级（5 层）

keyword_discovery.py 内置 5 层过滤，有效率从 12% 提升到 50%+：

1. **域名排除** — 120+ 非目标域名（媒体、招聘、教育、政府等）
2. **URL 模式** — 排除 `/news/`、`/articles/`、`/for-sale/` 等
3. **AU 地理增强** — 短查询自动加 `site:.com.au`
4. **联系信号** — 页面必须有邮箱/电话/contact 链接
5. **行业验证** — 至少 3 个 venue 类关键词

## 批次质量控制

| 指标 | 阈值 | 动作 |
|------|------|------|
| 有效率 | ≥ 50% | 继续，自动合并 |
| 有效率 | < 50% | **暂停**，优化过滤/关键词 |
| 谷歌 429 | 出现 | 等待恢复，控制单次 ≤ 8 关键词 |

**有效率计算：** 有效公司数 / 发现总数 × 100%

**低于 50% 时必须：**
1. 停止扩大批次
2. 分析失败根因（文章？国际公司？供应商？）
3. 优化过滤规则或关键词
4. 报告有效率和改进建议

## 生成新关键词

```bash
# 预览
python -m scripts.keyword_scheduler.generator --dry-run --max 50

# 生成并写入 suggested_keywords.csv
python -m scripts.keyword_scheduler.generator --max 100

# 自动审核
python -m scripts.keyword_scheduler.auto_review

# 导入已审核的
python -m scripts.keyword_scheduler.import_suggestions
```

## 衔接 A 区

发现新公司后：
1. 写入 `data/leads.csv`（自动去重）
2. 更新关键词状态为 Testing
3. 提示用户对新公司跑 kp-discovery 补充联系信息

## 阻塞处理

遇到阻塞（同一问题 2-3 次无进展）时：

1. **分类** — 查 `docs/logs/changelog.md` 标签表
2. **查表** — 在"历史阻塞索引"中查找匹配标签
3. **解决并记录** — 无匹配则调试解决，追加到 changelog.md

**常见阻塞：**
- `NET-FETCH-HTTP-429` — 谷歌限流，等待或减少搜索次数
- `DATA-QUALITY-FILTER` — 过滤器误判，调整规则
- `NET-FETCH-HTTP-403` — 反爬，用 CloakBrowser 兜底

**阶段结束必做：** 检查是否有未登记的阻塞，补充到 changelog.md。

## 运行清单（每批必须严格执行）

**每次管线运行必须用 TodoWrite 创建清单，按顺序执行，全部完成才能开始下一批。**

**模板：**
```
1. [in_progress] 读取上下文（AGENTS.md / current-progress.md / guide）
2. [pending] 运行管线（scheduler/discovery/generator）
3. [pending] 分析结果（有效率 / 新公司 / 去重）
4. [pending] 保存数据（leads.csv，备份→写入→验证行数只增不减）
5. [pending] 更新 current-progress.md（数据快照 + 运行记录 + 下一步）
6. [pending] 生成 Run 报告（generate_keyword_report.py --auto-timing）
```

**强制规则：**
- **步骤 5-6 未完成，不能开始下一批管线运行**
- 每批运行 = 一次 TodoWrite 清单循环
- 有效率 < 50% 时，步骤 3 后暂停，不进入步骤 4

## 关键文件

| 文件 | 用途 |
|------|------|
| `scripts/extraction/keyword_discovery.py` | 关键词发现脚本 |
| `scripts/keyword_scheduler/scheduler.py` | 调度器 |
| `scripts/keyword_scheduler/generator.py` | 关键词生成器 |
| `scripts/keyword_scheduler/auto_review.py` | 自动审核 |
| `scripts/keyword_scheduler/import_suggestions.py` | 导入工具 |
| `data/search_keywords.csv` | 关键词主库 |
| `data/keyword_runs.csv` | 运行日志 |
| `config/keyword_scheduler.json` | 调度器配置 |
| `config/keyword_dimensions.json` | 维度值 + 查询模板 |

## 数据安全

- `data/leads.csv` 只追加，不删除，不覆盖
- 非目标公司写入 `reports/rejected-{timestamp}.csv`
- 写入前：备份 → dry-run → 合并报告 → 确认行数只增不减
- 谷歌搜索必须用 `search_google()` 或 `cloak_fetch()`，不能用 `smart_fetch()`
