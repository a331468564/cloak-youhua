<!-- DOC_META
lifecycle:  long-term
audience:   both
write_when: 计划内容变更时更新
read_when:  执行 KP 管线任务前读取
delete_when: 计划完成后归档到 archive/
-->
# KP 半自动化测试与实施方案

> **给 Agent 执行者:** 必须使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务执行本计划。步骤使用 checkbox (`- [ ]`) 语法追踪进度。

**目标:** 构建一套半自动化的 KP（关键人）发现管线，相比当前人工/半人工方式，提升效率和准确率，并设定明确的自动化门槛指标。

**架构:** 三阶段管线：(1) 通过网页抓取自动发现 KP 候选人，(2) 自动评分和去重，(3) 人工审核门控最终验证。每个阶段产出可量化的指标。自动化由准确率门槛驱动——只有达到质量标准的阶段才允许无人干预运行。

**技术栈:** Python、Scrapling（static/dynamic/stealth 抓取器）、现有 CSV 数据层、workflow_checker 模块、Google 搜索查询、可选 Tavily API。

---

## 一、现状分析

### 已有能力
- `extract_public_contact_candidates.py`: 从官网抓取邮箱、电话、表单、团队链接、角色片段、角色词附近的人名
- `generate_kp_search_tasks.py`: 为每条线索生成 Google dork 查询用于 KP 发现
- `build_form_kp_candidate_queue.py`: 从现有线索构建优先级搜索队列
- `workflow_checker.py`: 执行阈值控制（最多 3 页、每条线索 5 分钟、70% 无效页比率、防重复）
- `build_boss_report.py`: 生成 HTML 仪表盘报告

### 当前瓶颈（来自实验报告）
1. **KP 名字识别率不错（60%+ 提升）** 但 **直联发现率很低（~0-8%）**
2. 官网找到的人名很少附带个人邮箱/电话
3. 公司名称有时太泛化，导致搜索查询噪声大
4. LinkedIn 结果需要人工审核——无法自动化
5. 没有自动验证找到的名字是否确实匹配目标公司
6. 没有对已识别的 KP 名字做后续直联搜索（缺少"直联路径"步骤）

### 指标基线（来自 2026-05-09 和 2026-05-13 实验）
| 指标 | 当前值 | 目标 |
|------|--------|------|
| KP 名字识别率 | ~60% (12/20) | 80%+ |
| 直联（邮箱/电话）获取率 | ~0-8% | 25%+ |
| 每条线索平均耗时（人工） | 5+ 分钟 | <2 分钟（自动化） |
| 误报率（错误人名） | 未知 | <10% |
| 重复候选率 | 低（workflow_checker 有效） | 0% |

---

## 二、文件结构

```
scripts/
  kp_pipeline/
    __init__.py                  # 包初始化
    config.py                    # 管线配置和阈值
    metrics.py                   # 指标收集和报告
    stage1_discover.py           # 自动化：发现 KP 候选人
    stage2_enrich.py             # 自动化：直联路径富化
    stage3_validate.py           # 半自动：验证和评分候选人
    run_pipeline.py              # 管线编排器
  tests/
    test_kp_pipeline.py          # 管线集成测试
    test_stage1_discover.py      # Stage 1 单元测试
    test_stage2_enrich.py        # Stage 2 单元测试
    test_stage3_validate.py      # Stage 3 单元测试
    test_metrics.py              # 指标单元测试
    conftest.py                  # 共享测试 fixtures
data/
  kp_metrics.json                # 管线运行指标日志
  kp_validation_log.csv          # 人工审核决策日志
reports/
  kp-pipeline-run-*.md           # 管线运行报告
  kp-pipeline-run-*.csv          # 管线运行候选输出
config/
  kp_pipeline.json               # 管线配置文件
```

---

## 三、实施阶段

### 阶段 1：基础设施 — 指标与测试

#### 任务 1：创建管线配置

**文件：**
- 创建: `config/kp_pipeline.json`
- 创建: `scripts/kp_pipeline/__init__.py`
- 创建: `scripts/kp_pipeline/config.py`

- [ ] **步骤 1：创建管线配置 JSON**

```json
{
  "version": "1.0",
  "stages": {
    "stage1_discover": {
      "enabled": true,
      "max_pages_per_lead": 3,
      "max_time_per_lead_seconds": 120,
      "follow_links": 2,
      "fetcher_mode": "static",
      "delay_between_requests_seconds": 2.0,
      "search_patterns": [
        "site:{domain} team OR people OR leadership OR management",
        "site:{domain} founder OR owner OR director OR partner",
        "site:{domain} \"operations manager\" OR \"general manager\" OR \"food and beverage\"",
        "\"{company_name}\" founder OR owner OR director Australia",
        "\"{company_name}\" \"operations manager\" OR \"general manager\" OR procurement"
      ],
      "noisy_domains_blocklist": [
        "crownmelbourne.com.au",
        "crownperth.com.au",
        "linkedin.com",
        "facebook.com",
        "instagram.com",
        "youtube.com",
        "yelp.com",
        "tripadvisor.com",
        "zomato.com",
        "menulog.com.au"
      ]
    },
    "stage2_enrich": {
      "enabled": true,
      "max_pages_per_lead": 2,
      "max_time_per_lead_seconds": 90,
      "follow_links": 1,
      "fetcher_mode": "static",
      "search_patterns_for_known_kp": [
        "\"{key_contact_name}\" \"{company_name}\" email OR phone OR contact",
        "site:{domain} \"{key_contact_name}\"",
        "\"{key_contact_name}\" \"{company_name}\" LinkedIn"
      ]
    },
    "stage3_validate": {
      "enabled": true,
      "auto_approve_threshold": 85,
      "auto_reject_threshold": 30,
      "human_review_range": [30, 85],
      "validation_rules": {
        "require_source_link": true,
        "require_confidence_note": true,
        "min_name_length": 4,
        "max_name_length": 50,
        "reject_common_false_positives": [
          "Contact", "Dining", "Menu", "Home", "About", "Team",
          "Leadership", "Management", "Staff", "People", "Careers"
        ]
      }
    }
  },
  "automation_gates": {
    "stage1_auto": {
      "condition": "false_positive_rate < 0.15 AND kp_identification_rate > 0.5",
      "description": "当发现准确率超过 85% 时，Stage 1 可自动运行"
    },
    "stage2_auto": {
      "condition": "direct_contact_rate > 0.1 AND false_positive_rate < 0.1",
      "description": "当直联富化成功率超过 10% 时，Stage 2 可自动运行"
    },
    "stage3_auto_approve": {
      "condition": "auto_approve_accuracy > 0.95",
      "description": "当验证准确率超过 95% 时，高置信度候选人自动保存"
    }
  },
  "metrics": {
    "log_file": "data/kp_metrics.json",
    "validation_log": "data/kp_validation_log.csv",
    "report_dir": "reports/"
  }
}
```

- [ ] **步骤 2：创建包初始化文件**

```python
# scripts/kp_pipeline/__init__.py
"""KP 半自动化管线。"""
```

- [ ] **步骤 3：创建配置模块**

```python
# scripts/kp_pipeline/config.py
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "kp_pipeline.json"


def load_config(config_path=None):
    path = config_path or CONFIG_PATH
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_stage_config(config, stage_name):
    return config.get("stages", {}).get(stage_name, {})


def get_automation_gate(config, gate_name):
    return config.get("automation_gates", {}).get(gate_name, {})
```

- [ ] **步骤 4：提交**

```bash
git add config/kp_pipeline.json scripts/kp_pipeline/__init__.py scripts/kp_pipeline/config.py
git commit -m "feat(kp-pipeline): 添加管线配置和配置模块"
```

---

#### 任务 2：创建指标收集模块

**文件：**
- 创建: `scripts/kp_pipeline/metrics.py`
- 创建: `data/kp_metrics.json`（空初始）
- 创建: `data/kp_validation_log.csv`（仅表头）

- [ ] **步骤 1：创建指标模块**

