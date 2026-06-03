"""HS 编码驱动的潜客发现脚本。

用 HS 编码相关关键词搜索 Google，从搜索结果中提取进口商/经销商/采购商，
去重后写入 data/leads.csv。

与 keyword_discovery.py 的区别：
- 关键词来自 config/hs_codes.json（HS 编码 + 产品关键词）
- 目标是进口商/经销商/批发商（非终端 venue）
- 支持多国搜索（非仅澳大利亚）
- 搜索意图：找买家，不是找餐厅

用法:
  python scripts/extraction/hs_lead_discovery.py --limit 5
  python scripts/extraction/hs_lead_discovery.py --country AU --limit 3
  python scripts/extraction/hs_lead_discovery.py --category restaurant_chairs --limit 5
  python scripts/extraction/hs_lead_discovery.py --dry-run --limit 3
"""

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))
from kp_pipeline.cloak_fetcher import search_google, cloak_fetch, close_browser, scrapling_fetch
from kp_pipeline.proxy_manager import get_manager
from utils.domain_cache import is_visited, mark_visited, get_cookies, is_cloudflare, should_recheck_cloudflare
from scripts.reports.timer import RunTimer

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA = PROJECT_ROOT / "data"
REPORTS = PROJECT_ROOT / "reports"
CONFIG_FILE = PROJECT_ROOT / "config" / "hs_codes.json"

# 排除的域名（非公司网站）— 复用 keyword_discovery.py 的排除列表
EXCLUDE_DOMAINS = {
    # Search engines & social
    "google.com", "google.com.au", "googleapis.com", "gstatic.com",
    "youtube.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "linkedin.com", "tiktok.com", "pinterest.com", "reddit.com",
    # Review & directory sites
    "yelp.com", "yelp.com.au", "tripadvisor.com", "tripadvisor.com.au",
    "zomato.com", "opentable.com", "menulog.com.au", "ubereats.com",
    "yellowpages.com", "yellowpages.com.au", "truelocal.com.au", "hotfrog.com.au",
    "wikipedia.org",
    # Booking platforms
    "booking.com", "expedia.com", "agoda.com", "hotels.com",
    # Job sites
    "seek.com.au", "au.seek.com", "seek.com",
    "indeed.com", "glassdoor.com",
    # B2B platforms (separate script handles these)
    "alibaba.com", "made-in-china.com", "globalsources.com",
    # Data/enrichment tools
    "rocketreach.co", "prospeo.io", "hunter.io", "apollo.io",
    "lusha.com", "zoominfo.com", "clearbit.com", "snov.io",
    "lead411.io", "adapt.io", "aeroleads.com", "kaspr.io",
    "uplead.com", "leadfeeder.com", "6sense.com", "seamless.ai",
    # Listing/SEO spam
    "mapquest.com", "foursquare.com", "bbb.org", "manta.com",
    "chamberofcommerce.com", "bizapedia.com", "opendi.com",
    "whereorg.com", "theorg.com", "crunchbase.com",
    "dnb.com", "leadiq.com", "wiza.co", "pitchbook.com",
    "datanyze.com",
    # Publishing / content platforms
    "issuu.com", "medium.com", "substack.com",
    # News & media
    "theguardian.com", "bbc.com", "cnn.com", "reuters.com",
    "bloomberg.com", "forbes.com", "businessinsider.com",
    # Trade data platforms (not actual companies)
    "trademap.org", "comtrade.un.org", "worldbank.org",
    "wto.org", "unctad.org",
    # HS code lookup sites
    "hsbianma.com", "hts.usitc.gov", "tariffnumber.com",
    "foreign-trade.com", "tradingeconomics.com",
}

# URL patterns indicating non-company pages
NON_COMPANY_URL_PATTERNS = [
    "/news/", "/articles/", "/article/", "/blog/",
    "/press/", "/stories/", "/story/", "/opinion/", "/feature/",
    "/wiki/", "/faq/", "/help/", "/support/",
    "/forum/", "/thread/", "/discussion/",
    "/jobs/", "/careers/", "/vacancies/",
    "/for-sale/", "/buy-a-", "/businesses-for-sale/",
    "/event/", "/events/",
    "/login", "/register", "/sign-up", "/sign-in",
    "/privacy", "/terms", "/cookie",
]

