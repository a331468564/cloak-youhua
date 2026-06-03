# scripts/kp_pipeline/stage2_enrich.py
"""
Stage 2: 直联路径富化

补缺模块：对已识别 KP 名字但缺少直联（邮箱/电话）的线索，
通过网页搜索寻找直联路径。

优化策略（v2）：
- 先深挖公司网站（sitemap + team pages + 邮箱模式推断）
- 公司级批量处理（同一公司只抓取一次网站）
- LinkedIn 公开 URL 直接访问（不消耗 Google 搜索配额）
- Google 搜索仅作为最后兜底，使用更自然的查询格式
- 结果缓存避免重复搜索

已有能力复用：
- extract_public_contact_candidates.py 中的邮箱/电话提取逻辑
- workflow_checker.py 中的防重复和阈值控制
本模块只做"已知人名 → 搜直联"这一件事。
"""
import random
import re
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, quote_plus

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapling.fetchers import Fetcher
from workflow_checker import checker as workflow_checker

# --- 结果缓存 ---
_company_cache = {}  # {domain: {kp_name: result}}
_domain_pages_cache = {}  # {domain: {urls_fetched: set, contacts: list, emails: set, email_pattern: str}}
_google_search_count = 0  # 当前会话 Google 搜索计数
_google_daily_limit = 50  # 每日 Google 搜索上限

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(
    r"(?:"
    r"(?:\+?61[\s.-]*(?:0)?4\d{2}[\s.-]*\d{3}[\s.-]*\d{3})|"
    r"(?:04\d{2}[\s.-]*\d{3}[\s.-]*\d{3})|"
    r"(?:\(?0[2378]\)?[\s.-]*\d{4}[\s.-]*\d{4})|"
    r"(?:(?:1300|1800)[\s.-]*\d{3}[\s.-]*\d{3})"
    r")"
)

EMAIL_SKIP = {"noreply", "no-reply", "careers", "jobs", "hr", "privacy", "media", "marketing"}
EMAIL_DEPARTMENT = {"sales", "procurement", "accounts", "events", "functions", "enquiries", "hello", "info", "admin"}
LINKEDIN_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/in/[\w\-]+/?", re.I)


def classify_email(email):
    """将邮箱分类为个人、部门或公司邮箱。"""
    if not email:
        return "unknown"
    local = email.split("@")[0].lower()
    # 个人邮箱优先（含点或下划线）
    if "." in local or "_" in local:
        parts = local.replace("_", ".").split(".")
        if len(parts) >= 2 and all(p.isalpha() for p in parts):
            return "person_email"
    # 公司通用邮箱（先于部门判断）
    if local in ("info", "admin", "contact", "hello", "enquiries"):
        return "company_email"
    # 部门邮箱
    if any(local.startswith(p) for p in EMAIL_DEPARTMENT):
        return "department_email"
    return "possible_person_email"


def classify_contact_directness(email, phone, linkedin=""):
    """分类联系路径的直联程度。"""
    has_email = bool(email and email.strip())
    has_phone = bool(phone and phone.strip())
    has_linkedin = bool(linkedin and linkedin.strip())

    if has_email:
        email_type = classify_email(email)
        if email_type == "person_email":
            return "direct", "High"
        if email_type == "possible_person_email":
            return "direct", "Medium"

    if has_phone and phone.strip().startswith("04"):
        return "direct", "High"

    if has_linkedin:
        return "linkedin_only", "Medium"

    if has_email or has_phone:
        return "company_route", "Medium"

    return "name_only", "Low"


def is_noisy_domain(url, blocklist):
    """检查 URL 是否在噪声域名黑名单中。"""
    if not url:
        return False
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return any(noisy in domain for noisy in blocklist)
    except Exception:
        return False


def fetch_page_text(url, timeout=15):
    """抓取页面并提取文本。智能路由：Scrapling → CloakBrowser 兜底 + cookie 回传。"""
    try:
        from .cloak_fetcher import smart_fetch
        text, html, status, error, tool = smart_fetch(url, timeout=timeout)
        if error:
            return None, error
        return text, None
    except ImportError:
        # cloak_fetcher 不可用时回退到 Scrapling
        try:
            page = Fetcher.get(url, timeout=timeout, retries=1)
            status = getattr(page, "status", 0)
            if not str(status).startswith("2"):
                return None, f"HTTP {status}"
            text = page.get_all_text(separator=" ") if hasattr(page, "get_all_text") else page.text
            return text, None
        except Exception as e:
            return None, f"{type(e).__name__}: {e}"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _get_page_xml(page):
    """从 Scrapling response 提取 XML 文本（兼容 text/body）。"""
    body = getattr(page, "body", None)
    if body:
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="replace")
        return str(body)
    text = getattr(page, "text", None)
    return text or ""