```python
# scripts/kp_pipeline/metrics.py
import json
import csv
from datetime import datetime
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def init_metrics_log():
    log_path = DATA_DIR / "kp_metrics.json"
    if not log_path.exists():
        log_path.write_text("[]", encoding="utf-8")


def init_validation_log():
    log_path = DATA_DIR / "kp_validation_log.csv"
    if not log_path.exists():
        fields = [
            "timestamp", "run_id", "lead_id", "company_name",
            "candidate_name", "candidate_title", "candidate_type",
            "auto_score", "human_decision", "human_notes",
            "source_url", "confidence"
        ]
        with open(log_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
            writer.writeheader()


def log_run_metrics(run_id, stage, metrics_dict):
    log_path = DATA_DIR / "kp_metrics.json"
    entries = []
    if log_path.exists():
        try:
            entries = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            entries = []

    entry = {
        "run_id": run_id,
        "stage": stage,
        "timestamp": datetime.now().isoformat(),
        **metrics_dict,
    }
    entries.append(entry)
    log_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    return entry


def log_validation_decision(run_id, lead_id, company_name, candidate_name,
                            candidate_title, candidate_type, auto_score,
                            human_decision, human_notes, source_url, confidence):
    log_path = DATA_DIR / "kp_validation_log.csv"
    fields = [
        "timestamp", "run_id", "lead_id", "company_name",
        "candidate_name", "candidate_title", "candidate_type",
        "auto_score", "human_decision", "human_notes",
        "source_url", "confidence"
    ]
    row = {
        "timestamp": datetime.now().isoformat(),
        "run_id": run_id,
        "lead_id": lead_id,
        "company_name": company_name,
        "candidate_name": candidate_name,
        "candidate_title": candidate_title,
        "candidate_type": candidate_type,
        "auto_score": str(auto_score),
        "human_decision": human_decision,
        "human_notes": human_notes,
        "source_url": source_url,
        "confidence": confidence,
    }
    with open(log_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writerow(row)


def compute_accuracy_metrics(validation_log_path=None):
    log_path = validation_log_path or (DATA_DIR / "kp_validation_log.csv")
    if not log_path.exists():
        return {}

    rows = []
    with open(log_path, "r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    if not rows:
        return {"total_decisions": 0}

    decisions = Counter(r.get("human_decision", "") for r in rows)
    total = len(rows)
    correct = decisions.get("correct", 0) + decisions.get("approved", 0)
    incorrect = decisions.get("incorrect", 0) + decisions.get("rejected", 0)
    uncertain = decisions.get("uncertain", 0) + decisions.get("skip", 0)

    return {
        "total_decisions": total,
        "approved": correct,
        "rejected": incorrect,
        "uncertain": uncertain,
        "accuracy_rate": round(correct / max(total - uncertain, 1), 3),
        "false_positive_rate": round(incorrect / max(total, 1), 3),
    }


def compute_pipeline_metrics(run_log_path=None):
    log_path = run_log_path or (DATA_DIR / "kp_metrics.json")
    if not log_path.exists():
        return {}

    try:
        entries = json.loads(log_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValueError):
        return {}

    if not entries:
        return {}

    latest = entries[-1]
    return {
        "total_runs": len(entries),
        "latest_run": latest,
        "stages_run": list(set(e.get("stage", "") for e in entries)),
    }
```

- [ ] **步骤 2：初始化空指标文件**

```python
from scripts.kp_pipeline.metrics import init_metrics_log, init_validation_log
init_metrics_log()
init_validation_log()
```

- [ ] **步骤 3：提交**

```bash
git add scripts/kp_pipeline/metrics.py
git commit -m "feat(kp-pipeline): 添加指标收集和验证日志模块"
```

---

#### 任务 3：创建测试基础设施

**文件：**
- 创建: `scripts/tests/__init__.py`
- 创建: `scripts/tests/conftest.py`
- 创建: `scripts/tests/test_metrics.py`

- [ ] **步骤 1：创建测试包初始化**

```python
# scripts/tests/__init__.py
```

- [ ] **步骤 2：创建共享测试 fixtures**

```python
# scripts/tests/conftest.py
import pytest
import csv
import json
from pathlib import Path


@pytest.fixture
def tmp_data_dir(tmp_path):
    """创建包含样本文件的临时数据目录。"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    leads_fields = [
        "lead_id", "company_name", "website", "country", "city_or_region",
        "customer_type", "contact_data_level", "key_contact_name",
        "key_contact_job_title", "key_contact_email", "key_contact_phone",
        "company_email", "company_phone", "company_contact_form_url",
        "customer_strength_level", "contact_priority"
    ]
    leads = [
        {
            "lead_id": "LEAD-TEST-001",
            "company_name": "Test Restaurant Group",
            "website": "https://testrestaurant.com.au",
            "country": "Australia",
            "city_or_region": "Sydney",
            "customer_type": "restaurant group",
            "contact_data_level": "Company Contact Only",
            "key_contact_name": "",
            "key_contact_job_title": "",
            "key_contact_email": "",
            "key_contact_phone": "",
            "company_email": "info@testrestaurant.com.au",
            "company_phone": "02 1234 5678",
            "company_contact_form_url": "https://testrestaurant.com.au/contact",
            "customer_strength_level": "High",
            "contact_priority": "High",
        },
        {
            "lead_id": "LEAD-TEST-002",
            "company_name": "Another Hotel",
            "website": "https://anotherhotel.com.au",
            "country": "Australia",
            "city_or_region": "Melbourne",
            "customer_type": "hotel group",
            "contact_data_level": "Key Person Identified",
            "key_contact_name": "John Smith",
            "key_contact_job_title": "Director",
            "key_contact_email": "",
            "key_contact_phone": "",
            "company_email": "",
            "company_phone": "",
            "company_contact_form_url": "",
            "customer_strength_level": "High",
            "contact_priority": "High",
        },
    ]
    with open(data_dir / "leads.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=leads_fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(leads)

    contacts_fields = [
        "contact_id", "lead_id", "company_name", "contact_name",
        "job_title", "email", "phone", "linkedin_url",
        "source_link", "contact_confidence", "contact_status"
    ]
    contacts = [
        {
            "contact_id": "CONTACT-TEST-001",
            "lead_id": "LEAD-TEST-002",
            "company_name": "Another Hotel",
            "contact_name": "John Smith",
            "job_title": "Director",
            "email": "",
            "phone": "",
            "linkedin_url": "",
            "source_link": "https://anotherhotel.com.au/team",
            "contact_confidence": "Medium",
            "contact_status": "已识别联系人",
        },
    ]
    with open(data_dir / "contacts.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=contacts_fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(contacts)

    return data_dir


@pytest.fixture
def sample_config(tmp_path):
    """创建最小管线配置。"""
    config = {
        "version": "1.0",
        "stages": {
            "stage1_discover": {
                "enabled": True,
                "max_pages_per_lead": 2,
                "max_time_per_lead_seconds": 60,
                "follow_links": 1,
                "fetcher_mode": "static",
                "delay_between_requests_seconds": 1.0,
                "search_patterns": [
                    "site:{domain} team OR people",
                    '"{company_name}" founder OR owner OR director',
                ],
                "noisy_domains_blocklist": ["linkedin.com"],
            },
            "stage2_enrich": {
                "enabled": True,
                "max_pages_per_lead": 1,
                "max_time_per_lead_seconds": 30,
                "search_patterns_for_known_kp": [
                    '"{key_contact_name}" "{company_name}" email',
                ],
            },
            "stage3_validate": {
                "enabled": True,
                "auto_approve_threshold": 85,
                "auto_reject_threshold": 30,
                "human_review_range": [30, 85],
                "validation_rules": {
                    "require_source_link": True,
                    "require_confidence_note": True,
                    "min_name_length": 4,
                    "max_name_length": 50,
                    "reject_common_false_positives": ["Contact", "Dining", "Menu"],
                },
            },
        },
        "automation_gates": {},
        "metrics": {
            "log_file": str(tmp_path / "data" / "kp_metrics.json"),
            "validation_log": str(tmp_path / "data" / "kp_validation_log.csv"),
            "report_dir": str(tmp_path / "reports"),
        },
    }
    config_path = tmp_path / "config" / "kp_pipeline.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config_path
```

