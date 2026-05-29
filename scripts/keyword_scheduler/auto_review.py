"""Auto-review keyword suggestions using historical performance scores.

Reads suggested_keywords.csv, scores candidates via market_intel.score_candidates(),
and sets review_status to approved / review / rejected based on thresholds.
"""

import csv
import argparse
from pathlib import Path


def auto_review(
    suggested_csv: Path,
    runs_csv: Path,
    keywords_csv: Path,
    approve_threshold: float = 0.6,
    reject_threshold: float = 0.4,
    dry_run: bool = False,
) -> dict[str, int]:
    """Score and auto-classify keyword suggestions.

    Returns counts: {"approved": N, "review": N, "rejected": N, "skipped": N}
    """
    from scripts.keyword_scheduler.market_intel import score_candidates

    # Load suggestions
    rows = []
    with open(suggested_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else []

    if not rows:
        print("[AutoReview] No suggestions found.")
        return {"approved": 0, "review": 0, "rejected": 0, "skipped": 0}

    # Build candidate dicts for scoring (only pending rows)
    pending_indices = []
    candidates = []
    for i, row in enumerate(rows):
        status = (row.get("review_status") or "").strip().lower()
        if status in ("approved", "rejected"):
            continue  # already decided
        pending_indices.append(i)
        candidates.append({
            "keyword_pattern": row.get("keyword_pattern", ""),
            "template_id": row.get("template_id", ""),
            "generation_source": row.get("generation_source", "generator"),
            "risk_level": row.get("risk_level", "medium"),
            "priority_hint": row.get("priority_hint", "medium"),
            "dimensions_used": {
                "customer_type": row.get("customer_type", ""),
                "role": row.get("role", ""),
                "geo": row.get("geo", ""),
                "intent": row.get("intent", ""),
                "org_form": row.get("org_form", ""),
                "source_modifier": row.get("source_modifier", ""),
                "trigger_event": row.get("trigger_event", ""),
            },
        })

    if not candidates:
        print("[AutoReview] No pending suggestions to review.")
        return {"approved": 0, "review": 0, "rejected": 0, "skipped": len(rows)}

    # Score candidates
    scored = score_candidates(candidates, runs_csv, keywords_csv)

    # Apply thresholds and update review_status
    counts = {"approved": 0, "review": 0, "rejected": 0, "skipped": 0}
    for candidate, idx in zip(scored, pending_indices):
        score = candidate.get("score", 0.0)
        rows[idx]["score"] = str(round(score, 3))

        if score >= approve_threshold:
            rows[idx]["review_status"] = "approved"
            counts["approved"] += 1
        elif score < reject_threshold:
            rows[idx]["review_status"] = "rejected"
            counts["rejected"] += 1
        else:
            rows[idx]["review_status"] = "review"
            counts["review"] += 1

    # Count already-decided rows as skipped
    for row in rows:
        status = (row.get("review_status") or "").strip().lower()
        if status in ("approved", "rejected") and row not in [rows[i] for i in pending_indices]:
            counts["skipped"] += 1

    if not dry_run:
        with open(suggested_csv, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return counts


def main():
    parser = argparse.ArgumentParser(description="Auto-review keyword suggestions")
    parser.add_argument("--suggested", default=str(Path(__file__).resolve().parents[2] / "reports" / "suggested_keywords.csv"))
    parser.add_argument("--runs", default=str(Path(__file__).resolve().parents[2] / "data" / "keyword_runs.csv"))
    parser.add_argument("--keywords", default=str(Path(__file__).resolve().parents[2] / "data" / "search_keywords.csv"))
    parser.add_argument("--approve-threshold", type=float, default=0.6)
    parser.add_argument("--reject-threshold", type=float, default=0.4)
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    counts = auto_review(
        suggested_csv=Path(args.suggested),
        runs_csv=Path(args.runs),
        keywords_csv=Path(args.keywords),
        approve_threshold=args.approve_threshold,
        reject_threshold=args.reject_threshold,
        dry_run=args.dry_run,
    )

    action = "Would classify" if args.dry_run else "Classified"
    print(f"[AutoReview] {action}:")
    print(f"  approved: {counts['approved']}")
    print(f"  review:   {counts['review']}")
    print(f"  rejected: {counts['rejected']}")
    print(f"  skipped:  {counts['skipped']}")


if __name__ == "__main__":
    main()
