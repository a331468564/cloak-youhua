"""Keyword selection and template expansion."""

import csv
import random
from datetime import datetime
from pathlib import Path

try:
    from scripts.reports.timer import RunTimer
except ImportError:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "reports"))
    from timer import RunTimer

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


# --- CLI entry point ---

def main():
    import argparse
    from scripts.keyword_scheduler.config import load_config
    from scripts.keyword_scheduler.tracker import update_keyword_stats, append_run_log
    from scripts.extraction.keyword_discovery import discover_from_keyword, save_to_leads, load_existing_leads, close_browser

    parser = argparse.ArgumentParser(description="Keyword scheduler — discovers new companies via Google search")
    parser.add_argument("--keywords", default=str(Path(__file__).resolve().parents[2] / "data" / "search_keywords.csv"))
    parser.add_argument("--runs-log", default=str(Path(__file__).resolve().parents[2] / "data" / "keyword_runs.csv"))
    parser.add_argument("--limit", type=int, default=None, help="Override max keywords per run")
    parser.add_argument("--max-results", type=int, default=5, help="Google results per keyword")
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

    with RunTimer():
        # Load existing leads for dedup
        existing_names, existing_domains, _ = load_existing_leads()
        print(f"[Scheduler] Existing: {len(existing_names)} companies, {len(existing_domains)} domains")

        # Discover companies for each keyword
        batch_id = args.batch_id or f"BATCH-KW-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        all_new = []
        result_counts = {}

        for item in queue:
            kid = item["keyword_id"]
            query = item["source_query"]
            print(f"\n[Scheduler] Searching: {kid} — {query}")

            new_companies = discover_from_keyword(
                query, args.max_results, existing_names, existing_domains
            )
            print(f"  Found {len(new_companies)} new companies")

            # Count contacts found
            contacts = sum(1 for c in new_companies if c.get("email") or c.get("phone"))
            result_counts[kid] = {"leads": len(new_companies), "contacts": contacts}
            all_new.extend(new_companies)

            # Update tracking per keyword
            update_keyword_stats(
                keywords_csv, kid,
                leads_collected=len(new_companies),
                contacts_found=contacts,
            )
            append_run_log(
                runs_csv,
                batch_id=batch_id,
                keyword_id=kid,
                keyword_source_query=query,
                leads_collected=len(new_companies),
                contacts_found=contacts,
            )

        # Save all new companies to leads.csv
        if all_new:
            added = save_to_leads(all_new)
            print(f"\n[Scheduler] Added {added} new leads to data/leads.csv")
        else:
            print("\n[Scheduler] No new companies discovered.")

        close_browser()
    print(f"[Scheduler] Updated tracking for {len(queue)} keywords.")


if __name__ == "__main__":
    main()