- [ ] **步骤 3：编写指标测试**

```python
# scripts/tests/test_metrics.py
import json
import csv
from pathlib import Path
from scripts.kp_pipeline.metrics import (
    init_metrics_log,
    init_validation_log,
    log_run_metrics,
    log_validation_decision,
    compute_accuracy_metrics,
)


def test_init_metrics_log_creates_file(tmp_path):
    log_path = tmp_path / "kp_metrics.json"
    import scripts.kp_pipeline.metrics as m
    old_dir = m.DATA_DIR
    m.DATA_DIR = tmp_path
    try:
        init_metrics_log()
        assert log_path.exists()
        assert json.loads(log_path.read_text()) == []
    finally:
        m.DATA_DIR = old_dir


def test_init_validation_log_creates_file_with_header(tmp_path):
    log_path = tmp_path / "kp_validation_log.csv"
    import scripts.kp_pipeline.metrics as m
    old_dir = m.DATA_DIR
    m.DATA_DIR = tmp_path
    try:
        init_validation_log()
        assert log_path.exists()
        with open(log_path, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader)
        assert "timestamp" in header
        assert "human_decision" in header
    finally:
        m.DATA_DIR = old_dir


def test_log_run_metrics_appends_entry(tmp_path):
    import scripts.kp_pipeline.metrics as m
    old_dir = m.DATA_DIR
    m.DATA_DIR = tmp_path
    try:
        init_metrics_log()
        entry = log_run_metrics("RUN-001", "stage1", {"leads_processed": 5})
        assert entry["run_id"] == "RUN-001"
        assert entry["leads_processed"] == 5

        entries = json.loads((tmp_path / "kp_metrics.json").read_text())
        assert len(entries) == 1
    finally:
        m.DATA_DIR = old_dir


def test_compute_accuracy_metrics_empty(tmp_path):
    result = compute_accuracy_metrics(tmp_path / "nonexistent.csv")
    assert result == {}


def test_compute_accuracy_metrics_with_data(tmp_path):
    log_path = tmp_path / "validation.csv"
    fields = ["timestamp", "run_id", "lead_id", "company_name",
              "candidate_name", "candidate_title", "candidate_type",
              "auto_score", "human_decision", "human_notes",
              "source_url", "confidence"]
    with open(log_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerow({f: "" for f in fields} | {"human_decision": "approved"})
        writer.writerow({f: "" for f in fields} | {"human_decision": "approved"})
        writer.writerow({f: "" for f in fields} | {"human_decision": "rejected"})

    result = compute_accuracy_metrics(log_path)
    assert result["total_decisions"] == 3
    assert result["approved"] == 2
    assert result["rejected"] == 1
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd E:\AI\TestProject-v2
python -m pytest scripts/tests/test_metrics.py -v
```

预期：全部测试 PASS。

- [ ] **步骤 5：提交**

```bash
git add scripts/tests/__init__.py scripts/tests/conftest.py scripts/tests/test_metrics.py
git commit -m "test(kp-pipeline): 添加测试基础设施和指标测试"
```

---

### 阶段 2：Stage 1 — 自动化 KP 发现

#### 任务 4：实现 Stage 1 发现引擎

**文件：**
- 创建: `scripts/kp_pipeline/stage1_discover.py`
- 创建: `scripts/tests/test_stage1_discover.py`

- [ ] **步骤 1：编写 Stage 1 单元测试**

```python
# scripts/tests/test_stage1_discover.py
import pytest
from scripts.kp_pipeline.stage1_discover import (
    clean_company_name,
    build_search_queries,
    is_noisy_domain,
    extract_kp_candidates_from_text,
    score_candidate,
)


def test_clean_company_name_removes_suffixes():
    assert clean_company_name("Test Restaurant Group Pty Ltd") == "Test Restaurant Group"
    assert clean_company_name("Another Hotel Pty. Ltd.") == "Another Hotel"
    assert clean_company_name("Simple Name") == "Simple Name"


def test_clean_company_name_removes_country():
    assert clean_company_name("Test Restaurant Group Australia") == "Test Restaurant Group"


def test_build_search_queries_with_domain():
    config_patterns = [
        "site:{domain} team OR people",
        '"{company_name}" founder OR owner',
    ]
    queries = build_search_queries(
        domain="testrestaurant.com.au",
        company_name="Test Restaurant Group",
        patterns=config_patterns,
    )
    assert len(queries) == 2
    assert "site:testrestaurant.com.au" in queries[0]
    assert "Test Restaurant Group" in queries[1]


def test_build_search_queries_without_domain():
    config_patterns = ['"{company_name}" founder OR owner']
    queries = build_search_queries(
        domain="",
        company_name="Test Restaurant Group",
        patterns=config_patterns,
    )
    assert len(queries) == 1
    assert "Test Restaurant Group" in queries[0]


def test_is_noisy_domain():
    blocklist = ["linkedin.com", "facebook.com"]
    assert is_noisy_domain("https://linkedin.com/in/someone", blocklist) is True
    assert is_noisy_domain("https://testrestaurant.com.au/team", blocklist) is False


def test_extract_kp_candidates_from_text():
    text = """
    Our Team
    John Smith - Managing Director
    Jane Doe - Operations Manager
    Contact us at info@example.com
    """
    candidates = extract_kp_candidates_from_text(text, "https://example.com")
    names = [c["name"] for c in candidates]
    assert "John Smith" in names
    assert "Jane Doe" in names


def test_extract_kp_candidates_filters_false_positives():
    text = "Contact Dining Menu About Team Leadership"
    candidates = extract_kp_candidates_from_text(text, "https://example.com")
    names = [c["name"] for c in candidates]
    assert "Contact" not in names
    assert "Dining" not in names


def test_score_candidate_director():
    score = score_candidate("John Smith", "Managing Director", "https://example.com/team")
    assert score >= 70


def test_score_candidate_generic_role():
    score = score_candidate("Jane Doe", "Staff Member", "https://example.com")
    assert score < 70
```

- [ ] **步骤 2：运行测试验证失败**

```bash
python -m pytest scripts/tests/test_stage1_discover.py -v
```

预期：FAIL，报 "ModuleNotFoundError"

- [ ] **步骤 3：实现 Stage 1 发现引擎**

