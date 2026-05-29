"""
智能抓取器：Scrapling + CloakBrowser 深度联动。

联动策略：
1. 域名路由记忆 — 记住每个域名哪个工具可用，避免重复试探
2. Cookie 传递 — CloakBrowser 探路拿到 cookies/UA → 传给 Scrapling
3. 智能降级 — Scrapling 失败 → CloakBrowser 兜底 → cookies 回传 Scrapling

路由表持久化到 data/fetch_routes.json，跨会话复用。

设计约束：
- Google 搜索始终用 CloakBrowser（Scrapling 会被 429）
- CloakBrowser 使用同步 launch() API，避免 asyncio.run() 事件循环生命周期问题
- Scrapling 传 headers（不是 extra_headers）参数
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_ROUTES_FILE = _DATA_DIR / "fetch_routes.json"

# 路由状态
ROUTE_SCRAPOK = "scrapling_ok"       # Scrapling 可用
ROUTE_CLOAKOK = "cloak_ok"           # 需要 CloakBrowser
ROUTE_BLOCKED = "blocked"            # 两个都不行

_browser = None
_routes = {}  # {domain: {"status": str, "cookies": [...], "ua": str, "updated": str}}


def _load_routes():
    """加载持久化路由表。"""
    global _routes
    if _ROUTES_FILE.exists():
        try:
            _routes = json.loads(_ROUTES_FILE.read_text(encoding="utf-8"))
        except Exception:
            _routes = {}


def _save_routes():
    """保存路由表。"""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _ROUTES_FILE.write_text(json.dumps(_routes, ensure_ascii=False, indent=2), encoding="utf-8")


def _domain_of(url):
    """提取域名（去掉 www.）。"""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


# --- CloakBrowser 管理（同步 API）---

def _get_browser():
    """复用全局 CloakBrowser 同步实例。"""
    global _browser
    if _browser is None:
        from cloakbrowser import launch
        _browser = launch(headless=True)
    return _browser


def close_browser():
    """关闭全局浏览器。"""
    global _browser
    if _browser:
        try:
            _browser.close()
        except Exception:
            pass
        _browser = None


# --- CloakBrowser 抓取（同步）---

def cloak_fetch(url, timeout=30):
    """用 CloakBrowser 抓取页面。返回 (text, html, cookies, ua, status, error)。"""
    try:
        browser = _get_browser()
        page = browser.new_page()
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            status = resp.status if resp else 0
            if not str(status).startswith("2"):
                return None, None, [], "", status, f"HTTP {status}"

            text = page.evaluate("document.body.innerText")
            html = page.content()

            # 提取 cookies 和 UA
            cookies = page.context.cookies()
            ua = page.evaluate("navigator.userAgent")

            return text, html, cookies, ua, status, None
        finally:
            page.close()
    except Exception as e:
        return None, None, [], "", 0, f"{type(e).__name__}: {e}"


# --- Scrapling 带 cookies 抓取 ---

def scrapling_fetch(url, cookies=None, ua=None, timeout=15):
    """用 Scrapling 抓取，可选传入 cookies 和 UA。返回 (text, status, error)。"""
    from scrapling.fetchers import Fetcher

    headers = {}
    if ua:
        headers["User-Agent"] = ua

    cookie_str = ""
    if cookies:
        # cookies 是 Playwright 格式: [{"name": ..., "value": ..., "domain": ...}, ...]
        # 转为 "name=value; name2=value2" 格式
        target_domain = _domain_of(url)
        relevant = [c for c in cookies if target_domain.endswith(c.get("domain", "").lstrip("."))]
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in relevant)

    if cookie_str:
        headers["Cookie"] = cookie_str

    try:
        kwargs = {"timeout": timeout, "retries": 1}
        if headers:
            kwargs["headers"] = headers

        page = Fetcher.get(url, **kwargs)
        status = getattr(page, "status", 0)
        if not str(status).startswith("2"):
            return None, status, f"HTTP {status}"
        text = page.get_all_text(separator=" ") if hasattr(page, "get_all_text") else page.text
        return text, status, None
    except Exception as e:
        return None, 0, f"{type(e).__name__}: {e}"


# --- 智能路由 ---

def smart_fetch(url, timeout=15):
    """智能抓取：根据域名路由表选择工具，CloakBrowser cookies 传递给 Scrapling。

    流程：
    1. 路由表有记录 → 按记录走
    2. 无记录 → 先试 Scrapling
       - 成功 → 记录 scrapling_ok
       - 失败 → CloakBrowser 兜底
         - 成功 → 拿 cookies → 记录 cloak_ok
         - 失败 → 记录 blocked
    3. 返回 (text, html, status, error, tool_used)
    """
    _load_routes()
    domain = _domain_of(url)
    route = _routes.get(domain, {})
    route_status = route.get("status")

    # 路由表命中：Scrapling 可用
    if route_status == ROUTE_SCRAPOK:
        text, status, error = scrapling_fetch(url, timeout=timeout)
        if error and status in (403, 429):
            # 路由过期，降级到 CloakBrowser
            _routes[domain]["status"] = ROUTE_CLOAKOK
            _save_routes()
            return _fallback_to_cloak(url, domain, timeout)
        return text, None, status, error, "scrapling"

    # 路由表命中：需要 CloakBrowser
    if route_status == ROUTE_CLOAKOK:
        saved_cookies = route.get("cookies", [])
        saved_ua = route.get("ua", "")
        text, status, error = scrapling_fetch(url, cookies=saved_cookies, ua=saved_ua, timeout=timeout)
        if not error:
            return text, None, status, None, "scrapling+cookies"
        # cookies 过期，重新用 CloakBrowser
        return _fallback_to_cloak(url, domain, timeout)

    # 路由表命中：两个都不行
    if route_status == ROUTE_BLOCKED:
        # 每 10 分钟重试一次
        updated = route.get("updated", "")
        if updated:
            try:
                t = datetime.fromisoformat(updated)
                if datetime.now() - t < timedelta(minutes=10):
                    return None, None, 0, "domain_blocked", "blocked"
            except Exception:
                pass
        # 重新试探
        return _try_scrapling_first(url, domain, timeout)

    # 未知域名：先试 Scrapling
    return _try_scrapling_first(url, domain, timeout)


def _try_scrapling_first(url, domain, timeout):
    """先 Scrapling，失败则 CloakBrowser 兜底 + cookie 回传。"""
    text, status, error = scrapling_fetch(url, timeout=timeout)
    if not error:
        _routes[domain] = {"status": ROUTE_SCRAPOK, "updated": _now_iso()}
        _save_routes()
        return text, None, status, None, "scrapling"

    # Scrapling 失败，CloakBrowser 兜底
    return _fallback_to_cloak(url, domain, timeout)


def _fallback_to_cloak(url, domain, timeout):
    """CloakBrowser 兜底 + cookies 回传给 Scrapling 重试。"""
    c_text, c_html, cookies, ua, c_status, c_error = cloak_fetch(url, timeout=timeout)

    if c_error:
        _routes[domain] = {"status": ROUTE_BLOCKED, "updated": _now_iso()}
        _save_routes()
        return None, None, c_status, c_error, "blocked"

    # 保存 cookies 和 UA 到路由表
    _routes[domain] = {
        "status": ROUTE_CLOAKOK,
        "cookies": cookies[:20],  # 最多保存 20 个
        "ua": ua,
        "updated": _now_iso(),
    }
    _save_routes()

    return c_text, c_html, c_status, None, "cloak"


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


# --- Google 搜索（始终用 CloakBrowser）---

def search_google(query, max_results=5):
    """用 CloakBrowser 执行 Google 搜索。

    始终用 CloakBrowser，不走 smart_fetch 的 Scrapling 路径。
    Google 会 429 封 Scrapling，CloakBrowser 可绕过。

    Google 结果 URL 格式有两种：
    1. 旧格式: /url?q=https://example.com&sa=...
    2. 新格式: https://example.com/?srsltid=... (直接 href)
    """
    from urllib.parse import quote_plus

    url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}&hl=en"
    text, html, cookies, ua, status, error = cloak_fetch(url, timeout=30)

    if error or not html:
        return []

    result_urls = []
    seen_domains = set()

    # 格式 1: /url?q= 重定向链接
    for match in re.finditer(r'href="(/url\?q=https?://[^"]+)"', html):
        real_url = match.group(1).split("/url?q=")[1].split("&")[0]
        parsed = urlparse(real_url)
        d = parsed.netloc.lower()
        if "google.com" not in d and "googleapis.com" not in d:
            result_urls.append(real_url)
            seen_domains.add(d)
            if len(result_urls) >= max_results:
                break

    if result_urls:
        return result_urls

    # 格式 2: 直接外部链接（带 srsltid 参数的有机结果）
    for match in re.finditer(r'href="(https?://[^"]+)"', html):
        raw = match.group(1).replace("&amp;", "&")
        parsed = urlparse(raw)
        d = parsed.netloc.lower()
        if d in ("google.com", "www.google.com", "googleapis.com", "gstatic.com",
                 "accounts.google.com", "support.google.com", "maps.google.com"):
            continue
        if d.endswith(".google.com") or d.endswith(".googleapis.com"):
            continue
            continue
        # 去掉 fragment 和 srsltid
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
        if d not in seen_domains:
            result_urls.append(clean)
            seen_domains.add(d)
            if len(result_urls) >= max_results:
                break

    return result_urls
