"""Keyword selection and template expansion."""

import csv
import random
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

    # Status boost: New keywords get a bonus so untested keywords aren't starved
    _STATUS_BOOST = {"New": 3.0, "Active": 0.0, "Testing": 0.0}

    def _sort_key(kw: dict) -> tuple[float, float]:
        priority = (kw.get("priority_level") or "low").strip().lower()
        weight = priority_weights.get(priority, 0.0)
        try:
            quality = float(kw.get("discovery_quality_score") or 0)
        except ValueError:
            quality = 0.0
        status = (kw.get("keyword_status") or "").strip()
        boost = _STATUS_BOOST.get(status, 0.0)
        # Jitter to rotate among same-score keywords across runs
        jitter = random.uniform(-0.5, 0.5)
        return (-weight, -(quality + boost + jitter))

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


def _parse_extraction_results(output_csv: Path) -> dict[str, dict[str, int]]:
    """Parse extraction output CSV and count results per keyword_id.

    Returns dict: keyword_id -> {"leads": N, "contacts": N}
    """
    _CONTACT_TYPES = {"email", "phone", "mobile", "person_email", "person_phone"}
    counts: dict[str, dict[str, int]] = {}
    if not output_csv or not output_csv.exists():
        return counts

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            kid = (row.get("lead_id") or "").strip()
            if not kid:
                continue
            if kid not in counts:
                counts[kid] = {"leads": 0, "contacts": 0}
            counts[kid]["leads"] += 1
            ctype = (row.get("candidate_type") or "").strip().lower()
            if ctype in _CONTACT_TYPES:
                counts[kid]["contacts"] += 1

    return counts


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

    # Parse extraction results for feedback
    result_counts = _parse_extraction_results(output_csv) if output_csv and output_csv.exists() else {}

    # Update tracking with actual results
    batch_id = args.batch_id or f"BATCH-KW-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    for item in queue:
        kid = item["keyword_id"]
        counts = result_counts.get(kid, {"leads": 0, "contacts": 0})
        update_keyword_stats(
            keywords_csv, kid,
            leads_collected=counts["leads"],
            contacts_found=counts["contacts"],
        )
        append_run_log(
            runs_csv,
            batch_id=batch_id,
            keyword_id=kid,
            keyword_source_query=item["source_query"],
            leads_collected=counts["leads"],
            contacts_found=counts["contacts"],
        )

    print(f"[Scheduler] Updated tracking for {len(queue)} keywords.")


if __name__ == "__main__":
    main()
