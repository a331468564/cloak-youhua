<!-- DOC_META
lifecycle:  long-term
audience:   agent, user
write_when: Keyword Scheduler 模块功能或流程变更时更新
read_when:  执行关键词驱动采集时读取
delete_when: 不删除
-->
# Keyword Scheduler 操作指南

> 独立于表单采集（Form Collection）的关键词驱动采集模块。

## 模块定位

| 维度 | 表单采集（现有） | 关键词调度器（本模块） |
|------|-----------------|----------------------|
| 数据源 | `data/leads.csv` 中已有线索 | `data/search_keywords.csv` 中的关键词 |
| 触发方式 | 手动指定线索或 KP Pipeline | 关键词自动选择 + 模板展开 |
| 搜索方式 | 逐个公司名搜索 | 关键词 × 维度组合批量搜索 |
| 结果去向 | `reports/` 下的提取报告 | `data/keyword_runs.csv` + `reports/` |
| 适用场景 | 已知目标公司，找联系人 | 探索未知市场，发现新线索 |

**核心原则：** 表单采集用于"已知公司找人"，关键词调度器用于"未知市场发现公司"。

---

## 架构总览

```
data/search_keywords.csv     ← 关键词库（人工维护 + 自动导入）
        │
        ▼
┌─────────────────────┐
│  scheduler.py       │  选择合格关键词（状态、冷却、优先级）
│  → expand_templates │  展开 [city] [country] 占位符
│  → build_query_queue│  生成查询队列
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  keyword_discovery.py        │  调用 extract_public_contact_candidates.py
│  → run_extraction   │  执行搜索，产出报告 CSV
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  tracker.py         │  更新 keyword_runs.csv（运行日志）
│                     │  更新 search_keywords.csv（统计列）
└─────────────────────┘

独立子模块：
┌─────────────────────┐
│  generator.py       │  多维度关键词生成（维度 × 模板）
│  → write_suggested  │  产出 suggested_keywords.csv
└────────┬────────────┘
         │ 人工审核 review_status
         ▼
┌─────────────────────┐
│  import_suggestions │  将 approved 行导入 search_keywords.csv
└─────────────────────┘

┌─────────────────────┐
│  market_intel.py    │  分析历史运行数据，评分候选关键词
│                     │  产出 market-intelligence.md
└─────────────────────┘
```

---

## 数据文件说明

| 文件 | 用途 | 谁写入 |
|------|------|--------|
| `data/search_keywords.csv` | 关键词主库 | 人工编辑 + `import_suggestions.py` |
| `data/keyword_runs.csv` | 每次运行日志 | `tracker.py`（自动追加） |
| `config/keyword_scheduler.json` | 调度器配置 | 人工编辑 |
| `config/keyword_dimensions.json` | 维度值 + 查询模板 | 人工编辑 |
| `reports/suggested_keywords.csv` | 生成的候选关键词 | `generator.py` + `market_intel.py` |
| `reports/market-intelligence.md` | 市场分析报告 | `market_intel.py` |

---

## 操作流程

### 流程 A：日常采集（最常用）

直接从现有关键词库中选取合格关键词执行搜索。

```bash
# 1. 查看当前有哪些合格关键词
python -m scripts.keyword_scheduler.scheduler --dry-run

# 2. 执行采集（默认取 top 5 关键词）
python -m scripts.keyword_scheduler.scheduler

# 3. 指定数量
python -m scripts.keyword_scheduler.scheduler --limit 10

# 4. 查看运行日志
tail -5 data/keyword_runs.csv
```

**合格条件：**
- `keyword_status` 为 Active / Testing / New
- `next_allowed_at` 为空或已过期（冷却期默认 14 天）
- 按 `priority_level`（high > medium > low）+ `discovery_quality_score` 排序

**运行后自动更新：**
- `total_runs` +1
- `last_used_at` 设为当前时间
- `next_allowed_at` 设为当前时间 + cooldown_days
- `used_recently` 设为 Yes

---

### 流程 B：生成新关键词

当关键词库需要扩充时，用多维度生成器产生候选。

```bash
# 1. 生成候选（dry-run 预览）
python -m scripts.keyword_scheduler.generator --dry-run --max 50

# 2. 生成并写入 suggested_keywords.csv
python -m scripts.keyword_scheduler.generator --max 100

# 3. 人工审核 suggested_keywords.csv
#    将认可的行的 review_status 改为 "approved"

# 4. 导入已审核的关键词
python -m scripts.keyword_scheduler.import_suggestions

# 5. 确认导入结果
python -m scripts.keyword_scheduler.import_suggestions --dry-run
```

