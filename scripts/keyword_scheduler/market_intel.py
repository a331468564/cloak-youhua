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