```python
# scripts/kp_pipeline/stage1_discover.py
"""
Stage 1: 自动化 KP 候选人发现

从官网使用网页抓取发现关键人候选人。
产出带评分的候选行，供 Stage 2 富化或人工审核。
"""
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, quote_plus

from scrapling.fetchers import Fetcher, DynamicFetcher, StealthyFetcher

sys_path = Path(__file__).parent.parent
import sys
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

from workflow_checker import checker as workflow_checker

ROLE_HINTS_HIGH = [
    "managing director", "chief executive", "ceo", "founder", "co-founder",
    "owner", "director", "partner", "general manager",
]
ROLE_HINTS_MEDIUM = [
    "operations manager", "procurement", "purchasing", "food and beverage",
    "f&b", "head chef", "executive chef", "events manager", "projects manager",
    "growth", "cfo", "head of venues",
]
ROLE_HINTS_LOW = [
    "manager", "supervisor", "coordinator", "team lead", "chef",
]

PERSON_NAME_RE = re.compile(
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})"
)

FALSE_POSITIVE_NAMES = {
    "contact", "dining", "menu", "home", "about", "team", "leadership",
    "management", "staff", "people", "careers", "our team", "the team",
    "our people", "meet the", "read more", "learn more", "find out",
    "get in", "click here", "sign up", "subscribe", "privacy", "terms",
    "copyright", "all rights", "reserved", "rights reserved",
}


def clean_company_name(name):
    """去除 Pty Ltd、Australia 等公司名后缀。"""
    if not name:
        return ""
    cleaned = name.strip()
    suffixes = [
        "pty ltd", "pty. ltd.", "pty ltd.", "pty. ltd",
        "limited", "ltd", "ltd.", "inc", "inc.",
        "australia", "au", "group",
    ]
    for suffix in suffixes:
        pattern = re.compile(r"\s+" + re.escape(suffix) + r"\s*$", re.IGNORECASE)
        cleaned = pattern.sub("", cleaned)
    return cleaned.strip()


def build_search_queries(domain, company_name, patterns):
    """从配置模式构建搜索查询。"""
    queries = []
    clean_name = clean_company_name(company_name)
    for pattern in patterns:
        query = pattern.format(
            domain=domain,
            company_name=clean_name,
        )
        if query.strip():
            queries.append(query)
    return queries


def is_noisy_domain(url, blocklist):
    """检查 URL 域名是否在噪声域名黑名单中。"""
    if not url:
        return False
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return any(noisy in domain for noisy in blocklist)
    except Exception:
        return False


def extract_kp_candidates_from_text(text, source_url):
    """从页面文本中提取角色词附近的人名。"""
    if not text:
        return []

    candidates = []
    text_lower = text.lower()

    all_roles = ROLE_HINTS_HIGH + ROLE_HINTS_MEDIUM + ROLE_HINTS_LOW

    for role in sorted(all_roles, key=len, reverse=True):
        idx = text_lower.find(role)
        if idx < 0:
            continue

        context_start = max(0, idx - 100)
        context_end = min(len(text), idx + len(role) + 100)
        context = text[context_start:context_end]

        for match in PERSON_NAME_RE.finditer(context):
            name = match.group(1).strip()
            name_lower = name.lower()

            if name_lower in FALSE_POSITIVE_NAMES:
                continue
            if len(name) < 4 or len(name) > 50:
                continue
            name_words = set(name_lower.split())
            if name_words & FALSE_POSITIVE_NAMES:
                continue

            candidates.append({
                "name": name,
                "role_context": role,
                "source_url": source_url,
                "context_snippet": context[max(0, match.start() - 20):match.end() + 20].strip(),
            })

    # 按名字去重
    seen = set()
    unique = []
    for c in candidates:
        key = c["name"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


def score_candidate(name, role_context, source_url):
    """根据角色和来源为 KP 候选人评分。"""
    score = 50  # 基础分

    role_lower = (role_context or "").lower()

    # 角色评分
    if any(r in role_lower for r in ROLE_HINTS_HIGH):
        score += 30
    elif any(r in role_lower for r in ROLE_HINTS_MEDIUM):
        score += 20
    elif any(r in role_lower for r in ROLE_HINTS_LOW):
        score += 10

    # 来源评分
    if source_url:
        url_lower = source_url.lower()
        if "/team" in url_lower or "/about" in url_lower or "/people" in url_lower:
            score += 15
        if "/leadership" in url_lower or "/management" in url_lower:
            score += 10

    return min(score, 100)


def fetch_page_safe(url, fetcher_mode, timeout=20000):
    """带错误处理的页面抓取。"""
    try:
        if fetcher_mode == "dynamic":
            page = DynamicFetcher.fetch(url, headless=True, timeout=timeout)
        elif fetcher_mode == "stealth":
            page = StealthyFetcher.fetch(url, headless=True, timeout=timeout)
        else:
            page = Fetcher.get(url, timeout=timeout // 1000, retries=1)

        status = getattr(page, "status", 0)
        if not str(status).startswith("2"):
            return None, f"HTTP {status}"

        text = page.get_all_text(separator=" ") if hasattr(page, "get_all_text") else page.text
        return text, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def discover_kp_for_lead(lead, config):
    """对单条线索运行 Stage 1 KP 发现。"""
    stage_config = config.get("stages", {}).get("stage1_discover", {})

    website = (lead.get("website") or "").strip()
    if not website:
        return [], "no_website"

    try:
        parsed = urlparse(website if "://" in website else f"https://{website}")
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
    except Exception:
        return [], "invalid_url"

    blocklist = stage_config.get("noisy_domains_blocklist", [])
    if is_noisy_domain(website, blocklist):
        return [], "noisy_domain"

    lead_id = lead.get("lead_id", "")
    workflow_checker.load_existing_data()
    if workflow_checker.should_skip_lead(lead_id):
        return [], "already_has_kp_or_contact"

    patterns = stage_config.get("search_patterns", [])
    company_name = lead.get("company_name", "")
    queries = build_search_queries(domain, company_name, patterns)

    fetcher_mode = stage_config.get("fetcher_mode", "static")
    follow_links = stage_config.get("follow_links", 2)
    delay = stage_config.get("delay_between_requests_seconds", 2.0)

    all_candidates = []
    pages_searched = 0
    errors = []

    # 抓取主站
    text, error = fetch_page_safe(website, fetcher_mode)
    if text:
        candidates = extract_kp_candidates_from_text(text, website)
        for c in candidates:
            c["score"] = score_candidate(c["name"], c["role_context"], website)
            c["lead_id"] = lead_id
            c["company_name"] = company_name
        all_candidates.extend(candidates)
        pages_searched += 1
    else:
        errors.append(f"{website}: {error}")

    # 跟踪发现的链接（团队/关于页面）
    if text and follow_links > 0:
        team_links = []
        try:
            if hasattr(text, 'css'):
                for element in text.css("a"):
                    href = element.attrib.get("href", "")
                    if href:
                        label = (element.text or "").lower() + " " + href.lower()
                        if any(kw in label for kw in ["team", "about", "people", "leadership", "management"]):
                            full_url = text.urljoin(href)
                            if not is_noisy_domain(full_url, blocklist):
                                team_links.append(full_url)
        except Exception:
            pass

        for link in team_links[:follow_links]:
            time.sleep(delay)
            link_text, link_error = fetch_page_safe(link, fetcher_mode)
            if link_text:
                candidates = extract_kp_candidates_from_text(link_text, link)
                for c in candidates:
                    c["score"] = score_candidate(c["name"], c["role_context"], link)
                    c["lead_id"] = lead_id
                    c["company_name"] = company_name
                all_candidates.extend(candidates)
                pages_searched += 1
            else:
                errors.append(f"{link}: {link_error}")

    return all_candidates, {
        "pages_searched": pages_searched,
        "errors": errors,
        "queries_used": len(queries),
    }


def run_stage1(leads, config, limit=None):
    """对线索列表运行 Stage 1 发现。"""
    from .config import get_stage_config
    from .metrics import log_run_metrics

    stage_config = get_stage_config(config, "stage1_discover")
    if not stage_config.get("enabled", True):
        return [], {"skipped": True}

    run_id = f"S1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    all_candidates = []
    leads_processed = 0
    leads_with_candidates = 0
    total_errors = 0

    for lead in leads[:limit] if limit else leads:
        candidates, info = discover_kp_for_lead(lead, config)
        leads_processed += 1

        if candidates:
            leads_with_candidates += 1
            all_candidates.extend(candidates)

        if isinstance(info, dict):
            total_errors += len(info.get("errors", []))

        time.sleep(stage_config.get("delay_between_requests_seconds", 2.0))

    metrics = {
        "leads_processed": leads_processed,
        "leads_with_candidates": leads_with_candidates,
        "total_candidates": len(all_candidates),
        "total_errors": total_errors,
        "kp_identification_rate": round(leads_with_candidates / max(leads_processed, 1), 3),
        "avg_candidates_per_lead": round(len(all_candidates) / max(leads_processed, 1), 1),
    }
    log_run_metrics(run_id, "stage1_discover", metrics)

    return all_candidates, metrics
```

- [ ] **步骤 4：运行测试验证通过**

```bash
python -m pytest scripts/tests/test_stage1_discover.py -v
```

预期：全部测试 PASS。

- [ ] **步骤 5：提交**

```bash
git add scripts/kp_pipeline/stage1_discover.py scripts/tests/test_stage1_discover.py
git commit -m "feat(kp-pipeline): 实现 Stage 1 自动化 KP 发现引擎"
```

