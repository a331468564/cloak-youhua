<!-- DOC_META
lifecycle:  long-term
audience:   both
write_when: 报告系统设计完成时写入
read_when:  实施报告系统重构前读取
delete_when: 实施完成后可删除
-->
# Run Report System V2 Design

*Created: 2026-05-29*

## 问题

1. A区（表单收集）和 B区（关键词发现）的运行记录混在同一个 `run-log.md`
2. 时间格式模糊（"2026-05-20 上午"），没有精确计时
3. 缺少关键词级别的指标（有效率、去重率、搜索性能）
4. 没有汇总仪表盘，需要翻日志才能看趋势
5. 字段含义不明确，新人看不懂

## 设计方案

### 文件结构

```
E:\自动跑表单的成果和情况\
├── run-log.md          # A区表单收集运行记录
├── keyword-log.md      # B区关键词发现运行记录
└── summary.md          # 汇总仪表盘（自动生成）
```

### 自动计时机制

Python context manager，脚本执行时自动记录开始/结束/耗时。

文件：`scripts/reports/timer.py`

```python
class RunTimer:
    """自动记录开始/结束/耗时，写入 JSON 供报告脚本读取。"""
    def __enter__(self):
        self.start = datetime.now()
        return self
    def __exit__(self, ...):
        self.end = datetime.now()
        self.duration = self.end - self.start
        # 写入 data/.last_run_timing.json
```

脚本调用方式：
```python
with RunTimer() as timer:
    # 跑管线...
```

报告脚本读取 `data/.last_run_timing.json` 自动填入时间。

### run-log.md 格式

文件开头有字段说明表：

| 字段 | 含义 | 计算方式 |
|------|------|----------|
| 公司数 | leads.csv 总行数 | csv 行计数 |
| 联系人数 | contacts.csv 总行数 | csv 行计数 |
| 覆盖率 | 有至少一种联系信息的公司比例 | 有联系的公司数 / 总公司数 × 100% |
| AU 无联系 | 澳洲公司中无任何联系信息的数量 | country=Australia 且无邮箱/电话/表单 |
| 有邮箱 | 有公司邮箱或人名邮箱的公司数 | company_email 或 email_address 非空 |
| 有电话 | 有公司电话或手机的公司数 | company_phone 或 phone_number 非空 |
| 有表单 | 有联系表单 URL 的公司数 | company_contact_form_url 非空 |
| 直联率 | 有人名邮箱+手机的联系人比例 | (人名邮箱+手机) / 联系人数 × 100% |
| 批次数 | 本次 extraction 跑了几批 | --limit 参数值 |
| 候选数 | extraction 产出的原始候选总数 | 报告 CSV 行数 |

每条记录格式：
```markdown
## A-Run {N}

> {开始时间} → {结束时间}（耗时 {duration}）
> **任务：** {task description}

| 指标 | 跑前 | 跑后 | 变化 |
|------|------|------|------|
| ... | ... | ... | ... |

- 亮点
- 问题
- 备注
```

### keyword-log.md 格式

文件开头有字段说明表：

| 字段 | 含义 | 计算方式 |
|------|------|----------|
| 产出数 | 该关键词搜到的新公司数 | 入库 leads.csv 的行数 |
| 有效率 | 搜到的公司中符合目标客户的比例 | 符合条件数 / 总搜到数 × 100% |
| 去重率 | 搜到但已存在的公司比例 | 已存在数 / 总搜到数 × 100% |
| 搜索耗时 | Google 搜索 + 页面抓取总时间 | 自动计时（RunTimer） |
| 429 次数 | Google 返回限流错误的次数 | 统计 stderr 中 429 出现次数 |
| 过滤命中 | 被过滤器拦截的非目标结果数 | EXCLUDE_DOMAINS + 其他过滤器 |
| 备注 | 阻塞事件、意外发现、优化建议 | 人工/agent 填写 |

每条记录格式：
```markdown
## B-Run {N}

> {开始时间} → {结束时间}（耗时 {duration}）
> **任务：** {task description}

| 关键词 | 产出 | 有效率 | 去重率 | 搜索耗时 | 429 | 过滤命中 | 备注 |
|--------|------|--------|--------|----------|-----|----------|------|
| ... | ... | ... | ... | ... | ... | ... | ... |
| **合计** | **N** | **X%** | **X%** | **XmXs** | **N** | **N** | |

- 亮点/问题/备注
```

### summary.md 格式

自动从 run-log.md 和 keyword-log.md 生成，包含：

1. **最新状态** — 公司数、联系人数、覆盖率、直联数、关键词库规模、最近 Run 编号
2. **A-Run 趋势** — 最近 5 次的公司数、覆盖率、联系人数、耗时
3. **B-Run 趋势** — 最近 5 次的关键词数、新公司、有效率、耗时

### 脚本清单

| 脚本 | 用途 | 输入 | 输出 |
|------|------|------|------|
| `scripts/reports/timer.py` | 自动计时 context manager | 被其他脚本 import | data/.last_run_timing.json |
| `scripts/reports/generate_run_report.py` | A区报告（改造） | CLI 参数 + timing.json | run-log.md |
| `scripts/reports/generate_keyword_report.py` | B区报告（新增） | CLI 参数 + timing.json + keyword_runs.csv | keyword-log.md |
| `scripts/reports/generate_summary.py` | 汇总仪表盘（新增） | run-log.md + keyword-log.md | summary.md |

### 改造要点

1. `generate_run_report.py`：
   - 改时间格式为精确到秒
   - 读取 timing.json 自动填入开始/结束/耗时
   - 改标题前缀为 "A-Run"（区分 B-Run）
   - 文件开头加字段说明表

2. 新增 `generate_keyword_report.py`：
   - 读取 keyword_runs.csv 的数据
   - 按关键词分行展示
   - 计算有效率、去重率
   - 统计 429 次数和过滤命中
   - 支持备注列

3. 新增 `generate_summary.py`：
   - 解析 run-log.md 和 keyword-log.md
   - 提取最近 5 次趋势
   - 输出到 summary.md

4. 新增 `timer.py`：
   - RunTimer context manager
   - 写入 data/.last_run_timing.json
   - 格式：`{"start": "ISO", "end": "ISO", "duration_seconds": N}`