def fetch_sitemap_urls(domain, timeout=10):
    """从 sitemap.xml 提取页面 URL 列表。"""
    sitemap_urls = [
        f"https://{domain}/sitemap.xml",
        f"https://{domain}/sitemap_index.xml",
        f"https://{domain}/sitemap-index.xml",
        f"https://www.{domain}/sitemap.xml",
    ]

    for sitemap_url in sitemap_urls:
        try:
            page = Fetcher.get(sitemap_url, timeout=timeout, retries=1)
            status = getattr(page, "status", 0)
            if not str(status).startswith("2"):
                continue
            xml_text = _get_page_xml(page)
            if not xml_text or "<" not in xml_text:
                continue

            # 解析 XML
            try:
                root = ET.fromstring(xml_text)
            except ET.ParseError:
                continue

            # 处理 sitemap index（嵌套 sitemap）
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            sitemap_tags = root.findall(".//sm:sitemap/sm:loc", ns)
            if sitemap_tags:
                all_urls = []
                for loc in sitemap_tags[:3]:  # 最多读 3 个子 sitemap
                    sub_url = loc.text.strip() if loc.text else ""
                    if sub_url:
                        sub_page = Fetcher.get(sub_url, timeout=timeout, retries=1)
                        if str(getattr(sub_page, "status", 0)).startswith("2"):
                            sub_xml = _get_page_xml(sub_page)
                            if sub_xml:
                                try:
                                    sub_root = ET.fromstring(sub_xml)
                                    for u in sub_root.findall(".//sm:loc", ns):
                                        if u.text:
                                            all_urls.append(u.text.strip())
                                except ET.ParseError:
                                    pass
                return all_urls

            # 直接 sitemap
            urls = []
            for loc in root.findall(".//sm:loc", ns):
                if loc.text:
                    urls.append(loc.text.strip())
            return urls

        except Exception:
            continue
    return []


def filter_team_pages(sitemap_urls):
    """从 sitemap URL 列表中筛选团队/联系相关页面。"""
    team_keywords = [
        "team", "about", "people", "staff", "leadership", "management",
        "our-team", "meet-the-team", "contact", "who-we-are",
        "directors", "founders", "executives",
    ]
    matched = []
    for url in sitemap_urls:
        url_lower = url.lower()
        path = urlparse(url_lower).path
        if any(kw in path for kw in team_keywords):
            matched.append(url)
    return matched


def extract_emails_from_text(text):
    """从文本提取并过滤邮箱。"""
    if not text:
        return []
    raw = set(EMAIL_RE.findall(text))
    return [e.lower() for e in raw if not any(e.lower().split("@")[0].startswith(s) for s in EMAIL_SKIP)]


def extract_phones_from_text(text):
    """从文本提取澳大利亚电话号码。"""
    if not text:
        return []
    return list(set(PHONE_RE.findall(text)))


def find_person_email(emails, kp_name):
    """从邮箱列表中找到匹配 KP 名字的邮箱。"""
    if not emails or not kp_name:
        return ""
    name_parts = kp_name.lower().split()
    for email in emails:
        local = email.split("@")[0].lower()
        if all(part in local for part in name_parts if len(part) > 2):
            return email
    return ""


def extract_linkedin_urls(text):
    """从文本提取 LinkedIn 个人主页 URL。"""
    if not text:
        return []
    return list(set(LINKEDIN_RE.findall(text)))


def extract_email_pattern(emails, target_domain=None):
    """从已有邮箱列表中推断公司邮箱模式。

    常见模式：
    - firstname.lastname@domain.com
    - firstnamelastname@domain.com
    - f.lastname@domain.com
    - firstname.l@domain.com

    Args:
        emails: 邮箱列表
        target_domain: 目标公司域名（如 "example.com"）。如果提供，
            只分析该域名的邮箱，避免跨域名邮箱污染推断结果。

    返回 (pattern_type, domain) 或 (None, None)。
    """
    if not emails:
        return None, None

    # 按域名过滤，避免跨域名邮箱污染
    if target_domain:
        td = target_domain.lower()
        filtered = [e for e in emails if e.split("@")[1].lower() == td]
    else:
        filtered = list(emails)

    # 筛选个人邮箱（含点或下划线）
    person_emails = []
    for email in filtered:
        local = email.split("@")[0].lower()
        if "." in local or "_" in local:
            parts = local.replace("_", ".").split(".")
            if len(parts) >= 2 and all(p.isalpha() and len(p) > 1 for p in parts):
                person_emails.append(email)

    if not person_emails:
        return None, None

    # 分析模式
    patterns = {"firstname.lastname": 0, "firstnamelastname": 0, "f.lastname": 0, "firstname.l": 0}

    for email in person_emails:
        local = email.split("@")[0].lower().replace("_", ".")
        parts = local.split(".")

        if len(parts) == 2:
            first, last = parts
            if len(first) > 1 and len(last) > 1:
                patterns["firstname.lastname"] += 1
            elif len(first) == 1 and len(last) > 1:
                patterns["f.lastname"] += 1
            elif len(first) > 1 and len(last) == 1:
                patterns["firstname.l"] += 1

    # 返回最常见的模式
    if patterns["firstname.lastname"] > 0:
        return "firstname.lastname", person_emails[0].split("@")[1].lower()
    if patterns["f.lastname"] > 0:
        return "f.lastname", person_emails[0].split("@")[1].lower()
    if patterns["firstname.l"] > 0:
        return "firstname.l", person_emails[0].split("@")[1].lower()

    return None, None


