"""Generate keywords for new search strategies to break B区 saturation.

Strategies:
1. Association directory crawling (P0) - direct directory pages
2. Expanded venue_subtype + city combinations (P1)
3. Suburb + venue type combinations (P1)

Output: reports/suggested_keywords.csv for import.
"""

import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]


def generate_association_keywords():
    """P0: Association directory keywords - direct member directory pages."""
    kws = []

    # AHA state chapters
    for state_keyword in [
        "Australian Hotels Association member directory site:aha.com.au",
        "AHA NSW member directory hotels pubs venues",
        "AHA Victoria member list hotels venues",
        "AHA Queensland member directory venues",
        "AHA WA member directory Perth hotels",
        "AHA South Australia member directory",
        "AHA Tasmania member directory",
        "Australian Hotels Association ACT member list",
    ]:
        kws.append({
            "keyword_pattern": state_keyword,
            "template_id": "T17",
            "generation_source": "manual-association",
            "risk_level": "low",
            "priority_hint": "high",
        })

    # Restaurant & Catering Australia
    for kw in [
        "Restaurant and Catering Australia member directory",
        "RCA accredited restaurant list Australia",
        "Restaurant Catering Australia find a venue",
    ]:
        kws.append({
            "keyword_pattern": kw,
            "template_id": "T17",
            "generation_source": "manual-association",
            "risk_level": "low",
            "priority_hint": "high",
        })

    # Accommodation Association
    for kw in [
        "Accommodation Association member directory Australia",
        "Accommodation Australia member hotel list",
        "Tourism Accommodation Australia member list",
    ]:
        kws.append({
            "keyword_pattern": kw,
            "template_id": "T17",
            "generation_source": "manual-association",
            "risk_level": "low",
            "priority_hint": "high",
        })

    # State-level associations
    for kw in [
        "Queensland Hotels Association member directory",
        "WA Hotels Association member list Perth",
        "Tasmanian Hospitality Association member directory",
        "Hospitality NT member directory Darwin venues",
    ]:
        kws.append({
            "keyword_pattern": kw,
            "template_id": "T17",
            "generation_source": "manual-association",
            "risk_level": "low",
            "priority_hint": "high",
        })

    # Trade show exhibitors
    for kw in [
        "Fine Food Australia exhibitor list 2025 2026",
        "Foodservice Australia exhibitor directory hospitality",
        "Australian Hospitality Trade Show exhibitor list",
    ]:
        kws.append({
            "keyword_pattern": kw,
            "template_id": "T19",
            "generation_source": "manual-association",
            "risk_level": "low",
            "priority_hint": "high",
        })

    # Chamber of commerce
    for kw in [
        "NSW Business Chamber member hospitality restaurant hotel",
        "Victorian Chamber member restaurant hotel hospitality",
        "CCIWA member hospitality Perth restaurant",
        "Business SA member restaurant hotel Adelaide",
        "Tasmanian Chamber member hospitality restaurant",
    ]:
        kws.append({
            "keyword_pattern": kw,
            "template_id": "T17",
            "generation_source": "manual-association",
            "risk_level": "low",
            "priority_hint": "medium",
        })

    # Industry awards and directories
    for kw in [
        "Australian Hotels Association award winners 2024 2025",
        "Restaurant Catering Australia awards finalists",
        "Good Food Guide Australia restaurant list 2025",
        "Gourmet Traveller best restaurants Australia 2025",
        "AGFG Australian Good Food Guide restaurant directory",
    ]:
        kws.append({
            "keyword_pattern": kw,
            "template_id": "T24",
            "generation_source": "manual-association",
            "risk_level": "low",
            "priority_hint": "high",
        })

    return kws


def generate_venue_subtype_keywords():
    """P1: Expanded venue_subtype + city combinations."""
    kws = []

    # New venue subtypes not yet tested (or barely tested)
    new_subtypes = [
        "omakase restaurant",
        "natural wine bar",
        "craft beer taproom",
        "late night bar",
        "live music venue",
        "function venue",
        "breakfast cafe",
        "burger joint",
        "champagne bar",
        "rooftop restaurant",
        "hidden bar",
        "garden bar",
        "sports bar",
        "teppanyaki restaurant",
        "yakitori bar",
        "izakaya",
        "patisserie",
        "brunch spot",
    ]

    cities = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"]

    for subtype in new_subtypes:
        for city in cities:
            kws.append({
                "keyword_pattern": f"{subtype} {city} contact email",
                "template_id": "T20",
                "generation_source": "manual-venue-expanded",
                "risk_level": "low",
                "priority_hint": "high",
            })
            kws.append({
                "keyword_pattern": f"{subtype} {city} owner OR director",
                "template_id": "T18",
                "generation_source": "manual-venue-expanded",
                "risk_level": "low",
                "priority_hint": "high",
            })

    return kws


