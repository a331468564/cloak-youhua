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
- CloakBrowser 走独立代理端口 7898，不影响主 Clash Verge Rev（7897）
"""
import json
import random
import re
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

try:
    from scripts.kp_pipeline.proxy_manager import get_manager
except ImportError:
    from kp_pipeline.proxy_manager import get_manager

_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_ROUTES_FILE = _DATA_DIR / "fetch_routes.json"

# 路由状态
ROUTE_SCRAPOK = "scrapling_ok"       # Scrapling 可用
ROUTE_CLOAKOK = "cloak_ok"           # 需要 CloakBrowser
ROUTE_BLOCKED = "blocked"            # 两个都不行

_browser = None
_routes = {}  # {domain: {"status": str, "cookies": [...], "ua": str, "updated": str}}

# Thread-local storage for per-worker state (parallel search)
_tls = threading.local()
_browser_lock = threading.Lock()  # 共享浏览器锁（并行搜索时串行化浏览器访问）


def _get_tls(key, default=None):
    """获取 thread-local 值，未设置时返回 default。"""
    return getattr(_tls, key, default)


def _set_tls(key, value):
    """设置 thread-local 值。"""
    setattr(_tls, key, value)


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

_PROXY_URL = "http://127.0.0.1:7898"  # 独立 mihomo 实例，非主 Clash (7897)
_last_search_time = 0.0  # 全局搜索时间戳（并行 worker 共享）

# --- Humanize 配置 ---

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0",
]

_RESOLUTIONS = [
    {"width": 1920, "height": 1080},
    {"width": 2560, "height": 1440},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
]

_LOCALE_PROFILES = [
    {"locale": "en-AU", "timezone": "Australia/Sydney"},
    {"locale": "en-US", "timezone": "America/New_York"},
    {"locale": "zh-CN", "timezone": "Asia/Shanghai"},
]


def _detect_proxy_ip():
    """检测当前代理出口 IP（走本地代理）。"""
    import urllib.request
    for url in ["http://icanhazip.com", "http://api.ipify.org", "https://httpbin.org/ip"]:
        try:
            proxy_handler = urllib.request.ProxyHandler({"http": _PROXY_URL, "https": _PROXY_URL})
            opener = urllib.request.build_opener(proxy_handler)
            req = urllib.request.Request(url)
            with opener.open(req, timeout=10) as resp:
                body = resp.read().decode().strip()
                if body.startswith("{"):
                    return json.loads(body).get("origin", "")
                return body
        except Exception:
            continue
    return ""


def _pick_humanize_settings():
    """随机选择一组 humanize 设置（UA/分辨率/语言）。"""
    ua = random.choice(_UA_POOL)
    resolution = random.choice(_RESOLUTIONS)
    profile = random.choice(_LOCALE_PROFILES)
    return {
        "user_agent": ua,
        "viewport": resolution,
        "locale": profile["locale"],
        "timezone": profile["timezone"],
    }


# --- 自适应配置 ---

# FAST (default): 无间隔，无 humanize，瓶颈为 Google 响应时间（~3.4s）
# SAFE (fallback): 间隔 2-4s，有 humanize，429 恢复时使用
_CONFIGS = {
    "FAST": {"interval": (0, 0), "humanize": False},
    "SAFE": {"interval": (2.0, 4.0), "humanize": True},
}
_FAIL_THRESHOLD = 3     # 连续 3 次失败 → 切到 SAFE
_RECOVER_THRESHOLD = 20  # 连续 20 次成功 → 切回 FAST


def _get_config():
    """获取当前自适应配置（per-thread）。"""
    cfg_name = _get_tls("config", "FAST")
    return _CONFIGS[cfg_name]


def _record_result(ok: bool):
    """记录搜索结果，自动切换配置（per-thread）。"""
    cfg_name = _get_tls("config", "FAST")
    fail = _get_tls("consecutive_fail", 0)
    ok_count = _get_tls("consecutive_ok", 0)

    if ok:
        fail = 0
        ok_count += 1
        if cfg_name == "SAFE" and ok_count >= _RECOVER_THRESHOLD:
            cfg_name = "FAST"
            ok_count = 0
            print(f"[adaptive] Recovered → FAST (no interval)")
    else:
        ok_count = 0
        fail += 1
        if cfg_name == "FAST" and fail >= _FAIL_THRESHOLD:
            cfg_name = "SAFE"
            fail = 0
            print(f"[adaptive] {_FAIL_THRESHOLD} consecutive issues → SAFE (2-4s interval)")

    _set_tls("config", cfg_name)
    _set_tls("consecutive_fail", fail)
    _set_tls("consecutive_ok", ok_count)


def _enforce_search_interval():
    """根据自适应配置执行搜索间隔。FAST 模式无间隔。"""
    cfg = _get_config()
    min_s, max_s = cfg["interval"]
    if min_s <= 0:
        return  # FAST 模式，无间隔
    time.sleep(random.uniform(min_s, max_s))


def _get_browser(humanize=False):
    """获取 CloakBrowser 实例（per-thread），自动检测代理 IP 变化并重建。"""
    browser = _get_tls("browser")
    current_ip = _get_tls("current_proxy_ip")

    new_ip = _detect_proxy_ip()
    if new_ip and new_ip != current_ip:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
            browser = None
        _set_tls("current_proxy_ip", new_ip)

    if browser is None:
        from cloakbrowser import launch
        kwargs = {
            "headless": True,
            "proxy": {"server": _PROXY_URL},
        }
        if humanize:
            settings = _pick_humanize_settings()
            kwargs["humanize"] = True
            kwargs["human_preset"] = "careful"
            kwargs["locale"] = settings["locale"]
            kwargs["timezone"] = settings["timezone"]
        browser = launch(**kwargs)
        _set_tls("browser", browser)

    return browser


def close_browser():
    """关闭当前线程的浏览器。"""
    browser = _get_tls("browser")
    if browser:
        try:
            browser.close()
        except Exception:
            pass
        _set_tls("browser", None)


# --- CloakBrowser 抓取（同步）---

def cloak_fetch(url, timeout=30, humanize=False):
    """用 CloakBrowser 抓取页面。返回 (text, html, cookies, ua, status, error)。"""
    try:
        browser = _get_browser(humanize=humanize)
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


# --- Google 搜索（始终用 CloakBrowser，走独立代理 7898）---

def search_google_single(query, max_results=5, max_retries=3):
    """单次 Google 搜索，自适应配置。

    默认 FAST 模式（无间隔，无 humanize）。
    连续 3 次失败自动切 SAFE 模式（2-4s 间隔，有 humanize）。
    连续 20 次成功自动切回 FAST 模式。
    """
    from urllib.parse import quote_plus

    pm = get_manager()
    cfg = _get_config()

    for attempt in range(max_retries):
        _enforce_search_interval()

        url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}&hl=en"
        text, html, cookies, ua, status, error = cloak_fetch(url, timeout=30, humanize=cfg["humanize"])

        if status == 429 or (error and "429" in str(error)):
            print(f"[search_google_single] 429: {query}")
            _record_result(False)
            if pm.handle_429(browser_close_fn=close_browser):
                continue
            else:
                break

        if status == 403:
            print(f"[search_google_single] 403: {query}")
            _record_result(False)
            if pm.handle_429(browser_close_fn=close_browser):
                continue
            else:
                break

        if error or not html:
            _record_result(False)
            return []

        pm.reset_429_counter()

        result_urls = _extract_google_urls(html, max_results)
        _record_result(bool(result_urls))
        return result_urls

    _record_result(False)
    return []


def search_google(query, max_results=5, max_retries=3):
    """单次 Google 搜索（向后兼容）。

    内部调用 search_google_single。
    """
    return search_google_single(query, max_results, max_retries)


def search_google_batch(queries: list[str], max_results=5, workers=3) -> dict[str, list[str]]:
    """批量 Google 搜索（串行执行）。

    默认 FAST 模式（无间隔，无 humanize），瓶颈为 Google 响应时间（~3.4s）。
    200 次测试：100% 成功率，0 429，平均 3.4s/次，1.7x 提速。

    Args:
        queries: 搜索查询列表
        max_results: 每次搜索最大结果数
        workers: 保留参数（当前串行执行）

    Returns:
        {query: [urls]} 字典
    """
    results = {}
    start = time.time()

    for query in queries:
        urls = search_google_single(query, max_results)
        results[query] = urls

    elapsed = time.time() - start
    ok = sum(1 for v in results.values() if v)
    print(f"[batch] {ok}/{len(queries)} OK in {elapsed:.1f}s ({elapsed/60:.1f}min)")

    return results


def _simulate_click_first_result(html):
    """30% 概率访问第一个搜索结果，模拟用户点击行为。"""
    # 提取第一个外部链接
    for match in re.finditer(r'href="(/url\?q=https?://[^"]+)"', html):
        real_url = match.group(1).split("/url?q=")[1].split("&")[0]
        parsed = urlparse(real_url)
        d = parsed.netloc.lower()
        if "google.com" not in d and "googleapis.com" not in d:
            try:
                cloak_fetch(real_url, timeout=15, humanize=True)
                time.sleep(random.uniform(3, 5))  # 模拟阅读
            except Exception:
                pass
            break


def _extract_google_urls(html, max_results):
    """从 Google 搜索结果 HTML 中提取外部 URL。"""
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
        # Skip all Google domains
        if any(d == g or d.endswith("." + g) for g in (
            "google.com", "google.co.jp", "google.com.au", "googleapis.com",
            "gstatic.com", "google.co.uk", "google.de", "google.fr",
        )):
            continue
        if "google" in d and (d.endswith(".google.com") or "google." in d):
            continue
        # 去掉 fragment 和 srsltid
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
        if d not in seen_domains:
            result_urls.append(clean)
            seen_domains.add(d)
            if len(result_urls) >= max_results:
                break

    return result_urls