---

### 阶段 3：Stage 2 — 直联路径富化

#### 任务 5：实现 Stage 2 富化引擎

**文件：**
- 创建: `scripts/kp_pipeline/stage2_enrich.py`
- 创建: `scripts/tests/test_stage2_enrich.py`

- [ ] **步骤 1：编写 Stage 2 单元测试**

```python
# scripts/tests/test_stage2_enrich.py
import pytest
from scripts.kp_pipeline.stage2_enrich import (
    build_enrichment_queries,
    extract_email_from_text,
    extract_phone_from_text,
    classify_email,
    classify_contact_directness,
)


def test_build_enrichment_queries():
    patterns = [
        '"{key_contact_name}" "{company_name}" email OR phone',
        'site:{domain} "{key_contact_name}"',
    ]
    queries = build_enrichment_queries(
        key_contact_name="John Smith",
        company_name="Test Restaurant",
        domain="testrestaurant.com.au",
        patterns=patterns,
    )
    assert len(queries) == 2
    assert "John Smith" in queries[0]
    assert "Test Restaurant" in queries[0]


def test_extract_email_from_text():
    text = "Contact John Smith at john.smith@testrestaurant.com.au for details."
    emails = extract_email_from_text(text)
    assert "john.smith@testrestaurant.com.au" in emails


def test_extract_email_filters_noreply():
    text = "Send to noreply@example.com or john@example.com"
    emails = extract_email_from_text(text)
    assert "noreply@example.com" not in emails
    assert "john@example.com" in emails


def test_extract_phone_from_text():
    text = "Call us on 0412 345 678 or (02) 9876 5432"
    phones = extract_phone_from_text(text)
    assert any("0412" in p for p in phones)


def test_classify_email_person():
    assert classify_email("john.smith@test.com") == "person_email"
    assert classify_email("john@test.com") == "possible_person_email"


def test_classify_email_company():
    assert classify_email("info@test.com") == "company_email"
    assert classify_email("admin@test.com") == "company_email"


def test_classify_email_department():
    assert classify_email("sales@test.com") == "department_email"
    assert classify_email("procurement@test.com") == "department_email"


def test_classify_contact_directness_with_email():
    result = classify_contact_directness(
        name="John Smith",
        email="john.smith@test.com",
        phone="",
        title="Director",
    )
    assert result["level"] == "direct"
    assert result["confidence"] == "High"


def test_classify_contact_directness_name_only():
    result = classify_contact_directness(
        name="John Smith",
        email="",
        phone="",
        title="Director",
    )
    assert result["level"] == "identified"
    assert result["confidence"] == "Medium"
```

- [ ] **步骤 2：运行测试验证失败**

```bash
python -m pytest scripts/tests/test_stage2_enrich.py -v
```

预期：FAIL，报 "ModuleNotFoundError"

- [ ] **步骤 3：实现 Stage 2 富化引擎**

```python
# scripts/kp_pipeline/stage2_enrich.py
"""
Stage 2: 直联路径富化

对已识别的 KP 名字，搜索直联路径（邮箱、电话、个人 LinkedIn）。
基于 Stage 1 输出或已有 key_contact_name 但无直联的线索。
"""
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from scrapling.fetchers import Fetcher

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(
    r"(?:"
    r"(?:\+?61[\s.-]*(?:0)?4\d{2}[\s.-]*\d{3}[\s.-]*\d{3})|"
    r"(?:04\d{2}[\s.-]*\d{3}[\s.-]*\d{3})|"
    r"(?:\(?0[2378]\)?[\s.-]*\d{4}[\s.-]*\d{4})|"
    r"(?:(?:1300|1800)[\s.-]*\d{3}[\s.-]*\d{3})"
    r")"
)

EMAIL_SKIP = {"noreply", "no-reply", "careers", "jobs", "hr", "privacy", "media", "marketing"}
EMAIL_DEPARTMENT = {"sales", "procurement", "accounts", "events", "functions", "enquiries", "hello", "info", "admin"}


def build_enrichment_queries(key_contact_name, company_name, domain, patterns):
    """为已知 KP 构建搜索查询。"""
    queries = []
    for pattern in patterns:
        query = pattern.format(
            key_contact_name=key_contact_name,
            company_name=company_name,
            domain=domain,
        )
        if query.strip():
            queries.append(query)
    return queries


def extract_email_from_text(text):
    """从文本中提取并过滤邮箱地址。"""
    if not text:
        return []
    raw = set(EMAIL_RE.findall(text))
    filtered = []
    for email in raw:
        local = email.split("@")[0].lower()
        if any(local.startswith(skip) for skip in EMAIL_SKIP):
            continue
        filtered.append(email.lower())
    return filtered


def extract_phone_from_text(text):
    """从文本中提取澳大利亚电话号码。"""
    if not text:
        return []
    return list(set(PHONE_RE.findall(text)))


def classify_email(email):
    """将邮箱分类为个人、部门或公司邮箱。"""
    if not email:
        return "unknown"
    local = email.split("@")[0].lower()
    if "." in local or "_" in local:
        parts = local.replace("_", ".").split(".")
        if len(parts) >= 2 and all(p.isalpha() for p in parts):
            return "person_email"
    if any(local.startswith(p) for p in EMAIL_DEPARTMENT):
        return "department_email"
    if local in ("info", "admin", "contact", "hello", "enquiries"):
        return "company_email"
    return "possible_person_email"


def classify_contact_directness(name, email, phone, title):
    """分类联系路径的直联程度。"""
    has_email = bool(email and email.strip())
    has_phone = bool(phone and phone.strip())
    has_title = bool(title and title.strip())

    if has_email:
        email_type = classify_email(email)
        if email_type == "person_email":
            return {"level": "direct", "confidence": "High", "reason": "person_email_found"}
        if email_type == "possible_person_email":
            return {"level": "direct", "confidence": "Medium", "reason": "possible_person_email"}

    if has_phone and phone.strip().startswith("04"):
        return {"level": "direct", "confidence": "High", "reason": "mobile_phone_found"}

    if has_email or has_phone:
        return {"level": "company_route", "confidence": "Medium", "reason": "company_contact_found"}

    if has_title:
        return {"level": "identified", "confidence": "Medium", "reason": "name_and_title_only"}

    return {"level": "name_only", "confidence": "Low", "reason": "name_only"}


def fetch_page_text(url, timeout=15):
    """抓取页面并提取文本。"""
    try:
        page = Fetcher.get(url, timeout=timeout, retries=1)
        status = getattr(page, "status", 0)
        if not str(status).startswith("2"):
            return None
        return page.get_all_text(separator=" ") if hasattr(page, "get_all_text") else page.text
    except Exception:
        return None


def enrich_kp_from_page(url, kp_name, company_name):
    """从页面中提取特定 KP 的联系信息。"""
    text = fetch_page_text(url)
    if not text:
        return None

    if kp_name.lower() not in text.lower():
        return None

    emails = extract_email_from_text(text)
    phones = extract_phone_from_text(text)

    # 尝试找到匹配人名的邮箱
    name_parts = kp_name.lower().split()
    person_email = None
    for email in emails:
        local = email.split("@")[0].lower()
        if all(part in local for part in name_parts if len(part) > 2):
            person_email = email
            break

    return {
        "name": kp_name,
        "company_name": company_name,
        "source_url": url,
        "emails": emails,
        "phones": phones,
        "best_email": person_email or (emails[0] if emails else ""),
        "best_phone": phones[0] if phones else "",
    }


def run_stage2(candidates, config):
    """对 KP 候选人列表运行 Stage 2 富化。"""
    from .config import get_stage_config
    from .metrics import log_run_metrics

    stage_config = get_stage_config(config, "stage2_enrich")
    if not stage_config.get("enabled", True):
        return [], {"skipped": True}

    run_id = f"S2-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    enriched = []
    candidates_processed = 0
    direct_contacts_found = 0

    for candidate in candidates:
        candidates_processed += 1
        name = candidate.get("name", "")
        company = candidate.get("company_name", "")
        source_url = candidate.get("source_url", "")

        if not name or not source_url:
            continue

        result = enrich_kp_from_page(source_url, name, company)
        if result:
            directness = classify_contact_directness(
                name, result["best_email"], result["best_phone"],
                candidate.get("role_context", "")
            )
            result["directness"] = directness
            result["score"] = candidate.get("score", 50)

            if directness["level"] == "direct":
                direct_contacts_found += 1
                result["score"] = min(result["score"] + 20, 100)

            enriched.append(result)

    metrics = {
        "candidates_processed": candidates_processed,
        "enriched_candidates": len(enriched),
        "direct_contacts_found": direct_contacts_found,
        "direct_contact_rate": round(direct_contacts_found / max(candidates_processed, 1), 3),
    }
    log_run_metrics(run_id, "stage2_enrich", metrics)

    return enriched, metrics
```

