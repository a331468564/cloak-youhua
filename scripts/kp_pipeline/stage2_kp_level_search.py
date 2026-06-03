#!/usr/bin/env python3
"""
Stage 2 KP-Level Search Strategy

针对 Tier 3 联系人（仅 LinkedIn，无邮箱/电话）的优化搜索策略。
使用 KP 级搜索查询（人名+公司名）而非公司级查询，提高直联发现率。

Usage:
    python -m scripts.kp_pipeline.stage2_kp_level_search --limit 5
"""
import argparse
import csv
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .stage2_enrich import (
    build_google_dork_queries,
    classify_contact_directness,
    classify_email,
    extract_emails_from_text,
    extract_phones_from_text,
    fetch_page_text,
    human_delay,
)
from .cloak_fetcher import search_google as cloak_search


def load_tier3_contacts(limit=None):
    """加载 Tier 3 联系人（仅 LinkedIn，无邮箱/电话）。"""
    contacts_path = Path(__file__).parent.parent.parent / "data" / "contacts.csv"

    with open(contacts_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    tier3 = []
    for r in rows:
        if r.get("contact_status") == "needs_review":
            continue
        email = r.get("email", "").strip()
        phone = r.get("phone", "").strip()
        linkedin = r.get("linkedin_url", "").strip()

        # Only direct LinkedIn profiles (not search URLs)
        if linkedin and "/in/" in linkedin and not email and not phone:
            tier3.append(r)

    # Group by company to avoid duplicate searches
    by_company = defaultdict(list)
    for r in tier3:
        company = r.get("company_name", "")
        by_company[company].append(r)

    # Flatten with limit
    result = []
    for company, contacts in by_company.items():
        for c in contacts:
            result.append(c)
            if limit and len(result) >= limit:
                break
        if limit and len(result) >= limit:
            break

    return result


def search_kp_contact(kp_name, company_name, domain=None):
    """使用 KP 级搜索查询寻找联系方式。

    Returns:
        dict: {email, phone, linkedin, source_url, confidence}
    """
    result = {
        "email": "",
        "phone": "",
        "linkedin": "",
        "source_url": "",
        "confidence": "Low",
    }

    # Build KP-level queries
    queries = build_google_dork_queries(kp_name, company_name, domain)

    for query in queries[:2]:  # Limit to first 2 queries to save search quota
        try:
            urls = cloak_search(query, max_results=3)
            human_delay(1.0, 0.5)

            for url in urls:
                # Skip LinkedIn URLs (we already have them)
                if "linkedin.com" in url:
                    continue

                # Fetch and extract contacts
                text, error = fetch_page_text(url)
                if not text:
                    continue

                emails = extract_emails_from_text(text)
                phones = extract_phones_from_text(text)

                # Find personal emails matching KP name
                kp_parts = kp_name.lower().split()
                for email in emails:
                    email_lower = email.lower()
                    # Check if email contains KP name parts
                    if any(part in email_lower for part in kp_parts if len(part) > 2):
                        email_type = classify_email(email)
                        if email_type in ("person_email", "possible_person_email"):
                            result["email"] = email
                            result["source_url"] = url
                            result["confidence"] = "High" if email_type == "person_email" else "Medium"
                            return result

                # Find mobile phones (04xx)
                for phone in phones:
                    phone_clean = phone.replace(" ", "").replace("-", "")
                    if phone_clean.startswith("04") or phone_clean.startswith("+614"):
                        result["phone"] = phone
                        result["source_url"] = url
                        result["confidence"] = "High"
                        return result

                human_delay(0.5, 0.3)

        except Exception as e:
            print(f"  Error searching: {e}")
            continue

    return result


def update_contact(contact_id, email, phone, source_url, confidence):
    """更新 contacts.csv 中的联系人信息。"""
    contacts_path = Path(__file__).parent.parent.parent / "data" / "contacts.csv"

    # Read all contacts
    with open(contacts_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    # Find and update target contact
    updated = False
    for row in rows:
        if row.get("contact_id") == contact_id:
            if email:
                row["email"] = email
            if phone:
                row["phone"] = phone
            if source_url:
                row["source_link"] = source_url
            row["contact_status"] = "已找到直联"
            row["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row["change_note"] = f"Stage 2 KP-level search: {confidence} confidence"
            updated = True
            break

    if updated:
        # Write back
        with open(contacts_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return updated


def main():
    parser = argparse.ArgumentParser(description="Stage 2 KP-Level Search")
    parser.add_argument("--limit", type=int, default=5, help="Max contacts to process")
    parser.add_argument("--dry-run", action="store_true", help="Don't update contacts.csv")
    args = parser.parse_args()

    print(f"=== Stage 2 KP-Level Search ===")
    print(f"Limit: {args.limit}, Dry-run: {args.dry_run}")

    # Load Tier 3 contacts
    contacts = load_tier3_contacts(limit=args.limit)
    print(f"Found {len(contacts)} Tier 3 contacts to process")

    # Process each contact
    results = {
        "processed": 0,
        "email_found": 0,
        "phone_found": 0,
        "updated": 0,
    }

    for i, contact in enumerate(contacts, 1):
        contact_id = contact.get("contact_id", "")
        kp_name = contact.get("contact_name", "")
        company_name = contact.get("company_name", "")
        linkedin = contact.get("linkedin_url", "")

        print(f"\n[{i}/{len(contacts)}] {kp_name} @ {company_name}")
        print(f"  LinkedIn: {linkedin}")

        # Extract domain from LinkedIn or company name
        domain = None
        if linkedin:
            # Try to infer domain from company name
            company_lower = company_name.lower().replace(" ", "")
            domain = f"{company_lower}.com.au"

        # Search for contact
        result = search_kp_contact(kp_name, company_name, domain)
        results["processed"] += 1

        if result["email"]:
            print(f"  [EMAIL] {result['email']}")
            results["email_found"] += 1
        if result["phone"]:
            print(f"  [PHONE] {result['phone']}")
            results["phone_found"] += 1

        if result["email"] or result["phone"]:
            if not args.dry_run:
                success = update_contact(
                    contact_id,
                    result["email"],
                    result["phone"],
                    result["source_url"],
                    result["confidence"],
                )
                if success:
                    results["updated"] += 1
                    print(f"  [OK] Contact updated")
        else:
            print(f"  [--] No direct contact found")

        # Rate limiting
        human_delay(2.0, 1.0)

    # Summary
    print(f"\n=== Summary ===")
    print(f"Processed: {results['processed']}")
    print(f"Email found: {results['email_found']}")
    print(f"Phone found: {results['phone_found']}")
    print(f"Contacts updated: {results['updated']}")
    print(f"Direct contact rate: {(results['email_found'] + results['phone_found']) / max(results['processed'], 1) * 100:.1f}%")


if __name__ == "__main__":
    main()
