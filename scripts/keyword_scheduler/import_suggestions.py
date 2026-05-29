"""Import approved keyword suggestions into search_keywords.csv."""

import csv
from pathlib import Path


# All columns expected in search_keywords.csv
_KEYWORDS_FIELDNAMES = [
    "keyword_id", "target_customer_type", "country_or_region", "city",
    "keyword_pattern", "example_search_query", "search_intent",
    "keyword_intent_type", "priority_level", "keyword_status", "used_recently",
    "last_used_at", "next_allowed_at", "cooldown_days", "blocked_reason",
    "manual_review_required", "discovery_quality_score",
    "contactability_score", "total_runs", "total_leads_collected",
    "ready_to_contact_count", "contact_found_count", "duplicate_count",
    "news_only_count", "no_contact_count", "relevance_ratio",
    "notes", "last_updated", "change_note",
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
    existing_fieldnames: list[str] = []
    max_id = 0

    if keywords_csv.exists():
        with open(keywords_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            existing_fieldnames = list(reader.fieldnames or [])
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

    # Write to keywords CSV — rewrite if existing file has fewer columns than expected
    if new_rows:
        needs_rewrite = (
            existing_fieldnames
            and set(existing_fieldnames) != set(_KEYWORDS_FIELDNAMES)
        )

        if needs_rewrite:
            # Rewrite: full header,补齐 old rows, append new
            all_rows = []
            for row in existing_rows:
                full_row = {fn: "" for fn in _KEYWORDS_FIELDNAMES}
                full_row.update(row)
                all_rows.append(full_row)
            all_rows.extend(new_rows)

            with open(keywords_csv, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=_KEYWORDS_FIELDNAMES)
                writer.writeheader()
                writer.writerows(all_rows)
        else:
            # Append mode — original behavior
            file_existed = keywords_csv.exists() and keywords_csv.stat().st_size > 0
            with open(keywords_csv, "a", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=_KEYWORDS_FIELDNAMES)
                if not file_existed:
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
