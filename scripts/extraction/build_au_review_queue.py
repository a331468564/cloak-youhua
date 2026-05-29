import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path


DATA = Path("data")
REPORTS = Path("reports")

SECONDARY_TERMS = [
    "fit-out",
    "fit out",
    "interior design",
    "design company",
    "commercial kitchen",
    "procurement",
    "ff&e",
    "os&e",
    "supplier",
    "project company",
    "construction",
    "stainless",
    "equipment",
]

FINAL_TERMS = [
    "restaurant group",
    "multi-location restaurant",
    "hotel group",
    "hotel / hospitality",
    "hotel f&b",
    "hospitality group",
    "event venue",
    "bar group",
    "venue group",
    "restaurant / bar",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def has_any(value, terms):
    text = (value or "").lower()
    return any(term in text for term in terms)


def classify_segment(lead):
    customer_type = lead.get("customer_type", "")
    notes = " ".join([
        lead.get("notes", ""),
        lead.get("enrichment_notes", ""),
        lead.get("next_action", ""),
    ]).lower()
    if "taverners" in lead.get("company_name", "").lower() or "family-office" in notes:
        return "Review Needed"
    if has_any(customer_type, SECONDARY_TERMS):
        return "Secondary Supplier/Partner"
    if has_any(customer_type, FINAL_TERMS):
        return "Restaurant/Hotel Final Customer"
    return "Review Needed"


def contact_score(lead, lead_contacts):
    level = lead.get("contact_data_level", "")
    priority = lead.get("contact_priority", "")
    has_key_email = bool((lead.get("key_contact_email") or "").strip())
    has_key_phone = bool((lead.get("key_contact_phone") or "").strip())
    direct_contacts = [
        c for c in lead_contacts
        if c.get("contact_status") == "Direct Contact Found" or c.get("email") or c.get("phone")
    ]
    if level == "Direct Key Contact Found" and (has_key_email or has_key_phone or direct_contacts):
        return 100 if priority == "High" else 85
    if level == "Key Person Identified":
        return 70
    if level == "Company Contact Only":
        return 45
    return 10


def best_contact_summary(lead, lead_contacts):
    parts = []
    if lead.get("key_contact_name"):
        parts.append(f"KP: {lead.get('key_contact_name')} ({lead.get('key_contact_job_title')})")
    direct = [c for c in lead_contacts if c.get("email") or c.get("phone")]
    if direct:
        samples = []
        for c in direct[:3]:
            bits = [c.get("contact_name") or "Unnamed"]
            if c.get("email"):
                bits.append(c.get("email"))
            if c.get("phone"):
                bits.append(c.get("phone"))
            samples.append(" / ".join(bits))
        parts.append("Direct: " + "; ".join(samples))
    if lead.get("company_email"):
        parts.append("Company email: " + lead.get("company_email"))
    if lead.get("company_phone"):
        parts.append("Company phone: " + lead.get("company_phone"))
    if lead.get("company_contact_form_url"):
        parts.append("Form: " + lead.get("company_contact_form_url"))
    return " | ".join(parts)


def review_action(segment, score, lead):
    if segment == "Secondary Supplier/Partner":
        return "Keep as secondary; do not count toward restaurant/hotel final-customer toolization unless supplier direction is approved."
    if segment == "Review Needed":
        return "Manually confirm fit before outreach or further enrichment."
    if score >= 85:
        return "Review as priority final-customer outreach candidate; verify direct contact confidence before outreach."
    if score >= 70:
        return "Search direct buyer route for identified KP before outreach."
    return "Use company route only as fallback; search procurement/F&B/operations buyer if this account is high value."


def build_rows(leads, contacts):
    contacts_by_lead = {}
    for contact in contacts:
        contacts_by_lead.setdefault(contact.get("lead_id"), []).append(contact)

    rows = []
    for lead in leads:
        if lead.get("country") != "Australia":
            continue
        lead_contacts = contacts_by_lead.get(lead.get("lead_id"), [])
        segment = classify_segment(lead)
        score = contact_score(lead, lead_contacts)
        rows.append({
            "review_rank": "",
            "review_segment": segment,
            "contact_score": score,
            "lead_id": lead.get("lead_id", ""),
            "company_name": lead.get("company_name", ""),
            "customer_type": lead.get("customer_type", ""),
            "city_or_region": lead.get("city_or_region", ""),
            "contact_data_level": lead.get("contact_data_level", ""),
            "contact_priority": lead.get("contact_priority", ""),
            "primary_contact_method": lead.get("primary_contact_method", ""),
            "customer_strength_level": lead.get("customer_strength_level", ""),
            "key_contact_confidence": lead.get("key_contact_confidence", ""),
            "best_contact_summary": best_contact_summary(lead, lead_contacts),
            "recommended_action": review_action(segment, score, lead),
            "next_action": lead.get("next_action", ""),
            "website": lead.get("website", ""),
            "source_link": lead.get("source_link", ""),
        })

    rows.sort(key=lambda r: (
        r["review_segment"] != "Restaurant/Hotel Final Customer",
        -int(r["contact_score"]),
        r["company_name"].lower(),
    ))
    for idx, row in enumerate(rows, start=1):
        row["review_rank"] = idx
    return rows


def write_markdown(path, rows):
    total = len(rows)
    segment_counts = Counter(r["review_segment"] for r in rows)
    level_counts = Counter(r["contact_data_level"] for r in rows)
    priority = [r for r in rows if r["review_segment"] == "Restaurant/Hotel Final Customer" and int(r["contact_score"]) >= 85]
    needs_direct = [r for r in rows if r["review_segment"] == "Restaurant/Hotel Final Customer" and r["contact_data_level"] == "Key Person Identified"]
    secondary = segment_counts.get("Secondary Supplier/Partner", 0)

    lines = [
        "# Australia Final-Customer Review Queue",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Summary",
        "",
        f"- Australia leads reviewed: {total}",
        f"- Restaurant/hotel final customers: {segment_counts.get('Restaurant/Hotel Final Customer', 0)}",
        f"- Secondary supplier/partner leads: {secondary}",
        f"- Review needed: {segment_counts.get('Review Needed', 0)}",
        f"- Priority final-customer candidates: {len(priority)}",
        f"- Final customers with KP identified but direct buyer route still needed: {len(needs_direct)}",
        "",
        "## Contact Levels",
        "",
    ]
    for key, value in level_counts.most_common():
        lines.append(f"- {key or 'Blank'}: {value}")

    lines.extend([
        "",
        "## Highest Priority Final Customers",
        "",
        "| Rank | Company | Contact Level | Contact Method | Recommended Action |",
        "| --- | --- | --- | --- | --- |",
    ])
    for row in priority[:20]:
        lines.append(
            f"| {row['review_rank']} | {row['company_name']} | {row['contact_data_level']} | "
            f"{row['primary_contact_method']} | {row['recommended_action']} |"
        )

    lines.extend([
        "",
        "## Toolization Notes",
        "",
        "- This review queue is auxiliary evidence only. Do not build more segmentation workflow around it unless explicitly requested.",
        "- Do not treat secondary supplier/partner leads as restaurant/hotel final-customer validation samples.",
        "- Direct buyer contact quality remains the main bottleneck after sample-size completion.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build AU final-customer review queue.")
    parser.add_argument("--output-prefix", default="", help="Output prefix without extension.")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    prefix = Path(args.output_prefix) if args.output_prefix else REPORTS / f"au-final-customer-review-{ts}"

    leads = read_csv(DATA / "leads.csv")
    contacts = read_csv(DATA / "contacts.csv")
    rows = build_rows(leads, contacts)

    fields = [
        "review_rank",
        "review_segment",
        "contact_score",
        "lead_id",
        "company_name",
        "customer_type",
        "city_or_region",
        "contact_data_level",
        "contact_priority",
        "primary_contact_method",
        "customer_strength_level",
        "key_contact_confidence",
        "best_contact_summary",
        "recommended_action",
        "next_action",
        "website",
        "source_link",
    ]
    write_csv(prefix.with_suffix(".csv"), rows, fields)
    write_markdown(prefix.with_suffix(".md"), rows)
    print(prefix)


if __name__ == "__main__":
    main()