# 进口商/经销商相关关键词（用于判断页面是否是潜在客户）
IMPORTER_KEYWORDS = [
    "importer", "import", "distributor", "wholesale", "wholesaler",
    "supplier", "procurement", "purchasing", "buyer", "reseller",
    "dealer", "agent", "trading", "trade", "commerce",
    "hospitality", "catering", "restaurant", "hotel", "food service",
    "furniture", "equipment", "tableware", "kitchen",
    "stockist", "outfitter", "furnishings",
]

# 供应商信号（需排除，因为这些是 Ron Group 的竞争对手）
COMPETITOR_SIGNALS = [
    "manufacturer", "factory", "made in china", "oem", "odm",
    "we manufacture", "our factory", "production line",
    "guangdong", "foshan", "shenzhen", "dongguan",
    "export from china", "china supplier", "chinese manufacturer",
]


def load_config():
    """加载 HS 编码配置。"""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_existing_leads():
    """加载已有线索，返回 (company_names, website_domains)。"""
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


def _is_excluded_domain(domain):
    """检查域名是否在排除列表中。"""
    for excluded in EXCLUDE_DOMAINS:
        if domain == excluded or domain.endswith("." + excluded):
            return True
    return False


def _is_article_or_directory(url, title=""):
    """判断 URL 是否是文章、目录或非公司页面。"""
    url_lower = url.lower()
    for pattern in NON_COMPANY_URL_PATTERNS:
        if pattern in url_lower:
            return True
    if title:
        title_lower = title.lower()
        article_signals = [
            "top 10", "best ", "how to", "what is", "guide to",
            "review:", "comparison", "vs ", "versus",
            "for sale", "buy a", "businesses for sale",
            "wiki", "definition", "meaning",
            "hs code", "tariff code", "customs code",
            "the best", "the top", "our favourite",
        ]
        for sig in article_signals:
            if sig in title_lower:
                return True
    return False


def _extract_company_name_from_title(title, domain):
    """从页面标题和域名推断公司名。"""
    if not title:
        parts = domain.replace(".com.au", "").replace(".com", "").replace(".co.uk", "").replace(".au", "").split(".")
        return parts[0].replace("-", " ").title() if parts else ""
    # 清理标题
    title = re.sub(r'\s*[-–|]\s*(?:Home|Welcome|Official|About|Contact)\s*$', '', title, flags=re.I)
    title = re.sub(r'\s*[-–|]\s*$', '', title)
    title = title.replace('&amp;', '&').replace('&#x27;', "'")
    return title.strip()


def _is_potential_importer(text, url, domain):
    """判断页面是否是潜在的进口商/经销商/采购商。"""
    text_lower = text.lower() if text else ""
    url_lower = url.lower()

    # 排除竞争对手（中国制造商/出口商）
    competitor_match = sum(1 for sig in COMPETITOR_SIGNALS if sig in text_lower)
    if competitor_match >= 2:
        return False

    # 进口商/经销商信号
    importer_match = sum(1 for kw in IMPORTER_KEYWORDS if kw in text_lower)

    # 需要至少 2 个进口商信号
    if importer_match >= 2:
        return True

    # URL 包含进口商/经销商相关词
    importer_url_kws = ["import", "distributor", "wholesale", "trade", "supply", "furniture"]
    url_match = sum(1 for kw in importer_url_kws if kw in url_lower)
    if url_match >= 1 and importer_match >= 1:
        return True

    return False


def _has_contact_signal(text, html):
    """检查页面是否有联系方式。"""
    # 邮箱
    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text or ""):
        return True
    # 电话（多国格式）
    phone_patterns = [
        r'(?:(?:\+61|0)[2-478]\s?\d{4}\s?\d{4})',  # AU
        r'(?:(?:\+1|1)?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})',  # US/CA
        r'(?:(?:\+44|0)\s?\d{2,4}\s?\d{3,4}\s?\d{3,4})',  # UK
        r'(?:(?:\+65)\s?\d{4}\s?\d{4})',  # SG
        r'(?:(?:\+971|0)\s?\d{1,2}\s?\d{3}\s?\d{4})',  # AE
        r'(?:(?:\+81|0)\s?\d{1,4}\s?\d{1,4}\s?\d{1,4})',  # JP
    ]
    for pattern in phone_patterns:
        if re.search(pattern, text or ""):
            return True
    # 联系页链接
    if html:
        if re.search(r'href="[^"]*(?:contact|get-in-touch|enquir)[^"]*"', html, re.I):
            return True
    return False