def infer_email_from_pattern(kp_name, pattern_type, domain):
    """根据邮箱模式为 KP 生成候选邮箱。

    Args:
        kp_name: KP 全名（如 "John Smith"）
        pattern_type: 邮箱模式类型
        domain: 邮箱域名

    Returns:
        候选邮箱列表（按可能性排序）
    """
    if not kp_name or not pattern_type or not domain:
        return []

    parts = kp_name.strip().split()
    if len(parts) < 2:
        return []

    first = parts[0].lower()
    last = parts[-1].lower()

    candidates = []

    if pattern_type == "firstname.lastname":
        candidates.append(f"{first}.{last}@{domain}")
        candidates.append(f"{first}{last}@{domain}")
    elif pattern_type == "f.lastname":
        candidates.append(f"{first[0]}.{last}@{domain}")
        candidates.append(f"{first[0]}{last}@{domain}")
    elif pattern_type == "firstname.l":
        candidates.append(f"{first}.{last[0]}@{domain}")
        candidates.append(f"{first}{last[0]}@{domain}")

    # 通用模式（不论什么 pattern_type 都尝试）
    candidates.append(f"{first}.{last}@{domain}")
    candidates.append(f"{first}{last}@{domain}")
    candidates.append(f"{first[0]}.{last}@{domain}")

    # 去重保持顺序
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    return unique


def build_company_level_queries(company_name, domain):
    """构建公司级 Google 查询（比 KP 级查询更自然，消耗更少搜索配额）。

    返回查询列表，每个查询用于发现公司团队/联系信息。
    """
    queries = []

    # 公司团队页面搜索（不带 site: 前缀，更自然）
    queries.append(f'"{company_name}" team OR leadership OR staff')
    queries.append(f'"{company_name}" contact OR "get in touch"')

    # 带 site: 的精确搜索（仅在需要时使用）
    if domain:
        queries.append(f'site:{domain} team OR about OR leadership')

    return queries


def human_delay(base=2.0, jitter=1.5):
    """随机延迟，模拟人类浏览节奏。"""
    time.sleep(base + random.uniform(0, jitter))


def build_google_dork_queries(kp_name, company_name, domain):
    """构建 Google dork 查询列表（复用 generate_kp_search_tasks.py 的模式）。"""
    queries = []
    if domain:
        queries.append(f'site:{domain} "{kp_name}"')
    queries.append(f'"{kp_name}" "{company_name}" email OR phone OR contact')
    queries.append(f'"{kp_name}" "{company_name}" director OR operations OR procurement')
    # LinkedIn 搜索
    queries.append(f'site:linkedin.com/in "{kp_name}" "{company_name}"')
    return queries


def search_google(query, max_results=5):
    """执行 Google 搜索，返回结果页面 URL 列表。始终用 CloakBrowser 绕过 429。"""
    try:
        from .cloak_fetcher import search_google as _search
        return _search(query, max_results=max_results)
    except ImportError:
        return []
    except Exception:
        return []


def extract_all_contacts_from_url(url, company_name, existing_names=None):
    """从页面提取所有可识别的联系人（同公司多人）。"""
    text, error = fetch_page_text(url)
    if not text:
        return []

    emails = extract_emails_from_text(text)
    phones = extract_phones_from_text(text)
    linkedin_urls = extract_linkedin_urls(text)
    existing_names = set(n.lower() for n in (existing_names or []))

    contacts = []

    # 从个人邮箱推断联系人
    for email in emails:
        local = email.split("@")[0].lower()
        # 个人邮箱（含点或下划线）
        if "." in local or "_" in local:
            parts = local.replace("_", ".").split(".")
            if len(parts) >= 2 and all(p.isalpha() and len(p) > 1 for p in parts):
                name = " ".join(p.capitalize() for p in parts)
                if name.lower() not in existing_names:
                    contacts.append({
                        "name": name,
                        "company_name": company_name,
                        "source_url": url,
                        "best_email": email,
                        "best_phone": "",
                        "best_linkedin": "",
                        "person_email_found": True,
                        "inferred_from": "email_pattern",
                    })
                    existing_names.add(name.lower())

    # 从 LinkedIn URL 推断联系人
    for lu in linkedin_urls:
        # linkedin.com/in/firstname-lastname
        slug = lu.rstrip("/").split("/")[-1].lower()
        parts = slug.split("-")
        if len(parts) >= 2 and all(p.isalpha() and len(p) > 1 for p in parts):
            name = " ".join(p.capitalize() for p in parts if p not in ("au", "com", "linkedin"))
            if name and name.lower() not in existing_names:
                contacts.append({
                    "name": name,
                    "company_name": company_name,
                    "source_url": url,
                    "best_email": "",
                    "best_phone": "",
                    "best_linkedin": lu,
                    "person_email_found": False,
                    "inferred_from": "linkedin_url",
                })
                existing_names.add(name.lower())

    return contacts


