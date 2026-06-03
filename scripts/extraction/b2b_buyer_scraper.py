"""B2B 平台买家爬取脚本。

从 TradeKey、EC21 等 B2B 平台爬取采购需求，提取买家信息，
去重后写入 data/leads.csv。

用法:
  python scripts/extraction/b2b_buyer_scraper.py --limit 3
  python scripts/extraction/b2b_buyer_scraper.py --platform tradekey --limit 5
  python scripts/extraction/b2b_buyer_scraper.py --dry-run --limit 3

注意：
- TradeKey 买家详情页需要登录才能看到联系方式
- 本脚本先提取公开可见的买家列表信息（公司名、国家、采购产品）
- 联系方式补全需要后续通过 Google 搜索公司名来完成
"""

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin

sys.path.insert(0, str(Path(__file__).parent.parent))
from kp_pipeline.cloak_fetcher import cloak_fetch, close_browser
from scripts.reports.timer import RunTimer

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA = PROJECT_ROOT / "data"
REPORTS = PROJECT_ROOT / "reports"
CONFIG_FILE = PROJECT_ROOT / "config" / "hs_codes.json"

# TradeKey 产品 → URL 映射
TRADEKEY_PRODUCT_URLS = {
    "restaurant_furniture": "restaurant-furniture",
    "dining_chairs": "dining-chairs",
    "restaurant_tables": "restaurant-tables",
    "commercial_furniture": "commercial-furniture",
    "hotel_furniture": "hotel-furniture",
    "cafe_furniture": "cafe-furniture",
    "bar_stools": "bar-stools",
    "outdoor_furniture": "outdoor-furniture",
    "kitchen_equipment": "commercial-kitchen-equipment",
    "tableware": "tableware",
    "porcelain": "porcelain-dinnerware",
    "stainless_steel": "stainless-steel-tableware",
}

# EC21 产品搜索关键词
EC21_PRODUCT_KEYWORDS = {
    "restaurant_furniture": "restaurant furniture",
    "dining_chairs": "dining chairs",
    "restaurant_tables": "restaurant tables",
    "commercial_furniture": "commercial furniture",
    "hotel_furniture": "hotel furniture",
    "cafe_furniture": "cafe furniture",
    "bar_stools": "bar stools",
    "outdoor_furniture": "outdoor furniture",
    "kitchen_equipment": "commercial kitchen equipment",
    "tableware": "restaurant tableware",
    "porcelain": "porcelain dinnerware",
    "stainless_steel": "stainless steel tableware",
}