- [ ] **步骤 4：运行测试验证通过**

```bash
python -m pytest scripts/tests/test_stage2_enrich.py -v
```

预期：全部测试 PASS。

- [ ] **步骤 5：提交**

```bash
git add scripts/kp_pipeline/stage2_enrich.py scripts/tests/test_stage2_enrich.py
git commit -m "feat(kp-pipeline): 实现 Stage 2 直联路径富化引擎"
```

---

### 阶段 4：Stage 3 — 验证与人工审核门控

#### 任务 6：实现 Stage 3 验证引擎

**文件：**
- 创建: `scripts/kp_pipeline/stage3_validate.py`
- 创建: `scripts/tests/test_stage3_validate.py`

- [ ] **步骤 1：编写 Stage 3 单元测试**

```python
# scripts/tests/test_stage3_validate.py
import pytest
from scripts.kp_pipeline.stage3_validate import (
    validate_candidate,
    classify_auto_decision,
    format_review_table,
)


def test_validate_candidate_valid():
    candidate = {
        "name": "John Smith",
        "role_context": "Managing Director",
        "source_url": "https://example.com/team",
        "score": 80,
        "best_email": "john.smith@example.com",
    }
    rules = {
        "require_source_link": True,
        "require_confidence_note": True,
        "min_name_length": 4,
        "max_name_length": 50,
        "reject_common_false_positives": ["Contact", "Dining"],
    }
    result = validate_candidate(candidate, rules)
    assert result["valid"] is True
    assert len(result["issues"]) == 0


def test_validate_candidate_rejects_false_positive():
    candidate = {
        "name": "Contact",
        "role_context": "Team",
        "source_url": "https://example.com",
        "score": 50,
    }
    rules = {
        "require_source_link": True,
        "require_confidence_note": True,
        "min_name_length": 4,
        "max_name_length": 50,
        "reject_common_false_positives": ["Contact", "Dining"],
    }
    result = validate_candidate(candidate, rules)
    assert result["valid"] is False
    assert any("false positive" in i.lower() for i in result["issues"])


def test_validate_candidate_rejects_missing_source():
    candidate = {
        "name": "John Smith",
        "role_context": "Director",
        "source_url": "",
        "score": 80,
    }
    rules = {
        "require_source_link": True,
        "require_confidence_note": True,
        "min_name_length": 4,
        "max_name_length": 50,
        "reject_common_false_positives": [],
    }
    result = validate_candidate(candidate, rules)
    assert result["valid"] is False


def test_classify_auto_decision_auto_approve():
    candidate = {"score": 90, "name": "John Smith"}
    config = {
        "auto_approve_threshold": 85,
        "auto_reject_threshold": 30,
        "human_review_range": [30, 85],
    }
    decision = classify_auto_decision(candidate, config, is_valid=True)
    assert decision == "auto_approve"


def test_classify_auto_decision_auto_reject():
    candidate = {"score": 20, "name": "John Smith"}
    config = {
        "auto_approve_threshold": 85,
        "auto_reject_threshold": 30,
        "human_review_range": [30, 85],
    }
    decision = classify_auto_decision(candidate, config, is_valid=False)
    assert decision == "auto_reject"


def test_classify_auto_decision_human_review():
    candidate = {"score": 60, "name": "John Smith"}
    config = {
        "auto_approve_threshold": 85,
        "auto_reject_threshold": 30,
        "human_review_range": [30, 85],
    }
    decision = classify_auto_decision(candidate, config, is_valid=True)
    assert decision == "human_review"


def test_format_review_table():
    candidates = [
        {"name": "John Smith", "score": 80, "decision": "human_review"},
        {"name": "Jane Doe", "score": 90, "decision": "auto_approve"},
    ]
    table = format_review_table(candidates)
    assert "John Smith" in table
    assert "Jane Doe" in table
```

- [ ] **步骤 2：运行测试验证失败**

```bash
python -m pytest scripts/tests/test_stage3_validate.py -v
```

预期：FAIL，报 "ModuleNotFoundError"

- [ ] **步骤 3：实现 Stage 3 验证引擎**

```python
# scripts/kp_pipeline/stage3_validate.py
"""
Stage 3: 验证与人工审核门控

验证 KP 候选人，应用自动批准/拒绝规则，
将剩余候选人格式化供人工审核。
"""
from datetime import datetime


FALSE_POSITIVE_NAMES = {
    "contact", "dining", "menu", "home", "about", "team", "leadership",
    "management", "staff", "people", "careers", "our team", "the team",
    "our people", "meet the", "read more", "learn more", "find out",
    "get in", "click here", "sign up", "subscribe", "privacy", "terms",
}


def validate_candidate(candidate, rules):
    """根据规则验证单个 KP 候选人。"""
    issues = []

    name = (candidate.get("name") or "").strip()
    source_url = (candidate.get("source_url") or "").strip()

    # 检查误报
    reject_list = rules.get("reject_common_false_positives", [])
    reject_set = {fp.lower() for fp in reject_list} | FALSE_POSITIVE_NAMES
    if name.lower() in reject_set:
        issues.append(f"Rejected as false positive: '{name}'")

    # 检查名字长度
    min_len = rules.get("min_name_length", 4)
    max_len = rules.get("max_name_length", 50)
    if len(name) < min_len:
        issues.append(f"Name too short: '{name}' ({len(name)} < {min_len})")
    if len(name) > max_len:
        issues.append(f"Name too long: '{name}' ({len(name)} > {max_len})")

    # 检查来源链接
    if rules.get("require_source_link", True) and not source_url:
        issues.append("Missing source link")

    # 检查置信度说明
    if rules.get("require_confidence_note", True):
        if not candidate.get("role_context") and not candidate.get("directness"):
            issues.append("Missing confidence/role context")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


def classify_auto_decision(candidate, config, is_valid):
    """将候选人分类为 auto_approve、auto_reject 或 human_review。"""
    score = candidate.get("score", 0)
    approve_threshold = config.get("auto_approve_threshold", 85)
    reject_threshold = config.get("auto_reject_threshold", 30)

    if not is_valid:
        return "auto_reject"

    if score >= approve_threshold:
        return "auto_approve"

    if score < reject_threshold:
        return "auto_reject"

    return "human_review"


def format_review_table(candidates):
    """将候选人格式化为 markdown 表格供人工审核。"""
    if not candidates:
        return "没有需要审核的候选人。"

    lines = [
        "| # | 姓名 | 职位/角色 | 评分 | 决策 | 邮箱 | 电话 | 来源 |",
        "|---|------|----------|------|------|------|------|------|",
    ]

    for i, c in enumerate(candidates, 1):
        lines.append(
            f"| {i} | {c.get('name', '')} | {c.get('role_context', '')} | "
            f"{c.get('score', '')} | {c.get('decision', '')} | "
            f"{c.get('best_email', '')} | {c.get('best_phone', '')} | "
            f"{c.get('source_url', '')} |"
        )

    return "\n".join(lines)


def run_stage3(candidates, config):
    """对候选人列表运行 Stage 3 验证。"""
    from .config import get_stage_config
    from .metrics import log_run_metrics, log_validation_decision

    stage_config = get_stage_config(config, "stage3_validate")
    if not stage_config.get("enabled", True):
        return {"skipped": True}

    run_id = f"S3-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    rules = stage_config.get("validation_rules", {})

    auto_approved = []
    auto_rejected = []
    human_review = []

    for candidate in candidates:
        validation = validate_candidate(candidate, rules)
        decision = classify_auto_decision(candidate, stage_config, validation["valid"])
        candidate["decision"] = decision
        candidate["validation_issues"] = validation["issues"]

        if decision == "auto_approve":
            auto_approved.append(candidate)
        elif decision == "auto_reject":
            auto_rejected.append(candidate)
        else:
            human_review.append(candidate)

    metrics = {
        "total_candidates": len(candidates),
        "auto_approved": len(auto_approved),
        "auto_rejected": len(auto_rejected),
        "human_review": len(human_review),
        "auto_approve_rate": round(len(auto_approved) / max(len(candidates), 1), 3),
    }
    log_run_metrics(run_id, "stage3_validate", metrics)

    return {
        "auto_approved": auto_approved,
        "auto_rejected": auto_rejected,
        "human_review": human_review,
        "review_table": format_review_table(human_review),
        "metrics": metrics,
    }
```

