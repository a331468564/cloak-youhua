<!-- DOC_META
lifecycle:  long-term
audience:   agent
write_when: 关键词发现流程、规则、指标变更时更新
read_when:  执行关键词发现任务时读取
delete_when: 不删除
-->
# Keyword Discovery Workflow

<!-- CODEx_START: discovery_workflow -->
*Updated: 2026-05-29*

## Keyword Discovery Workflow

Keyword discovery means using search keywords to find new AU restaurant/hotel companies that are not yet in `data/leads.csv`. It does not mean the company is ready for outreach.

For each discovered company, record:

- Company name
- Website
- Country (verify, do not rely on domain suffix alone)
- City or region
- Industry type / customer type
- Source keyword and query
- Source link
- Confidence level (High / Medium / Low)

A discovered company is valid when:
- It matches Ron Group target customer types (restaurant, hotel, hospitality group)
- It has a public source link
- It has at least one contact signal on its website (email, phone, or contact page link)

Discovery flow:

1. **Select keywords** — From `data/search_keywords.csv`, pick keywords with status Active/New/Testing, not in cooldown.
2. **Expand templates** — Replace `[city]`, `[country]` placeholders per `config/keyword_scheduler.json`.
3. **Execute search** — Run `keyword_discovery.py` or `scheduler.py` with expanded queries.
4. **Filter results** — Apply 5-layer filters (domain exclusion, URL pattern, AU enhancement, contact signal, industry match).
5. **Dedup** — Check against existing leads by domain normalization, name normalization, email domain.
6. **Validate** — Confirm company has website + contact signal + industry match.
7. **Write to leads.csv** — Append qualified companies with source, confidence, and notes.
8. **Log run** — Record in `data/keyword_runs.csv`.

Read `docs/guides/keyword-scheduler-guide.md` for commands and configuration details.

<!-- CODEx_END: discovery_workflow -->

<!-- CODEx_START: discovery_quality_rules -->
*Updated: 2026-05-29*

## Discovery Quality Rules

After each keyword discovery run, calculate batch valid rate. Valid rate = qualified companies / total results found.

| Valid Rate | Status | Action |
|------------|--------|--------|
| ≥ 50% | Healthy | Continue, consider scaling keyword |
| 30%–49% | Warning | Review filters, consider refining keyword |
| < 30% | Critical | **Pause keyword, optimize before retry** |

**Mandatory pause triggers:**
- Valid rate < 50% for a batch → stop expanding that keyword, report valid rate and suggested improvements
- 3 consecutive runs with valid rate < 30% → auto-Pause keyword, require manual review before reactivation

**Quality signals to track per keyword:**
- `discovery_quality_score`: How well the keyword finds relevant companies (0–1 scale)
- `contactability_score`: How well the keyword results have usable contact paths (0–1 scale)

Scores are updated by `tracker.py` after each run and by `market_intel.py` during analysis.

Inline check:

```python
total_found = len(raw_results)
qualified = len([r for r in raw_results if r.get('qualified')])
valid_rate = qualified / total_found * 100 if total_found else 0
if valid_rate < 50:
    print(f"WARNING: valid rate {valid_rate:.0f}% < 50%, pausing expansion")
```

<!-- CODEx_END: discovery_quality_rules -->

<!-- CODEx_START: keyword_stopping_rules -->
*Updated: 2026-05-29*

## Keyword Stopping Rules

Stop using a keyword when any of these conditions are met:

**Hard stops (immediate):**
- Target count for the run is reached
- Google returns 429 rate limit
- Results are entirely unrelated to target industry
- Valid rate < 30% for the current batch

**Soft stops (after evaluation):**
- 3 consecutive runs with 0 new leads → auto-Pause keyword
- Duplicate ratio > 70% in results → pause, consider retiring
- News-only ratio > 70% → pause, add media domain filters
- No-contact ratio > 80% → pause, keyword finds companies without public contact info

**Auto-status adjustments (by tracker.py):**
- 3 runs with 0 leads → auto-set `keyword_status` to `Paused`
- 5 runs with valid_rate > 50% and contact_rate > 10% → auto-set to `Scale`
- Manual override always takes precedence over auto-adjustment

**Cooldown enforcement:**
- Default cooldown: 14 days between uses of the same keyword
- Override: clear `next_allowed_at` or set to past time
- Cooldown does not apply to keywords with status `New` (first use)

<!-- CODEx_END: keyword_stopping_rules -->

<!-- CODEx_START: batch_validation -->
*Updated: 2026-05-29*

## Batch Validation

Before adding discovered companies to `data/leads.csv`, each candidate must pass entity-level dedup and qualification checks.

**Dedup checks (3 layers):**

1. **Domain normalization** — Extract website domain, strip `www.`, compare root domain. `bargroup.au` and `bargroup.com.au` are the same company.
2. **Name normalization** — `.strip().lower()` comparison. Watch for abbreviations ("Fink" vs "Fink Group").
3. **Email domain match** — If candidate's email domain matches an existing lead's email domain, likely same company.