def enrich_kp_from_url(url, kp_name, company_name):
    """从指定 URL 提取 KP 的直联信息。"""
    text, error = fetch_page_text(url)
    if not text:
        return None

    # 检查 KP 名字是否出现在页面上
    if kp_name.lower() not in text.lower():
        return None

    emails = extract_emails_from_text(text)
    phones = extract_phones_from_text(text)
    linkedin_urls = extract_linkedin_urls(text)
    person_email = find_person_email(emails, kp_name)

    # 匹配 KP 名字的 LinkedIn（名字出现在 URL 附近）
    best_linkedin = ""
    if linkedin_urls:
        # 优先选择包含 KP 名字部分的 LinkedIn URL
        name_parts = [p.lower() for p in kp_name.split() if len(p) > 2]
        for lu in linkedin_urls:
            if any(part in lu.lower() for part in name_parts):
                best_linkedin = lu
                break
        if not best_linkedin:
            best_linkedin = linkedin_urls[0]

    return {
        "name": kp_name,
        "company_name": company_name,
        "source_url": url,
        "emails": emails,
        "phones": phones,
        "linkedin_urls": linkedin_urls,
        "best_email": person_email or (emails[0] if emails else ""),
        "best_phone": phones[0] if phones else "",
        "best_linkedin": best_linkedin,
        "person_email_found": bool(person_email),
    }


