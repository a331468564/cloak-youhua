"""Quick data check script. Edit the check_* functions as needed."""
import csv
import json
import os


def check_keyword_coverage():
    """Check which customer types are covered in search_keywords.csv."""
    existing = set()
    with open('data/search_keywords.csv', 'r', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            ct = r.get('target_customer_type', '').strip()
            if ct:
                existing.add(ct.lower())

    with open('config/keyword_dimensions.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    all_ct = config['dimensions']['customer_type']

    covered = [ct for ct in all_ct if ct.lower() in existing]
    uncovered = [ct for ct in all_ct if ct.lower() not in existing]
    print(f'Covered ({len(covered)}): {covered}')
    print(f'Uncovered ({len(uncovered)}): {uncovered}')


def check_kp_metrics(n=5):
    """Show last N entries from kp_metrics.json."""
    path = 'data/kp_metrics.json'
    if not os.path.exists(path):
        print('kp_metrics.json not found')
        return
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for entry in data[-n:]:
        print(json.dumps(entry, indent=2, ensure_ascii=False))


def check_high_priority_ct():
    """Check high-priority customer types: existing vs generated vs missing."""
    existing = set()
    with open('data/search_keywords.csv', 'r', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            ct = r.get('target_customer_type', '').strip()
            if ct:
                existing.add(ct.lower())

    generated_ct = set()
    if os.path.exists('reports/suggested_keywords.csv'):
        with open('reports/suggested_keywords.csv', 'r', encoding='utf-8-sig') as f:
            for r in csv.DictReader(f):
                ct = r.get('customer_type', '').strip()
                if ct:
                    generated_ct.add(ct.lower())

    high_priority = [
        'motel group', 'restaurant franchise', 'hotel chain',
        'restaurant management company', 'hotel management company',
        'hospital food service', 'student accommodation food service',
        'stadium catering', 'airline catering',
        'hospitality consulting firm', 'hotel technology provider',
        'restaurant marketing agency',
    ]

    for ct in high_priority:
        if ct in existing:
            status = 'EXISTING'
        elif ct in generated_ct:
            status = 'GENERATED'
        else:
            status = 'MISSING'
        print(f'  {ct}: {status}')


def check_leads_summary():
    """Quick summary of leads.csv."""
    with open('data/leads.csv', 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    print(f'Total leads: {len(rows)}')
    countries = {}
    for r in rows:
        c = r.get('country', 'unknown')
        countries[c] = countries.get(c, 0) + 1
    for c, n in sorted(countries.items(), key=lambda x: -x[1]):
        print(f'  {c}: {n}')


if __name__ == '__main__':
    import sys
    checks = {
        'keyword': check_keyword_coverage,
        'kp': check_kp_metrics,
        'leads': check_leads_summary,
        'priority': check_high_priority_ct,
    }
    if len(sys.argv) < 2:
        print(f'Usage: python {sys.argv[0]} <{"|".join(checks.keys())}>')
        sys.exit(1)
    name = sys.argv[1]
    if name in checks:
        checks[name]()
    else:
        print(f'Unknown check: {name}. Available: {list(checks.keys())}')
