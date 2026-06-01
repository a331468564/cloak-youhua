# Keyword Scheduler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bridge the disconnected keyword management CSV to the search pipeline, enabling automated keyword selection, query generation, execution, result tracking, and market-intelligence-driven keyword discovery — without modifying any existing pipeline stage code.

**Architecture:** A new `scripts/keyword_scheduler/` module reads `data/search_keywords.csv`, selects eligible keywords (respecting cooldown, priority, status), expands template patterns into concrete queries, delegates search execution to the existing `extract_public_contact_candidates.py`, and writes results back to `keyword_runs.csv` and `search_keywords.csv`. A market intelligence submodule analyzes historical run data to identify high-performing keyword patterns, discover untapped market segments, and auto-suggest new keywords. The pipeline orchestrator (`run_pipeline.py`) gains an optional `--keyword-driven` flag that runs the scheduler before Stage 1.

**Tech Stack:** Python 3.14, existing Scrapling/CloakBrowser fetchers, CSV I/O, subprocess calls to existing extraction scripts.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `scripts/keyword_scheduler/__init__.py` | Create | Package marker |
| `scripts/keyword_scheduler/scheduler.py` | Create | Core logic: read keywords, select eligible, expand templates, build query queue |
| `scripts/keyword_scheduler/executor.py` | Create | Execute search queries by calling `extract_public_contact_candidates.py`, collect results |
| `scripts/keyword_scheduler/tracker.py` | Create | Write results back to `keyword_runs.csv` and `search_keywords.csv` |
| `scripts/keyword_scheduler/config.py` | Create | Load scheduler config from `config/keyword_scheduler.json` |
| `config/keyword_scheduler.json` | Create | Scheduler settings: cooldown enforcement, priority weights, expansion defaults |
| `tests/test_scheduler.py` | Create | Unit tests for scheduler logic (keyword selection, template expansion, cooldown) |
| `tests/test_tracker.py` | Create | Unit tests for result tracking (CSV writes, score updates) |
| `tests/test_executor.py` | Create | Integration test for executor (mock subprocess calls) |
| `scripts/kp_pipeline/run_pipeline.py:70` | Modify | Add `--keyword-driven` flag that runs scheduler before Stage 1 |
| `scripts/keyword_scheduler/market_intel.py` | Create | Analyze keyword performance, discover market segments, score and rank generated candidates |
| `tests/test_market_intel.py` | Create | Unit tests for market analysis and candidate scoring |
| `scripts/keyword_scheduler/generator.py` | Create | Multi-dimensional keyword generation from templates × dimensions |
| `tests/test_generator.py` | Create | Unit tests for generator: multi-template, dedup, cap, metadata |
| `config/keyword_dimensions.json` | Create | Dimension values and query templates for keyword generation |
| `scripts/keyword_scheduler/import_suggestions.py` | Create | Import approved suggestions into search_keywords.csv with dedup |
| `tests/test_import_suggestions.py` | Create | Unit tests for import: approved-only, ID generation, dedup, defaults |

---

## Key Design Decisions

1. **No modification to existing extraction scripts.** The scheduler calls `extract_public_contact_candidates.py` as a subprocess (same pattern as `run_pipeline.py` Stage 1). This keeps the blast radius minimal.

2. **Template expansion is declarative.** Template keywords with `[city]` and `[country]` placeholders are expanded using a config-driven mapping, not hardcoded logic. New city/country combos are added to config, not code.

3. **Cooldown is enforced at read time.** When the scheduler reads `search_keywords.csv`, it immediately filters out keywords where `next_allowed_at` > now. No separate lock file or state machine needed.

4. **Results are append-only.** `keyword_runs.csv` gets new rows appended. `search_keywords.csv` columns (`total_runs`, `last_used_at`, `next_allowed_at`, etc.) are updated in-place on the matching `keyword_id` row.

5. **The scheduler is idempotent.** Running it twice with the same inputs produces the same query queue. Duplicate prevention uses the same `--skip-existing` flag that the extraction script already supports.

---

### Task 1: Create Package Skeleton and Config

**Files:**
- Create: `scripts/keyword_scheduler/__init__.py`
- Create: `scripts/keyword_scheduler/config.py`
- Create: `config/keyword_scheduler.json`

- [ ] **Step 1: Create package init**

```python
# scripts/keyword_scheduler/__init__.py
"""Keyword scheduler — bridges search_keywords.csv to the extraction pipeline."""
```

- [ ] **Step 2: Create scheduler config JSON**

```json
{
  "version": "1.0",
  "cooldown_enforcement": true,
  "default_cooldown_days": 14,
  "default_country": "Australia",
  "template_expansions": {
    "[city]": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast", "Canberra", "Hobart"],
    "[country]": ["Australia"]
  },
  "priority_weights": {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.4
  },
  "max_keywords_per_run": 5,
  "extraction_defaults": {
    "follow_links": 2,
    "fetcher": "static",
    "delay": 2,
    "skip_existing": true
  }
}
```

- [ ] **Step 3: Create config loader**

```python
# scripts/keyword_scheduler/config.py
import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "keyword_scheduler.json"

def load_config() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_template_expansions(config: dict) -> dict[str, list[str]]:
    return config.get("template_expansions", {})

def get_extraction_defaults(config: dict) -> dict:
    return config.get("extraction_defaults", {})
```

- [ ] **Step 4: Verify files exist and config loads**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -c "from scripts.keyword_scheduler.config import load_config; print(load_config())"`
Expected: JSON dict printed with no errors.

- [ ] **Step 5: Commit**

```bash
git add scripts/keyword_scheduler/__init__.py scripts/keyword_scheduler/config.py config/keyword_scheduler.json
git commit -m "feat: add keyword scheduler package skeleton and config"
```

---

### Task 2: Implement Keyword Selection Logic

**Files:**
- Create: `scripts/keyword_scheduler/scheduler.py`
- Create: `tests/test_scheduler.py`

- [ ] **Step 1: Write failing test for keyword selection**

```python
# tests/test_scheduler.py
import csv
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