def _extract_contacts(text, html, domain):
    """从页面提取联系方式。"""
    emails = list(set(re.findall(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text or "")))
    # 过滤掉常见非公司邮箱
    skip_domains = {"example.com", "test.com", "sentry.io", "wixpress.com", "google.com"}
    emails = [e for e in emails if not any(s in e.lower() for s in skip_domains)]

    phones = list(set(re.findall(
        r'(?:(?:\+?\d{1,3})?[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4})', text or "")))

    contact_url = ""
    if html:
        contact_match = re.search(r'href="([^"]*(?:contact|about|team)[^"]*)"', html, re.I)
        if contact_match:
            href = contact_match.group(1)
            if href.startswith("/"):
                contact_url = f"https://{domain}{href}"
            elif href.startswith("http"):
                contact_url = href

    return {
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "contact_page": contact_url,
    }


def discover_from_keyword(keyword_query, country_code, max_results=5,
                          existing_names=None, existing_domains=None,
                          use_cache=True, dry_run=False):
    """用一个关键词搜索 Google，发现新公司。"""
    if existing_names is None:
        existing_names = set()
    if existing_domains is None:
        existing_domains = set()

    def _mark(domain, **kwargs):
        if not dry_run:
            mark_visited(domain, **kwargs)

    results = search_google(keyword_query, max_results=max_results)
    if not results:
        return []

    _stats = {"google_results": len(results), "excluded_domain": 0, "article": 0,
              "dup_domain": 0, "cached_domain": 0, "fetch_error": 0, "cloudflare": 0,
              "competitor": 0, "not_importer": 0, "no_contact": 0, "dup_name": 0, "accepted": 0}

    new_companies = []
    for url in results:
        domain = _extract_domain(url)
        if not domain or _is_excluded_domain(domain):
            _stats["excluded_domain"] += 1
            continue
        if _is_article_or_directory(url):
            _stats["article"] += 1
            continue
        if domain in existing_domains:
            _stats["dup_domain"] += 1
            continue

        # 域名缓存
        if use_cache and is_visited(domain):
            if is_cloudflare(domain):
                pm = get_manager()
                current_ip = pm.verify_proxy_ip() or ""
                if should_recheck_cloudflare(domain, current_ip):
                    pass
                else:
                    _stats["cached_domain"] += 1
                    continue
            else:
                _stats["cached_domain"] += 1
                continue

        # 抓取页面
        cookies, ua = [], ""
        try:
            text, html, cookies, ua, status, error = cloak_fetch(url, timeout=15)
        except Exception:
            text, html, cookies, ua, status, error = None, None, [], "", 0, "fetch error"

        if error or not text:
            _stats["fetch_error"] += 1
            _mark(domain, valid=False)
            continue

        # Cloudflare 检测
        if html and any(x in html.lower() for x in ['challenge-platform', 'turnstile', 'just a moment']):
            pm = get_manager()
            current_ip = pm.verify_proxy_ip() or ""
            _mark(domain, valid=False, cloudflare=True, ip=current_ip)
            _stats["cloudflare"] += 1
            continue

        # 标题提取
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html or "", re.I)
        title = title_match.group(1).strip() if title_match else ""

        # 文章检测
        if _is_article_or_directory(url, title):
            _stats["article"] += 1
            _mark(domain, valid=False)
            continue

        # 进口商/经销商检测
        if not _is_potential_importer(text, url, domain):
            _stats["not_importer"] += 1
            _mark(domain, valid=False)
            continue

        # 联系方式检测
        if not _has_contact_signal(text, html):
            _stats["no_contact"] += 1
            _mark(domain, valid=False)
            continue

        company_name = _extract_company_name_from_title(title, domain)
        if not company_name or company_name.lower() in existing_names:
            _stats["dup_name"] += 1
            _mark(domain, valid=False)
            continue

        contacts = _extract_contacts(text, html, domain)

        company = {
            "company_name": company_name,
            "website": f"https://{domain}",
            "domain": domain,
            "country_code": country_code,
            "email": contacts["email"],
            "phone": contacts["phone"],
            "contact_page": contacts["contact_page"],
            "source_query": keyword_query,
            "source_url": url,
        }
        new_companies.append(company)
        existing_names.add(company_name.lower())
        existing_domains.add(domain)
        _stats["accepted"] += 1
        _mark(domain, valid=True, cookies=cookies, ua=ua)

    # 打印过滤统计
    total_filtered = sum(v for k, v in _stats.items() if k not in ("google_results", "accepted"))
    if _stats["google_results"] > 0:
        print(f"  [Filter] {_stats['google_results']} results → "
              f"excluded={_stats['excluded_domain']}, article={_stats['article']}, "
              f"dup={_stats['dup_domain'] + _stats['dup_name']}, cached={_stats['cached_domain']}, "
              f"competitor={_stats['competitor']}, not_importer={_stats['not_importer']}, "
              f"no_contact={_stats['no_contact']}, fetch_err={_stats['fetch_error']}, "
              f"cf={_stats['cloudflare']} → accepted={_stats['accepted']}")

    return new_companies


