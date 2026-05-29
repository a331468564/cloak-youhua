import argparse
import csv
from datetime import datetime
from pathlib import Path


DEFAULT_CITIES = [
    "Sydney",
    "Melbourne",
    "Brisbane",
    "Perth",
    "Adelaide",
    "Gold Coast",
    "Canberra",
    "Hobart",
]

CUSTOMER_TYPES = [
    ("restaurant fit out company", "Supplier / Partner Finding"),
    ("hospitality interior design", "Supplier / Partner Finding"),
    ("commercial kitchen fit out", "Supplier / Partner Finding"),
    ("restaurant design company", "Supplier / Partner Finding"),
    ("hotel procurement FF&E OS&E", "Contact Finding"),
    ("restaurant group", "Discovery"),
    ("hospitality group", "Discovery"),
]

KP_PATTERNS = [
    '"{query}" "{city}" "contact" "director"',
    '"{query}" "{city}" "quote" OR "enquiry"',
    '"{query}" "{city}" "project manager"',
    '"{query}" "{city}" "operations manager"',
    '"{query}" "{city}" "supplier" OR "procurement"',
    '"{query}" "{city}" filetype:pdf "director"',
    'site:theorg.com "{query}" "{city}" CEO OR Director',
    'site:linkedin.com/in "{query}" "{city}" director OR operations',
    'site:linkedin.com/in "{query}" "{city}" owner OR founder OR "general manager"',
    'site:linkedin.com/in "{query}" "{city}" "food and beverage" OR F&B OR procurement',
]

DOMAIN_PATTERNS = [
    'site:{domain} contact',
    'site:{domain} team OR people OR leadership',
    'site:{domain} director OR founder OR partner',
    'site:{domain} procurement OR supplier OR "trade account"',
    'site:{domain} filetype:pdf director OR "capability statement"',
    'site:linkedin.com/in "{domain}" director OR owner OR founder OR operations',
    'site:linkedin.com/in "{domain}" procurement OR purchasing OR "food and beverage" OR F&B',
    'site:linkedin.com/company "{domain}"',
]


def build_discovery_queries(country, cities, limit):
    rows = []
    for city in cities:
        for customer_type, intent in CUSTOMER_TYPES:
            for pattern in KP_PATTERNS:
                query = pattern.format(query=customer_type, city=city)
                rows.append({
                    "task_id": f"TASK-{len(rows) + 1:04d}",
                    "country": country,
                    "city": city,
                    "customer_type": customer_type,
                    "search_intent": intent,
                    "query_type": "discovery_kp_form",
                    "query": query,
                    "review_goal": "Find official website, official form, and public KP source.",
                    "minimum_save_rule": "Save only if official company page or reviewable public KP source is found.",
                })
                if len(rows) >= limit:
                    return rows
    return rows


def build_domain_queries(country, domains):
    rows = []
    for domain in domains:
        clean = domain.replace("https://", "").replace("http://", "").strip("/ ")
        for pattern in DOMAIN_PATTERNS:
            rows.append({
                "task_id": f"DOMAIN-{len(rows) + 1:04d}",
                "country": country,
                "city": "",
                "customer_type": "",
                "search_intent": "Decision Maker Finding",
                "query_type": "domain_kp_form",
                "query": pattern.format(domain=clean),
                "review_goal": "Find official team/contact/supplier/KP page for known lead.",
                "minimum_save_rule": "Update lead/contact only with source link and confidence note.",
            })
    return rows


def write_rows(rows, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "task_id",
        "country",
        "city",
        "customer_type",
        "search_intent",
        "query_type",
        "query",
        "review_goal",
        "minimum_save_rule",
    ]
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Generate reviewable KP/form search queries.")
    parser.add_argument("--country", default="Australia")
    parser.add_argument("--cities", default=",".join(DEFAULT_CITIES), help="Comma-separated city list.")
    parser.add_argument("--limit", type=int, default=20, help="Number of discovery tasks to generate.")
    parser.add_argument("--domains", default="", help="Comma-separated known domains for domain-specific KP searches.")
    parser.add_argument("--output", default="", help="Output CSV path. Defaults to reports/kp-form-query-tasks-YYYYMMDD-HHMMSS.csv")
    args = parser.parse_args()

    cities = [c.strip() for c in args.cities.split(",") if c.strip()]
    rows = build_discovery_queries(args.country, cities, args.limit)
    if args.domains.strip():
        domains = [d.strip() for d in args.domains.split(",") if d.strip()]
        rows.extend(build_domain_queries(args.country, domains))

    if args.output:
        output = Path(args.output)
    else:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = Path("reports") / f"kp-form-query-tasks-{ts}.csv"
    write_rows(rows, output)
    print(f"Wrote {len(rows)} query tasks to {output}")


if __name__ == "__main__":
    main()