**维度说明（config/keyword_dimensions.json）：**

| 维度 | 示例值 | 作用 |
|------|--------|------|
| `customer_type` | restaurant group, hotel F&B manager | 目标客户类型 |
| `role` | owner, director, procurement manager | 决策者角色 |
| `geo` | Sydney, Melbourne, Australia | 地理位置 |
| `intent` | contact, email, supplier registration | 搜索意图 |
| `org_form` | group, holdings, collective | 组织形式 |
| `source_modifier` | site:.com.au, inurl:team | Google 搜索修饰符 |
| `trigger_event` | new opening, expansion | 触发事件 |

**模板示例（config/keyword_dimensions.json → query_templates）：**

| 模板 | 模式 | 优先级 |
|------|------|--------|
| T1 | `{customer_type} {geo} {intent}` | high |
| T2 | `{customer_type} {role} {geo}` | high |
| T4 | `"{role}" "{customer_type}" {geo}` | high |
| T7 | `"{trigger_event}" {customer_type} {geo}` | high |

---

### 流程 C：市场分析

分析历史运行数据，找出高效关键词和未开发市场段。

```bash
# 生成市场分析报告
python -c "
from scripts.keyword_scheduler.market_intel import generate_market_report
from pathlib import Path
generate_market_report(
    Path('data/keyword_runs.csv'),
    Path('data/search_keywords.csv'),
    config_path=Path('config/keyword_dimensions.json'),
    output_path=Path('reports/market-intelligence.md')
)
"
```

**报告内容：**
- 关键词效果排名（按 contact_rate 排序）
- 市场段分析（按 customer_type 分组统计）
- 生成候选关键词评分（基于历史数据加权）

---

### 流程 D：与 KP Pipeline 联动

关键词调度器可作为 KP Pipeline 的前置阶段运行。

```bash
# 先运行关键词发现，再执行 KP 三阶段管线
python -m scripts.kp_pipeline.run_pipeline --stage all --limit 10 --keyword-driven
```

**执行顺序：**
1. Keyword Scheduler → 发现新线索写入 `data/leads.csv`
2. Stage 1 → KP 发现（复用已有提取脚本）
3. Stage 2 → 直联富化
4. Stage 3 → 验证门控

---

## 配置说明

### config/keyword_scheduler.json

```json
{
  "cooldown_enforcement": true,      // 是否执行冷却期
  "default_cooldown_days": 14,       // 默认冷却天数
  "max_keywords_per_run": 5,         // 每次运行最多选取关键词数
  "priority_weights": {              // 优先级权重（影响排序）
    "high": 1.0,
    "medium": 0.7,
    "low": 0.4
  },
  "template_expansions": {           // 模板占位符展开
    "[city]": ["Sydney", "Melbourne", ...],
    "[country]": ["Australia"]
  },
  "extraction_defaults": {           // 提取脚本默认参数
    "follow_links": 2,
    "fetcher": "static",
    "delay": 2,
    "skip_existing": true
  }
}
```

### config/keyword_dimensions.json

```json
{
  "max_candidates": 200,             // 生成器最大候选数
  "min_per_template": 2,             // 每个模板最少产出数
  "dimensions": { ... },             // 维度值列表
  "query_templates": [ ... ],        // 查询模板
  "dimension_weights": { ... }       // 维度权重（供评分用）
}
```

---

## search_keywords.csv 字段说明

| 字段 | 含义 | 写入方 |
|------|------|--------|
| `keyword_id` | 唯一 ID（KW-XXXX） | import_suggestions |
| `keyword_pattern` | 关键词模式（含占位符） | 人工 / generator |
| `keyword_status` | Active / Paused / New / Archived | 人工 |
| `priority_level` | high / medium / low | 人工 / generator |
| `cooldown_days` | 冷却天数 | 人工（默认 14） |
| `total_runs` | 累计运行次数 | tracker（自动 +1） |
| `total_leads_collected` | 累计线索数 | tracker（自动累加） |
| `contact_found_count` | 累计联系人数 | tracker（自动累加） |
| `last_used_at` | 上次使用时间 | tracker（自动更新） |
| `next_allowed_at` | 下次允许运行时间 | tracker（自动计算） |
| `discovery_quality_score` | 发现质量分 | 人工 / market_intel |
| `contactability_score` | 可联系性分 | 人工 / market_intel |