- [ ] **步骤 4：运行测试验证通过**

```bash
python -m pytest scripts/tests/test_stage3_validate.py -v
```

预期：全部测试 PASS。

- [ ] **步骤 5：提交**

```bash
git add scripts/kp_pipeline/stage3_validate.py scripts/tests/test_stage3_validate.py
git commit -m "feat(kp-pipeline): 实现 Stage 3 验证和人工审核门控"
```

---

### 阶段 5：管线编排器

#### 任务 7：构建管线编排器

**文件：**
- 创建: `scripts/kp_pipeline/run_pipeline.py`

- [ ] **步骤 1：实现管线编排器**

```python
# scripts/kp_pipeline/run_pipeline.py
"""
KP 半自动化管线编排器

运行三阶段管线：
1. 从官网发现 KP 候选人
2. 用直联路径富化
3. 验证并分流到自动批准或人工审核

用法：
    python -m scripts.kp_pipeline.run_pipeline --leads data/leads.csv --limit 10
    python -m scripts.kp_pipeline.run_pipeline --leads data/leads.csv --country Australia --stage 1
"""
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

from .config import load_config, get_stage_config
from .metrics import log_run_metrics, compute_accuracy_metrics
from .stage1_discover import run_stage1
from .stage2_enrich import run_stage2
from .stage3_validate import run_stage3

PROJECT_ROOT = Path(__file__).parent.parent.parent
REPORTS = PROJECT_ROOT / "reports"


def read_leads(path, country=None, limit=None):
    """读取线索 CSV，可选按国家过滤。"""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if country:
        rows = [r for r in rows if r.get("country") == country]

    if limit:
        rows = rows[:limit]

    return rows


def write_report(output_path, results, metrics_all):
    """写入管线运行报告。"""
    lines = [
        "# KP 管线运行报告",
        "",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Stage 1: 发现",
        "",
    ]

    s1 = metrics_all.get("stage1", {})
    lines.extend([
        f"- 处理线索数: {s1.get('leads_processed', 0)}",
        f"- 有候选人的线索数: {s1.get('leads_with_candidates', 0)}",
        f"- 候选人总数: {s1.get('total_candidates', 0)}",
        f"- KP 识别率: {s1.get('kp_identification_rate', 0):.1%}",
        "",
        "## Stage 2: 富化",
        "",
    ])

    s2 = metrics_all.get("stage2", {})
    lines.extend([
        f"- 处理候选人: {s2.get('candidates_processed', 0)}",
        f"- 富化候选人: {s2.get('enriched_candidates', 0)}",
        f"- 发现直联: {s2.get('direct_contacts_found', 0)}",
        f"- 直联率: {s2.get('direct_contact_rate', 0):.1%}",
        "",
        "## Stage 3: 验证",
        "",
    ])

    s3 = results.get("stage3", {})
    s3m = s3.get("metrics", {})
    lines.extend([
        f"- 候选人总数: {s3m.get('total_candidates', 0)}",
        f"- 自动批准: {s3m.get('auto_approved', 0)}",
        f"- 自动拒绝: {s3m.get('auto_rejected', 0)}",
        f"- 需人工审核: {s3m.get('human_review', 0)}",
        "",
        "## 人工审核候选人",
        "",
    ])

    review_table = s3.get("review_table", "无")
    lines.append(review_table)

    lines.extend([
        "",
        "## 自动化门槛状态",
        "",
    ])

    accuracy = compute_accuracy_metrics()
    if accuracy:
        lines.extend([
            f"- 历史决策总数: {accuracy.get('total_decisions', 0)}",
            f"- 准确率: {accuracy.get('accuracy_rate', 0):.1%}",
            f"- 误报率: {accuracy.get('false_positive_rate', 0):.1%}",
        ])
    else:
        lines.append("- 尚无验证历史。运行人工审核以建立准确率基线。")

    lines.extend([
        "",
        "## 下一步",
        "",
        "1. 审核上方的人工审核候选人",
        "2. 使用 `log_validation_decision()` 记录决策",
        "3. 积累足够数据后，检查自动化门槛条件",
        "",
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_candidates_csv(output_path, candidates):
    """将候选人写入 CSV 供审核。"""
    if not candidates:
        return

    fields = [
        "name", "company_name", "role_context", "score", "decision",
        "best_email", "best_phone", "source_url", "directness",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(candidates)


def main():
    parser = argparse.ArgumentParser(description="运行 KP 半自动化管线。")
    parser.add_argument("--leads", default="data/leads.csv", help="线索 CSV 路径。")
    parser.add_argument("--country", default="Australia", help="按国家过滤线索。")
    parser.add_argument("--limit", type=int, default=10, help="最大处理线索数。")
    parser.add_argument("--stage", choices=["1", "2", "3", "all"], default="all",
                        help="运行哪个阶段（默认：all）。")
    parser.add_argument("--config", default="", help="管线配置 JSON 路径。")
    parser.add_argument("--output-prefix", default="", help="报告输出前缀。")
    args = parser.parse_args()

    config = load_config(args.config if args.config else None)
    leads = read_leads(args.leads, args.country, args.limit)

    if not leads:
        print("未找到符合条件的线索。")
        return

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    prefix = Path(args.output_prefix) if args.output_prefix else REPORTS / f"kp-pipeline-run-{ts}"

    print(f"处理 {len(leads)} 条线索...")
    print(f"配置: {args.config or '默认'}")
    print(f"阶段: {args.stage}")
    print()

    results = {}
    metrics_all = {}

    # Stage 1: 发现
    if args.stage in ("1", "all"):
        print("=== Stage 1: KP 发现 ===")
        candidates_s1, metrics_s1 = run_stage1(leads, config, limit=args.limit)
        results["stage1_candidates"] = candidates_s1
        metrics_all["stage1"] = metrics_s1
        print(f"  处理线索: {metrics_s1.get('leads_processed', 0)}")
        print(f"  发现候选人: {metrics_s1.get('total_candidates', 0)}")
        print(f"  KP 率: {metrics_s1.get('kp_identification_rate', 0):.1%}")
        print()

    # Stage 2: 富化
    if args.stage in ("2", "all"):
        print("=== Stage 2: 直联路径富化 ===")
        s1_candidates = results.get("stage1_candidates", [])
        if not s1_candidates:
            print("  Stage 1 无候选人，跳过。")
            metrics_all["stage2"] = {"skipped": True, "reason": "no_candidates"}
        else:
            enriched, metrics_s2 = run_stage2(s1_candidates, config)
            results["stage2_enriched"] = enriched
            metrics_all["stage2"] = metrics_s2
            print(f"  富化: {metrics_s2.get('enriched_candidates', 0)}")
            print(f"  直联: {metrics_s2.get('direct_contacts_found', 0)}")
            print()

    # Stage 3: 验证
    if args.stage in ("3", "all"):
        print("=== Stage 3: 验证 ===")
        s2_candidates = results.get("stage2_enriched", results.get("stage1_candidates", []))
        if not s2_candidates:
            print("  无候选人可验证，跳过。")
            results["stage3"] = {"metrics": {"total_candidates": 0}}
        else:
            stage3_results = run_stage3(s2_candidates, config)
            results["stage3"] = stage3_results
            s3m = stage3_results.get("metrics", {})
            print(f"  自动批准: {s3m.get('auto_approved', 0)}")
            print(f"  自动拒绝: {s3m.get('auto_rejected', 0)}")
            print(f"  人工审核: {s3m.get('human_review', 0)}")
            print()

    # 写入输出
    report_path = prefix.with_suffix(".md")
    write_report(report_path, results, metrics_all)
    print(f"报告: {report_path}")

    all_candidates = results.get("stage2_enriched", results.get("stage1_candidates", []))
    if all_candidates:
        csv_path = prefix.with_suffix(".csv")
        write_candidates_csv(csv_path, all_candidates)
        print(f"候选人 CSV: {csv_path}")

    print("\n完成。")


if __name__ == "__main__":
    main()
```