def _make_keywords_csv(rows: list[dict], path: Path):
    """Helper: write a minimal search_keywords.csv."""
    fieldnames = [
        "keyword_id", "keyword_pattern", "keyword_status", "priority_level",
        "country_or_region", "city", "keyword_intent_type", "search_intent",
        "last_used_at", "next_allowed_at", "cooldown_days", "total_runs",
        "discovery_quality_score", "contactability_score"
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({fn: row.get(fn, "") for fn in fieldnames})


def test_select_eligible_keywords_respects_cooldown():
    """Keywords with next_allowed_at in the future should be excluded."""
    from scripts.keyword_scheduler.scheduler import select_eligible_keywords

    now = datetime.now()
    rows = [
        {
            "keyword_id": "KW-0001",
            "keyword_pattern": "restaurant group [country] contact",
            "keyword_status": "Active",
            "priority_level": "high",
            "country_or_region": "Australia",
            "city": "",
            "keyword_intent_type": "Discovery",
            "search_intent": "Find new leads",
            "last_used_at": (now - timedelta(days=20)).isoformat(),
            "next_allowed_at": (now - timedelta(days=1)).isoformat(),
            "cooldown_days": "14",
            "total_runs": "3",
            "discovery_quality_score": "0.8",
            "contactability_score": "0.6",
        },
        {
            "keyword_id": "KW-0002",
            "keyword_pattern": "hotel procurement [city]",
            "keyword_status": "Active",
            "priority_level": "medium",
            "country_or_region": "Australia",
            "city": "",
            "keyword_intent_type": "Discovery",
            "search_intent": "Find hotels",
            "last_used_at": now.isoformat(),
            "next_allowed_at": (now + timedelta(days=12)).isoformat(),
            "cooldown_days": "14",
            "total_runs": "1",
            "discovery_quality_score": "0.5",
            "contactability_score": "0.4",
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "search_keywords.csv"
        _make_keywords_csv(rows, csv_path)
        config = {"cooldown_enforcement": True, "max_keywords_per_run": 10}
        eligible = select_eligible_keywords(csv_path, config)
        ids = [kw["keyword_id"] for kw in eligible]
        assert "KW-0001" in ids
        assert "KW-0002" not in ids


def test_select_eligible_keywords_respects_status():
    """Keywords with status 'Paused' or 'Archived' should be excluded."""
    from scripts.keyword_scheduler.scheduler import select_eligible_keywords

    rows = [
        {
            "keyword_id": "KW-0010",
            "keyword_pattern": "test query",
            "keyword_status": "Paused",
            "priority_level": "high",
            "country_or_region": "Australia",
            "city": "",
            "keyword_intent_type": "Discovery",
            "search_intent": "test",
            "last_used_at": "",
            "next_allowed_at": "",
            "cooldown_days": "14",
            "total_runs": "0",
            "discovery_quality_score": "",
            "contactability_score": "",
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "search_keywords.csv"
        _make_keywords_csv(rows, csv_path)
        config = {"cooldown_enforcement": True, "max_keywords_per_run": 10}
        eligible = select_eligible_keywords(csv_path, config)
        assert len(eligible) == 0


def test_select_eligible_keywords_prioritizes_high():
    """High-priority keywords should come before medium/low."""
    from scripts.keyword_scheduler.scheduler import select_eligible_keywords

    rows = [
        {
            "keyword_id": "KW-LOW",
            "keyword_pattern": "low priority",
            "keyword_status": "Active",
            "priority_level": "low",
            "country_or_region": "Australia",
            "city": "",
            "keyword_intent_type": "Discovery",
            "search_intent": "",
            "last_used_at": "",
            "next_allowed_at": "",
            "cooldown_days": "14",
            "total_runs": "0",
            "discovery_quality_score": "",
            "contactability_score": "",
        },
        {
            "keyword_id": "KW-HIGH",
            "keyword_pattern": "high priority",
            "keyword_status": "Active",
            "priority_level": "high",
            "country_or_region": "Australia",
            "city": "",
            "keyword_intent_type": "Discovery",
            "search_intent": "",
            "last_used_at": "",
            "next_allowed_at": "",
            "cooldown_days": "14",
            "total_runs": "0",
            "discovery_quality_score": "",
            "contactability_score": "",
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "search_keywords.csv"
        _make_keywords_csv(rows, csv_path)
        config = {"cooldown_enforcement": True, "max_keywords_per_run": 10,
                  "priority_weights": {"high": 1.0, "medium": 0.7, "low": 0.4}}
        eligible = select_eligible_keywords(csv_path, config)
        assert eligible[0]["keyword_id"] == "KW-HIGH"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m pytest tests/test_scheduler.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.keyword_scheduler.scheduler'`

- [ ] **Step 3: Implement scheduler.py**

```python
# scripts/keyword_scheduler/scheduler.py
"""Keyword selection and template expansion."""

import csv
from datetime import datetime
from pathlib import Path

_ACTIVE_STATUSES = {"Active", "Testing", "New"}

def select_eligible_keywords(keywords_csv: Path, config: dict) -> list[dict]:
    """Read keywords CSV, filter by status and cooldown, sort by priority.

    Returns list of keyword dicts sorted by priority (high > medium > low),
    then by discovery_quality_score descending.
    """
    enforce_cooldown = config.get("cooldown_enforcement", True)
    max_kw = config.get("max_keywords_per_run", 5)
    priority_weights = config.get("priority_weights", {"high": 1.0, "medium": 0.7, "low": 0.4})
    now = datetime.now()

    rows = []
    with open(keywords_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = (row.get("keyword_status") or "").strip()
            if status not in _ACTIVE_STATUSES:
                continue

            if enforce_cooldown:
                next_allowed = (row.get("next_allowed_at") or "").strip()
                if next_allowed:
                    try:
                        if datetime.fromisoformat(next_allowed) > now:
                            continue
                    except ValueError:
                        pass  # malformed date — allow the keyword

            rows.append(row)

    def _sort_key(kw: dict) -> tuple[float, float]:
        priority = (kw.get("priority_level") or "low").strip().lower()
        weight = priority_weights.get(priority, 0.0)
        try:
            quality = float(kw.get("discovery_quality_score") or 0)
        except ValueError:
            quality = 0.0
        return (-weight, -quality)  # negative for descending

    rows.sort(key=_sort_key)
    return rows[:max_kw]


def expand_templates(keywords: list[dict], expansions: dict[str, list[str]]) -> list[dict]:
    """Expand template placeholders like [city] into concrete queries.

    Returns a new list where each template keyword is duplicated per expansion value.
    Non-template keywords are passed through unchanged.
    """
    expanded = []
    for kw in keywords:
        pattern = kw.get("keyword_pattern") or ""
        has_template = any(placeholder in pattern for placeholder in expansions)

        if not has_template:
            expanded.append(kw)
            continue

        # Find all placeholders present in this pattern
        applicable = {p: vals for p, vals in expansions.items() if p in pattern}

        # For simplicity: expand the first placeholder found (single-level expansion)
        # Multi-placeholder patterns (e.g. [city] [country]) get cartesian product
        # via recursive expansion
        _expand_recursive(kw, pattern, list(applicable.items()), expanded)

    return expanded


def _expand_recursive(kw: dict, pattern: str, placeholders: list[tuple[str, list[str]]], out: list[dict]):
    """Recursively expand all placeholders in a keyword pattern."""
    if not placeholders:
        expanded_kw = kw.copy()
        expanded_kw["keyword_pattern"] = pattern
        out.append(expanded_kw)
        return

    placeholder, values = placeholders[0]
    remaining = placeholders[1:]
    for val in values:
        new_pattern = pattern.replace(placeholder, val, 1)
        # If the same placeholder appears multiple times, replace all
        while placeholder in new_pattern:
            new_pattern = new_pattern.replace(placeholder, val, 1)
        _expand_recursive(kw, new_pattern, remaining, out)


def build_query_queue(keywords_csv: Path, config: dict) -> list[dict]:
    """Main entry: select eligible keywords, expand templates, return query queue.

    Each item in the returned list has:
      - keyword_id: original keyword ID (may be shared across expansions)
      - keyword_pattern: expanded concrete query string
      - source_query: the pattern to use as search input
      - keyword_intent_type, search_intent, country_or_region, city: metadata
    """
    eligible = select_eligible_keywords(keywords_csv, config)
    expansions = config.get("template_expansions", {})
    expanded = expand_templates(eligible, expansions)

    queue = []
    for kw in expanded:
        queue.append({
            "keyword_id": kw.get("keyword_id", ""),
            "keyword_pattern": kw.get("keyword_pattern", ""),
            "source_query": kw.get("keyword_pattern", ""),
            "keyword_intent_type": kw.get("keyword_intent_type", ""),
            "search_intent": kw.get("search_intent", ""),
            "country_or_region": kw.get("country_or_region", ""),
            "city": kw.get("city", ""),
        })
    return queue
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m pytest tests/test_scheduler.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/keyword_scheduler/scheduler.py tests/test_scheduler.py
git commit -m "feat: implement keyword selection and template expansion logic"
```

---

### Task 3: Implement Result Tracker

**Files:**
- Create: `scripts/keyword_scheduler/tracker.py`
- Create: `tests/test_tracker.py`

- [ ] **Step 1: Write failing test for tracker**

```python
# tests/test_tracker.py
import csv
import tempfile
from pathlib import Path
from datetime import datetime

def _make_keywords_csv(path: Path):
    fieldnames = [
        "keyword_id", "keyword_pattern", "keyword_status", "priority_level",
        "country_or_region", "city", "total_runs", "total_leads_collected",
        "ready_to_contact_count", "contact_found_count", "last_used_at",
        "next_allowed_at", "cooldown_days", "discovery_quality_score",
        "contactability_score", "used_recently"
    ]
    rows = [
        {fn: "" for fn in fieldnames} | {
            "keyword_id": "KW-0001",
            "keyword_pattern": "restaurant group Australia contact",
            "keyword_status": "Active",
            "total_runs": "3",
            "total_leads_collected": "7",
            "cooldown_days": "14",
        },
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _make_runs_csv(path: Path):
    fieldnames = [
        "batch_id", "run_id", "keyword_id", "keyword_source_query",
        "collection_round", "run_date", "target_leads_count",
        "actual_leads_collected", "ready_to_contact_count",
        "contact_found_count", "direct_key_contact_count",
        "company_contact_only_count", "duplicate_count", "news_only_count",
        "no_contact_count", "discovery_quality_score", "contactability_score",
        "run_status"
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()


def test_update_keywords_csv_increments_runs():
    """After a run, total_runs should increment and last_used_at should update."""
    from scripts.keyword_scheduler.tracker import update_keyword_stats

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "search_keywords.csv"
        _make_keywords_csv(csv_path)

        update_keyword_stats(csv_path, "KW-0001", leads_collected=3, contacts_found=1)

        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        assert row["total_runs"] == "4"
        assert row["total_leads_collected"] == "10"
        assert row["contact_found_count"] == "1"
        assert row["last_used_at"] != ""
        assert row["next_allowed_at"] != ""


def test_append_run_log():
    """New run results should be appended to keyword_runs.csv."""
    from scripts.keyword_scheduler.tracker import append_run_log

    with tempfile.TemporaryDirectory() as tmpdir:
        runs_path = Path(tmpdir) / "keyword_runs.csv"
        _make_runs_csv(runs_path)

        append_run_log(
            runs_path,
            batch_id="BATCH-TEST-001",
            keyword_id="KW-0001",
            keyword_source_query="restaurant group Australia contact",
            leads_collected=3,
            contacts_found=1,
        )

        with open(runs_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["keyword_id"] == "KW-0001"
        assert rows[0]["actual_leads_collected"] == "3"
        assert rows[0]["contact_found_count"] == "1"
        assert rows[0]["run_status"] == "completed"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m pytest tests/test_tracker.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.keyword_scheduler.tracker'`

- [ ] **Step 3: Implement tracker.py**

```python
# scripts/keyword_scheduler/tracker.py
"""Write keyword run results back to CSV files."""

import csv
from datetime import datetime, timedelta
from pathlib import Path

_KEYWORDS_FIELDNAMES = [
    "keyword_id", "target_customer_type", "country_or_region", "city",
    "keyword_pattern", "example_search_query", "search_intent",
    "keyword_intent_type", "priority_level", "keyword_status", "used_recently",
    "last_used_at", "next_allowed_at", "cooldown_days", "discovery_quality_score",
    "contactability_score", "total_runs", "total_leads_collected",
    "ready_to_contact_count", "contact_found_count", "duplicate_count",
    "news_only_count", "no_contact_count", "relevance_ratio",
]

_RUNS_FIELDNAMES = [
    "batch_id", "run_id", "keyword_id", "keyword_source_query",
    "collection_round", "run_date", "target_leads_count",
    "actual_leads_collected", "ready_to_contact_count", "contact_found_count",
    "direct_key_contact_count", "company_contact_only_count", "duplicate_count",
    "news_only_count", "no_contact_count", "discovery_quality_score",
    "contactability_score", "run_status",
]


def update_keyword_stats(
    keywords_csv: Path,
    keyword_id: str,
    leads_collected: int = 0,
    contacts_found: int = 0,
    ready_to_contact: int = 0,
):
    """Update a keyword's aggregate stats in search_keywords.csv after a run."""
    rows = []
    with open(keywords_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("keyword_id") == keyword_id:
                now = datetime.now()
                cooldown = int(row.get("cooldown_days") or 14)
                row["total_runs"] = str(int(row.get("total_runs") or 0) + 1)
                row["total_leads_collected"] = str(
                    int(row.get("total_leads_collected") or 0) + leads_collected
                )
                row["contact_found_count"] = str(
                    int(row.get("contact_found_count") or 0) + contacts_found
                )
                row["ready_to_contact_count"] = str(
                    int(row.get("ready_to_contact_count") or 0) + ready_to_contact
                )
                row["last_used_at"] = now.isoformat()
                row["next_allowed_at"] = (now + timedelta(days=cooldown)).isoformat()
                row["used_recently"] = "Yes"
            rows.append(row)

    with open(keywords_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def append_run_log(
    runs_csv: Path,
    batch_id: str,
    keyword_id: str,
    keyword_source_query: str,
    leads_collected: int = 0,
    contacts_found: int = 0,
    ready_to_contact: int = 0,
):
    """Append a new run entry to keyword_runs.csv."""
    now = datetime.now()
    run_id = f"RUN-{now.strftime('%Y%m%d%H%M%S')}-{keyword_id}"

    row = {
        "batch_id": batch_id,
        "run_id": run_id,
        "keyword_id": keyword_id,
        "keyword_source_query": keyword_source_query,
        "collection_round": "",
        "run_date": now.strftime("%Y-%m-%d %H:%M"),
        "target_leads_count": "",
        "actual_leads_collected": str(leads_collected),
        "ready_to_contact_count": str(ready_to_contact),
        "contact_found_count": str(contacts_found),
        "direct_key_contact_count": "",
        "company_contact_only_count": "",
        "duplicate_count": "",
        "news_only_count": "",
        "no_contact_count": "",
        "discovery_quality_score": "",
        "contactability_score": "",
        "run_status": "completed",
    }

    file_exists = runs_csv.exists()
    with open(runs_csv, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_RUNS_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m pytest tests/test_tracker.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/keyword_scheduler/tracker.py tests/test_tracker.py
git commit -m "feat: implement keyword run result tracking"
```

---

### Task 4: Implement Search Executor

> **STATUS: NOT NEEDED** — executor.py was designed as a bridge between scheduler.py and extract_public_contact_candidates.py, but keyword_discovery.py now handles the entire flow independently (search + extract + write to leads.csv). executor.py was never created and is no longer required. scheduler.py was cleaned up to remove executor imports.

**Files:**
- Create: `scripts/keyword_scheduler/executor.py` (NOT NEEDED)
- Create: `tests/test_executor.py` (NOT NEEDED)

- [ ] **Step 1: Write failing test for executor**

```python
# tests/test_executor.py
import csv
import tempfile
from pathlib import Path

def _make_queue_csv(path: Path, queries: list[str]):
    fieldnames = ["lead_id", "company_name", "website", "query"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, q in enumerate(queries):
            writer.writerow({
                "lead_id": f"KW-{i+1:04d}",
                "company_name": "",
                "website": "",
                "query": q,
            })


def test_build_extraction_queue_creates_csv():
    """executor should write a queue CSV compatible with extract_public_contact_candidates.py."""
    from scripts.keyword_scheduler.executor import build_extraction_queue

    with tempfile.TemporaryDirectory() as tmpdir:
        queue = [
            {"keyword_id": "KW-0001", "source_query": "restaurant group Sydney contact", "keyword_pattern": "restaurant group Sydney contact"},
            {"keyword_id": "KW-0002", "source_query": "hotel procurement Melbourne", "keyword_pattern": "hotel procurement Melbourne"},
        ]
        out_path = Path(tmpdir) / "queue.csv"
        build_extraction_queue(queue, out_path)

        with open(out_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["query"] == "restaurant group Sydney contact"
        assert rows[1]["query"] == "hotel procurement Melbourne"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m pytest tests/test_executor.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement executor.py**

```python
# scripts/keyword_scheduler/executor.py
"""Execute keyword-driven searches via existing extraction scripts."""

import csv
import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_EXTRACTION_SCRIPT = _PROJECT_ROOT / "scripts" / "extraction" / "extract_public_contact_candidates.py"


def build_extraction_queue(query_queue: list[dict], out_path: Path) -> Path:
    """Write a queue CSV that extract_public_contact_candidates.py can consume.

    Each row: lead_id, company_name, website, query
    """
    fieldnames = ["lead_id", "company_name", "website", "query"]
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, item in enumerate(query_queue):
            writer.writerow({
                "lead_id": f"KW-{i+1:04d}",
                "company_name": "",
                "website": "",
                "query": item.get("source_query", ""),
            })
    return out_path


def run_extraction(
    queue_path: Path,
    output_prefix: str = "kw-scheduler-",
    limit: int = 10,
    follow_links: int = 2,
    fetcher: str = "static",
    skip_existing: bool = True,
) -> tuple[int, Path]:
    """Run extract_public_contact_candidates.py on the queue.

    Returns (exit_code, output_csv_path).
    """
    reports_dir = _PROJECT_ROOT / "reports"
    cmd = [
        sys.executable,
        str(_EXTRACTION_SCRIPT),
        "--input", str(queue_path),
        "--output-prefix", str(reports_dir / output_prefix),
        "--limit", str(limit),
        "--follow-links", str(follow_links),
        "--fetcher", fetcher,
        "--delay", "2",
    ]
    if skip_existing:
        cmd.append("--skip-existing")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_PROJECT_ROOT))

    # Find the output CSV
    output_csv = None
    for f in sorted(reports_dir.glob(f"{output_prefix}*.csv"), reverse=True):
        output_csv = f
        break

    return result.returncode, output_csv
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m pytest tests/test_executor.py -v`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/keyword_scheduler/executor.py tests/test_executor.py
git commit -m "feat: implement keyword search executor"
```

---

### Task 5: Implement CLI Entry Point and Pipeline Integration

**Files:**
- Modify: `scripts/keyword_scheduler/scheduler.py` (add `__main__` block)
- Modify: `scripts/kp_pipeline/run_pipeline.py:70` (add `--keyword-driven` flag)

- [ ] **Step 1: Add CLI entry point to scheduler.py**

Append to `scripts/keyword_scheduler/scheduler.py`:

```python
# --- CLI entry point ---

def main():
    import argparse
    from scripts.keyword_scheduler.config import load_config, get_extraction_defaults
    from scripts.keyword_scheduler.executor import build_extraction_queue, run_extraction
    from scripts.keyword_scheduler.tracker import update_keyword_stats, append_run_log

    parser = argparse.ArgumentParser(description="Keyword scheduler — bridges search_keywords.csv to extraction pipeline")
    parser.add_argument("--keywords", default=str(Path(__file__).resolve().parents[2] / "data" / "search_keywords.csv"))
    parser.add_argument("--runs-log", default=str(Path(__file__).resolve().parents[2] / "data" / "keyword_runs.csv"))
    parser.add_argument("--limit", type=int, default=None, help="Override max keywords per run")
    parser.add_argument("--dry-run", action="store_true", help="Show selected keywords without executing")
    parser.add_argument("--batch-id", default=None, help="Batch ID for run log")
    args = parser.parse_args()

    config = load_config()
    if args.limit:
        config["max_keywords_per_run"] = args.limit

    keywords_csv = Path(args.keywords)
    runs_csv = Path(args.runs_log)

    print(f"[Scheduler] Loading keywords from {keywords_csv}")
    queue = build_query_queue(keywords_csv, config)
    print(f"[Scheduler] Selected {len(queue)} keyword queries")

    if not queue:
        print("[Scheduler] No eligible keywords. Exiting.")
        return

    for item in queue:
        print(f"  - {item['keyword_id']}: {item['keyword_pattern']}")

    if args.dry_run:
        print("[Scheduler] Dry run — not executing.")
        return

    # Build extraction queue
    queue_path = Path(__file__).resolve().parents[2] / "reports" / "kw-scheduler-queue.csv"
    build_extraction_queue(queue, queue_path)
    print(f"[Scheduler] Wrote queue to {queue_path}")

    # Run extraction
    ext_defaults = get_extraction_defaults(config)
    exit_code, output_csv = run_extraction(
        queue_path,
        output_prefix="kw-scheduler-",
        limit=ext_defaults.get("limit", 10),
        follow_links=ext_defaults.get("follow_links", 2),
        fetcher=ext_defaults.get("fetcher", "static"),
        skip_existing=ext_defaults.get("skip_existing", True),
    )

    if exit_code != 0:
        print(f"[Scheduler] Extraction exited with code {exit_code}")
    else:
        print(f"[Scheduler] Extraction complete. Results: {output_csv}")

    # Update tracking
    batch_id = args.batch_id or f"BATCH-KW-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    for item in queue:
        # We don't have per-keyword result counts from the extraction script,
        # so we record 1 run per keyword with 0 leads (manual review needed)
        update_keyword_stats(keywords_csv, item["keyword_id"])
        append_run_log(
            runs_csv,
            batch_id=batch_id,
            keyword_id=item["keyword_id"],
            keyword_source_query=item["source_query"],
        )

    print(f"[Scheduler] Updated tracking for {len(queue)} keywords.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test dry-run mode**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m scripts.keyword_scheduler.scheduler --dry-run --limit 3`
Expected: Prints 3 selected keywords with their patterns, no execution.

- [ ] **Step 3: Add --keyword-driven flag to run_pipeline.py**

In `scripts/kp_pipeline/run_pipeline.py`, add argument:

```python
# In the argparse section (around line 25), add:
parser.add_argument("--keyword-driven", action="store_true", help="Run keyword scheduler before Stage 1 to discover new leads")
```

In the main function (before Stage 1 execution, around line 70), add:

```python
    # Keyword-driven discovery: run scheduler before Stage 1
    if args.keyword_driven:
        print("[Pipeline] Running keyword scheduler for new lead discovery...")
        from scripts.keyword_scheduler.scheduler import main as scheduler_main
        # Scheduler runs as a pre-stage
        import sys
        old_argv = sys.argv
        sys.argv = ["scheduler", "--limit", str(args.limit or 5)]
        try:
            scheduler_main()
        finally:
            sys.argv = old_argv
        print("[Pipeline] Keyword scheduler complete. Proceeding to Stage 1...")
```

- [ ] **Step 4: Verify pipeline still works without the flag**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m scripts.kp_pipeline.run_pipeline --stage all --limit 1 2>&1 | tail -5`
Expected: Pipeline runs normally, no keyword scheduler output.

- [ ] **Step 5: Commit**

```bash
git add scripts/keyword_scheduler/scheduler.py scripts/kp_pipeline/run_pipeline.py
git commit -m "feat: add CLI entry point and --keyword-driven pipeline flag"
```

---

### Task 6: Integration Test — Full Keyword-to-Leads Flow

**Files:**
- No new files. This is a manual integration test.

- [ ] **Step 1: Run scheduler in dry-run mode to verify keyword selection**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m scripts.keyword_scheduler.scheduler --dry-run --limit 3`
Expected: 3 keywords selected, sorted by priority. Template keywords expanded (e.g., "restaurant group [country] contact" → "restaurant group Australia contact"). No execution.

- [ ] **Step 2: Run scheduler for real with limit 2**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m scripts.keyword_scheduler.scheduler --limit 2`
Expected: 2 keywords selected, extraction runs, results written to `reports/kw-scheduler-*.csv`, `data/keyword_runs.csv` appended, `data/search_keywords.csv` updated.

- [ ] **Step 3: Verify keyword_runs.csv was updated**

Run: `tail -3 e:/AI/TestProject-v2/data/keyword_runs.csv`
Expected: 2 new rows with the batch ID and keyword IDs.

- [ ] **Step 4: Verify search_keywords.csv stats updated**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -c "import csv; r=csv.DictReader(open('data/search_keywords.csv','r',encoding='utf-8-sig')); rows=[x for x in r if x['keyword_id'] in ('KW-0001','KW-0002')]; [print(f\"{x['keyword_id']}: runs={x['total_runs']} next={x['next_allowed_at']}\") for x in rows]"`
Expected: `total_runs` incremented, `next_allowed_at` set to ~14 days from now.

- [ ] **Step 5: Run full pipeline with --keyword-driven flag**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m scripts.kp_pipeline.run_pipeline --stage all --limit 3 --keyword-driven 2>&1 | tail -10`
Expected: Keyword scheduler runs first, then Stage 1+2+3 proceed normally.

- [ ] **Step 6: Check git status for temp files**

Run: `cd e:/AI/TestProject-v2 && git status --short | grep -E "(temp_|test_|debug_)"`
Expected: No temp files.

- [ ] **Step 7: Commit integration test artifacts**

```bash
git add data/keyword_runs.csv data/search_keywords.csv
git commit -m "chore: keyword scheduler integration test results"
```

---

### Task 7: Keyword Form Generator — Multi-Dimensional Candidate Generation

**Files:**
- Create: `scripts/keyword_scheduler/generator.py`
- Create: `tests/test_generator.py`
- Create: `config/keyword_dimensions.json`

**Context:** The existing `suggest_new_keywords()` in market_intel.py only does city/customer_type string replacement — too narrow. Real Google search queries benefit from combining multiple dimensions: customer type, role, geography, intent, organization form, source modifier, trigger event. This module generates keyword candidates declaratively from a dimension config and a set of query templates, producing structured candidates with metadata for downstream scoring.

- [ ] **Step 1: Create keyword_dimensions.json config**

```json
{
  "version": "1.0",
  "max_candidates": 200,
  "dimensions": {
    "customer_type": [
      "restaurant group", "restaurant owner", "hotel group", "hotel F&B manager",
      "pub group", "brewery venue", "catering company", "event venue",
      "aged care food service", "corporate catering", "cafe chain",
      "food court operator", "winery restaurant", "resort F&B",
      "hospitality recruitment", "restaurant renovation",
      "restaurant fit-out company", "restaurant design company",
      "multi-location restaurant", "hospitality venue group",
      "hotel procurement manager", "new restaurant opening",
      "restaurant supply chain", "ghost kitchen operator",
      "hotel housekeeping supplier", "restaurant equipment supplier"
    ],
    "role": [
      "owner", "director", "CEO", "founder", "general manager",
      "procurement manager", "operations manager", "head chef",
      "F&B director", "purchasing manager", "venue manager",
      "group executive chef", "supply chain manager", "regional manager"
    ],
    "geo": [
      "Australia", "Sydney", "Melbourne", "Brisbane", "Perth",
      "Adelaide", "Gold Coast", "Canberra", "Hobart", "Darwin",
      "Newcastle", "Wollongong", "NSW", "VIC", "QLD", "WA", "SA"
    ],
    "intent": [
      "contact", "email", "phone", "supplier registration",
      "become a supplier", "vendor application", "procurement",
      "request a quote", "tender", "partnership enquiry",
      "directory", "team page", "about us", "leadership"
    ],
    "org_form": [
      "group", "holdings", "collective", "hospitality",
      "venues", "collection", "management", "enterprises"
    ],
    "source_modifier": [
      "site:.com.au", "site:.com.au intitle:contact",
      "filetype:pdf", "inurl:team", "inurl:about",
      "intitle:\"meet the team\"", "intitle:leadership"
    ],
    "trigger_event": [
      "new opening", "new venue", "expansion", "rebranding",
      "new management", "acquisition", "renovation",
      "just opened", "now hiring", "coming soon"
    ]
  },
  "query_templates": [
    {"id": "T1", "pattern": "{customer_type} {geo} {intent}", "priority_hint": "high"},
    {"id": "T2", "pattern": "{customer_type} {role} {geo}", "priority_hint": "high"},
    {"id": "T3", "pattern": "{org_form} {customer_type} head office {geo}", "priority_hint": "medium"},
    {"id": "T4", "pattern": "\"{role}\" \"{customer_type}\" {geo}", "priority_hint": "high"},
    {"id": "T5", "pattern": "{source_modifier} {customer_type} {intent} {geo}", "priority_hint": "medium"},
    {"id": "T6", "pattern": "filetype:pdf {customer_type} procurement {geo}", "priority_hint": "low"},
    {"id": "T7", "pattern": "\"{trigger_event}\" {customer_type} {geo}", "priority_hint": "high"},
    {"id": "T8", "pattern": "{customer_type} {geo} {trigger_event} {intent}", "priority_hint": "medium"},
    {"id": "T9", "pattern": "{role} {customer_type} {geo} email OR phone OR contact", "priority_hint": "high"},
    {"id": "T10", "pattern": "{customer_type} {geo} \"{intent}\" -jobs -careers", "priority_hint": "medium"}
  ],
  "dimension_weights": {
    "customer_type": 1.0,
    "role": 0.8,
    "geo": 0.6,
    "intent": 0.9,
    "org_form": 0.5,
    "source_modifier": 0.4,
    "trigger_event": 0.7
  }
}
```

- [ ] **Step 2: Write failing tests for generator**

```python
# tests/test_generator.py
import json
import tempfile
from pathlib import Path


def _make_config(tmpdir: str) -> Path:
    config = {
        "max_candidates": 50,
        "dimensions": {
            "customer_type": ["restaurant group", "hotel group"],
            "role": ["owner", "director"],
            "geo": ["Sydney", "Melbourne"],
            "intent": ["contact", "email"],
            "org_form": ["group", "collective"],
            "source_modifier": ["site:.com.au"],
            "trigger_event": ["new opening"],
        },
        "query_templates": [
            {"id": "T1", "pattern": "{customer_type} {geo} {intent}", "priority_hint": "high"},
            {"id": "T2", "pattern": "{customer_type} {role} {geo}", "priority_hint": "high"},
            {"id": "T3", "pattern": "\"{role}\" \"{customer_type}\" {geo}", "priority_hint": "medium"},
        ],
    }
    path = Path(tmpdir) / "keyword_dimensions.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f)
    return path


def test_generate_multi_template():
    """Generator should produce candidates from multiple templates."""
    from scripts.keyword_scheduler.generator import generate_candidates

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = _make_config(tmpdir)
        candidates = generate_candidates(config_path)

        # T1: 2 customer_type × 2 geo × 2 intent = 8
        # T2: 2 customer_type × 2 role × 2 geo = 8
        # T3: 2 role × 2 customer_type × 2 geo = 8
        assert len(candidates) == 24

        # Check that all 3 templates are represented
        template_ids = {c["template_id"] for c in candidates}
        assert template_ids == {"T1", "T2", "T3"}


def test_generate_deduplicates():
    """Duplicate patterns from different template combos should be deduped."""
    from scripts.keyword_scheduler.generator import generate_candidates

    with tempfile.TemporaryDirectory() as tmpdir:
        config = {
            "max_candidates": 100,
            "dimensions": {
                "customer_type": ["restaurant"],
                "role": ["owner"],
                "geo": ["Sydney"],
                "intent": ["contact"],
                "org_form": ["group"],
                "source_modifier": ["site:.com.au"],
                "trigger_event": ["new opening"],
            },
            "query_templates": [
                {"id": "T1", "pattern": "{customer_type} {geo} {intent}", "priority_hint": "high"},
                {"id": "T1B", "pattern": "{customer_type} {geo} {intent}", "priority_hint": "low"},
            ],
        }
        config_path = Path(tmpdir) / "keyword_dimensions.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f)

        candidates = generate_candidates(config_path)
        patterns = [c["keyword_pattern"] for c in candidates]
        # Same pattern from T1 and T1B should be deduped to 1
        assert len(patterns) == len(set(patterns))
        assert len(candidates) == 1


def test_generate_respects_max_candidates():
    """Generator should cap output at max_candidates."""
    from scripts.keyword_scheduler.generator import generate_candidates

    with tempfile.TemporaryDirectory() as tmpdir:
        config = {
            "max_candidates": 5,
            "dimensions": {
                "customer_type": ["restaurant", "hotel", "pub", "cafe", "catering"],
                "role": ["owner"],
                "geo": ["Sydney"],
                "intent": ["contact"],
                "org_form": ["group"],
                "source_modifier": ["site:.com.au"],
                "trigger_event": ["new opening"],
            },
            "query_templates": [
                {"id": "T1", "pattern": "{customer_type} {geo} {intent}", "priority_hint": "high"},
            ],
        }
        config_path = Path(tmpdir) / "keyword_dimensions.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f)

        candidates = generate_candidates(config_path)
        assert len(candidates) <= 5


def test_generate_covers_multiple_templates_with_small_max():
    """Even with small max_candidates, multiple templates should be represented."""
    from scripts.keyword_scheduler.generator import generate_candidates

    with tempfile.TemporaryDirectory() as tmpdir:
        config = {
            "max_candidates": 6,
            "min_per_template": 2,
            "dimensions": {
                "customer_type": ["restaurant", "hotel", "pub"],
                "role": ["owner", "director"],
                "geo": ["Sydney", "Melbourne"],
                "intent": ["contact", "email"],
                "org_form": ["group"],
                "source_modifier": ["site:.com.au"],
                "trigger_event": ["new opening"],
            },
            "query_templates": [
                {"id": "T1", "pattern": "{customer_type} {geo} {intent}", "priority_hint": "high"},
                {"id": "T2", "pattern": "{customer_type} {role} {geo}", "priority_hint": "high"},
                {"id": "T3", "pattern": "\"{role}\" \"{customer_type}\" {geo}", "priority_hint": "medium"},
            ],
        }
        config_path = Path(tmpdir) / "keyword_dimensions.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f)

        candidates = generate_candidates(config_path)
        assert len(candidates) <= 6

        # All 3 templates should be represented (each gets at least 2)
        template_ids = {c["template_id"] for c in candidates}
        assert len(template_ids) == 3, f"Expected 3 templates, got {template_ids}: {[c['template_id'] for c in candidates]}"


def test_write_suggested_csv_includes_score():
    """write_suggested_csv should export the score field when present."""
    from scripts.keyword_scheduler.generator import write_suggested_csv

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "suggested.csv"
        candidates = [
            {
                "keyword_pattern": "restaurant Sydney contact",
                "template_id": "T1",
                "generation_source": "generator",
                "risk_level": "low",
                "priority_hint": "high",
                "score": 0.85,
                "dimensions_used": {"customer_type": "restaurant", "geo": "Sydney", "intent": "contact"},
            },
            {
                "keyword_pattern": "hotel owner Melbourne",
                "template_id": "T2",
                "generation_source": "generator",
                "risk_level": "medium",
                "priority_hint": "medium",
                "score": 0.42,
                "dimensions_used": {"customer_type": "hotel", "role": "owner", "geo": "Melbourne"},
            },
        ]
        write_suggested_csv(candidates, out_path)

        import csv
        with open(out_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert "score" in rows[0], f"score column missing from CSV: {rows[0].keys()}"
        assert rows[0]["score"] == "0.85"
        assert rows[1]["score"] == "0.42"


def test_generate_preserves_metadata():
    """Each candidate should carry template_id, generation_source, risk_level, priority_hint."""
    from scripts.keyword_scheduler.generator import generate_candidates

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = _make_config(tmpdir)
        candidates = generate_candidates(config_path)

        for c in candidates:
            assert "template_id" in c, f"Missing template_id in {c}"
            assert "generation_source" in c
            assert "risk_level" in c
            assert "priority_hint" in c
            assert c["template_id"] in ("T1", "T2", "T3")
            assert c["risk_level"] in ("low", "medium", "high")
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m pytest tests/test_generator.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.keyword_scheduler.generator'`

- [ ] **Step 4: Implement generator.py**

```python
# scripts/keyword_scheduler/generator.py
"""Multi-dimensional keyword candidate generator.

Reads dimensions and templates from config, produces deduplicated candidates
with metadata (template_id, generation_source, risk_level, priority_hint).
Output: suggested_keywords.csv for human review.
"""

import csv
import itertools
import json
from pathlib import Path


def load_dimensions_config(config_path: Path) -> dict:
    """Load keyword dimensions config."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_candidates(config_path: Path) -> list[dict]:
    """Generate keyword candidates from dimensions × templates.

    Quota is distributed evenly across templates so that early templates
    cannot consume the entire max_candidates budget. Each template gets
    at least min_per_template (default 2) candidates when possible.

    Returns list of dicts, each with:
      - keyword_pattern: the concrete search query string
      - template_id: which template produced it (e.g. "T1")
      - generation_source: "generator"
      - risk_level: "low" / "medium" / "high" based on template specificity
      - priority_hint: from template config ("high" / "medium" / "low")
      - dimensions_used: dict of which dimension values were used
    """
    config = load_dimensions_config(config_path)
    dimensions = config["dimensions"]
    templates = config["query_templates"]
    max_candidates = config.get("max_candidates", 200)
    min_per_template = config.get("min_per_template", 2)

    # Phase 1: compute how many combos each template can produce
    template_info = []
    for template in templates:
        tid = template["id"]
        pattern = template["pattern"]
        priority_hint = template.get("priority_hint", "medium")

        placeholders = _extract_placeholders(pattern)
        if not placeholders:
            continue

        dim_values = {}
        valid = True
        for ph in placeholders:
            vals = dimensions.get(ph, [])
            if not vals:
                valid = False
                break
            dim_values[ph] = vals

        if not valid:
            continue

        # Compute total possible combos
        total_combos = 1
        for vals in dim_values.values():
            total_combos *= len(vals)

        template_info.append({
            "id": tid,
            "pattern": pattern,
            "priority_hint": priority_hint,
            "dim_values": dim_values,
            "total_combos": total_combos,
        })

    if not template_info:
        return []

    # Phase 2: distribute quota across templates
    n_templates = len(template_info)
    base_quota = max(max_candidates // n_templates, min_per_template)
    remaining = max_candidates

    candidates = []
    seen_patterns: set[str] = set()

    for info in template_info:
        tid = info["id"]
        pattern = info["pattern"]
        priority_hint = info["priority_hint"]
        dim_values = info["dim_values"]

        # This template's quota: min of base_quota, remaining budget, and total combos
        quota = min(base_quota, remaining, info["total_combos"])

        ph_names = list(dim_values.keys())
        ph_lists = [dim_values[ph] for ph in ph_names]

        count = 0
        for combo in itertools.product(*ph_lists):
            if count >= quota:
                break

            concrete = pattern
            used = {}
            for ph_name, val in zip(ph_names, combo):
                concrete = concrete.replace("{" + ph_name + "}", val, 1)
                used[ph_name] = val

            if concrete in seen_patterns:
                continue
            seen_patterns.add(concrete)

            risk = _assess_risk(used, tid)

            candidates.append({
                "keyword_pattern": concrete,
                "template_id": tid,
                "generation_source": "generator",
                "risk_level": risk,
                "priority_hint": priority_hint,
                "dimensions_used": used,
            })
            count += 1
            remaining -= 1

        if remaining <= 0:
            break

    return candidates


def _extract_placeholders(pattern: str) -> list[str]:
    """Extract {dimension_name} placeholders from a template pattern."""
    import re
    return re.findall(r"\{(\w+)\}", pattern)


def _assess_risk(dimensions_used: dict, template_id: str) -> str:
    """Assess risk level of a generated keyword.

    low = generic broad query (few dimensions, no quotes)
    medium = moderately specific
    high = very specific (uses role, source_modifier, trigger_event)
    """
    risky_dims = {"role", "source_modifier", "trigger_event"}
    used_risky = risky_dims & set(dimensions_used.keys())

    if len(used_risky) >= 2:
        return "high"
    elif len(used_risky) == 1:
        return "medium"
    else:
        return "low"


def write_suggested_csv(candidates: list[dict], output_path: Path) -> Path:
    """Write candidates to suggested_keywords.csv for human review.

    Columns: keyword_pattern, template_id, generation_source, risk_level,
             priority_hint, score, customer_type, role, geo, intent, org_form,
             source_modifier, trigger_event, review_status
    """
    fieldnames = [
        "keyword_pattern", "template_id", "generation_source", "risk_level",
        "priority_hint", "score", "customer_type", "role", "geo", "intent",
        "org_form", "source_modifier", "trigger_event", "review_status",
    ]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in candidates:
            dims = c.get("dimensions_used", {})
            writer.writerow({
                "keyword_pattern": c["keyword_pattern"],
                "template_id": c["template_id"],
                "generation_source": c["generation_source"],
                "risk_level": c["risk_level"],
                "priority_hint": c["priority_hint"],
                "score": c.get("score", ""),
                "customer_type": dims.get("customer_type", ""),
                "role": dims.get("role", ""),
                "geo": dims.get("geo", ""),
                "intent": dims.get("intent", ""),
                "org_form": dims.get("org_form", ""),
                "source_modifier": dims.get("source_modifier", ""),
                "trigger_event": dims.get("trigger_event", ""),
                "review_status": "pending",
            })

    return output_path


# --- CLI entry point ---

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate keyword candidates from dimensions × templates")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[2] / "config" / "keyword_dimensions.json"))
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[2] / "reports" / "suggested_keywords.csv"))
    parser.add_argument("--max", type=int, default=None, help="Override max_candidates")
    parser.add_argument("--dry-run", action="store_true", help="Print candidates without writing CSV")
    args = parser.parse_args()

    config_path = Path(args.config)
    output_path = Path(args.output)

    # Override max_candidates if specified
    if args.max:
        config = load_dimensions_config(config_path)
        config["max_candidates"] = args.max
        tmp_path = config_path.parent / "_tmp_dimensions.json"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(config, f)
        config_path = tmp_path

    candidates = generate_candidates(config_path)
    print(f"[Generator] Generated {len(candidates)} keyword candidates")

    # Summary by template
    from collections import Counter
    by_template = Counter(c["template_id"] for c in candidates)
    for tid, count in sorted(by_template.items()):
        print(f"  {tid}: {count} candidates")

    if args.dry_run:
        print("\n[Generator] Dry run — top 10:")
        for c in candidates[:10]:
            print(f"  [{c['template_id']}] [{c['risk_level']}] {c['keyword_pattern']}")
        return

    write_suggested_csv(candidates, output_path)
    print(f"[Generator] Wrote to {output_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m pytest tests/test_generator.py -v`
Expected: 6 passed.

- [ ] **Step 6: Run generator on real config**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m scripts.keyword_scheduler.generator --dry-run --max 30`
Expected: Prints 30 candidates across templates T1-T10 with metadata.

- [ ] **Step 7: Commit**

```bash
git add scripts/keyword_scheduler/generator.py tests/test_generator.py config/keyword_dimensions.json
git commit -m "feat: add multi-dimensional keyword form generator"
```

---

### Task 8: Market Intelligence — Score and Rank Generated Candidates

**Files:**
- Create: `scripts/keyword_scheduler/market_intel.py`
- Create: `tests/test_market_intel.py`

**Context:** The existing 38 keywords in `search_keywords.csv` were mostly hand-crafted. The AU restaurant/hotel market has many untapped segments. This module analyzes historical run data to: (a) rank existing keyword effectiveness, (b) identify market segments with high contact rates, (c) score and rank candidates produced by generator.py based on historical performance signals.

- [ ] **Step 1: Write failing test for keyword performance analysis**

```python
# tests/test_market_intel.py
import csv
import tempfile
from pathlib import Path

def _make_runs_csv(path: Path, rows: list[dict]):
    fieldnames = [
        "batch_id", "run_id", "keyword_id", "keyword_source_query",
        "collection_round", "run_date", "target_leads_count",
        "actual_leads_collected", "ready_to_contact_count",
        "contact_found_count", "direct_key_contact_count",
        "company_contact_only_count", "duplicate_count", "news_only_count",
        "no_contact_count", "discovery_quality_score", "contactability_score",
        "run_status"
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({fn: row.get(fn, "") for fn in fieldnames})


def _make_keywords_csv(path: Path, rows: list[dict]):
    fieldnames = [
        "keyword_id", "target_customer_type", "country_or_region", "city",
        "keyword_pattern", "example_search_query", "search_intent",
        "keyword_intent_type", "priority_level", "keyword_status",
        "total_runs", "total_leads_collected", "ready_to_contact_count",
        "contact_found_count", "discovery_quality_score", "contactability_score",
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({fn: row.get(fn, "") for fn in fieldnames})


def test_analyze_keyword_performance_ranks_by_contact_rate():
    """Keywords with higher contact_found / total_leads should rank higher."""
    from scripts.keyword_scheduler.market_intel import analyze_keyword_performance

    with tempfile.TemporaryDirectory() as tmpdir:
        runs_path = Path(tmpdir) / "keyword_runs.csv"
        keywords_path = Path(tmpdir) / "search_keywords.csv"

        _make_runs_csv(runs_path, [
            {"keyword_id": "KW-0011", "actual_leads_collected": "7", "contact_found_count": "0", "discovery_quality_score": "0.86", "run_status": "completed"},
            {"keyword_id": "KW-0016", "actual_leads_collected": "3", "contact_found_count": "2", "discovery_quality_score": "1.00", "run_status": "completed"},
        ])
        _make_keywords_csv(keywords_path, [
            {"keyword_id": "KW-0011", "keyword_pattern": "restaurant group Australia contact", "keyword_status": "Active", "total_runs": "3", "total_leads_collected": "7", "contact_found_count": "0"},
            {"keyword_id": "KW-0016", "keyword_pattern": "restaurant owner Sydney contact", "keyword_status": "Active", "total_runs": "2", "total_leads_collected": "3", "contact_found_count": "2"},
        ])

        report = analyze_keyword_performance(runs_path, keywords_path)

        # KW-0016 has 2/3 = 67% contact rate, should rank above KW-0011 (0/7 = 0%)
        assert report[0]["keyword_id"] == "KW-0016"
        assert report[0]["contact_rate"] > report[1]["contact_rate"]


def test_score_candidates_boosts_proven_segments():
    """Candidates with customer_types that historically have high contact rates should score higher."""
    from scripts.keyword_scheduler.market_intel import score_candidates

    with tempfile.TemporaryDirectory() as tmpdir:
        runs_path = Path(tmpdir) / "keyword_runs.csv"
        keywords_path = Path(tmpdir) / "search_keywords.csv"

        # Historical data: "restaurant owner" has 67% contact rate
        _make_runs_csv(runs_path, [
            {"keyword_id": "KW-0016", "actual_leads_collected": "3", "contact_found_count": "2", "discovery_quality_score": "1.00", "run_status": "completed"},
        ])
        _make_keywords_csv(keywords_path, [
            {"keyword_id": "KW-0016", "keyword_pattern": "restaurant owner Sydney contact", "keyword_status": "Active", "target_customer_type": "Restaurant Owner", "total_runs": "2", "total_leads_collected": "3", "contact_found_count": "2"},
        ])

        # Two candidates: one in proven segment, one in unproven
        candidates = [
            {"keyword_pattern": "restaurant owner Brisbane contact", "template_id": "T1", "generation_source": "generator", "risk_level": "low", "priority_hint": "high", "dimensions_used": {"customer_type": "restaurant owner", "geo": "Brisbane", "intent": "contact"}},
            {"keyword_pattern": "ghost kitchen Darwin email", "template_id": "T1", "generation_source": "generator", "risk_level": "low", "priority_hint": "high", "dimensions_used": {"customer_type": "ghost kitchen operator", "geo": "Darwin", "intent": "email"}},
        ]

        scored = score_candidates(candidates, runs_path, keywords_path)

        # Restaurant owner candidate should score higher (proven segment)
        assert scored[0]["keyword_pattern"] == "restaurant owner Brisbane contact"
        assert scored[0]["score"] > scored[1]["score"]


def test_identify_market_segments():
    """Group keywords by customer type segment and compute segment stats."""
    from scripts.keyword_scheduler.market_intel import identify_market_segments

    keywords = [
        {"keyword_id": "KW-0011", "keyword_pattern": "restaurant group Australia contact", "target_customer_type": "Restaurant Group", "total_leads_collected": "7", "contact_found_count": "0"},
        {"keyword_id": "KW-0016", "keyword_pattern": "restaurant owner Sydney", "target_customer_type": "Restaurant Owner", "total_leads_collected": "3", "contact_found_count": "2"},
        {"keyword_id": "KW-0017", "keyword_pattern": "restaurant owner Melbourne", "target_customer_type": "Restaurant Owner", "total_leads_collected": "5", "contact_found_count": "3"},
    ]

    segments = identify_market_segments(keywords)

    assert "Restaurant Owner" in segments
    assert "Restaurant Group" in segments
    # Restaurant Owner segment: 3+5=8 leads, 2+3=5 contacts
    assert segments["Restaurant Owner"]["total_leads"] == 8
    assert segments["Restaurant Owner"]["total_contacts"] == 5
    assert segments["Restaurant Owner"]["contact_rate"] == 5 / 8
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m pytest tests/test_market_intel.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.keyword_scheduler.market_intel'`

- [ ] **Step 3: Implement market_intel.py**

```python
# scripts/keyword_scheduler/market_intel.py
"""Market intelligence: analyze keyword performance, discover segments, suggest new keywords."""

import csv
from pathlib import Path

# Default Australian cities for keyword expansion
DEFAULT_CITIES = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast", "Canberra", "Hobart"]

# Restaurant/hotel market segments to explore
MARKET_SEGMENTS = [
    "restaurant group", "restaurant owner", "hotel group", "hotel F&B",
    "pub group", "brewery venue", "catering company", "event venue",
    "aged care food service", "corporate catering", "cafe chain",
    "food court operator", "winery restaurant", "resort F&B",
    "hospitality recruitment", "restaurant renovation",
]


def analyze_keyword_performance(runs_csv: Path, keywords_csv: Path) -> list[dict]:
    """Analyze keyword performance from run history.

    Returns list of dicts sorted by contact_rate descending:
      - keyword_id, keyword_pattern, total_leads, total_contacts, contact_rate, avg_quality
    """
    # Aggregate from runs CSV
    run_stats: dict[str, dict] = {}
    with open(runs_csv, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            kid = row.get("keyword_id", "")
            if not kid:
                continue
            if kid not in run_stats:
                run_stats[kid] = {"leads": 0, "contacts": 0, "quality_sum": 0.0, "runs": 0}
            stats = run_stats[kid]
            stats["leads"] += int(row.get("actual_leads_collected") or 0)
            stats["contacts"] += int(row.get("contact_found_count") or 0)
            try:
                stats["quality_sum"] += float(row.get("discovery_quality_score") or 0)
            except ValueError:
                pass
            stats["runs"] += 1

    # Join with keywords CSV for pattern info
    keywords_map: dict[str, dict] = {}
    with open(keywords_csv, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            keywords_map[row.get("keyword_id", "")] = row

    results = []
    for kid, stats in run_stats.items():
        kw = keywords_map.get(kid, {})
        leads = stats["leads"]
        contacts = stats["contacts"]
        contact_rate = contacts / leads if leads > 0 else 0.0
        avg_quality = stats["quality_sum"] / stats["runs"] if stats["runs"] > 0 else 0.0
        results.append({
            "keyword_id": kid,
            "keyword_pattern": kw.get("keyword_pattern", ""),
            "target_customer_type": kw.get("target_customer_type", ""),
            "total_leads": leads,
            "total_contacts": contacts,
            "contact_rate": round(contact_rate, 3),
            "avg_quality": round(avg_quality, 3),
            "runs": stats["runs"],
        })

    results.sort(key=lambda x: (-x["contact_rate"], -x["avg_quality"]))
    return results


def identify_market_segments(keywords: list[dict]) -> dict[str, dict]:
    """Group keywords by target_customer_type and compute segment-level stats.

    Returns dict: segment_name -> {total_leads, total_contacts, contact_rate, keyword_count}
    """
    segments: dict[str, dict] = {}
    for kw in keywords:
        segment = (kw.get("target_customer_type") or "Unknown").strip()
        if segment not in segments:
            segments[segment] = {"total_leads": 0, "total_contacts": 0, "keyword_count": 0}
        seg = segments[segment]
        seg["total_leads"] += int(kw.get("total_leads_collected") or 0)
        seg["total_contacts"] += int(kw.get("contact_found_count") or 0)
        seg["keyword_count"] += 1

    for seg in segments.values():
        seg["contact_rate"] = round(
            seg["total_contacts"] / seg["total_leads"], 3
        ) if seg["total_leads"] > 0 else 0.0

    return segments


def score_candidates(
    candidates: list[dict],
    runs_csv: Path,
    keywords_csv: Path,
) -> list[dict]:
    """Score and rank generator candidates based on historical performance.

    Scoring factors:
    1. Template effectiveness: templates that historically produced high contact_rate keywords score higher
    2. Segment coverage: customer_types with proven track record get a boost
    3. Geo coverage: cities/regions with existing successful keywords get a boost
    4. Risk penalty: high-risk candidates (very specific) get a small penalty
    5. Priority hint: template's own priority_hint is factored in

    Returns candidates with added 'score' field, sorted descending.
    """
    performance = analyze_keyword_performance(runs_csv, keywords_csv)
    all_keywords = []
    with open(keywords_csv, "r", encoding="utf-8-sig") as f:
        all_keywords = list(csv.DictReader(f))

    # Build lookup tables from historical data
    # Contact rate by customer_type keyword presence
    segment_contact_rates: dict[str, list[float]] = {}
    for p in performance:
        ct = (p.get("target_customer_type") or "").strip().lower()
        if ct:
            segment_contact_rates.setdefault(ct, []).append(p["contact_rate"])

    segment_avg_rates = {
        ct: sum(rates) / len(rates)
        for ct, rates in segment_contact_rates.items()
    }

    # Contact rate by geo presence in pattern
    geo_contact_rates: dict[str, list[float]] = {}
    for p in performance:
        pattern_lower = p["keyword_pattern"].lower()
        for geo in ["sydney", "melbourne", "brisbane", "perth", "adelaide", "australia"]:
            if geo in pattern_lower:
                geo_contact_rates.setdefault(geo, []).append(p["contact_rate"])

    geo_avg_rates = {
        g: sum(rates) / len(rates)
        for g, rates in geo_contact_rates.items()
    }

    # Template effectiveness from historical patterns
    template_scores: dict[str, float] = {}
    for p in performance:
        # Heuristic: map historical patterns to template types
        pattern = p["keyword_pattern"].lower()
        if "\"" in pattern or "intitle:" in pattern:
            template_scores["T4"] = max(template_scores.get("T4", 0), p["contact_rate"])
        if "filetype:" in pattern:
            template_scores["T6"] = max(template_scores.get("T6", 0), p["contact_rate"])
        if "site:" in pattern:
            template_scores["T5"] = max(template_scores.get("T5", 0), p["contact_rate"])

    priority_weights = {"high": 1.0, "medium": 0.7, "low": 0.4}
    risk_penalty = {"low": 0.0, "medium": -0.05, "high": -0.10}

    scored = []
    for c in candidates:
        dims = c.get("dimensions_used", {})
        ct = dims.get("customer_type", "").lower()
        geo = dims.get("geo", "").lower()
        tid = c.get("template_id", "")
        risk = c.get("risk_level", "medium")
        priority = c.get("priority_hint", "medium")

        score = 0.5  # base

        # Segment boost (up to +0.2)
        if ct in segment_avg_rates:
            score += segment_avg_rates[ct] * 0.3

        # Geo boost (up to +0.15)
        if geo in geo_avg_rates:
            score += geo_avg_rates[geo] * 0.2

        # Template effectiveness (up to +0.15)
        if tid in template_scores:
            score += template_scores[tid] * 0.2

        # Priority hint
        score *= priority_weights.get(priority, 0.5)

        # Risk penalty
        score += risk_penalty.get(risk, 0)

        score = max(0.0, min(1.0, score))

        c["score"] = round(score, 3)
        scored.append(c)

    scored.sort(key=lambda x: -x["score"])
    return scored


def generate_market_report(
    runs_csv: Path,
    keywords_csv: Path,
    config_path: Path | None = None,
    output_path: Path | None = None,
) -> str:
    """Generate a markdown report of market intelligence.

    If config_path is provided, also generates and scores candidates via generator.
    Returns the report as a string. If output_path is given, also writes to file.
    """
    performance = analyze_keyword_performance(runs_csv, keywords_csv)

    all_keywords = []
    with open(keywords_csv, "r", encoding="utf-8-sig") as f:
        all_keywords = list(csv.DictReader(f))

    segments = identify_market_segments(all_keywords)

    lines = [
        "# Market Intelligence Report",
        "",
        f"## Keyword Performance Ranking ({len(performance)} keywords analyzed)",
        "",
        "| Rank | Keyword | Customer Type | Leads | Contacts | Contact Rate | Quality |",
        "|------|---------|---------------|-------|----------|-------------|---------|",
    ]
    for i, p in enumerate(performance[:15], 1):
        lines.append(
            f"| {i} | {p['keyword_pattern'][:50]} | {p['target_customer_type']} | "
            f"{p['total_leads']} | {p['total_contacts']} | {p['contact_rate']:.1%} | {p['avg_quality']:.2f} |"
        )

    lines.extend([
        "",
        "## Market Segments",
        "",
        "| Segment | Keywords | Leads | Contacts | Contact Rate |",
        "|---------|----------|-------|----------|-------------|",
    ])
    for seg_name, seg_data in sorted(segments.items(), key=lambda x: -x[1]["contact_rate"]):
        lines.append(
            f"| {seg_name} | {seg_data['keyword_count']} | {seg_data['total_leads']} | "
            f"{seg_data['total_contacts']} | {seg_data['contact_rate']:.1%} |"
        )

    # Generator-powered suggestions (if config provided)
    if config_path and config_path.exists():
        from scripts.keyword_scheduler.generator import generate_candidates, write_suggested_csv

        candidates = generate_candidates(config_path)
        scored = score_candidates(candidates, runs_csv, keywords_csv)

        existing_patterns = {kw.get("keyword_pattern", "") for kw in all_keywords}
        new_candidates = [c for c in scored if c["keyword_pattern"] not in existing_patterns]

        lines.extend([
            "",
            f"## Generated Keyword Candidates ({len(new_candidates)} new, scored)",
            "",
            "| Score | Template | Risk | Pattern | Customer Type | Geo |",
            "|-------|----------|------|---------|---------------|-----|",
        ])
        for c in new_candidates[:30]:
            dims = c.get("dimensions_used", {})
            lines.append(
                f"| {c['score']:.2f} | {c['template_id']} | {c['risk_level']} | "
                f"{c['keyword_pattern'][:55]} | {dims.get('customer_type', '')[:20]} | {dims.get('geo', '')} |"
            )

        if len(new_candidates) > 30:
            lines.append(f"\n... and {len(new_candidates) - 30} more candidates.")

        # Write full scored candidates to suggested_keywords.csv
        suggested_path = (output_path or Path(".")).parent / "suggested_keywords.csv"
        write_suggested_csv(new_candidates, suggested_path)
        lines.append(f"\nFull list saved to: `{suggested_path}`")

    report = "\n".join(lines)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

    return report
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m pytest tests/test_market_intel.py -v`
Expected: 3 passed (test_analyze_keyword_performance_ranks_by_contact_rate, test_score_candidates_boosts_proven_segments, test_identify_market_segments).

- [ ] **Step 5: Generate real market report from existing data**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -c "from scripts.keyword_scheduler.market_intel import generate_market_report; from pathlib import Path; r = generate_market_report(Path('data/keyword_runs.csv'), Path('data/search_keywords.csv'), config_path=Path('config/keyword_dimensions.json'), output_path=Path('reports/market-intelligence.md')); print(r[:500])"`
Expected: Markdown report with keyword performance, market segments, and scored generated candidates. Also writes `reports/suggested_keywords.csv`.

- [ ] **Step 6: Commit**

```bash
git add scripts/keyword_scheduler/market_intel.py tests/test_market_intel.py reports/market-intelligence.md
git commit -m "feat: add market intelligence — keyword performance analysis and suggestion engine"
```

---

### Task 9: Import Approved Suggestions into Search Keywords

**Files:**
- Create: `scripts/keyword_scheduler/import_suggestions.py`
- Create: `tests/test_import_suggestions.py`
- Modify: `scripts/keyword_scheduler/config.py` (add `_SUGGESTED_PATH` helper)

**Context:** After human review of `reports/suggested_keywords.csv`, approved rows need to be promoted into `data/search_keywords.csv` as real keywords. This module reads the suggested file, filters for `review_status = approved`, generates new keyword IDs, deduplicates against existing patterns, and appends to the master keywords CSV.

- [ ] **Step 1: Write failing tests for import**

```python
# tests/test_import_suggestions.py
import csv
import tempfile
from pathlib import Path

def _make_suggested_csv(path: Path, rows: list[dict]):
    fieldnames = [
        "keyword_pattern", "template_id", "generation_source", "risk_level",
        "priority_hint", "score", "customer_type", "role", "geo", "intent",
        "org_form", "source_modifier", "trigger_event", "review_status",
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({fn: row.get(fn, "") for fn in fieldnames})


def _make_keywords_csv(path: Path, rows: list[dict]):
    fieldnames = [
        "keyword_id", "target_customer_type", "country_or_region", "city",
        "keyword_pattern", "example_search_query", "search_intent",
        "keyword_intent_type", "priority_level", "keyword_status",
        "total_runs", "total_leads_collected", "contact_found_count",
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({fn: row.get(fn, "") for fn in fieldnames})


def test_import_only_approved():
    """Only rows with review_status=approved should be imported."""
    from scripts.keyword_scheduler.import_suggestions import import_approved

    with tempfile.TemporaryDirectory() as tmpdir:
        suggested = Path(tmpdir) / "suggested_keywords.csv"
        keywords = Path(tmpdir) / "search_keywords.csv"

        _make_suggested_csv(suggested, [
            {"keyword_pattern": "pub group Sydney contact", "template_id": "T1", "review_status": "approved", "priority_hint": "high", "customer_type": "pub group", "geo": "Sydney"},
            {"keyword_pattern": "cafe chain Melbourne email", "template_id": "T2", "review_status": "rejected", "priority_hint": "medium", "customer_type": "cafe chain", "geo": "Melbourne"},
            {"keyword_pattern": "brewery venue Brisbane", "template_id": "T3", "review_status": "pending", "priority_hint": "low", "customer_type": "brewery venue", "geo": "Brisbane"},
        ])
        _make_keywords_csv(keywords, [])

        count = import_approved(suggested, keywords)
        assert count == 1

        with open(keywords, "r", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 1
        assert rows[0]["keyword_pattern"] == "pub group Sydney contact"
        assert rows[0]["keyword_status"] == "New"


def test_import_generates_keyword_id():
    """Imported keywords should get KW-XXXX IDs that don't collide with existing."""
    from scripts.keyword_scheduler.import_suggestions import import_approved

    with tempfile.TemporaryDirectory() as tmpdir:
        suggested = Path(tmpdir) / "suggested_keywords.csv"
        keywords = Path(tmpdir) / "search_keywords.csv"

        _make_suggested_csv(suggested, [
            {"keyword_pattern": "test keyword one", "template_id": "T1", "review_status": "approved", "priority_hint": "high", "customer_type": "test", "geo": "Sydney"},
            {"keyword_pattern": "test keyword two", "template_id": "T2", "review_status": "approved", "priority_hint": "medium", "customer_type": "test", "geo": "Melbourne"},
        ])
        _make_keywords_csv(keywords, [
            {"keyword_id": "KW-0038", "keyword_pattern": "existing keyword", "keyword_status": "Active"},
        ])

        count = import_approved(suggested, keywords)
        assert count == 2

        with open(keywords, "r", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        ids = [r["keyword_id"] for r in rows]
        assert "KW-0038" in ids
        assert "KW-0039" in ids
        assert "KW-0040" in ids


def test_import_deduplicates_by_pattern():
    """Keywords with patterns already in search_keywords.csv should be skipped."""
    from scripts.keyword_scheduler.import_suggestions import import_approved

    with tempfile.TemporaryDirectory() as tmpdir:
        suggested = Path(tmpdir) / "suggested_keywords.csv"
        keywords = Path(tmpdir) / "search_keywords.csv"

        _make_suggested_csv(suggested, [
            {"keyword_pattern": "restaurant group Australia contact", "template_id": "T1", "review_status": "approved", "priority_hint": "high", "customer_type": "restaurant group", "geo": "Australia"},
            {"keyword_pattern": "new unique pattern", "template_id": "T2", "review_status": "approved", "priority_hint": "medium", "customer_type": "pub group", "geo": "Sydney"},
        ])
        _make_keywords_csv(keywords, [
            {"keyword_id": "KW-0011", "keyword_pattern": "restaurant group Australia contact", "keyword_status": "Active"},
        ])

        count = import_approved(suggested, keywords)
        assert count == 1

        with open(keywords, "r", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        patterns = [r["keyword_pattern"] for r in rows]
        assert patterns.count("restaurant group Australia contact") == 1  # no duplicate
        assert "new unique pattern" in patterns


def test_import_sets_default_fields():
    """Imported keywords should have sensible defaults for tracking fields."""
    from scripts.keyword_scheduler.import_suggestions import import_approved

    with tempfile.TemporaryDirectory() as tmpdir:
        suggested = Path(tmpdir) / "suggested_keywords.csv"
        keywords = Path(tmpdir) / "search_keywords.csv"

        _make_suggested_csv(suggested, [
            {"keyword_pattern": "test import", "template_id": "T1", "review_status": "approved", "priority_hint": "high", "customer_type": "restaurant", "geo": "Sydney", "role": "owner", "intent": "contact"},
        ])
        _make_keywords_csv(keywords, [])

        import_approved(suggested, keywords)

        with open(keywords, "r", encoding="utf-8-sig") as f:
            row = list(csv.DictReader(f))[0]

        assert row["keyword_status"] == "New"
        assert row["total_runs"] == "0"
        assert row["total_leads_collected"] == "0"
        assert row["priority_level"] == "high"
        assert row["target_customer_type"] == "restaurant"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m pytest tests/test_import_suggestions.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.keyword_scheduler.import_suggestions'`

- [ ] **Step 3: Implement import_suggestions.py**

```python
# scripts/keyword_scheduler/import_suggestions.py
"""Import approved keyword suggestions into search_keywords.csv."""

import csv
from pathlib import Path


# All columns expected in search_keywords.csv
_KEYWORDS_FIELDNAMES = [
    "keyword_id", "target_customer_type", "country_or_region", "city",
    "keyword_pattern", "example_search_query", "search_intent",
    "keyword_intent_type", "priority_level", "keyword_status", "used_recently",
    "last_used_at", "next_allowed_at", "cooldown_days", "discovery_quality_score",
    "contactability_score", "total_runs", "total_leads_collected",
    "ready_to_contact_count", "contact_found_count", "duplicate_count",
    "news_only_count", "no_contact_count", "relevance_ratio",
]


def import_approved(
    suggested_csv: Path,
    keywords_csv: Path,
) -> int:
    """Read suggested_keywords.csv, import approved rows into search_keywords.csv.

    Returns the number of new keywords imported.
    """
    # Load existing patterns for dedup
    existing_patterns: set[str] = set()
    existing_rows: list[dict] = []
    max_id = 0

    if keywords_csv.exists():
        with open(keywords_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_rows.append(row)
                existing_patterns.add((row.get("keyword_pattern") or "").strip())
                kid = row.get("keyword_id", "")
                if kid.startswith("KW-"):
                    try:
                        max_id = max(max_id, int(kid.split("-")[1]))
                    except ValueError:
                        pass

    # Read approved suggestions
    approved = []
    with open(suggested_csv, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if (row.get("review_status") or "").strip().lower() == "approved":
                pattern = (row.get("keyword_pattern") or "").strip()
                if pattern and pattern not in existing_patterns:
                    approved.append(row)
                    existing_patterns.add(pattern)  # prevent dupes within batch

    # Build new keyword rows
    new_rows = []
    for suggestion in approved:
        max_id += 1
        new_row = {fn: "" for fn in _KEYWORDS_FIELDNAMES}
        new_row["keyword_id"] = f"KW-{max_id:04d}"
        new_row["keyword_pattern"] = suggestion["keyword_pattern"]
        new_row["keyword_status"] = "New"
        new_row["priority_level"] = suggestion.get("priority_hint", "medium")
        new_row["target_customer_type"] = suggestion.get("customer_type", "")
        new_row["country_or_region"] = suggestion.get("geo", "")
        new_row["keyword_intent_type"] = "Discovery"
        new_row["total_runs"] = "0"
        new_row["total_leads_collected"] = "0"
        new_row["ready_to_contact_count"] = "0"
        new_row["contact_found_count"] = "0"
        new_row["cooldown_days"] = "14"
        new_row["search_intent"] = f"Generator: template={suggestion.get('template_id', '')}, risk={suggestion.get('risk_level', '')}"
        new_rows.append(new_row)

    # Append to keywords CSV
    if new_rows:
        with open(keywords_csv, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_KEYWORDS_FIELDNAMES)
            # If file was empty, write header
            if not existing_rows:
                writer.writeheader()
            writer.writerows(new_rows)

    return len(new_rows)


# --- CLI entry point ---

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Import approved keyword suggestions into search_keywords.csv")
    parser.add_argument("--suggested", default=str(Path(__file__).resolve().parents[2] / "reports" / "suggested_keywords.csv"))
    parser.add_argument("--keywords", default=str(Path(__file__).resolve().parents[2] / "data" / "search_keywords.csv"))
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported without writing")
    args = parser.parse_args()

    suggested_csv = Path(args.suggested)
    keywords_csv = Path(args.keywords)

    if not suggested_csv.exists():
        print(f"[Import] Suggested file not found: {suggested_csv}")
        return

    # Count approved
    approved_count = 0
    with open(suggested_csv, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if (row.get("review_status") or "").strip().lower() == "approved":
                approved_count += 1

    print(f"[Import] Found {approved_count} approved suggestions")

    if args.dry_run:
        print("[Import] Dry run — not writing.")
        return

    imported = import_approved(suggested_csv, keywords_csv)
    print(f"[Import] Imported {imported} new keywords into {keywords_csv}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd e:/AI/TestProject-v2 && .venv/Scripts/python.exe -m pytest tests/test_import_suggestions.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/keyword_scheduler/import_suggestions.py tests/test_import_suggestions.py
git commit -m "feat: add reviewed keyword import — promote approved suggestions to search_keywords.csv"
```

---

## Verification Checklist

After all tasks are complete:

1. `pytest tests/test_scheduler.py tests/test_tracker.py tests/test_executor.py tests/test_generator.py tests/test_market_intel.py tests/test_import_suggestions.py -v` — all pass
2. `python -m scripts.keyword_scheduler.scheduler --dry-run` — shows eligible keywords
3. `python -m scripts.keyword_scheduler.scheduler --limit 2` — runs extraction, updates tracking
4. `python -m scripts.keyword_scheduler.generator --dry-run --max 30` — generates 30 candidates, multiple templates represented
5. `python -m scripts.kp_pipeline.run_pipeline --stage all --limit 2 --keyword-driven` — scheduler runs before Stage 1
6. `python -c "from scripts.keyword_scheduler.market_intel import generate_market_report; ..."` — generates `reports/market-intelligence.md` + `reports/suggested_keywords.csv`
7. `reports/suggested_keywords.csv` — has `score` column, `template_id`, `generation_source`, `risk_level`, `review_status`
8. Manually set a few rows `review_status = approved` in `reports/suggested_keywords.csv`
9. `python -m scripts.keyword_scheduler.import_suggestions --dry-run` — shows count of approved
10. `python -m scripts.keyword_scheduler.import_suggestions` — imports approved rows into `data/search_keywords.csv`
11. `git status` — no temp files, no stray reports
12. `data/keyword_runs.csv` — new rows appended
13. `data/search_keywords.csv` — new keywords with `keyword_status=New`, non-colliding `keyword_id`
