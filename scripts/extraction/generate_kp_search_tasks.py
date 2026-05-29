import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


FINAL_CUSTOMER_KEYWORDS = (
    "restaurant",
    "hotel",
    "hospitality",
    "venue",
    "bar",
    "餐厅",
    "酒店",
    "餐饮",
    "酒吧",
    "场地",
)

SECONDARY_KEYWORDS = (
    "design",
    "fitout",
    "fit out",
    "interior",
    "kitchen",
    "supplier",
    "procurement",
    "ff&e",
    "os&e",
    "设计",
    "装修",
    "施工",
    "厨房",
    "采购",
    "供应",
)

DIRECT_CONTACT_LEVELS = {
    "Direct Key Contact Found",
    "已找到关键人直联",
}

TASK_PATTERNS = (
    {
        "task_type": "official_team_leadership",
        "search_intent": "Decision Maker Finding",
        "query": 'site:{domain} team OR people OR leadership OR management',
        "review_goal": "Find official team, leadership, management, or people pages.",
    },
    {
        "task_type": "official_owner_director",
        "search_intent": "Decision Maker Finding",
        "query": 'site:{domain} founder OR owner OR director OR partner OR executive',
        "review_goal": "Find official owner, founder, director, partner, or executive evidence.",
    },
    {
        "task_type": "official_operations_fb",
        "search_intent": "Decision Maker Finding",
        "query": 'site:{domain} "operations manager" OR "general manager" OR "food and beverage" OR F&B',
        "review_goal": "Find official operations, general manager, or food-and-beverage contacts.",
    },
    {
        "task_type": "official_procurement",
        "search_intent": "Decision Maker Finding",
        "query": 'site:{domain} procurement OR purchasing OR supplier OR "trade account"',
        "review_goal": "Find official procurement, purchasing, or supplier contact evidence.",
    },
    {
        "task_type": "official_pdf_people",
        "search_intent": "Decision Maker Finding",
        "query": 'site:{domain} filetype:pdf director OR founder OR owner OR manager',
        "review_goal": "Find official PDFs with named decision makers.",
    },
    {
        "task_type": "web_owner_director",
        "search_intent": "Decision Maker Finding",
        "query": '"{company_name}" founder OR owner OR director OR partner',
        "review_goal": "Find public source evidence for owners, founders, directors, or partners.",
    },
    {
        "task_type": "web_operations_fb",
        "search_intent": "Decision Maker Finding",
        "query": '"{company_name}" "operations manager" OR "general manager" OR "food and beverage" OR F&B',
        "review_goal": "Find public source evidence for operations, GM, or F&B decision makers.",
    },
    {
        "task_type": "linkedin_manual_review",
        "search_intent": "Manual Review Entry Point",
        "query": 'site:linkedin.com/in "{company_name}" director OR owner OR founder OR operations OR "general manager"',
        "review_goal": "Find LinkedIn profile URLs for manual review only; do not automate LinkedIn browsing.",
    },
)

KNOWN_KP_PATTERNS = (
    {
        "task_type": "known_kp_official_site",
        "search_intent": "Direct Contact Finding",
        "query": 'site:{domain} "{key_contact_name}"',
        "review_goal": "Find official source evidence for the known key person.",
    },
    {
        "task_type": "known_kp_direct_email",
        "search_intent": "Direct Contact Finding",
        "query": '"{key_contact_name}" "{company_name}" email OR phone OR contact',
        "review_goal": "Find direct email, phone, or contact evidence for the known key person.",
    },
    {
        "task_type": "known_kp_linkedin_manual_review",
        "search_intent": "Manual Review Entry Point",
        "query": 'site:linkedin.com/in "{key_contact_name}" "{company_name}"',
        "review_goal": "Find a LinkedIn profile URL for manual review only; do not automate LinkedIn browsing.",
    },
)


def clean_domain(website):
    if not website:
        return ""

    parsed = urlparse(website if "://" in website else f"https://{website}")
    domain = parsed.netloc or parsed.path
    domain = domain.lower().strip().strip("/")

    if domain.startswith("www."):
        domain = domain[4:]

    return domain