def enrich_company_kps(company_leads, config):
    """公司级批量处理：对同一公司的多个 KP 进行富化。

    优化策略：
    1. 只抓取一次公司网站（sitemap + team pages）
    2. 从团队页面提取所有联系人
    3. 为每个 KP 尝试匹配已提取的联系人
    4. 如果有邮箱模式，为未匹配的 KP 生成候选邮箱
    5. 尝试 LinkedIn 公开 URL（不消耗 Google 配额）
    6. 最后才用 Google 搜索（公司级查询，非 KP 级）

    Args:
        company_leads: 同一公司的所有 KP 线索列表
        config: 配置

    Returns:
        list of (lead, result, status) tuples
    """
    if not company_leads:
        return []

    stage_config = config.get("stages", {}).get("stage2_enrich", {})
    blocklist = stage_config.get("noisy_domains_blocklist", [])
    delay = stage_config.get("delay_between_requests_seconds", 2.0)

    # 取第一个 lead 的公司信息
    first_lead = company_leads[0]
    company_name = first_lead.get("company_name", "")
    website = (first_lead.get("website") or "").strip()

    if not website:
        return [(lead, None, "missing_website") for lead in company_leads]

    # 解析域名
    try:
        parsed = urlparse(website if "://" in website else f"https://{website}")
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
    except Exception:
        return [(lead, None, "invalid_url") for lead in company_leads]

    if is_noisy_domain(website, blocklist):
        return [(lead, None, "noisy_domain") for lead in company_leads]

    # 检查缓存
    cache_key = domain
    if cache_key in _company_cache:
        cached = _company_cache[cache_key]
        results = []
        for lead in company_leads:
            kp_name = lead.get("key_contact_name", "").strip()
            if kp_name in cached:
                results.append((lead, cached[kp_name], "cached"))
            else:
                results.append((lead, None, "not_found_in_cache"))
        return results

    # 初始化公司级缓存
    company_results = {}
    _kp_lead_id_map = {}  # kp_name -> lead_id 映射，用于 Google 搜索阶段
    all_extracted_contacts = []
    all_emails = set()
    email_pattern = None
    email_domain = None

    # 构建 kp_name -> lead_id 映射
    for lead in company_leads:
        kp_name = lead.get("key_contact_name", "").strip()
        lead_id = lead.get("lead_id", "")
        if kp_name:
            _kp_lead_id_map[kp_name] = lead_id

    # --- 阶段 1：抓取公司网站，提取所有联系信息 ---

    # 已知的联系页面
    candidate_urls = []
    contact_page = first_lead.get("company_contact_page", "").strip()
    contact_form = first_lead.get("company_contact_form_url", "").strip()
    if contact_page:
        candidate_urls.append(contact_page)
    if contact_form and contact_form != contact_page:
        candidate_urls.append(contact_form)

    # 从 sitemap 获取团队/联系页面
    sitemap_urls = fetch_sitemap_urls(domain)
    if sitemap_urls:
        team_pages = filter_team_pages(sitemap_urls)
        candidate_urls.extend(team_pages)

    # sitemap 没找到时，回退到猜路径
    _team_kw = {"team", "about", "people", "leadership", "our-team", "contact"}
    if not any(kw in u.lower() for u in candidate_urls for kw in _team_kw):
        for path in ["/team", "/about", "/people", "/leadership", "/our-team"]:
            candidate_urls.append(f"https://{domain}{path}")

    # 抓取每个页面，提取联系信息
    fetched_urls = set()
    for url in candidate_urls:
        if is_noisy_domain(url, blocklist):
            continue
        if url in fetched_urls:
            continue
        fetched_urls.add(url)

        text, error = fetch_page_text(url)
        if not text:
            continue

        # 提取所有邮箱、电话、LinkedIn
        emails = extract_emails_from_text(text)
        phones = extract_phones_from_text(text)
        linkedin_urls = extract_linkedin_urls(text)

        all_emails.update(emails)

        # 从个人邮箱推断联系人
        for email in emails:
            local = email.split("@")[0].lower()
            if "." in local or "_" in local:
                parts = local.replace("_", ".").split(".")
                if len(parts) >= 2 and all(p.isalpha() and len(p) > 1 for p in parts):
                    name = " ".join(p.capitalize() for p in parts)
                    all_extracted_contacts.append({
                        "name": name,
                        "company_name": company_name,
                        "source_url": url,
                        "best_email": email,
                        "best_phone": "",
                        "best_linkedin": "",
                        "person_email_found": True,
                        "inferred_from": "email_pattern",
                    })

        # 从 LinkedIn URL 推断联系人
        for lu in linkedin_urls:
            slug = lu.rstrip("/").split("/")[-1].lower()
            parts = slug.split("-")
            if len(parts) >= 2 and all(p.isalpha() and len(p) > 1 for p in parts):
                name = " ".join(p.capitalize() for p in parts if p not in ("au", "com", "linkedin"))
                if name:
                    all_extracted_contacts.append({
                        "name": name,
                        "company_name": company_name,
                        "source_url": url,
                        "best_email": "",
                        "best_phone": "",
                        "best_linkedin": lu,
                        "person_email_found": False,
                        "inferred_from": "linkedin_url",
                    })

        # 提取页面上的电话（用于后续匹配）
        for phone in phones:
            all_extracted_contacts.append({
                "name": "",
                "company_name": company_name,
                "source_url": url,
                "best_email": "",
                "best_phone": phone,
                "best_linkedin": "",
                "person_email_found": False,
                "inferred_from": "phone",
            })

        human_delay(delay)

    # 推断邮箱模式（只使用公司域名的邮箱，避免跨域名污染）
    email_pattern, email_domain = extract_email_pattern(list(all_emails), target_domain=domain)

    # --- 阶段 2：为每个 KP 匹配或推断直联信息 ---

    for lead in company_leads:
        kp_name = lead.get("key_contact_name", "").strip()
        lead_id = lead.get("lead_id", "")

        if not kp_name:
            company_results[kp_name] = None
            continue

        # 检查是否已有直联
        existing_email = lead.get("key_contact_email", "").strip()
        existing_phone = lead.get("key_contact_phone", "").strip()
        if existing_email or existing_phone:
            company_results[kp_name] = None
            continue

        # 2a: 从已提取的联系人中匹配
        best_match = None
        for contact in all_extracted_contacts:
            contact_name = contact.get("name", "").lower()
            if contact_name and kp_name.lower() in contact_name:
                best_match = contact.copy()
                best_match["name"] = kp_name
                best_match["lead_id"] = lead_id
                best_match["search_phase"] = "company_page_match"
                break

        # 2b: 如果有邮箱模式，生成候选邮箱
        if not best_match and email_pattern and email_domain:
            candidate_emails = infer_email_from_pattern(kp_name, email_pattern, email_domain)
            if candidate_emails:
                best_match = {
                    "name": kp_name,
                    "company_name": company_name,
                    "source_url": f"inferred_from_pattern ({email_pattern})",
                    "best_email": candidate_emails[0],
                    "best_phone": "",
                    "best_linkedin": "",
                    "person_email_found": False,
                    "inferred_from": "email_pattern_inference",
                    "lead_id": lead_id,
                    "search_phase": "email_inference",
                }

        # 2c: 在已抓取的页面中搜索 KP 名字
        if not best_match:
            for url in fetched_urls:
                text, error = fetch_page_text(url)
                if text and kp_name.lower() in text.lower():
                    # 找到 KP 名字出现在页面上
                    emails = extract_emails_from_text(text)
                    phones = extract_phones_from_text(text)
                    linkedin_urls = extract_linkedin_urls(text)
                    person_email = find_person_email(emails, kp_name)

                    best_linkedin = ""
                    if linkedin_urls:
                        name_parts = [p.lower() for p in kp_name.split() if len(p) > 2]
                        for lu in linkedin_urls:
                            if any(part in lu.lower() for part in name_parts):
                                best_linkedin = lu
                                break
                        if not best_linkedin:
                            best_linkedin = linkedin_urls[0]

                    best_match = {
                        "name": kp_name,
                        "company_name": company_name,
                        "source_url": url,
                        "emails": emails,
                        "phones": phones,
                        "linkedin_urls": linkedin_urls,
                        "best_email": person_email or (emails[0] if emails else ""),
                        "best_phone": phones[0] if phones else "",
                        "best_linkedin": best_linkedin,
                        "person_email_found": bool(person_email),
                        "lead_id": lead_id,
                        "search_phase": "company_page_search",
                    }
                    break

        if best_match:
            # 分类直联程度
            directness, confidence = classify_contact_directness(
                best_match.get("best_email", ""),
                best_match.get("best_phone", ""),
                best_match.get("best_linkedin", "")
            )
            best_match["directness"] = directness
            best_match["confidence"] = confidence
            company_results[kp_name] = best_match
        else:
            company_results[kp_name] = None

    # --- 阶段 3：Google 搜索（仅对未找到直联的 KP，且有搜索配额）---

    global _google_search_count
    kps_needing_google = [
        kp_name for kp_name, result in company_results.items()
        if result is None or result.get("directness") != "direct"
    ]

    if kps_needing_google and _google_search_count < _google_daily_limit:
        # 使用公司级查询（更自然，消耗更少配额）
        company_queries = build_company_level_queries(company_name, domain)

        for query in company_queries:
            if _google_search_count >= _google_daily_limit:
                print(f"[Stage 2] Google 搜索配额已达上限 ({_google_daily_limit})")
                break

            search_urls = search_google(query, max_results=3)
            _google_search_count += 1

            for url in search_urls:
                if is_noisy_domain(url, blocklist):
                    continue
                if url in fetched_urls:
                    continue
                fetched_urls.add(url)

                text, error = fetch_page_text(url)
                if not text:
                    continue

                # 从搜索结果中提取联系信息
                emails = extract_emails_from_text(text)
                phones = extract_phones_from_text(text)
                linkedin_urls = extract_linkedin_urls(text)
                all_emails.update(emails)

                # 为每个未匹配的 KP 检查
                for kp_name in kps_needing_google:
                    if company_results.get(kp_name) and company_results[kp_name].get("directness") == "direct":
                        continue

                    if kp_name.lower() in text.lower():
                        person_email = find_person_email(emails, kp_name)

                        best_linkedin = ""
                        if linkedin_urls:
                            name_parts = [p.lower() for p in kp_name.split() if len(p) > 2]
                            for lu in linkedin_urls:
                                if any(part in lu.lower() for part in name_parts):
                                    best_linkedin = lu
                                    break
                            if not best_linkedin:
                                best_linkedin = linkedin_urls[0]

                        result = {
                            "name": kp_name,
                            "company_name": company_name,
                            "source_url": url,
                            "emails": emails,
                            "phones": phones,
                            "linkedin_urls": linkedin_urls,
                            "best_email": person_email or (emails[0] if emails else ""),
                            "best_phone": phones[0] if phones else "",
                            "best_linkedin": best_linkedin,
                            "person_email_found": bool(person_email),
                            "lead_id": _kp_lead_id_map.get(kp_name, ""),
                            "search_phase": "google_company",
                            "search_query": query,
                        }

                        directness, confidence = classify_contact_directness(
                            result["best_email"], result["best_phone"], result.get("best_linkedin", "")
                        )
                        result["directness"] = directness
                        result["confidence"] = confidence

                        # 只有当结果更好时才更新
                        current = company_results.get(kp_name)
                        if not current or _is_better_result(result, current):
                            company_results[kp_name] = result

                human_delay(delay)

            # 如果所有 KP 都找到直联，提前停止
            if all(
                company_results.get(kp) and company_results[kp].get("directness") == "direct"
                for kp in kps_needing_google
            ):
                break

    # --- 阶段 4：整理结果 ---

    # 更新邮箱模式（可能从 Google 搜索结果中发现了新模式，只用公司域名邮箱）
    email_pattern, email_domain = extract_email_pattern(list(all_emails), target_domain=domain)

    # 为仍然没有直联的 KP 生成候选邮箱（如果发现了新模式）
    if email_pattern and email_domain:
        for kp_name in kps_needing_google:
            if company_results.get(kp_name) is None:
                candidate_emails = infer_email_from_pattern(kp_name, email_pattern, email_domain)
                if candidate_emails:
                    lead = next((l for l in company_leads if l.get("key_contact_name", "").strip() == kp_name), None)
                    if lead:
                        company_results[kp_name] = {
                            "name": kp_name,
                            "company_name": company_name,
                            "source_url": f"inferred_from_pattern ({email_pattern})",
                            "best_email": candidate_emails[0],
                            "best_phone": "",
                            "best_linkedin": "",
                            "person_email_found": False,
                            "inferred_from": "email_pattern_inference_late",
                            "lead_id": lead.get("lead_id", ""),
                            "search_phase": "email_inference_late",
                        }

    # 缓存结果
    _company_cache[cache_key] = company_results

    # 构建返回结果
    results = []
    for lead in company_leads:
        kp_name = lead.get("key_contact_name", "").strip()
        result = company_results.get(kp_name)
        if result:
            directness, confidence = classify_contact_directness(
                result.get("best_email", ""),
                result.get("best_phone", ""),
                result.get("best_linkedin", "")
            )
            result["directness"] = directness
            result["confidence"] = confidence
            results.append((lead, result, "enriched"))
        else:
            results.append((lead, None, "no_contact_found"))

    return results


