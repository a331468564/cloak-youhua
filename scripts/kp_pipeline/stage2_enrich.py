# scripts/kp_pipeline/stage2_enrich.py
"""
Stage 2: 直联路径富化

补缺模块：对已识别 KP 名字但缺少直联（邮箱/电话）的线索，
通过网页搜索寻找直联路径。

已有能力复用：
- extract_public_contact_candidates.py 中的邮箱/电话提取逻辑
- workflow_checker.py 中的防重复和阈值控制
本模块只做"已知人名 → 搜直联"这一件事。
"""
import random
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, quote_plus

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapling.fetchers import Fetcher
from workflow_checker import checker as workflow_checker

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
    if not any(kw in url.lower() for url in candidate_urls
               for kw in ["team", "about", "people", "leadership", "our-team", "contact"]):
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
    """对已有 KP 名字但缺直联的线索列表运行 Stage 2。"""
    from .metrics import log_run_metrics

    stage_config = config.get("stages", {}).get("stage2_enrich", {})
    if not stage_config.get("enabled", True):
        return [], {"skipped": True}

    run_id = f"S2-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    workflow_checker.load_existing_data()

    enriched = []
    processed = 0
    direct_found = 0
    additional_count = 0
    skipped = 0

    for lead in leads_with_kp:
        processed += 1
        result, status = enrich_lead_kp(lead, config)

        if result:
            enriched.append(result)
            if result.get("directness") == "direct":
                direct_found += 1
            # 将同公司其他联系人也加入结果
            extras = result.get("additional_contacts", [])
            additional_count += len(extras)
            for extra in extras:
                enriched.append(extra)
                if extra.get("directness") == "direct":
                    direct_found += 1
        elif status in ("already_has_direct_contact", "missing_kp_or_website", "noisy_domain"):
            skipped += 1

    # 关闭 CloakBrowser 实例
    try:
        from .cloak_fetcher import close_browser
        close_browser()
    except Exception:
        pass

    metrics = {
        "candidates_processed": processed,
        "enriched": len(enriched),
        "direct_contacts_found": direct_found,
        "additional_contacts": additional_count,
        "skipped": skipped,
        "direct_contact_rate": round(direct_found / max(processed - skipped, 1), 3),
    }
    log_run_metrics(run_id, "stage2_enrich", metrics)

    return enriched, metrics