def looks_like_final_customer(row):
    text = " ".join(
        row.get(field, "")
        for field in (
            "company_name",
            "industry_type",
            "customer_type",
            "project_signal",
            "product_service_fit",
            "notes",
        )
    ).lower()

    has_final_signal = any(keyword in text for keyword in FINAL_CUSTOMER_KEYWORDS)
    has_secondary_signal = any(keyword in text for keyword in SECONDARY_KEYWORDS)
    return has_final_signal and not has_secondary_signal


def priority_bucket(row):
    level = row.get("contact_data_level", "")
    strength = row.get("customer_strength_level", "")
    has_contact_route = any(
        row.get(field, "").strip()
        for field in (
            "company_email",
            "company_phone",
            "company_contact_page",
            "company_contact_form_url",
            "company_linkedin_url",
            "key_contact_linkedin_url",
        )
    )

    if level in DIRECT_CONTACT_LEVELS:
        return "P3_verify_existing_direct_kp"

    if "已识别关键人" in level or "Key Person Identified" in level:
        return "P1_find_direct_route_for_known_kp"

    if strength in ("高", "High") and has_contact_route:
        return "P2_find_kp_for_strong_company_route"

    return "P4_lower_priority_kp_discovery"


def split_known_people(row):
    names = [item.strip() for item in row.get("key_contact_name", "").split(";") if item.strip()]
    titles = [item.strip() for item in row.get("key_contact_job_title", "").split(";") if item.strip()]

    people = []
    for index, name in enumerate(names):
        title = titles[index] if index < len(titles) else ""
        people.append((name, title))

    return people


def build_tasks(leads, country, include_secondary, limit_leads, max_tasks_per_lead):
    selected = []

    for row in leads:
        if row.get("country") != country:
            continue

        is_final = looks_like_final_customer(row)
        if not is_final and not include_secondary:
            continue

        domain = clean_domain(row.get("website", ""))
        if not domain:
            continue

        selected.append((priority_bucket(row), is_final, domain, row))

    selected.sort(
        key=lambda item: (
            item[0],
            item[3].get("lead_id", ""),
        )
    )

    if limit_leads:
        selected = selected[:limit_leads]

    rows = []
    for bucket, is_final, domain, lead in selected:
        patterns = []
        known_people = split_known_people(lead)
        for person_name, person_title in known_people:
            for pattern in KNOWN_KP_PATTERNS:
                patterns.append((pattern, person_name, person_title))
        for pattern in TASK_PATTERNS:
            patterns.append((pattern, "", ""))

        for pattern, person_name, person_title in patterns[:max_tasks_per_lead]:
            query = pattern["query"].format(
                domain=domain,
                company_name=lead.get("company_name", ""),
                key_contact_name=person_name,
            )
            rows.append(
                {
                    "task_id": f"KPSEARCH-{len(rows) + 1:04d}",
                    "lead_id": lead.get("lead_id", ""),
                    "company_name": lead.get("company_name", ""),
                    "website": lead.get("website", ""),
                    "domain": domain,
                    "country": lead.get("country", ""),
                    "city_or_region": lead.get("city_or_region", ""),
                    "customer_type": lead.get("customer_type", ""),
                    "customer_strength_level": lead.get("customer_strength_level", ""),
                    "contact_data_level": lead.get("contact_data_level", ""),
                    "key_contact_name": person_name,
                    "key_contact_job_title": person_title,
                    "priority_bucket": bucket,
                    "is_final_customer_candidate": "Yes" if is_final else "No",
                    "task_type": pattern["task_type"],
                    "search_intent": pattern["search_intent"],
                    "query": query,
                    "review_goal": pattern["review_goal"],
                    "save_rule": (
                        "Register in contacts.csv when a person name or person-specific URL/email/phone "
                        "has a source link, confidence, status, and uncertainty note; review again before outreach."
                    ),
                    "linkedin_boundary": (
                        "LinkedIn URLs are manual review entry points only; do not automate login, browsing, "
                        "messaging, or export."
                        if pattern["task_type"] in (
                            "linkedin_manual_review",
                            "known_kp_linkedin_manual_review",
                        )
                        else ""
                    ),
                }
            )

    return rows