- [ ] **步骤 2：测试管线 dry run**

```bash
cd E:\AI\TestProject-v2
python -m scripts.kp_pipeline.run_pipeline --leads data/leads.csv --country Australia --limit 3 --stage 1
```

预期：生成包含 Stage 1 指标的报告。

- [ ] **步骤 3：提交**

```bash
git add scripts/kp_pipeline/run_pipeline.py
git commit -m "feat(kp-pipeline): 添加三阶段管线编排器"
```

---

### 阶段 6：测试与校准

#### 任务 8：在真实数据上运行集成测试

**文件：**
- 创建: `scripts/tests/test_kp_pipeline.py`

- [ ] **步骤 1：编写集成测试**

```python
# scripts/tests/test_kp_pipeline.py
"""KP 管线集成测试。"""
import pytest
from scripts.kp_pipeline.config import load_config, get_stage_config
from scripts.kp_pipeline.stage1_discover import clean_company_name, extract_kp_candidates_from_text, score_candidate
from scripts.kp_pipeline.stage2_enrich import classify_email, classify_contact_directness
from scripts.kp_pipeline.stage3_validate import validate_candidate, classify_auto_decision


def test_full_pipeline_flow():
    """用合成数据测试完整管线流程。"""
    # Stage 1: 模拟发现
    page_text = """
    About Us
    Founded in 2010, Test Restaurant Group has grown to become one of
    Sydney's leading hospitality groups.

    Our Leadership
    Michael Chen - Managing Director
    Sarah Williams - Operations Manager
    David Park - Head Chef

    Contact us at info@testrestaurant.com.au
    """

    candidates = extract_kp_candidates_from_text(page_text, "https://testrestaurant.com.au/about")
    assert len(candidates) >= 2

    for c in candidates:
        c["score"] = score_candidate(c["name"], c["role_context"], c["source_url"])

    # Stage 3: 验证
    rules = {
        "require_source_link": True,
        "require_confidence_note": True,
        "min_name_length": 4,
        "max_name_length": 50,
        "reject_common_false_positives": ["Contact", "Dining"],
    }
    config = {
        "auto_approve_threshold": 85,
        "auto_reject_threshold": 30,
        "human_review_range": [30, 85],
    }

    for c in candidates:
        validation = validate_candidate(c, rules)
        decision = classify_auto_decision(c, config, validation["valid"])
        c["decision"] = decision
        c["valid"] = validation["valid"]

    # 检查高分候选人被自动批准
    md = next((c for c in candidates if "Managing Director" in c.get("role_context", "")), None)
    if md:
        assert md["decision"] == "auto_approve", f"Managing Director 应被自动批准，实际: {md['decision']}"
```

- [ ] **步骤 2：运行所有测试**

```bash
cd E:\AI\TestProject-v2
python -m pytest scripts/tests/ -v
```

预期：全部测试 PASS。

- [ ] **步骤 3：提交**

```bash
git add scripts/tests/test_kp_pipeline.py
git commit -m "test(kp-pipeline): 添加完整管线流程集成测试"
```

---

#### 任务 9：校准运行与指标基线

- [ ] **步骤 1：在 10 条真实线索上运行管线**

```bash
cd E:\AI\TestProject-v2
python -m scripts.kp_pipeline.run_pipeline --leads data/leads.csv --country Australia --limit 10 --stage all
```

- [ ] **步骤 2：审核报告并记录基线指标**

运行后记录：
- KP 识别率（目标: >50%）
- 直联获取率（目标: >10%）
- 自动批准准确率（人工验证）

- [ ] **步骤 3：在 30 条线索上运行以获得统计显著性**

```bash
python -m scripts.kp_pipeline.run_pipeline --leads data/leads.csv --country Australia --limit 30 --stage all
```

- [ ] **步骤 4：提交结果**

```bash
git add reports/kp-pipeline-run-*.md reports/kp-pipeline-run-*.csv data/kp_metrics.json
git commit -m "docs(kp-pipeline): 添加校准运行结果和基线指标"
```

---

## 四、自动化门槛评估

完成阶段 6 后，评估自动化就绪程度：

### 门槛 1：Stage 1 自动运行
**条件:** `误报率 < 0.15 且 KP 识别率 > 0.5`
**检查:** 运行 `compute_accuracy_metrics()` 并审核 Stage 1 指标。
**达标:** Stage 1 可在新线索上无人监督运行。
**未达标:** 继续人工审核 Stage 1 输出；改进 `extract_kp_candidates_from_text()` 过滤器。

### 门槛 2：Stage 2 自动运行
**条件:** `直联率 > 0.1 且 误报率 < 0.1`
**检查:** 审核 Stage 2 富化指标。
**达标:** Stage 2 可在 Stage 1 之后自动运行。
**未达标:** 增加更多富化模式；考虑集成 Tavily 做深度搜索。

### 门槛 3：Stage 3 自动批准
**条件:** `自动批准准确率 > 0.95`（通过人工抽检验证）
**检查:** 将自动批准的候选人与人工验证日志对比。
**达标:** 高置信度候选人自动保存到 `contacts.csv`。
**未达标:** 保持所有候选人在人工审核中；收紧 `auto_approve_threshold`。

### 完整管线自动化
**当三个门槛全部通过时：**
1. Stage 1 在新线索上自动运行
2. Stage 2 自动富化已发现的 KP 名字
3. Stage 3 自动批准高置信度结果
4. 人工仅审核中间带候选人（30-85 分）
5. 每周抽检自动批准的结果

**预计达到全自动的时间线：**
- 阶段 1-2（基础设施 + Stage 1）：1-2 周
- 阶段 3-4（Stage 2 + Stage 3）：1-2 周
- 阶段 5-6（编排器 + 校准）：1 周
- 门槛评估：处理 100+ 条线索后
- 完全自动化：迭代 3-4 周后

---

## 五、总结

| 阶段 | 内容 | 自动化程度 |
|------|------|-----------|
| 阶段 1 | 指标与测试基础设施 | 手动搭建 |
| 阶段 2 | Stage 1: KP 发现 | 半自动（需审核） |
| 阶段 3 | Stage 2: 直联路径富化 | 半自动（需审核） |
| 阶段 4 | Stage 3: 验证门控 | 半自动（人工审核中间带） |
| 阶段 5 | 管线编排器 | 半自动（CLI 执行） |
| 阶段 6 | 校准与门槛评估 | 手动评估 |

**最终状态:** 一套 CLI 管线，批量处理线索，发现 KP 候选人，富化直联路径，通过验证门控分流结果。人工仅需审核中等置信度候选人。高置信度结果自动保存；低置信度结果自动拒绝。随着准确率提升，自动化门槛逐步解锁。