On any hit: merge into existing entry, do not create new row. Keep the more complete record, append unique fields from the other.

**Qualification checks:**
- Must have a website URL
- Must have at least one contact signal (email, phone, contact page, contact form)
- Must match target industry (restaurant, hotel, hospitality, F&B)
- Must not be a recruitment agency, equipment supplier, booking platform, or media outlet

**Country verification:**
- Do not rely on domain suffix alone (`.com.au` is not proof of AU)
- Check for AU phone numbers (0x area codes), AU address, or AU-specific content
- Mark country as `Unknown` if uncertain, do not assume

Each discovery run must be recorded in `data/keyword_runs.csv` with `batch_id`, `run_id`, `keyword_id`, `keyword_source_query`, `actual_leads_collected`, and `collection_round`.

<!-- CODEx_END: batch_validation -->

<!-- CODEx_START: discovery_to_enrichment_trigger -->
*Updated: 2026-05-29*

## Discovery-to-Enrichment Trigger

When keyword discovery adds new companies to `data/leads.csv`, they become eligible for A区 form collection.

**Auto-flow rules:**
- AU leads with `customer_type` matching Final Customer or hospitality/restaurant terms are auto-included in the form collection queue.
- Before each form collection run, build the queue with `build_form_kp_candidate_queue.py`. The queue includes all AU leads with missing contact fields.
- No manual approval needed between discovery and enrichment. Approved discovery leads enter the queue on the next run.

**Trigger conditions for A区 handoff:**
- Discovery run added ≥ 10 new AU leads → signal in `current-progress.md` B区 next steps
- AU contact coverage (from A区) drops below 75% → discovery must run before more form collection
- Discovery run added leads with high KP potential (team/about page visible) → prioritize in next A区 run

**Coordination rule:**
- B区 discovery and A区 enrichment can run independently
- B区 writes to `data/leads.csv`, A区 reads from it
- Do not switch task zones without user confirmation (per AGENTS.md Data Operation Rules)

<!-- CODEx_END: discovery_to_enrichment_trigger -->

<!-- CODEx_START: keyword_health_metrics -->
*Updated: 2026-05-29*

## Keyword Health Metrics

B区独立指标，用于评估关键词库整体健康度和发现效率。

**Per-keyword metrics (tracked in `data/search_keywords.csv`):**

| Metric | Source | Meaning |
|--------|--------|---------|
| `discovery_quality_score` | tracker.py / market_intel.py | How well keyword finds relevant companies (0–1) |
| `contactability_score` | tracker.py / market_intel.py | How well keyword results have usable contacts (0–1) |
| `total_runs` | tracker.py | Cumulative run count |
| `total_leads_collected` | tracker.py | Cumulative leads found |
| `contact_found_count` | tracker.py | Cumulative contacts found |

**Per-run metrics (tracked in `data/keyword_runs.csv`):**

| Metric | Meaning |
|--------|---------|
| `actual_leads_collected` | Leads found in this run |
| `qualified_results` | Results passing quality filter |
| `valid_rate` | qualified / total found |

**Library health indicators (calculated on demand):**

| Indicator | Healthy | Warning | Critical |
|-----------|---------|---------|----------|
| Active keyword ratio | ≥ 60% | 40–59% | < 40% |
| Average valid rate (last 10 runs) | ≥ 50% | 30–49% | < 30% |
| Average contactability (active keywords) | ≥ 0.3 | 0.1–0.29 | < 0.1 |
| Keywords in Paused state | < 30% | 30–50% | > 50% |

**Health check command:**
```bash
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

Note: `keyword_health_metrics` is B区独立指标，与 A区的 `data/kp_metrics.json`（KP 管线指标）不冲突。两者存储在不同文件，追踪不同维度。

<!-- CODEx_END: keyword_health_metrics -->

<!-- CODEx_START: domain_cache -->
*Updated: 2026-06-01*

## Domain Cache

Domain cache skips already-visited URLs during B区 discovery, and provides cached cookies/UA for A区 enrichment.

**How it works:**

1. B区 `keyword_discovery.py` checks `E:/cache/domain_cache.json` before fetching each URL
2. If domain is already cached → skip (saves 2-3s per URL)
3. After fetching, domain is marked as valid (has contact signal) or invalid
4. Valid domains also store cookies and UA for A区 reuse
5. A区 `smart_fetch()` checks cache for cookies before making a new request

**Cache file:** `E:/cache/domain_cache.json`

**Cleanup:** Automatic — 5000 max entries, 30-day expiry. Manual: `from scripts.utils.domain_cache import force_cleanup; force_cleanup()`

**Code locations:**
- `scripts/utils/domain_cache.py` — cache module
- `scripts/extraction/keyword_discovery.py:22` — B区 import
- `scripts/kp_pipeline/cloak_fetcher.py:28` — A区 import

<!-- CODEx_END: domain_cache -->