def _is_better_result(new, old):
    """比较两个结果，判断新的是否更好。"""
    rank = {
        "direct": 3,
        "linkedin_only": 2,
        "company_route": 1,
        "name_only": 0,
    }
    new_rank = rank.get(new.get("directness", ""), -1)
    old_rank = rank.get(old.get("directness", ""), -1)

    if new_rank > old_rank:
        return True
    if new_rank == old_rank:
        # 同级别时，优先选择有个人邮箱的
        if new.get("person_email_found") and not old.get("person_email_found"):
            return True
    return False


def enrich_lead_kp(lead, config):
    """对单条线索的已知 KP 进行直联富化。"""
    stage_config = config.get("stages", {}).get("stage2_enrich", {})
    blocklist = stage_config.get("noisy_domains_blocklist", [])
    delay = stage_config.get("delay_between_requests_seconds", 2.0)

    lead_id = lead.get("lead_id", "")
    company_name = lead.get("company_name", "")
    kp_name = lead.get("key_contact_name", "").strip()
    website = (lead.get("website") or "").strip()

    if not kp_name or not website:
        return None, "missing_kp_or_website"

    # 解析域名
    try:
        parsed = urlparse(website if "://" in website else f"https://{website}")
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
    except Exception:
        return None, "invalid_url"

    if is_noisy_domain(website, blocklist):
        return None, "noisy_domain"

    # 检查是否已有直联
    existing_email = lead.get("key_contact_email", "").strip()
    existing_phone = lead.get("key_contact_phone", "").strip()
    if existing_email or existing_phone:
        return None, "already_has_direct_contact"

    # 先从已有官网联系页/团队页尝试富化
    candidate_urls = []

    # 已知的联系页面
    contact_page = lead.get("company_contact_page", "").strip()
    contact_form = lead.get("company_contact_form_url", "").strip()
    if contact_page:
        candidate_urls.append(contact_page)
    if contact_form and contact_form != contact_page:
        candidate_urls.append(contact_form)

    # 从 sitemap 获取团队/联系页面
    sitemap_urls = fetch_sitemap_urls(domain)
    if sitemap_urls:
        team_pages = filter_team_pages(sitemap_urls)
        candidate_urls.extend(team_pages)

    # sitemap 没找到时，回退到猜路径
    _team_kw = {"team", "about", "people", "leadership", "our-team", "contact"}
    if not any(kw in u.lower() for u in candidate_urls for kw in _team_kw):
        for path in ["/team", "/about", "/people", "/leadership", "/our-team"]:
            candidate_urls.append(f"https://{domain}{path}")

    results = []
    errors = []

    # 第一阶段：从已知官网页面提取
    for url in candidate_urls:
        if is_noisy_domain(url, blocklist):
            continue

        result = enrich_kp_from_url(url, kp_name, company_name)
        if result:
            directness, confidence = classify_contact_directness(result["best_email"], result["best_phone"], result.get("best_linkedin", ""))
            result["directness"] = directness
            result["confidence"] = confidence
            result["lead_id"] = lead_id
            result["search_phase"] = "direct_page"
            results.append(result)

            # 如果找到直联，不需要继续搜索
            if directness == "direct":
                break

        human_delay(delay)

    # 第二阶段：Google dork 搜索（仅当第一阶段未找到直联时）
    has_direct = any(r.get("directness") == "direct" for r in results)
    if not has_direct:
        dork_queries = build_google_dork_queries(kp_name, company_name, domain)
        for query in dork_queries:
            search_urls = search_google(query, max_results=3)
            for url in search_urls:
                if is_noisy_domain(url, blocklist):
                    continue

                result = enrich_kp_from_url(url, kp_name, company_name)
                if result:
                    directness, confidence = classify_contact_directness(result["best_email"], result["best_phone"], result.get("best_linkedin", ""))
                    result["directness"] = directness
                    result["confidence"] = confidence
                    result["lead_id"] = lead_id
                    result["search_phase"] = "google_dork"
                    result["search_query"] = query
                    results.append(result)

                    if directness == "direct":
                        break

                human_delay(delay)

            if any(r.get("directness") == "direct" for r in results):
                break

    if not results:
        return None, "no_contact_found"

    # 返回最佳结果（优先直联 > LinkedIn > 公司路径）
    def result_rank(r):
        d = r.get("directness", "")
        return (
            d == "direct",
            r.get("person_email_found", False),
            bool(r.get("best_linkedin")),
            d == "linkedin_only",
            d == "company_route",
            len(r.get("emails", [])),
        )

    best = max(results, key=result_rank)

    # 第三阶段：从团队页面提取同公司其他联系人
    team_pages = [url for url in candidate_urls
                  if any(kw in url.lower() for kw in ["team", "about", "people", "leadership", "our-team"])]
    additional = []
    known_names = {kp_name.lower()}
    if best.get("name"):
        known_names.add(best["name"].lower())

    for url in team_pages:
        if is_noisy_domain(url, blocklist):
            continue
        others = extract_all_contacts_from_url(url, company_name, existing_names=known_names)
        for o in others:
            o["lead_id"] = lead_id
            o["search_phase"] = "team_page"
            dc, cf = classify_contact_directness(o.get("best_email", ""), o.get("best_phone", ""), o.get("best_linkedin", ""))
            o["directness"] = dc
            o["confidence"] = cf
            additional.append(o)
            known_names.add(o["name"].lower())
        if additional:
            break  # 找到一个团队页就够了

    best["additional_contacts"] = additional
    return best, "enriched"


