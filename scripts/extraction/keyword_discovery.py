"""关键词驱动的新公司发现脚本。

用 Google 搜索关键词，从搜索结果中提取公司名和网站，
去重后写入 data/leads.csv。

用法:
  python scripts/extraction/keyword_discovery.py --limit 3 --max-results 5
  python scripts/extraction/keyword_discovery.py --keywords "KW-0049,KW-0054"
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

# 排除的域名（非公司网站）
EXCLUDE_DOMAINS = {
    # Search engines & social
    "google.com", "google.com.au", "googleapis.com", "gstatic.com",
    "youtube.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "linkedin.com", "tiktok.com", "pinterest.com", "reddit.com",
    # Review & directory sites
    "yelp.com.au", "tripadvisor.com.au", "zomato.com",
    "opentable.com.au", "menulog.com.au", "ubereats.com",
    "yellowpages.com.au", "truelocal.com.au", "hotfrog.com.au",
    "wikipedia.org",
    # Booking platforms
    "booking.com", "expedia.com.au", "agoda.com", "hotels.com",
    # Job sites
    "seek.com.au", "au.seek.com", "seek.com",
    "indeed.com.au", "au.indeed.com", "indeed.com",
    "glassdoor.com.au", "glassdoor.com",
    # Real estate
    "realestate.com.au", "domain.com.au",
    # Media & news
    "timeout.com", "broadsheet.com.au", "goodfood.com.au",
    "theguardian.com", "abc.net.au", "news.com.au", "smh.com.au",
    "theshout.com.au", "hospitalitymagazine.com.au",
    "restaurant.com.au", "eatdrinkplay.com",
    "theaustralian.com.au", "afr.com", "thewest.com.au",
    "adelaidenow.com.au", "couriermail.com.au", "heraldsun.com.au",
    "dailytelegraph.com.au", "canberratimes.com.au",
    "hotelmanagement.com.au", "theurbandeveloper.com",
    "propertyobserver.com.au", "commercialrealestate.com.au",
    "boothby.com.au", "urbanlist.com", "concreteplayground.com",
    "timeout.com.au", "messynessy.com", "theurbanlist.com",
    # Data/enrichment tools (not actual restaurants)
    "rocketreach.co", "prospeo.io", "hunter.io", "apollo.io",
    "lusha.com", "zoominfo.com", "clearbit.com", "snov.io",
    "lead411.io", "adapt.io", "aeroleads.com", "kaspr.io",
    "uplead.com", "leadfeeder.com", "6sense.com", "seamless.ai",
    # Listing/SEO spam
    "mapquest.com", "foursquare.com", "bbb.org", "manta.com",
    "chamberofcommerce.com", "bizapedia.com", "opendi.com",
    "whereorg.com", "theorg.com", "crunchbase.com",
    # Data enrichment / profile sites (not actual restaurants)
    "dnb.com", "leadiq.com", "wiza.co", "rocketreach.co", "prospeo.io",
    "pitchbook.com",
    "hunter.io", "apollo.io", "lusha.com", "zoominfo.com",
    "clearbit.com", "snov.io", "lead411.io", "adapt.io",
    "aeroleads.com", "kaspr.io", "uplead.com", "leadfeeder.com",
    "6sense.com", "seamless.ai", "datanyze.com",
    # Design awards / industry events
    "eat-drink-design.com", "eatdrinkdesign.com",
    # Chamber of commerce & industry associations
    "melbourneregionalchamber.com", "sydneychamber.com.au",
    "brisbanechamber.com.au", "rca.asn.au", "asn.au",
    # Recruitment agencies
    "thechefagency.com", "chefagency.com",
    # International hotel chains (not AU-specific targets)
    "ihg.com", "intercontinental.com", "hilton.com", "marriott.com",
    "hyatt.com", "accor.com", "radisson.com", "wyndhamhotels.com",
    "bestwestern.com", "choicehotels.com", "starwoodhotels.com",
    "1hotels.com", "fullertonhotels.com", "mandarinoriental.com",
    "fourseasons.com", "ritzcarlton.com", "peninsula.com",
    "sofitel.com", "novotel.com", "pullmanhotels.com",
    "mercure.com", "ibis.com", "joineasyhotel.com",
    "joinbwhhotels.com",
    # Franchise / business directories
    "topfranchise.com.au", "franchiseinsights.com.au",
    "franchise.sbx.com.au", "businessforsale.com.au",
    "smea.org.au", "issuu.com", "sprintlaw.com.au",
    # International hotel chains (AU versions)
    "joinbwhhotels.com.au", "ihg.com.au", "hilton.com.au",
    "marriott.com.au", "accor.com", "novotel.com.au",
    # Law firms / professional services
    "rubiconlaw.com.au",
    # Equipment suppliers
    "microbrewerysystem.com", "cateringequipment.com.au",
    # B-Run 25-29 non-target: suppliers, media, directories, recruitment, tech, property
    "seekbusiness.com.au", "glamadelaide.com.au", "melbournefoodandwine.com.au",
    "hellopeople.com.au", "hospitalitydirectory.com.au",
    "core4service.com.au", "chefhire.com.au",
    "cafefurniturecompany.com.au", "adagefurniture.com.au", "chairimports.com.au",
    "convenientinteriors.com.au", "phoeniks.com.au", "adgemisrefrigeration.com.au",
    "hospitalityconnect.com.au", "thecigroup.com.au", "lkhevents.com.au",
    "tbourke-solutions.com.au", "netway.com.au", "ihservices.com.au",
    "technology4hotels.com.au", "setthebar.com.au", "almliquor.com.au",
    "shop.buzzproducts.com.au", "swisstrade.com.au", "vanitygroup.com",
    "dolphy.com.au", "hostsupplies.com.au", "lightingspaces.com.au",
    "davolucelighting.com.au", "aaateatowels.com.au", "premiumlinen.com.au",
    "restaurantlinenservice.com.au", "britawash.com.au", "snowflakelaundry.com.au",
    "splservices.com.au", "xo2.com.au", "escalatehospitality.com.au",
    "infinityhospitality.com.au",
    # Procurement software / SaaS
    "fourth.com", "entegraps.com", "chefmod.com", "fourpl.com.au",
    "spend-solutions.com.au", "practicegreenhealth.org",
    "stevensfoodgroup.com",
    # Publishing / content platforms
    "issuu.com", "medium.com", "substack.com",
    # Sports travel
    "sportstravelhospitality.com",
    # Education & government
    "edu.au", "gov.au", "gov.uk", "edu.sg",
    "newcastle.edu.au", "bond.edu.au", "kbs.edu.au",
    "studyaustralia.gov.au", "fairwork.gov.au",
    "sbs.com.au", "abc.net.au",
    # Student accommodation
    "unilodge.com.au", "scape.com.au", "amberstudent.com",
    "universityliving.com", "homestaynetwork.org",
    "studenthousingaustralia.com.au", "sha.com.au",
    # Industry bodies & associations
    "accommodationaustralia.org", "foodsouthaustralia.com.au",
    "foodserviceaustralia.com.au", "visitnsw.com", "nswwine.com.au",
    "rca.asn.au", "asn.au",
    # Booking & directory platforms
    "businessesforsale.com", "nowbookit.com", "tagvenue.com",
    "cbre.com.au", "wyndhamap.com",
    # News & media (additional)
    "hotel-online.com", "craftypint.com", "thecaterer.com",
    "windowswear.com", "asiabrewersnetwork.com", "theurbanlist.com",
    "business-live.co.uk", "miragenews.com", "listnr.com",
    "eater.com", "ny.eater.com",
    # B-Run 35 non-target: tourism boards, travel blogs, food media
    "visitcanberra.com.au", "adventuresnsunsets.com", "thecitylane.com",
    # Recruitment (additional)
    "barcats.com.au", "executivesearchinternational.com.au",
    "careers.delawarenorth.com",
    # Architecture / design / case study sites
    "architectureau.com", "dezeen.com", "archdaily.com",
    "designboom.com", "yellowtrace.com.au",
    # Industry associations (additional)
    "wineriesofnewsouthwales.com.au", "accommodationaustralia.org.au",
    # Booking / directory platforms (AU)
    "hotels.com.au", "qsrmedia.com.au", "franchisebuyer.com.au",
    "tagvenue.com.au", "restaurants.com.au",
    # Media sites (AU)
    "geelongadvertiser.com.au", "beanscenemag.com.au",
    "clubmanagement.com.au", "hotelmanagement.com.au",
    # Directory / aggregation sites
    "luxurylodgesofaustralia.com.au", "beercrawl.com.au",
    # International hotel chains (AU franchise sites)
    "joinchoicehotels.com.au", "wvrap.com.au",
    "wyndhamap.com",
    # Venue management / hospitality tech platforms
    "doshii.com", "siteminder.com", "opentable.com",
    # Business list / directory sites
    "businesslistsaustralia.com",
    # Recruitment agencies (additional)
    "mondaygroup.com.au",
    # International (non-AU) domains
    "masonrybali.com",
    # Equipment suppliers / wholesalers / trade (not actual venues)
    "mipos.com.au", "accesspos.com.au",
    "winetitles.com.au", "yarravalleytrading.com.au",
    "hiller.com.au", "cabroto.com.au", "totalfitouts.com.au",
    "cateringequipment.com.au", "restaurantdesign.com.au",
    # Tourism / travel / articles (discovered B-Run 22)
    "australianbartender.com.au", "qantas.com.au",
    "fringeworld.com.au", "visitwangaratta.com.au", "experth.com.au",
}

# URL patterns indicating non-company pages (articles, directories, etc.)
NON_COMPANY_URL_PATTERNS = [
    "/news/", "/articles/", "/article/", "/court/", "/blog/",
    "/press/", "/stories/", "/story/", "/opinion/", "/feature/",
    "/company-profile/", "/companies/", "/people/", "/person/",
    "/owner/", "/management/employees/", "/overview/", "/competitors/",
    "/tenders/", "/jobs/", "/careers/", "/vacancies/",
    "/for-sale/", "/buy-a-", "/businesses-for-sale/",
    "/franchise/", "/franchising/",
    "/event/", "/events/", "/christmas-in-july/",
    "/hire/", "/book/", "/reservation/",
    "/thank-you", "/thankyou", "/registration",
    "/agent-registration", "/vendor-registration",
]

# 行业相关关键词（用于判断页面是否是公司网站）
INDUSTRY_KEYWORDS = [
    "restaurant", "hotel", "bar", "cafe", "bistro", "pub", "grill",
    "kitchen", "dining", "eatery", "venue", "hospitality", "catering",
    "food", "beverage", "wine", "cocktail", "brewery", "distillery",
    "accommodation", "resort", "motel", "inn", "tavern", "gastropub",
    "pizzeria", "steakhouse", "seafood", "sushi", "ramen", "thai",
    "italian", "french", "chinese", "japanese", "indian", "mexican",
    "group", "collective", "hospitality group", "restaurant group",
]


def load_existing_leads():
    """加载已有线索，返回 (company_names, website_domains, leads_rows)。"""
    leads_path = DATA / "leads.csv"
    names = set()
    domains = set()
    rows = []
    if leads_path.exists():
        with open(leads_path, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                rows.append(row)
                name = (row.get("company_name") or "").strip().lower()
                if name:
                    names.add(name)
                website = (row.get("website") or "").strip().lower()
                if website:
                    d = _extract_domain(website)
                    if d:
                        domains.add(d)
    return names, domains, rows


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


_TITLE_PREFIXES = (
    r'(?:'
    r'About(?:\s+Us)?|Contact(?:\s+Us)?|Get\s+in\s+Touch|Our\s+(?:Company|Story|Team)|'
    r'Meet\s+(?:the\s+team\s+behind|Us)?|Home|Welcome|Services\s+and\s+Products|'
    r'Shop(?:\s+Now)?|Call\s+Us|Visit\s+Us|Find\s+Us|Enquir(?:ies|e)|'
    r'Learn\s+More(?:\s+About)?|Discover|Explore'
    r')'
)

_TITLE_SUFFIXES = (
    r'(?:'
    r'Home|Welcome|Official|About(?:\s+Us)?|Contact(?:\s+Us)?|Menu|'
    r'Our\s+Company|Meet|Team|Get\s+in\s+Touch|Our\s+Story|'
    r'Australia|Sydney|Melbourne|Brisbane|Perth|Adelaide'
    r')'
)


def _extract_company_name_from_title(title, domain):
    """从页面标题和域名推断公司名。"""
    if not title:
        # 从域名推断
        parts = domain.replace(".com.au", "").replace(".com", "").replace(".au", "").split(".")
        return parts[0].replace("-", " ").title() if parts else ""
    # 清理标题：去掉网站通用后缀
    title = re.sub(rf'\s*[-–|]\s*{_TITLE_SUFFIXES}\s*$', '', title, flags=re.I)
    # 去掉前缀（如 "About Us | Phoeniks" → "Phoeniks"）
    title = re.sub(rf'^{_TITLE_PREFIXES}\s*[-–|:]\s*', '', title, flags=re.I)
    # 去掉 HTML entities
    title = title.replace('&amp;', '&').replace('&#x27;', "'").replace('&gt;', '>').replace('&lt;', '<')
    title = re.sub(r'\s*[-–|]\s*$', '', title)
    return title.strip()


def _is_article_or_directory(url, title=""):
    """判断 URL 是否是文章、目录或非公司页面。"""
    url_lower = url.lower()
    for pattern in NON_COMPANY_URL_PATTERNS:
        if pattern in url_lower:
            return True
    # 文章标题特征
    if title:
        title_lower = title.lower()
        article_signals = [
            "in court", "warns of", "tipped to", "withdraws bid",
            "appoints", "first look at", "new opening", "journey",
            "top 10", "top uk", "best ", "how to", "what is",
            "persons with significant control",  # UK company registry
            "for sale", "buy a", "businesses for sale",
            "| architecture", "| design", "award", "case study",
            "project by", "designed by", "built by",
            " to bring ", "latest news", "headlines", "insight",
            "commentary", "analysis", "reports", "announced",
            "acquires", "acquisition", "merger", "expands into",
            # Question-format titles (media articles)
            "how does", "how do", "how did", "how can",
            "what does", "what do", "what did", "what makes",
            "why does", "why do", "why did",
            "where to", "where do", "where does",
            "who is", "who are", "who was",
            # List/ranking articles
            "the best", "the top", "the most", "the biggest",
            "our favourite", "our favorite", "we tried",
            # Food/drink media patterns
            "review:", "reviewed:", "tasting notes",
            "wine of the week", "drink of the week",
        ]
        for sig in article_signals:
            if sig in title_lower:
                return True
    return False


def _is_australia_page(url, text="", domain=""):
    """判断页面是否与澳大利亚相关。"""
    # AU 域名直接通过
    if domain.endswith(".au") or domain.endswith(".com.au"):
        return True
    # 检查页面文本中的 AU 信号
    text_lower = text.lower() if text else ""
    au_signals = ["australia", "sydney", "melbourne", "brisbane", "perth",
                  "adelaide", "hobart", "darwin", "canberra", "gold coast",
                  "newcastle", "wollongong", "geelong", "townsville",
                  ".com.au", "abn ", "acn ", "australian"]
    matches = sum(1 for sig in au_signals if sig in text_lower)
    return matches >= 2


def _is_supplier_website(text, url, domain=""):
    """判断是否是供应商/批发商/制造商网站（非 venue 运营方）。

    供应商网站通常包含大量 venue 关键词（因为他们的客户是餐厅/酒店），
    但实际是卖设备/家具/布草/IT 服务的，不是 venue 运营方。
    """
    text_lower = text.lower() if text else ""
    url_lower = url.lower()

    # URL 直接排除
    supplier_url_kws = [
        "supplier", "wholesale", "manufacturer", "equipment",
        "furniture", "linen", "lighting", "amenities",
        "commercial-kitchen", "kitchen-equipment",
        "hire-a-chef", "hire-a", "recruitment", "staffing",
    ]
    if any(kw in url_lower for kw in supplier_url_kws):
        return True

    # 内容中的供应商信号（需要多个同时出现才判定）
    supplier_content_kws = [
        "wholesale", "manufacturer", "supplier", "distributor",
        "trade pricing", "trade price", "bulk order", "catalogue",
        "product range", "our products", "shop now", "add to cart",
        "free shipping", "delivery australia wide", "b2b",
        "wholesale enquiry", "wholesale inquiry", "reseller",
    ]
    supplier_match = sum(1 for kw in supplier_content_kws if kw in text_lower)
    if supplier_match >= 2:
        return True

    # 域名中的供应商信号
    supplier_domain_kws = [
        "furniture", "equipment", "supply", "supplies", "linen",
        "lighting", "kitchen", "wholesale", "trade", "imports",
        "laundry", "towels", "amenities", "products",
    ]
    if any(kw in domain.lower() for kw in supplier_domain_kws):
        # 域名含供应商词 + 内容有 venue 关键词 = 大概率是供应商
        venue_kws = ["restaurant", "hotel", "bar", "cafe", "pub", "hospitality"]
        if sum(1 for kw in venue_kws if kw in text_lower) >= 1:
            return True

    return False


def _is_media_or_directory(text, url, domain=""):
    """判断是否是媒体/新闻/目录/列表网站（非实际公司）。"""
    text_lower = text.lower() if text else ""
    url_lower = url.lower()
    domain_lower = domain.lower()

    # 域名中的媒体/目录信号
    media_domain_kws = [
        "news", "media", "magazine", "review", "directory",
        "listing", "list", "classifieds", "advertiser", "herald",
        "times", "post", "tribune", "gazette", "journal",
        "business-for-sale", "seekbusiness", "franchise",
        "glam", "urban", "lifestyle",
    ]
    if any(kw in domain_lower for kw in media_domain_kws):
        return True

    # 内容中的媒体/目录信号
    media_content_kws = [
        "subscribe", "newsletter", "sign up for updates",
        "latest news", "trending", "editorial", "sponsored",
        "advertisement", "classifieds", "listing",
        "for sale", "businesses for sale", "buy a business",
        "read more", "more articles", "more stories",
    ]
    media_match = sum(1 for kw in media_content_kws if kw in text_lower)
    if media_match >= 2:
        return True

    return False


def _is_restaurant_hotel_page(text, url):
    """判断页面是否是实际的餐饮/酒店公司网站（非文章/目录/供应商）。"""
    text_lower = text.lower() if text else ""
    url_lower = url.lower()

    # 排除词：URL 含这些词直接排除（招聘/物业/供应商/培训等非目标）
    EXCLUDE_URL_KEYWORDS = [
        "staffing", "recruitment", "hire-a-", "hire-a",
        "property", "facilities", "real-estate",
        "supplier", "wholesale", "manufacturer",
        "training", "course", "certificate", "academy",
        "franchise", "business-for-sale",
    ]
    if any(kw in url_lower for kw in EXCLUDE_URL_KEYWORDS):
        return False

    # 媒体/列表页检测：标题含 listicle 模式则排除
    LISTICLE_PATTERNS = [
        r"\d+\s+(?:best|top|hidden|must[- ]?visit|favorite|great)",
        r"(?:complete\s+list|ultimate\s+guide|full\s+guide|guide\s+to)",
        r"\d+\s+(?:bars|restaurants|hotels|pubs|cafes|venues|breweries)\b",
        r"(?:by\s+a\s+tour\s+guide|according\s+to|curated\s+list)",
    ]
    if any(re.search(p, text_lower) for p in LISTICLE_PATTERNS):
        return False

    # 强信号：URL 路径包含 venue 相关词（需 ≥2 个，减少单信号误判）
    venue_url_signals = ["restaurant", "hotel", "bar", "cafe", "pub",
                         "brewery", "winery", "motel", "resort", "venue",
                         "wine", "cellar", "bistro", "eatery", "dining",
                         "kitchen", "cocktail", "gastropub"]
    url_match = sum(1 for kw in venue_url_signals if kw in url_lower)
    if url_match >= 2:
        return True

    # 文本需要更强的信号（至少 3 个行业关键词）
    if text_lower:
        venue_text_signals = ["restaurant", "hotel", "bar", "cafe", "pub",
                              "brewery", "winery", "motel", "resort", "bistro",
                              "tavern", "gastropub", "venue", "accommodation",
                              "food", "wine", "dining", "eatery", "kitchen",
                              "cellar door", "distillery", "cocktail", "tapas",
                              "charcuterie", "sommelier", "cellar", "eat",
                              "drink", "lunch", "dinner", "breakfast", "brunch"]
        venue_matches = sum(1 for kw in venue_text_signals if kw in text_lower)
        if venue_matches >= 4:
            # 4+ text signals: still require at least 1 URL signal to avoid media/listicle false positives
            if url_match >= 1:
                return True
        if venue_matches >= 3:
            # 3 text signals: URL 有至少 1 个 venue 信号时通过（文本+URL 双确认）
            if url_match >= 1:
                return True
        if venue_matches >= 2:
            # 2 text signals + 1 URL signal: moderate confidence for venue-type domains
            if url_match >= 1:
                return True

    return False


def _enhance_query_for_au(query):
    """不再自动添加 site:.com.au（太窄，会漏掉 .com/.net 等 AU 域名）。

    AU 过滤改为后置：搜索结果通过 _is_australia_page() 判断。
    只在查询本身已含 site: 时保留原样。
    """
    return query


def _expand_templates(query):
    """展开查询中的模板占位符（[city], [country] 等）。

    返回展开后的查询列表。如果没有占位符，返回原查询。
    """
    config_path = PROJECT_ROOT / "config" / "keyword_scheduler.json"
    if not config_path.exists():
        return [query]

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        expansions = config.get("template_expansions", {})
    except Exception:
        return [query]

    if not expansions:
        return [query]

    # 检查是否有占位符
    has_placeholder = any(placeholder in query for placeholder in expansions)
    if not has_placeholder:
        return [query]

    # 展开所有占位符
    results = [query]
    for placeholder, values in expansions.items():
        new_results = []
        for q in results:
            if placeholder in q:
                for val in values:
                    new_results.append(q.replace(placeholder, val))
            else:
                new_results.append(q)
        results = new_results

    return results


def discover_from_keyword(keyword_query, max_results=5, existing_names=None, existing_domains=None, use_cache=True, dry_run=False):
    """用一个关键词搜索 Google，发现新公司。

    Args:
        use_cache: True 时使用域名缓存（跳过已访问域名）。dry-run 时设为 False。
        dry_run: True 时不更新域名缓存（仅预览）。
    """
    if existing_names is None:
        existing_names = set()
    if existing_domains is None:
        existing_domains = set()

    # dry-run 时不更新域名缓存
    def _mark(domain, **kwargs):
        if not dry_run:
            mark_visited(domain, **kwargs)

    # 自动增强 AU 查询
    enhanced_query = _enhance_query_for_au(keyword_query)
    if enhanced_query != keyword_query:
        print(f"  [Enhanced] {enhanced_query}")

    results = search_google(enhanced_query, max_results=max_results)
    if not results:
        return []

    # Filter layer statistics
    _stats = {"google_results": len(results), "excluded_domain": 0, "article_url": 0,
              "dup_domain": 0, "cached_domain": 0, "fetch_error": 0, "cloudflare": 0,
              "article_title": 0, "media_domain": 0, "professional_svc": 0,
              "not_au": 0, "not_venue": 0, "supplier": 0, "no_contact": 0, "dup_name": 0, "accepted": 0}

    new_companies = []
    for url in results:
        domain = _extract_domain(url)
        if not domain or _is_excluded_domain(domain):
            _stats["excluded_domain"] += 1
            continue
        # Skip article/directory URLs
        if _is_article_or_directory(url):
            _stats["article_url"] += 1
            continue
        if domain in existing_domains:
            _stats["dup_domain"] += 1
            continue

        # 域名缓存：跳过已访问的域名（dry-run 时禁用缓存）
        if use_cache and is_visited(domain):
            # Cloudflare 域名复查：超过 1 小时 + 换了 IP 后重新检查
            if is_cloudflare(domain):
                pm = get_manager()
                current_ip = pm.verify_proxy_ip() or ""
                if should_recheck_cloudflare(domain, current_ip):
                    pass  # 继续抓取，复查
                else:
                    _stats["cached_domain"] += 1
                    continue
            else:
                _stats["cached_domain"] += 1
                continue

        # Cloudflare 域名：先用 Scrapling 重试（有时能过）
        cookies, ua = [], ""
        if is_cloudflare(domain):
            text, status, error = scrapling_fetch(url, timeout=15)
            if not error and text:
                html = None  # Scrapling 不返回完整 HTML
            else:
                # Scrapling 也失败，跳过
                _stats["cloudflare"] += 1
                continue

        # 抓取页面获取更多信息
        if not is_cloudflare(domain):
            try:
                text, html, cookies, ua, status, error = cloak_fetch(url, timeout=15)
            except Exception:
                text, html, cookies, ua, status, error = None, None, [], "", 0, "fetch error"

        if error or not text:
            _stats["fetch_error"] += 1
            _mark(domain, valid=False)
            continue

        # 检测 Cloudflare 防护
        if html and any(x in html.lower() for x in ['challenge-platform', 'turnstile', 'just a moment', 'verify you are human']):
            pm = get_manager()
            current_ip = pm.verify_proxy_ip() or ""
            _mark(domain, valid=False, cloudflare=True, ip=current_ip)
            _stats["cloudflare"] += 1
            print(f"  [CF] {domain} — Cloudflare detected, skipping")
            continue

        # 提取标题（用于文章检测和公司名提取）
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html or "", re.I)
        title = title_match.group(1).strip() if title_match else ""

        # 二次文章检测（基于标题和域名）
        if _is_article_or_directory(url, title):
            _stats["article_title"] += 1
            _mark(domain, valid=False)
            continue
        # 媒体/新闻域名检测
        if any(x in domain for x in ["media", "news", "magazine", "review",
                                       "advertiser", "herald", "times", "post",
                                       "tribune", "gazette", "journal", "mag",
                                       "crawl", "lodges", "escapes"]):
            _stats["media_domain"] += 1
            _mark(domain, valid=False)
            continue
        # 专业服务（律所、会计等）检测
        if any(x in domain for x in ["law", "legal", "solicitor", "barrister",
                                       "accountant", "accounting", "consulting"]):
            _stats["professional_svc"] += 1
            _mark(domain, valid=False)
            continue

        # AU 地理过滤
        if not _is_australia_page(url, text, domain):
            _stats["not_au"] += 1
            _mark(domain, valid=False)
            continue

        # 供应商检测（在 venue 检查之前，因为供应商也能通过 venue 检查）
        if _is_supplier_website(text, url, domain):
            _stats["supplier"] += 1
            _mark(domain, valid=False)
            continue

        # 媒体/目录检测
        if _is_media_or_directory(text, url, domain):
            _stats["media_domain"] += 1
            _mark(domain, valid=False)
            continue

        if not _is_restaurant_hotel_page(text, url):
            _stats["not_venue"] += 1
            _mark(domain, valid=False)
            continue

        # 联系信号检测：页面必须有至少一种联系方式才算公司网站
        has_contact_signal = bool(re.search(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text or ""))
        if not has_contact_signal:
            has_contact_signal = bool(re.search(
                r'(?:(?:\+61|0)[2-478]\s?\d{4}\s?\d{4}|\(\d{2}\)\s?\d{4}\s?\d{4}|1300\s?\d{3}\s?\d{3}|1800\s?\d{3}\s?\d{3})',
                text or ""))
        if not has_contact_signal:
            # 检查是否有 contact 页面链接
            if html:
                has_contact_signal = bool(re.search(
                    r'href="[^"]*(?:contact|get-in-touch|enquir)[^"]*"', html, re.I))
        if not has_contact_signal:
            _stats["no_contact"] += 1
            _mark(domain, valid=False)
            continue

        company_name = _extract_company_name_from_title(title, domain)

        if not company_name or company_name.lower() in existing_names:
            _stats["dup_name"] += 1
            _mark(domain, valid=False)
            continue

        # 提取联系方式
        emails = list(set(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text or "")))
        phones = list(set(re.findall(r'(?:(?:\+61|0)[2-478]\s?\d{4}\s?\d{4}|\(\d{2}\)\s?\d{4}\s?\d{4}|1300\s?\d{3}\s?\d{3}|1800\s?\d{3}\s?\d{3})', text or "")))

        # 查找联系页链接
        contact_url = ""
        if html:
            contact_match = re.search(r'href="([^"]*(?:contact|about|team)[^"]*)"', html, re.I)
            if contact_match:
                href = contact_match.group(1)
                if href.startswith("/"):
                    contact_url = f"https://{domain}{href}"
                elif href.startswith("http"):
                    contact_url = href

        company = {
            "company_name": company_name,
            "website": f"https://{domain}",
            "domain": domain,
            "email": emails[0] if emails else "",
            "phone": phones[0] if phones else "",
            "contact_page": contact_url,
            "source_query": keyword_query,
            "source_url": url,
        }
        new_companies.append(company)
        existing_names.add(company_name.lower())
        existing_domains.add(domain)
        _stats["accepted"] += 1

        # 缓存：标记为有效公司，保存 cookies/UA 供 A区复用
        _mark(domain, valid=True, cookies=cookies, ua=ua)

    # Print filter layer statistics
    total_filtered = sum(v for k, v in _stats.items() if k not in ("google_results", "accepted"))
    if _stats["google_results"] > 0:
        print(f"  [Filter] {_stats['google_results']} results → "
              f"excluded={_stats['excluded_domain']}, article={_stats['article_url'] + _stats['article_title']}, "
              f"dup={_stats['dup_domain'] + _stats['dup_name']}, cached={_stats['cached_domain']}, "
              f"media={_stats['media_domain']}, supplier={_stats['supplier']}, "
              f"prof_svc={_stats['professional_svc']}, not_AU={_stats['not_au']}, "
              f"not_venue={_stats['not_venue']}, no_contact={_stats['no_contact']}, "
              f"fetch_err={_stats['fetch_error']}, cf={_stats['cloudflare']} → "
              f"accepted={_stats['accepted']}")

    return new_companies


def save_to_leads(new_companies):
    """将新发现的公司追加到 data/leads.csv。"""
    leads_path = DATA / "leads.csv"
    if not leads_path.exists():
        print("ERROR: leads.csv not found")
        return 0

    # 读取现有行数确定 lead_id
    with open(leads_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing_rows = list(reader)

    max_id = 0
    for row in existing_rows:
        lid = row.get("lead_id", "")
        m = re.search(r'(\d+)', lid)
        if m:
            max_id = max(max_id, int(m.group(1)))

    now = datetime.now().strftime("%Y-%m-%d")
    added = 0

    with open(leads_path, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for company in new_companies:
            max_id += 1
            lead_id = f"AU-{max_id:04d}"
            row = {fn: "" for fn in fieldnames}
            row.update({
                "lead_id": lead_id,
                "company_name": company["company_name"],
                "website": company["website"],
                "country": "Australia",
                "industry_type": "Restaurant/Hotel",
                "customer_type": "Final Customer",
                "source_type": "Keyword Discovery",
                "source_link": company["source_url"],
                "keyword_source_query": company["source_query"],
                "verification_status": "Discovered",
                "contact_research_status": "待处理",
                "last_updated": now,
                "enrichment_notes": f"Discovered via keyword search. Domain: {company['domain']}",
            })
            if company.get("email"):
                row["email_address"] = company["email"]
            if company.get("phone"):
                row["phone_number"] = company["phone"]
            if company.get("contact_page"):
                row["official_contact_page"] = company["contact_page"]
            writer.writerow(row)
            added += 1
            safe_name = company['company_name'].encode('ascii', 'replace').decode('ascii')
            print(f"  + {lead_id}: {safe_name} ({company['domain']})")

    return added


def main():
    parser = argparse.ArgumentParser(description="Discover new companies via keyword Google search")
    parser.add_argument("--limit", type=int, default=3, help="Number of keywords to use")
    parser.add_argument("--max-results", type=int, default=5, help="Google results per keyword")
    parser.add_argument("--keywords", type=str, default="", help="Comma-separated keyword IDs to use")
    parser.add_argument("--dry-run", action="store_true", help="Don't save to leads.csv")
    args = parser.parse_args()

    with RunTimer("b"):
        # Load existing data for dedup
        existing_names, existing_domains, _ = load_existing_leads()
        print(f"Existing leads: {len(existing_names)} companies, {len(existing_domains)} domains")

        # Load keywords
        kw_path = DATA / "search_keywords.csv"
        with open(kw_path, "r", encoding="utf-8-sig") as f:
            all_keywords = list(csv.DictReader(f))

        # Filter eligible keywords
        if args.keywords:
            target_ids = set(args.keywords.split(","))
            keywords = [kw for kw in all_keywords if kw.get("keyword_id") in target_ids]
        else:
            keywords = [kw for kw in all_keywords
                        if kw.get("keyword_status") == "New"
                        and kw.get("keyword_intent_type") == "Discovery"]

        # Sort by priority
        prio_order = {"high": 0, "High": 0, "medium": 1, "Medium": 1, "low": 2, "Low": 2}
        keywords.sort(key=lambda k: (prio_order.get(k.get("priority_level", ""), 3), k.get("keyword_id", "")))

        keywords = keywords[:args.limit]
        print(f"Selected {len(keywords)} keywords:")
        for kw in keywords:
            print(f"  {kw['keyword_id']}: {kw['keyword_pattern']}")

        # Discover
        all_new = []
        used_kw_ids = []
        use_cache = not args.dry_run  # dry-run 时禁用缓存
        for kw in keywords:
            raw_query = kw.get("example_search_query") or kw.get("keyword_pattern", "")
            if not raw_query:
                continue

            # 展开模板占位符
            queries = _expand_templates(raw_query)

            for query in queries:
                print(f"\nSearching: {query}")
                new = discover_from_keyword(query, args.max_results, existing_names, existing_domains, use_cache=use_cache, dry_run=args.dry_run)
                print(f"  Found {len(new)} new companies")
                all_new.extend(new)
                time.sleep(2)

            used_kw_ids.append(kw["keyword_id"])

        print(f"\nTotal new companies discovered: {len(all_new)}")

        if not args.dry_run:
            added = 0
            if all_new:
                added = save_to_leads(all_new)
                print(f"Added {added} new leads to data/leads.csv")
            # Always update keyword status (runs +1)
            _update_keyword_status(used_kw_ids, leads_count=added)
        elif args.dry_run:
            print("\n[Dry run] Would add:")
            for c in all_new:
                safe_name = c['company_name'].encode('ascii', 'replace').decode('ascii')
                print(f"  {safe_name} | {c['website']} | {c.get('email', '')}")

        close_browser()

        # 自动生成 B-Run 报告
        if not args.dry_run and used_kw_ids:
            print("\n--- 生成 B-Run 报告 ---")
            from scripts.reports.generate_keyword_report import main as gen_kw_report
            old_argv = sys.argv
            sys.argv = [
                "generate_keyword_report",
                "--auto-timing",
                "--task", f"关键词发现 limit {args.limit}",
            ]
            try:
                gen_kw_report()
            except Exception as e:
                print(f"  报告生成失败: {e}")
            finally:
                sys.argv = old_argv

    print("\nDone.")


def _update_keyword_status(kw_ids, leads_count=0):
    """更新已使用关键词的状态和运行统计。"""
    kw_path = DATA / "search_keywords.csv"
    rows = []
    with open(kw_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("keyword_id") in kw_ids:
                row["keyword_status"] = "Testing"
                row["used_recently"] = "Yes"
                row["last_used_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                # Increment total_runs
                try:
                    row["total_runs"] = str(int(row.get("total_runs") or 0) + 1)
                except ValueError:
                    row["total_runs"] = "1"
                # Increment total_leads_collected
                if leads_count > 0:
                    try:
                        row["total_leads_collected"] = str(int(row.get("total_leads_collected") or 0) + leads_count)
                    except ValueError:
                        row["total_leads_collected"] = str(leads_count)
            rows.append(row)

    with open(kw_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Updated {len(kw_ids)} keyword status to Testing (runs +1, leads +{leads_count})")


if __name__ == "__main__":
    main()