def save_to_staging(new_companies, source_tag="HS Discovery"):
    """将新发现的公司写入暂存文件 data/hs_leads_staging.csv。

    不直接写入 leads.csv，等人工审核后再合并。
    """
    staging_path = DATA / "hs_leads_staging.csv"

    # 读取 leads.csv 的列名作为模板
    leads_path = DATA / "leads.csv"
    if leads_path.exists():
        with open(leads_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            base_fieldnames = reader.fieldnames
    else:
        base_fieldnames = []

    # 暂存文件的列名 = leads.csv 列名 + staging 专属列
    staging_fieldnames = list(base_fieldnames) + ["staging_status", "staging_source", "staging_date"]

    # 如果暂存文件已存在，读取已有记录数
    existing_count = 0
    if staging_path.exists():
        with open(staging_path, "r", encoding="utf-8-sig") as f:
            existing_count = sum(1 for _ in csv.DictReader(f))

    now = datetime.now().strftime("%Y-%m-%d")
    added = 0

    # 国家代码 → 国家名映射
    country_names = {
        "AU": "Australia", "US": "United States", "UK": "United Kingdom",
        "CA": "Canada", "DE": "Germany", "SG": "Singapore",
        "AE": "UAE", "JP": "Japan", "KR": "South Korea",
        "NZ": "New Zealand", "SA": "Saudi Arabia", "FR": "France",
    }

    # 读取已有暂存文件的域名用于去重
    staging_domains = set()
    if staging_path.exists():
        with open(staging_path, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                website = (row.get("website") or "").strip().lower()
                if website:
                    d = _extract_domain(website)
                    if d:
                        staging_domains.add(d)

    write_header = not staging_path.exists()
    with open(staging_path, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=staging_fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()

        for company in new_companies:
            # 暂存文件内去重
            if company["domain"] in staging_domains:
                continue

            existing_count += 1
            lead_id = f"HS-{existing_count:04d}"
            cc = company.get("country_code", "AU")
            country = country_names.get(cc, cc)

            row = {fn: "" for fn in staging_fieldnames}
            row.update({
                "lead_id": lead_id,
                "company_name": company["company_name"],
                "website": company["website"],
                "country": country,
                "industry_type": "Importador/Distribuidor",
                "customer_type": "Importer/Distributor",
                "source_type": source_tag,
                "source_link": company["source_url"],
                "keyword_source_query": company["source_query"],
                "verification_status": "Discovered",
                "contact_research_status": "待处理",
                "last_updated": now,
                "enrichment_notes": f"Discovered via HS code search. Domain: {company['domain']}",
                "staging_status": "pending",
                "staging_source": "hs_lead_discovery",
                "staging_date": now,
            })
            if company.get("email"):
                row["email_address"] = company["email"]
            if company.get("phone"):
                row["phone_number"] = company["phone"]
            if company.get("contact_page"):
                row["official_contact_page"] = company["contact_page"]
            writer.writerow(row)
            staging_domains.add(company["domain"])
            added += 1
            safe_name = company['company_name'].encode('ascii', 'replace').decode('ascii')
            print(f"  + {lead_id}: {safe_name} ({company['domain']}) [{country}]")

    if added > 0:
        print(f"\n  写入暂存文件: {staging_path}")
        print(f"  待审核: {existing_count} 条 (新增 {added} 条)")
        print(f"  审核后运行: python -m scripts.extraction.merge_staging --source hs")
    else:
        print(f"\n  无新发现")

    return added


def _generate_queries(config, target_markets, strategy_filter=None, limit=10):
    """从搜索策略配置生成查询列表。

    Args:
        config: hs_codes.json 配置
        target_markets: 目标市场列表
        strategy_filter: 可选，只用指定策略（如 "demand_signals"）
        limit: 最大查询数

    Returns:
        list[dict]: [{query, country_code, strategy, keyword_id}]
    """
    strategies = config.get("search_strategies", {})
    current_year = datetime.now().year
    queries = []

    for strategy_name, strategy_data in strategies.items():
        if strategy_filter and strategy_name != strategy_filter:
            continue
        keywords = strategy_data.get("keywords", [])
        for kw in keywords:
            template = kw.get("template", "")
            kw_id = kw.get("id", "")
            kw_priority = kw.get("priority", "Low")
            kw_country = kw.get("country", "")  # 某些关键词限定国家

            for market in target_markets:
                # 如果关键词限定了国家，跳过不匹配的市场
                if kw_country and market["code"].upper() != kw_country.upper():
                    continue

                country = market["country"]
                query = template.replace("{country}", country).replace("{year}", str(current_year))
                queries.append({
                    "query": query,
                    "country_code": market["code"],
                    "strategy": strategy_name,
                    "keyword_id": kw_id,
                    "priority": kw_priority,
                })

    # 按优先级排序：High > Medium > Low
    prio_order = {"High": 0, "Medium": 1, "Low": 2}
    queries.sort(key=lambda q: prio_order.get(q["priority"], 3))

    return queries[:limit]


def main():
    parser = argparse.ArgumentParser(description="HS code driven lead discovery — demand signal approach")
    parser.add_argument("--limit", type=int, default=5, help="Number of search queries to run")
    parser.add_argument("--max-results", type=int, default=8, help="Google results per query")
    parser.add_argument("--country", type=str, default="", help="Target country code (e.g., AU, US, UK)")
    parser.add_argument("--strategy", type=str, default="",
                       help="Search strategy: demand_signals, buyer_profiles, importer_partner, trade_shows, local_search")
    parser.add_argument("--dry-run", action="store_true", help="Don't save to staging file")
    args = parser.parse_args()

    with RunTimer("hs_discovery"):
        config = load_config()
        existing_names, existing_domains = load_existing_leads()
        print(f"Existing leads: {len(existing_names)} companies, {len(existing_domains)} domains")

        # 确定目标国家
        if args.country:
            target_markets = [m for m in config["target_markets"] if m["code"].upper() == args.country.upper()]
            if not target_markets:
                print(f"ERROR: Country code '{args.country}' not found in config")
                sys.exit(1)
        else:
            target_markets = sorted(config["target_markets"], key=lambda x: x.get("priority", 99))[:3]

        # 生成搜索词
        queries = _generate_queries(config, target_markets, args.strategy, args.limit)

        if not queries:
            print("No queries generated. Check --strategy and --country flags.")
            sys.exit(1)

        print(f"\nGenerated {len(queries)} search queries:")
        for q in queries:
            print(f"  [{q['country_code']}] [{q['strategy']}] {q['query']}")

        # 执行搜索
        all_new = []
        use_cache = not args.dry_run
        for i, q in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Searching: {q['query']}")
            new = discover_from_keyword(
                q["query"], q["country_code"], args.max_results,
                existing_names, existing_domains,
                use_cache=use_cache, dry_run=args.dry_run
            )
            print(f"  Found {len(new)} new companies")
            all_new.extend(new)
            time.sleep(2)

        print(f"\nTotal new companies discovered: {len(all_new)}")

        if not args.dry_run:
            if all_new:
                added = save_to_staging(all_new)
            else:
                print("No new companies found")
        else:
            print("\n[Dry run] Would add:")
            for c in all_new:
                safe_name = c['company_name'].encode('ascii', 'replace').decode('ascii')
                print(f"  {safe_name} | {c['website']} | {c.get('email', '')} [{c['country_code']}]")

        close_browser()

    print("\nDone.")


if __name__ == "__main__":
    main()
