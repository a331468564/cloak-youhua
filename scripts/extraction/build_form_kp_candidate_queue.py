import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


DATA = Path("data")
REPORTS = Path("reports")

FINAL_CUSTOMER_TERMS = [
    "final customer",
    "restaurant group",
    "multi-location restaurant",
    "multi location restaurant",
    "hotel group",
    "hotel f&b",
    "hospitality group",
    "venue group",
    "event venue",
    "bar group",
    "restaurant / bar",
    "chain restaurant",
    "餐厅集团",
    "酒店集团",
    "酒店餐饮集团",
    "多门店餐厅",
    "餐厅/酒吧集团",
    "活动场地集团",
    "酒店餐饮运营方",
    "含餐饮空间的活动场地",
    "酒店",
    "餐饮",
    "承办",
    "酒吧",
]

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
    "equipment",
    "室内设计",
    "装修",
    "施工",
    "商用厨房",
    "采购",
    "项目公司",
    "设计公司",
    "ff&e",
    "os&e",
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


def text_has_any(value, terms):
    text = (value or "").lower()
    return any(term in text for term in terms)


def classify_lead(lead):
    customer_type = lead.get("customer_type", "")
    if text_has_any(customer_type, SECONDARY_TERMS):
        return "Secondary Supplier/Partner"
    if text_has_any(customer_type, FINAL_CUSTOMER_TERMS):
        return "Restaurant/Hotel Final Customer"
    return "Review Needed"