def generate_suburb_venue_keywords():
    """P1: Suburb + venue type combinations (granular discovery)."""
    kws = []

    # High-density hospitality suburbs
    suburbs = [
        # Sydney
        "Surry Hills", "Paddington", "Newtown", "Bondi", "Manly",
        "Darlinghurst", "Potts Point", "Redfern", "Marrickville", "Enmore",
        # Melbourne
        "Fitzroy", "Collingwood", "South Yarra", "St Kilda", "Richmond",
        "Northcote", "Brunswick", "Chapel Street", "Windsor", "Prahran",
        # Brisbane
        "Fortitude Valley", "West End", "New Farm", "Paddington",
        "James Street", "Howard Smith Wharves",
        # Perth
        "Fremantle", "Northbridge", "Leederville", "Mount Lawley",
        "Cottesloe", "South Fremantle",
        # Adelaide
        "Norwood", "Glenelg", "Burnside", "North Adelaide",
        "King William Road", "Gouger Street",
    ]

    venue_types = [
        "wine bar", "cocktail bar", "restaurant", "cafe", "pub",
        "gastropub", "bar", "brunch cafe", "bakery", "pizza restaurant",
    ]

    for suburb in suburbs:
        for vtype in venue_types:
            kws.append({
                "keyword_pattern": f"{vtype} {suburb} owner contact",
                "template_id": "T18",
                "generation_source": "manual-suburb-venue",
                "risk_level": "low",
                "priority_hint": "high",
            })

    return kws


def main():
    association_kws = generate_association_keywords()
    venue_kws = generate_venue_subtype_keywords()
    suburb_kws = generate_suburb_venue_keywords()

    all_kws = association_kws + venue_kws + suburb_kws

    print(f"Total new keywords generated: {len(all_kws)}")
    print(f"  Association directory: {len(association_kws)}")
    print(f"  Venue subtype expanded: {len(venue_kws)}")
    print(f"  Suburb + venue: {len(suburb_kws)}")

    # Load existing keywords for dedup
    existing_path = BASE / "data" / "search_keywords.csv"
    existing_patterns = set()
    if existing_path.exists():
        with open(existing_path, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                p = row.get("keyword_pattern", "").strip().lower()
                if p:
                    existing_patterns.add(p)

    # Dedup
    new_kws = []
    seen = set()
    duplicates = 0
    for kw in all_kws:
        pattern_lower = kw["keyword_pattern"].lower()
        if pattern_lower in existing_patterns or pattern_lower in seen:
            duplicates += 1
            continue
        seen.add(pattern_lower)
        new_kws.append(kw)

    print(f"After dedup: {len(new_kws)} new keywords ({duplicates} duplicates removed)")

    # Write to suggested_keywords.csv
    output_path = BASE / "reports" / "suggested_keywords.csv"
    fieldnames = [
        "keyword_pattern", "template_id", "generation_source", "risk_level",
        "priority_hint", "score", "customer_type", "role", "geo", "intent",
        "org_form", "source_modifier", "trigger_event", "review_status",
    ]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for kw in new_kws:
            row = {k: "" for k in fieldnames}
            row.update(kw)
            row["review_status"] = "approved"
            writer.writerow(row)

    print(f"\nWrote to {output_path}")
    print("\nSample keywords (first 15):")
    for kw in new_kws[:15]:
        print(f"  [{kw['template_id']}] [{kw['generation_source']}] {kw['keyword_pattern']}")

    # Also write a summary
    from collections import Counter
    by_source = Counter(kw["generation_source"] for kw in new_kws)
    by_template = Counter(kw["template_id"] for kw in new_kws)

    print("\nBy source:")
    for src, count in by_source.most_common():
        print(f"  {src}: {count}")

    print("\nBy template:")
    for tid, count in by_template.most_common():
        print(f"  {tid}: {count}")


if __name__ == "__main__":
    main()