---

## 常见操作

### 暂停某个关键词

将 `keyword_status` 改为 `Paused`，调度器会自动跳过。

### 重置冷却期

将 `next_allowed_at` 清空或设为过去的时间，下次运行即可选中。

### 批量导入新关键词

1. 用 `generator.py` 生成候选
2. 审核 `reports/suggested_keywords.csv`，将 `review_status` 改为 `approved`
3. 运行 `import_suggestions.py`

### 查看关键词效果

```bash
# 查看运行日志
python -c "
import csv
with open('data/keyword_runs.csv', 'r', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))
for r in rows[-5:]:
    print(f\"{r['keyword_id']}: {r['actual_leads_collected']} leads, {r['run_date']}\")
"
```

---

## 与表单采集的区别总结

| 场景 | 用哪个 |
|------|--------|
| 已知公司名，找联系人 | 表单采集 / KP Pipeline |
| 探索某个城市的新餐厅 | 关键词调度器 |
| 批量发现酒店采购经理 | 关键词调度器 + generator |
| 已有 38 个关键词想扩充 | generator → import |
| 分析哪些关键词效果好 | market_intel |
| 定期自动跑新线索 | scheduler（可配合 cron） |

---

## keyword_discovery.py（关键词发现脚本）

独立于 scheduler 的新公司发现脚本，位于 `scripts/extraction/keyword_discovery.py`。

**用法：**
```bash
# 发现新公司（dry-run）
python scripts/extraction/keyword_discovery.py --limit 5 --dry-run

# 指定关键词 ID
python scripts/extraction/keyword_discovery.py --keywords "KW-0487,KW-0470" --max-results 5

# 实际执行（写入 leads.csv）
python scripts/extraction/keyword_discovery.py --limit 10 --max-results 8
```

**过滤器层级（5 层）：**
1. `EXCLUDE_DOMAINS` — 排除 120+ 非目标域名（媒体、招聘、教育、政府、预订平台等）
2. `NON_COMPANY_URL_PATTERNS` — 排除文章/目录 URL（/news/、/articles/、/for-sale/ 等）
3. `_enhance_query_for_au()` — 自动为短 AU 查询（≤5 词）添加 `site:.com.au`
4. 联系信号检测 — 页面必须有邮箱/电话/contact 链接才算公司网站
5. `_is_restaurant_hotel_page()` — 要求至少 3 个 venue 类行业关键词

**已知限制：**
- 长关键词（>5 词）加 `site:.com.au` 后谷歌可能返回 0 结果
- `EXCLUDE_DOMAINS` 需持续维护（新发现的非目标域名需手动添加）
- 谷歌 429 限流时无法运行

**阻塞处理流程：**

遇到阻塞（同一问题尝试 2–3 次无进展）时，按以下顺序处理：

1. **分类** — 用 `docs/logs/changelog.md` 中的标签格式 `[大类-子类]` 标记（如 `NET-FETCH-HTTP-429`、`DATA-QUALITY-FILTER`）
2. **查表** — 在 changelog.md 的"历史阻塞索引"表中查找同标签，如有则直接应用已记录的修复方案，不重新调试
3. **解决并记录** — 如无匹配，正常调试解决后，在 changelog.md 追加新条目（症状 / 根因 / 修复 / 最佳实践），并更新索引表

常见阻塞标签：
- `NET-FETCH-HTTP-429` — 谷歌限流，需等待或换搜索方式
- `NET-FETCH-HTTP-403` — 反爬拦截，需用 CloakBrowser 兜底
- `DATA-QUALITY-FILTER` — 过滤器误判（漏过非目标或误拦目标），需调整过滤规则
- `DATA-QUALITY-DEDUP` — 去重失败，同一公司不同名称/域名入库

---

## 测试验证

```bash
# 运行所有单元测试
pytest tests/test_scheduler.py tests/test_tracker.py tests/test_keyword_discovery.py \
       tests/test_generator.py tests/test_market_intel.py tests/test_import_suggestions.py -v

# 验证生成器
python -m scripts.keyword_scheduler.generator --dry-run --max 30

# 验证调度器
python -m scripts.keyword_scheduler.scheduler --dry-run

# 检查无临时文件
git status --short | grep -E "(_tmp_|temp_|debug_)"
```
