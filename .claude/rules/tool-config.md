---
paths:
  - "scripts/**"
---

# Tool Configuration Rules

## CloakBrowser + Scrapling 联动配置

**用于绕过 Google 429、Cloudflare 等反爬：**

```python
from scripts.kp_pipeline.cloak_fetcher import cloak_fetch, search_google, smart_fetch, close_browser

# Google 搜索（始终用 CloakBrowser，不走 Scrapling）
results = search_google("company name director", max_results=5)

# 智能抓取（Scrapling 优先，CloakBrowser 兜底 + cookie 传递）
text, html, status, error, tool = smart_fetch(url, timeout=15)

# 直接用 CloakBrowser（绕过 Scrapling 无法处理的站点）
text, html, cookies, ua, status, error = cloak_fetch(url, timeout=30)

# 用完关闭浏览器
close_browser()
```

**已知限制：**
- Cloudflare 挑战页即使 CloakBrowser 也返回 403
- LinkedIn 搜索页需要登录，无法绕过
- Scrapling TLS 错误的站点可用 CloakBrowser 兜底

**关键约束：**
- Google 搜索**必须**用 `search_google()` 或 `cloak_fetch()`，不能用 `smart_fetch()`（会被 429）
- CloakBrowser 使用同步 `launch()` API，不要用 `asyncio.run()` 或 `nest_asyncio`
- Scrapling 传 cookies/UA 用 `headers` 参数，不是 `extra_headers`

## KP Pipeline

Three-stage pipeline for key person discovery and enrichment.

```bash
python -m scripts.kp_pipeline.run_pipeline --limit 50 --stage all
python -m scripts.kp_pipeline.run_pipeline --stage 2 --limit 20
```

- **Stage 1 (KP 发现):** Extract KP candidates from web.
- **Stage 2 (直联富化):** Scrape sitemap + company pages → find email/phone.
- **Stage 3 (验证门控):** Score → auto-approve (≥85) / auto-reject (<30) / human review (30-85).

## Extraction Scripts

```bash
python scripts/extraction/build_form_kp_candidate_queue.py
python scripts/extraction/extract_public_contact_candidates.py \
  --input reports/queue.csv --skip 0 --limit 10 \
  --follow-links 3 --fetcher static --skip-existing
```

## Dashboard (线索补全台)

```bash
cd D:\TestProject-v3 && python -m http.server 8765
# Open: http://localhost:8765/dashboard/
```