def domain_from_url(url):
    raw = (url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    domain = parsed.netloc or parsed.path
    return domain.lower().removeprefix("www.").strip("/")


def has_company_form(lead):
    return bool(
        (lead.get("company_contact_form_url") or "").strip()
        or (lead.get("contact_form_url") or "").strip()
    )


def has_company_contact_route(lead):
    fields = [
        "company_email",
        "company_phone",
        "company_contact_page",
        "company_contact_form_url",
        "official_contact_page",
        "contact_form_url",
    ]
    return any((lead.get(field) or "").strip() for field in fields)


def has_key_person(lead, contacts):
    if (lead.get("key_contact_name") or "").strip() or (lead.get("key_contact_job_title") or "").strip():
        return True
    return any((c.get("contact_name") or "").strip() or (c.get("job_title") or "").strip() for c in contacts)


def has_key_direct(lead, contacts):
    lead_direct = any(
        (lead.get(field) or "").strip()
        for field in ["key_contact_email", "key_contact_phone", "key_contact_linkedin_url"]
    )
    contact_direct = any(
        (c.get("email") or "").strip()
        or (c.get("phone") or "").strip()
        or (c.get("linkedin_url") or "").strip()
        for c in contacts
    )
    return lead_direct or contact_direct


def gap_labels(lead, contacts):
    gaps = []
    if not has_company_contact_route(lead):
        gaps.append("missing_company_contact")
    if not has_company_form(lead):
        gaps.append("missing_form")
    if not has_key_person(lead, contacts):
        gaps.append("missing_kp")
    elif not has_key_direct(lead, contacts):
        gaps.append("missing_kp_direct")
    return gaps


def priority_score(lead, contacts, gaps):
    score = 0
    if lead.get("customer_strength_level") in ["High", "高"]:
        score += 30
    if classify_lead(lead) == "Restaurant/Hotel Final Customer":
        score += 30
    if "missing_kp_direct" in gaps:
        score += 25
    if "missing_kp" in gaps:
        score += 20
    if "missing_form" in gaps:
        score += 10
    if has_company_contact_route(lead):
        score += 5
    if has_key_person(lead, contacts):
        score += 5
    return score


def build_queries(lead):
    company = lead.get("company_name", "").strip()
    domain = domain_from_url(lead.get("website", ""))
    base = f'"{company}" Australia' if company else "Australia restaurant group"
    queries = {
        "official_contact_query": f'{base} official contact',
        "form_query": f'{base} contact form OR enquiry OR suppliers',
        "kp_query": f'{base} owner OR founder OR director OR operations OR procurement OR "food and beverage"',
        "public_linkedin_query": f'site:linkedin.com/in "{company}" Australia director OR operations OR procurement',
    }
    if domain:
        queries["site_contact_query"] = f"site:{domain} contact OR enquiry OR suppliers"
        queries["site_kp_query"] = f'site:{domain} team OR people OR leadership OR director OR founder'
    else:
        queries["site_contact_query"] = ""
        queries["site_kp_query"] = ""
    return queries


def recommended_action(gaps):
    if "missing_company_contact" in gaps:
        return "Find official company contact page, email, phone, or form first."
    if "missing_kp" in gaps:
        return "Search owner/founder/director/operations/F&B/procurement KP evidence."
    if "missing_kp_direct" in gaps:
        return "Search direct KP email, phone, or public personal profile; keep confidence notes."
    if "missing_form" in gaps:
        return "Find official enquiry/contact/supplier form as secondary route."
    return "No immediate form/KP gap detected."


def build_queue(leads, contacts, include_review_needed=False):
    contacts_by_lead = {}
    for contact in contacts:
        contacts_by_lead.setdefault(contact.get("lead_id"), []).append(contact)

    rows = []
    for lead in leads:
        if lead.get("country") != "Australia":
            continue
        segment = classify_lead(lead)
        if segment == "Secondary Supplier/Partner":
            continue
        if segment == "Review Needed" and not include_review_needed:
            continue
        lead_contacts = contacts_by_lead.get(lead.get("lead_id"), [])
        gaps = gap_labels(lead, lead_contacts)
        if not gaps:
            continue
        queries = build_queries(lead)
        row = {
            "queue_rank": "",
            "priority_score": priority_score(lead, lead_contacts, gaps),
            "gap_labels": "; ".join(gaps),
            "review_segment": segment,
            "lead_id": lead.get("lead_id", ""),
            "company_name": lead.get("company_name", ""),
            "customer_type": lead.get("customer_type", ""),
            "city_or_region": lead.get("city_or_region", ""),
            "website": lead.get("website", ""),
            "contact_data_level": lead.get("contact_data_level", ""),
            "primary_contact_method": lead.get("primary_contact_method", ""),
            "contact_priority": lead.get("contact_priority", ""),
            "recommended_action": recommended_action(gaps),
            "official_contact_query": queries["official_contact_query"],
            "site_contact_query": queries["site_contact_query"],
            "form_query": queries["form_query"],
            "kp_query": queries["kp_query"],
            "site_kp_query": queries["site_kp_query"],
            "public_linkedin_query": queries["public_linkedin_query"],
            "source_link": lead.get("source_link", ""),
        }
        rows.append(row)

    rows.sort(key=lambda row: (-int(row["priority_score"]), row["company_name"].lower()))
    for index, row in enumerate(rows, start=1):
        row["queue_rank"] = index
    return rows


def write_markdown(path, rows):
    gap_counts = Counter()
    for row in rows:
        for gap in row["gap_labels"].split("; "):
            if gap:
                gap_counts[gap] += 1

    lines = [
        "# Australia Form/KP Candidate Queue",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Summary",
        "",
        f"- Candidate rows: {len(rows)}",
        "- Scope: Australia restaurant/hotel final-customer leads from existing CSV only.",
        "- No new collection or enrichment was executed by this script.",
        "",
        "## Gap Counts",
        "",
    ]
    for gap, count in gap_counts.most_common():
        lines.append(f"- `{gap}`: {count}")

    lines.extend([
        "",
        "## Top Candidates",
        "",
        "| Rank | Company | Gaps | Action |",
        "| --- | --- | --- | --- |",
    ])
    for row in rows[:20]:
        lines.append(
            f"| {row['queue_rank']} | {row['company_name']} | "
            f"{row['gap_labels']} | {row['recommended_action']} |"
        )

    lines.extend([
        "",
        "## Operating Notes",
        "",
        "- Use the CSV output as a manual search queue or as input for the next local helper.",
        "- Save only reviewable public-source evidence with source links and confidence notes.",
        "- Do not use account-based, paid, login-only, or automated social-platform tools without explicit approval.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build a form/KP search candidate queue from existing AU leads.")
    parser.add_argument("--include-review-needed", action="store_true")
    parser.add_argument("--output-prefix", default="", help="Output prefix without extension.")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    prefix = Path(args.output_prefix) if args.output_prefix else REPORTS / f"au-form-kp-candidate-queue-{ts}"

    leads = read_csv(DATA / "leads.csv")
    contacts = read_csv(DATA / "contacts.csv")
    rows = build_queue(leads, contacts, include_review_needed=args.include_review_needed)

    fields = [
        "queue_rank",
        "priority_score",
        "gap_labels",
        "review_segment",
        "lead_id",
        "company_name",
        "customer_type",
        "city_or_region",
        "website",
        "contact_data_level",
        "primary_contact_method",
        "contact_priority",
        "recommended_action",
        "official_contact_query",
        "site_contact_query",
        "form_query",
        "kp_query",
        "site_kp_query",
        "public_linkedin_query",
        "source_link",
    ]
    write_csv(prefix.with_suffix(".csv"), rows, fields)
    write_markdown(prefix.with_suffix(".md"), rows)
    print(f"Wrote {len(rows)} candidates to {prefix.with_suffix('.csv')} and {prefix.with_suffix('.md')}")


if __name__ == "__main__":
    main()