def load_config():
    """加载 HS 编码配置。"""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_existing_leads():
    """加载已有线索。"""
    leads_path = DATA / "leads.csv"
    names = set()
    domains = set()
    if leads_path.exists():
        with open(leads_path, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                name = (row.get("company_name") or "").strip().lower()
                if name:
                    names.add(name)
                website = (row.get("website") or "").strip().lower()
                if website:
                    d = _extract_domain(website)
                    if d:
                        domains.add(d)
    return names, domains


def _extract_domain(url):
    """从 URL 提取根域名。"""
    try:
        if "://" not in url:
            url = f"https://{url}"
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def scrape_tradekey_listings(product_slug, page=1):
    """爬取 TradeKey 买家列表页。

    Args:
        product_slug: 产品 URL slug (如 'restaurant-furniture')
        page: 页码

    Returns:
        list[dict]: 买家列表 [{title, description, country, date, detail_url}]
    """
    if page == 1:
        url = f"https://www.tradekey.com/{product_slug}-buyer/"
    else:
        url = f"https://www.tradekey.com/{product_slug}-buyer/page_no/{page}"

    print(f"  Fetching: {url}")
    try:
        text, html, cookies, ua, status, error = cloak_fetch(url, timeout=20)
    except Exception as e:
        print(f"  ERROR: Fetch failed: {e}")
        return []

    if error or not text:
        print(f"  ERROR: {error or 'Empty response'}")
        return []

    buyers = []

    # 解析 TradeKey 买家列表页结构
    # 每个买家卡片包含：
    # - 标题（H3 级别，链接到详情页）
    # - 描述片段
    # - 国家
    # - 发布日期

    # 提取所有买家卡片
    # TradeKey 的列表项结构：
    # <div class="..."> <h3><a href="...">Title</a></h3> <p>Description</p> <span>Country</span> <span>Date</span> </div>

    # 方法 1：用正则提取标题和链接
    title_pattern = re.compile(
        r'<h3[^>]*>\s*<a[^>]*href="([^"]*importer\.tradekey\.com[^"]*)"[^>]*>([^<]+)</a>\s*</h3>',
        re.I
    )
    matches = title_pattern.findall(html or "")

    for detail_url, title in matches:
        # 提取该标题附近的内容
        title_pos = (html or "").find(detail_url)
        context = (html or "")[title_pos:title_pos + 1000] if title_pos >= 0 else ""

        # 提取国家
        country = ""
        country_match = re.search(
            r'(?:country|location)[^>]*>\s*([^<]+)</[^>]*>',
            context, re.I
        )
        if country_match:
            country = country_match.group(1).strip()

        # 如果没找到国家，尝试从标志图片提取
        if not country:
            flag_match = re.search(r'alt="([^"]+)"', context)
            if flag_match and len(flag_match.group(1)) < 30:
                country = flag_match.group(1).strip()

        # 提取日期
        date = ""
        date_match = re.search(
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
            context
        )
        if date_match:
            date = date_match.group(1)

        # 提取描述
        desc = ""
        desc_match = re.search(r'<p[^>]*>([^<]{20,500})</p>', context, re.I)
        if desc_match:
            desc = desc_match.group(1).strip()

        buyers.append({
            "title": title.strip(),
            "description": desc,
            "country": country,
            "date": date,
            "detail_url": detail_url,
            "platform": "TradeKey",
        })

    # 方法 2：如果方法 1 没找到，用更宽泛的模式
    if not buyers:
        # 尝试匹配所有 importers.tradekey.com 链接
        all_links = re.findall(
            r'href="(https?://importers\.tradekey\.com/[^"]+)"[^>]*>([^<]+)</a>',
            html or "", re.I
        )
        for detail_url, title in all_links:
            if len(title.strip()) > 5:  # 过滤太短的链接文本
                buyers.append({
                    "title": title.strip(),
                    "description": "",
                    "country": "",
                    "date": "",
                    "detail_url": detail_url,
                    "platform": "TradeKey",
                })

    return buyers


def scrape_tradekey_detail(detail_url):
    """爬取 TradeKey 买家详情页（公开信息）。

    注意：联系方式通常需要登录才能看到。
    这里只提取公开可见的信息。
    """
    try:
        text, html, cookies, ua, status, error = cloak_fetch(detail_url, timeout=15)
    except Exception:
        return {}

    if error or not text:
        return {}

    info = {}

    # 提取公司名
    company_match = re.search(
        r'(?:company|buyer)[^>]*>\s*([^<]{3,100})</[^>]*>',
        html or "", re.I
    )
    if company_match:
        info["company_name"] = company_match.group(1).strip()

    # 提取国家
    country_match = re.search(
        r'(?:country|location)[^>]*>\s*([^<]{3,50})</[^>]*>',
        html or "", re.I
    )
    if country_match:
        info["country"] = country_match.group(1).strip()

    # 提取邮箱（有些公开可见）
    email_match = re.search(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        text or ""
    )
    if email_match:
        info["email"] = email_match.group(0)

    return info


def scrape_ec21_listings(keyword, page=1):
    """爬取 EC21 买家列表页。

    Args:
        keyword: 搜索关键词
        page: 页码

    Returns:
        list[dict]: 买家列表
    """
    url = f"https://www.ec21.com/buy-leads/{keyword.replace(' ', '-')}/"
    if page > 1:
        url = f"{url}?page={page}"

    print(f"  Fetching: {url}")
    try:
        text, html, cookies, ua, status, error = cloak_fetch(url, timeout=20)
    except Exception as e:
        print(f"  ERROR: Fetch failed: {e}")
        return []

    if error or not text:
        print(f"  ERROR: {error or 'Empty response'}")
        return []

    buyers = []

    # EC21 采购需求列表结构
    # 每个采购需求包含：标题、描述、国家、日期
    title_pattern = re.compile(
        r'<(?:h3|h4|div)[^>]*>\s*<a[^>]*href="([^"]*ec21\.com[^"]*)"[^>]*>([^<]+)</a>',
        re.I
    )
    matches = title_pattern.findall(html or "")

    for detail_url, title in matches:
        if "buy-lead" in detail_url or "offer" in detail_url:
            buyers.append({
                "title": title.strip(),
                "description": "",
                "country": "",
                "date": "",
                "detail_url": detail_url,
                "platform": "EC21",
            })

    return buyers


def extract_company_from_title(title):
    """从买家标题中提取公司名。

    TradeKey 标题格式通常是："Company Name wants to buy Product"
    """
    # 模式 1: "Company Name wants to buy..."
    match = re.match(r'^(.+?)\s+(?:wants?|looking|seeking|need)', title, re.I)
    if match:
        return match.group(1).strip()

    # 模式 2: "Buyer: Company Name"
    match = re.match(r'^(?:buyer|importer|company):\s*(.+)', title, re.I)
    if match:
        return match.group(1).strip()

    # 模式 3: 直接用标题（清理后）
    title = re.sub(r'\s*(?:wants?|looking|seeking|need)\s+.*$', '', title, flags=re.I)
    return title.strip() if len(title.strip()) > 3 else ""


def normalize_country(country):
    """标准化国家名称。"""
    country_map = {
        "australia": "Australia", "au": "Australia",
        "united states": "United States", "usa": "United States", "us": "United States",
        "united kingdom": "United Kingdom", "uk": "United Kingdom", "gb": "United Kingdom",
        "canada": "Canada", "ca": "Canada",
        "germany": "Germany", "de": "Germany",
        "singapore": "Singapore", "sg": "Singapore",
        "uae": "UAE", "united arab emirates": "UAE", "ae": "UAE",
        "japan": "Japan", "jp": "Japan",
        "south korea": "South Korea", "korea": "South Korea", "kr": "South Korea",
        "new zealand": "New Zealand", "nz": "New Zealand",
        "saudi arabia": "Saudi Arabia", "sa": "Saudi Arabia",
        "france": "France", "fr": "France",
        "india": "India", "in": "India",
        "indonesia": "Indonesia", "id": "Indonesia",
        "egypt": "Egypt", "eg": "Egypt",
        "turkey": "Turkey", "tr": "Turkey",
        "brazil": "Brazil", "br": "Brazil",
        "mexico": "Mexico", "mx": "Mexico",
        "south africa": "South Africa", "za": "South Africa",
        "nigeria": "Nigeria", "ng": "Nigeria",
        "philippines": "Philippines", "ph": "Philippines",
        "vietnam": "Vietnam", "vn": "Vietnam",
        "thailand": "Thailand", "th": "Thailand",
        "malaysia": "Malaysia", "my": "Malaysia",
    }
    return country_map.get(country.lower().strip(), country)


def save_to_staging(buyers, source_tag="B2B Platform"):
    """将买家信息写入暂存文件 data/b2b_leads_staging.csv。

    不直接写入 leads.csv，等人工审核后再合并。
    """
    staging_path = DATA / "b2b_leads_staging.csv"

    # 读取 leads.csv 的列名作为模板
    leads_path = DATA / "leads.csv"
    if leads_path.exists():
        with open(leads_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            base_fieldnames = reader.fieldnames
    else:
        base_fieldnames = []

    staging_fieldnames = list(base_fieldnames) + ["staging_status", "staging_source", "staging_date"]

    # 读取已有暂存记录数
    existing_count = 0
    existing_names = set()
    if staging_path.exists():
        with open(staging_path, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                existing_count += 1
                name = (row.get("company_name") or "").strip().lower()
                if name:
                    existing_names.add(name)

    now = datetime.now().strftime("%Y-%m-%d")
    added = 0

    write_header = not staging_path.exists()
    with open(staging_path, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=staging_fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()

        for buyer in buyers:
            company_name = buyer.get("company_name", buyer.get("title", "Unknown"))
            if company_name.lower() in existing_names:
                continue

            existing_count += 1
            lead_id = f"B2B-{existing_count:04d}"
            country = normalize_country(buyer.get("country", ""))

            row = {fn: "" for fn in staging_fieldnames}
            row.update({
                "lead_id": lead_id,
                "company_name": company_name,
                "website": "",
                "country": country,
                "industry_type": "Importador/Distribuidor",
                "customer_type": "Importer/Buyer",
                "source_type": source_tag,
                "source_link": buyer.get("detail_url", ""),
                "keyword_source_query": buyer.get("search_keyword", ""),
                "verification_status": "Discovered",
                "contact_research_status": "待处理",
                "last_updated": now,
                "enrichment_notes": f"Discovered via {buyer.get('platform', 'B2B')} platform. {buyer.get('title', '')}",
                "staging_status": "pending",
                "staging_source": "b2b_buyer_scraper",
                "staging_date": now,
            })
            if buyer.get("email"):
                row["email_address"] = buyer["email"]
            writer.writerow(row)
            existing_names.add(company_name.lower())
            added += 1
            safe_name = company_name.encode('ascii', 'replace').decode('ascii')
            print(f"  + {lead_id}: {safe_name} [{country}] ({buyer.get('platform', '')})")

    if added > 0:
        print(f"\n  写入暂存文件: {staging_path}")
        print(f"  待审核: {existing_count} 条 (新增 {added} 条)")
        print(f"  审核后运行: python -m scripts.extraction.merge_staging --source b2b")
    else:
        print(f"\n  无新发现")

    return added


def run_tradekey(product_categories, max_pages=2, existing_names=None, existing_domains=None):
    """运行 TradeKey 爬取。"""
    if existing_names is None:
        existing_names = set()

    all_buyers = []

    for cat_slug in product_categories:
        product_name = cat_slug.replace("-", " ").title()
        print(f"\n--- TradeKey: {product_name} ---")

        for page in range(1, max_pages + 1):
            buyers = scrape_tradekey_listings(cat_slug, page)
            if not buyers:
                print(f"  No results on page {page}, stopping")
                break

            print(f"  Found {len(buyers)} listings on page {page}")

            for buyer in buyers:
                company_name = extract_company_from_title(buyer["title"])
                if not company_name or company_name.lower() in existing_names:
                    continue

                buyer["company_name"] = company_name
                buyer["search_keyword"] = cat_slug
                all_buyers.append(buyer)
                existing_names.add(company_name.lower())

            time.sleep(3)  # 避免被限流

    return all_buyers


def run_ec21(keywords, max_pages=2, existing_names=None, existing_domains=None):
    """运行 EC21 爬取。"""
    if existing_names is None:
        existing_names = set()

    all_buyers = []

    for keyword in keywords:
        print(f"\n--- EC21: {keyword} ---")

        for page in range(1, max_pages + 1):
            buyers = scrape_ec21_listings(keyword, page)
            if not buyers:
                print(f"  No results on page {page}, stopping")
                break

            print(f"  Found {len(buyers)} listings on page {page}")

            for buyer in buyers:
                company_name = extract_company_from_title(buyer["title"])
                if not company_name or company_name.lower() in existing_names:
                    continue

                buyer["company_name"] = company_name
                buyer["search_keyword"] = keyword
                all_buyers.append(buyer)
                existing_names.add(company_name.lower())

            time.sleep(3)

    return all_buyers


def main():
    parser = argparse.ArgumentParser(description="B2B platform buyer scraper")
    parser.add_argument("--platform", choices=["tradekey", "ec21", "all"], default="all",
                       help="Platform to scrape")
    parser.add_argument("--limit", type=int, default=3, help="Number of product categories to search")
    parser.add_argument("--max-pages", type=int, default=2, help="Max pages per product category")
    parser.add_argument("--dry-run", action="store_true", help="Don't save to leads.csv")
    args = parser.parse_args()

    with RunTimer("b2b_scraper"):
        existing_names, existing_domains = load_existing_leads()
        print(f"Existing leads: {len(existing_names)} companies")

        # 确定产品类别
        product_slugs = list(TRADEKEY_PRODUCT_URLS.values())[:args.limit]
        product_keywords = list(EC21_PRODUCT_KEYWORDS.values())[:args.limit]

        all_buyers = []

        # TradeKey
        if args.platform in ("tradekey", "all"):
            tradekey_buyers = run_tradekey(
                product_slugs, args.max_pages, existing_names, existing_domains
            )
            all_buyers.extend(tradekey_buyers)
            print(f"\nTradeKey total: {len(tradekey_buyers)} new buyers")

        # EC21
        if args.platform in ("ec21", "all"):
            ec21_buyers = run_ec21(
                product_keywords, args.max_pages, existing_names, existing_domains
            )
            all_buyers.extend(ec21_buyers)
            print(f"\nEC21 total: {len(ec21_buyers)} new buyers")

        print(f"\nTotal new buyers: {len(all_buyers)}")

        if not args.dry_run:
            if all_buyers:
                added = save_to_staging(all_buyers)
            else:
                print("No new buyers found")
        else:
            print("\n[Dry run] Would add:")
            for b in all_buyers[:20]:  # 只显示前 20 个
                safe_name = (b.get("company_name", b.get("title", "Unknown"))
                            .encode('ascii', 'replace').decode('ascii'))
                print(f"  {safe_name} | {b.get('country', '')} | {b.get('platform', '')}")

        close_browser()

    print("\nDone.")


if __name__ == "__main__":
    main()