def write_csv(rows, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "task_id",
        "lead_id",
        "company_name",
        "website",
        "domain",
        "country",
        "city_or_region",
        "customer_type",
        "customer_strength_level",
        "contact_data_level",
        "key_contact_name",
        "key_contact_job_title",
        "priority_bucket",
        "is_final_customer_candidate",
        "task_type",
        "search_intent",
        "query",
        "review_goal",
        "save_rule",
        "linkedin_boundary",
    ]

    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows, output, source_path):
    output.parent.mkdir(parents=True, exist_ok=True)
    lead_ids = {row["lead_id"] for row in rows}
    buckets = Counter(row["priority_bucket"] for row in rows)
    task_types = Counter(row["task_type"] for row in rows)

    lines = [
        "# KP Search Tasks",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Scope",
        "",
        f"- Source: `{source_path}`",
        f"- Leads covered: {len(lead_ids)}",
        f"- Tasks generated: {len(rows)}",
        "- Default scope: Australia restaurant/hotel final-customer candidates with official websites.",
        "- Output is a search-task queue only; this generator does not update source CSV files.",
        "- Evidence found from these tasks may be registered directly in `contacts.csv` with source, confidence, status, and uncertainty notes.",
        "",
        "## Priority Buckets",
        "",
    ]

    for bucket, count in buckets.most_common():
        lines.append(f"- `{bucket}`: {count} tasks")

    lines.extend(["", "## Task Types", ""])
    for task_type, count in task_types.most_common():
        lines.append(f"- `{task_type}`: {count} tasks")

    lines.extend(
        [
            "",
            "## CSV Registration Rules",
            "",
            "- Prefer official company pages, official PDFs, and reviewable public evidence.",
            "- Register KP candidates directly when source link, confidence, status, and uncertainty notes are present.",
            "- Review registered candidates again before actual outreach.",
            "- Do not save pure role snippets or search-result URLs as contact records.",
            "- Treat LinkedIn profile URLs as manual review entry points only.",
            "",
            "## First Search Leads",
            "",
        ]
    )

    seen = set()
    for row in rows:
        if row["lead_id"] in seen:
            continue
        seen.add(row["lead_id"])
        lines.append(
            f"- `{row['lead_id']}` {row['company_name']} ({row['priority_bucket']}): {row['website']}"
        )
        if len(seen) >= 15:
            break

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Generate direct KP search tasks for existing lead records."
    )
    parser.add_argument("--leads", default="data/leads.csv")
    parser.add_argument("--country", default="Australia")
    parser.add_argument("--include-secondary", action="store_true")
    parser.add_argument("--limit-leads", type=int, default=30)
    parser.add_argument("--max-tasks-per-lead", type=int, default=len(TASK_PATTERNS))
    parser.add_argument("--output-prefix", default="")
    args = parser.parse_args()

    source_path = Path(args.leads)
    with source_path.open(newline="", encoding="utf-8-sig") as f:
        leads = list(csv.DictReader(f))

    max_tasks = max(1, min(args.max_tasks_per_lead, len(TASK_PATTERNS)))
    rows = build_tasks(
        leads=leads,
        country=args.country,
        include_secondary=args.include_secondary,
        limit_leads=args.limit_leads,
        max_tasks_per_lead=max_tasks,
    )

    if args.output_prefix:
        prefix = Path(args.output_prefix)
    else:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        prefix = Path("reports") / f"kp-search-tasks-{ts}"

    csv_output = prefix.with_suffix(".csv")
    md_output = prefix.with_suffix(".md")

    write_csv(rows, csv_output)
    write_markdown(rows, md_output, source_path)

    print(f"Wrote {len(rows)} KP search tasks for {len({row['lead_id'] for row in rows})} leads.")
    print(f"CSV: {csv_output}")
    print(f"Markdown: {md_output}")


if __name__ == "__main__":
    main()