def run_stage2(leads_with_kp, config):
    """对已有 KP 名字但缺直联的线索列表运行 Stage 2。

    优化版本：使用公司级批量处理，减少 HTTP 请求和 Google 搜索。
    """
    from .metrics import log_run_metrics

    stage_config = config.get("stages", {}).get("stage2_enrich", {})
    if not stage_config.get("enabled", True):
        return [], {"skipped": True}

    run_id = f"S2-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    workflow_checker.load_existing_data()

    # 重置缓存和搜索计数
    global _company_cache, _google_search_count
    _company_cache = {}
    _google_search_count = 0

    # 按公司分组 KP
    company_groups = defaultdict(list)
    skipped = 0

    for lead in leads_with_kp:
        kp_name = lead.get("key_contact_name", "").strip()
        website = (lead.get("website") or "").strip()

        if not kp_name or not website:
            skipped += 1
            continue

        # 检查是否已有直联
        existing_email = lead.get("key_contact_email", "").strip()
        existing_phone = lead.get("key_contact_phone", "").strip()
        if existing_email or existing_phone:
            skipped += 1
            continue

        # 解析域名作为分组键
        try:
            parsed = urlparse(website if "://" in website else f"https://{website}")
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
        except Exception:
            skipped += 1
            continue

        company_groups[domain].append(lead)

    print(f"  [Stage 2] {len(company_groups)} 家公司，{sum(len(v) for v in company_groups.values())} 个 KP")

    # 按公司批量处理
    enriched = []
    processed = 0
    direct_found = 0

    for domain, company_leads in company_groups.items():
        processed += len(company_leads)

        # 使用公司级批量处理
        results = enrich_company_kps(company_leads, config)

        for lead, result, status in results:
            if result:
                enriched.append(result)
                if result.get("directness") == "direct":
                    direct_found += 1

    # 关闭 CloakBrowser 实例
    try:
        from .cloak_fetcher import close_browser
        close_browser()
    except Exception:
        pass

    metrics = {
        "candidates_processed": processed,
        "companies_processed": len(company_groups),
        "enriched": len(enriched),
        "direct_contacts_found": direct_found,
        "skipped": skipped,
        "google_searches_used": _google_search_count,
        "direct_contact_rate": round(direct_found / max(processed - skipped, 1), 3),
    }
    log_run_metrics(run_id, "stage2_enrich", metrics)

    return enriched, metrics
