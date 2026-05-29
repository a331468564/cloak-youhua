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

                # Auto-compute scores from cumulative data
                runs = int(row.get("total_runs") or 0)
                total_leads = int(row.get("total_leads_collected") or 0)
                contacts = int(row.get("contact_found_count") or 0)
                avg_leads = total_leads / max(runs, 1)
                contact_rate = contacts / max(total_leads, 1)
                row["discovery_quality_score"] = str(round(min(5.0, avg_leads * 0.5), 1))
                row["contactability_score"] = str(round(min(5.0, contact_rate * 5), 1))

                # Auto status adjustment
                dq = float(row["discovery_quality_score"])
                if runs >= 3 and dq < 1.0:
                    row["keyword_status"] = "Paused"
                elif runs >= 1 and dq >= 3.0 and (row.get("keyword_status") or "") == "New":
                    row["keyword_status"] = "Active"
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
