"""Keyword selection and template expansion."""

import csv
import random
from datetime import datetime
from pathlib import Path

_ACTIVE_STATUSES = {"Active", "Testing", "New"}

def select_eligible_keywords(keywords_csv: Path, config: dict) -> list[dict]:
    """Read keywords CSV, filter by status and cooldown, sort by priority.

    Returns list of keyword dicts sorted by priority (high > medium > low),
    then by discovery_quality_score descending, with penalties for repeated failures.
    """
    enforce_cooldown = config.get("cooldown_enforcement", True)
    max_kw = config.get("max_keywords_per_run", 5)
    priority_weights = config.get("priority_weights", {"high": 1.0, "medium": 0.7, "low": 0.4})
    now = datetime.now()

    # Auto-pause: keywords with 5+ runs and 0 leads → Paused
    _AUTO_PAUSE_THRESHOLD = 5
    rows_to_writeback = []

    rows = []
    with open(keywords_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = (row.get("keyword_status") or "").strip()
            if status not in _ACTIVE_STATUSES:
                continue

            # Auto-pause check: 5+ runs, 0 leads → mark Paused
            try:
                total_runs = int(row.get("total_runs") or 0)
                total_leads = int(row.get("total_leads_collected") or 0)
            except ValueError:
                total_runs, total_leads = 0, 0
            if total_runs >= _AUTO_PAUSE_THRESHOLD and total_leads == 0:
                row["keyword_status"] = "Paused"
                rows_to_writeback.append(row)
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

    # Write back auto-paused keywords
    if rows_to_writeback:
        _writeback_paused(keywords_csv, rows_to_writeback)

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
        # Run count penalty: keywords with many runs but no results sink lower
        try:
            runs = int(kw.get("total_runs") or 0)
            leads = int(kw.get("total_leads_collected") or 0)
        except ValueError:
            runs, leads = 0, 0
        if runs > 0 and leads == 0:
            run_penalty = min(runs * 0.5, 4.0)  # cap at -4.0
        else:
            run_penalty = 0.0
        # Jitter to rotate among same-score keywords across runs
        jitter = random.uniform(-0.5, 0.5)
        return (-weight, -(quality + boost - run_penalty + jitter))

    rows.sort(key=_sort_key)
    return rows[:max_kw]


def _writeback_paused(keywords_csv: Path, paused_rows: list[dict]):
    """Write back auto-paused keyword statuses to the CSV file."""
    import shutil
    tmp_path = keywords_csv.with_suffix(".csv.tmp")
    paused_ids = {r["keyword_id"] for r in paused_rows}
    with open(keywords_csv, "r", encoding="utf-8-sig") as src, \
         open(tmp_path, "w", encoding="utf-8-sig", newline="") as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if row.get("keyword_id") in paused_ids:
                row["keyword_status"] = "Paused"
            writer.writerow(row)
    shutil.move(str(tmp_path), str(keywords_csv))


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


# --- CLI entry point ---

def main():
    """CLI entry point for keyword selection and queue building.

    Note: executor.py was removed — use keyword_discovery.py for end-to-end discovery.
    This module only provides: select_eligible_keywords(), expand_templates(), build_query_queue().
    """
    import argparse
    from scripts.keyword_scheduler.config import load_config

    parser = argparse.ArgumentParser(description="Keyword scheduler — selects and expands keywords")
    parser.add_argument("--keywords", default=str(Path(__file__).resolve().parents[2] / "data" / "search_keywords.csv"))
    parser.add_argument("--limit", type=int, default=None, help="Override max keywords per run")
    parser.add_argument("--dry-run", action="store_true", help="Show selected keywords without executing")
    args = parser.parse_args()

    config = load_config()
    if args.limit:
        config["max_keywords_per_run"] = args.limit

    keywords_csv = Path(args.keywords)

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

    # Use keyword_discovery.py for end-to-end discovery
    print("[Scheduler] To run discovery, use: python scripts/extraction/keyword_discovery.py --limit <N>")


if __name__ == "__main__":
    main()
