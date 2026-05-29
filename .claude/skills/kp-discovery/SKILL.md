---
name: kp-discovery
description: Use when discovering key persons for AU restaurant/hotel companies, enriching contact information, or running the KP pipeline. Triggers on keywords like "KP", "key person", "contact enrichment", "Stage 2", "直联", "富化", "表单收集".
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

# KP Discovery（关键人物发现与富化）

## Overview

三阶段管线：发现关键人物 → 富化直联方式 → 验证门控。目标是为 AU 餐饮/酒店公司找到可外联的决策者。

**核心原则：** 先有公司信息，再找人。没有公司邮箱/电话/联系页的线索不进入 KP 搜索。

## When to Use

- 用户说"做表单收集"、"跑 KP 管线"、"富化联系信息"
- `data/leads.csv` 中有线索缺少 `key_contact_name` 或直联方式
- 需要从 team/about 页面提取决策者信息

**不要用在：** 关键词发现新公司（用 keyword-discovery）、纯数据清理任务

## 前置条件

1. 读取 `AGENTS.md` 的操作规则
2. 读取 `docs/current-progress.md` A 区
3. 读取 `docs/workflows/lead-collection-workflow.md`

## 三阶段流程

### Stage 1: KP 发现

```
输入: leads.csv 中无 key_contact_name 的线索
  ↓
搜索公司 team/about 页面
  ↓
提取人名 + 职位
  ↓
输出: 候选 KP 列表（姓名 + 职位 + 来源 URL）
```

**命令：**
```bash
python -m scripts.kp_pipeline.run_pipeline --stage 1 --limit 20
```

### Stage 2: 直联富化

```
输入: 有 KP 姓名但无邮箱/电话/LinkedIn 的线索
  ↓
抓取公司 sitemap + 联系页
  ↓
搜索 KP 姓名 + 公司名（谷歌）
  ↓
提取邮箱/电话/LinkedIn URL
  ↓
输出: 更新 contacts.csv
```

**命令：**
```bash
python -m scripts.kp_pipeline.run_pipeline --stage 2 --limit 20
```

**工具优先级：** Scrapling 优先 → CloakBrowser 兜底 → 谷歌搜索（必须用 `search_google()`）

### Stage 3: 验证门控

```
输入: contacts.csv 中未验证的联系人
  ↓
评分（姓名+职位+直联方式 → 0-100 分）
  ↓
≥85: 自动批准 | <30: 自动拒绝 | 30-85: 人工审核
  ↓
输出: 更新 verification_status
```

**命令：**
```bash
python -m scripts.kp_pipeline.run_pipeline --stage 3 --limit 50
```

## 批次质量控制

| 指标 | 阈值 | 动作 |
|------|------|------|
| 有效率 | ≥ 50% | 继续 |
| 有效率 | < 50% | 暂停，优化关键词/过滤 |
| 直联率 | ≥ 10% | 良好 |
| 直联率 | < 10% | 正常（后续线索更难） |

## 阻塞处理

遇到阻塞（同一问题 2-3 次无进展）时：

1. **分类** — 查 `docs/logs/changelog.md` 标签表
2. **查表** — 在"历史阻塞索引"中查找匹配标签
3. **解决并记录** — 无匹配则调试解决，追加到 changelog.md

**阶段结束必做：** 检查是否有未登记的阻塞，补充到 changelog.md。

## Run 报告

每轮跑完后生成报告：
```bash
python scripts/reports/generate_run_report.py --auto-stats --auto-timing --task "KP Pipeline Run N"
```
输出到 `E:\自动跑表单的成果和情况\run-log.md`（A-Run 格式）
自动计时：用 `RunTimer` 包装管线脚本，`--auto-timing` 自动读取时间

## 关键文件

| 文件 | 用途 |
|------|------|
| `scripts/kp_pipeline/run_pipeline.py` | 管线入口 |
| `scripts/kp_pipeline/stage2_enrich.py` | 富化逻辑 |
| `scripts/kp_pipeline/stage3_validate.py` | 评分和路由 |
| `config/kp_pipeline.json` | 阶段配置和阈值 |
| `data/leads.csv` | 主线索表（只追加，不删除） |
| `data/contacts.csv` | 联系人表（只追加，不删除） |

## 数据安全

- 主表只追加，不删除，不覆盖
- 清理数据写入 `reports/rejected-{timestamp}.csv`
- 写入前：备份 → dry-run → 合并报告 → 确认行数只增不减
- 不确定的数据标记 `needs_review`，不删除
