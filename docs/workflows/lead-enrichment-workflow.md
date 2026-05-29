<!-- DOC_META
lifecycle:  long-term
audience:   agent
write_when: 充实流程、步骤、规则变更时更新
read_when:  执行线索充实时读取
delete_when: 不删除
-->
# Lead Enrichment Workflow

<!-- CODEx_START: enrichment_definition -->
*Updated: 2026-05-08 15:41*

## Discovery vs Enrichment

Lead discovery finds possible customer companies.

Lead enrichment tries to find usable outreach contact information for each discovered company.

A company name and source link are not enough for outreach. The lead should be enriched before it is considered ready to contact.

Enrichment must distinguish between company-level contact channels and key contact person information. A company email is not the same as a decision-maker's direct email, and a company LinkedIn page is not the same as a personal LinkedIn profile.

<!-- CODEx_END: enrichment_definition -->

<!-- CODEx_START: current_kp_priority -->
*Updated: 2026-05-09 17:25*

## Current KP Priority

For the current Australia workflow, key-person discovery is more important than collecting more general forms.

Prioritize contacts for restaurant and hotel final customers. The most valuable contact is a relevant key person with an email address, preferably with a phone number as well.

Acceptable key-person candidate sources include official company pages, official PDFs, public The Org pages, and publicly visible LinkedIn/search-result evidence. If the source is not an official company source, save it only as Low or Medium confidence and document the uncertainty in notes.

LinkedIn is useful even when the page content cannot be opened or should not be automated. A public LinkedIn profile URL or company LinkedIn URL may be saved to the relevant CSV as Low or Medium confidence candidate evidence when the source and uncertainty are documented. A search-result URL alone should remain in reports or notes, not a verified contact field. Do not mark a LinkedIn URL as high-confidence direct contact only because a URL exists.

2026-05-12 public-access test: unauthenticated scripted HTTP requests to LinkedIn were blocked with 999/connection errors. Unauthenticated Playwright browser access could open a company page, but tested personal profile URLs returned LinkedIn 404 pages. Practical rule: collect LinkedIn profile URLs and search URLs for manual review, but do not rely on local unauthenticated automation to verify personal profile contents.

General company email, company phone, and contact forms are secondary contact paths. They can support a lead, but they should not be treated as equal to a direct key-person email or phone.

<!-- CODEx_END: current_kp_priority -->

<!-- CODEx_START: australia_toolization_success_rules -->
*Updated: 2026-05-09 17:35*

## Australia Toolization Success Rules

The next milestone is to turn the Australia restaurant/hotel KP workflow into a successful reusable tool.

A method is not ready to become a tool just because it finds many company websites or contact forms. It is ready only if it can repeatedly produce useful, reviewable Australia restaurant/hotel contacts.

Minimum success targets before toolization:

- Test at least 80 Australia restaurant/hotel final-customer candidates.
- Keep duplicate rate below 25%.
- Keep official source coverage high, with source links recorded for every saved lead or contact.
- Reach at least 60% `Ready to Contact` for relevant candidates.
- Reach at least 25% key-person identification.
- Reach at least 8% to 10% direct key-person contact, preferably email and then phone.
- Keep public-source confidence clear: High for official company evidence, Medium or Low for public third-party evidence.
- Produce a repeatable query set, scoring rule, CSV update pattern, and batch report format.

If these targets are not met, continue testing/refining Australia queries before building broader automation.

<!-- CODEx_END: australia_toolization_success_rules -->

<!-- CODEx_START: contact_fields_to_enrich -->
*Updated: 2026-05-08 15:41*

## Contact Fields to Enrich

For each lead, try to find:

Company-level contact fields:

- `company_email`
- `company_phone`
- `company_linkedin_url`
- `company_instagram_url`
- `company_contact_page`
- `company_contact_form_url`

Key contact person fields:

- `key_contact_name`
- `key_contact_job_title`
- `key_contact_email`
- `key_contact_phone`
- `key_contact_linkedin_url`
- `key_contact_source_link`
- `key_contact_confidence`

Do not fabricate missing contact data. If a field cannot be found, leave it blank and explain the search in `enrichment_notes`.

Search company contacts first when the lead has no usable contact method. Search decision-makers next when the company has high customer strength or when general company contact is not enough for good outreach.

<!-- CODEx_END: contact_fields_to_enrich -->

<!-- CODEx_START: enrichment_search_patterns -->
*Updated: 2026-05-08 15:41*

## Enrichment Search Patterns

Use up to 5 to 8 reasonable source checks per lead.

Useful patterns:

- `[company name] official website`
- `[company name] contact`
- `[company name] email`
- `[company name] phone`
- `[company name] LinkedIn`
- `[company name] procurement`
- `[company name] F&B manager`
- `site:[company domain] contact`
- `site:[company domain] email`
- `site:[company domain] team`
- `site:[company domain] about`

Check up to 3 to 5 relevant public sources per lead.

For form/KP focused testing, evaluate at least 20 candidate companies or official forms before judging the keyword/tool quality unless the results are clearly unrelated, duplicate-heavy, or account-risky.

Useful Google search operators for KP finding:

- `site:[company domain] team OR people OR leadership`
- `site:[company domain] director OR founder OR partner`
- `site:[company domain] procurement OR supplier OR "trade account"`
- `site:[company domain] filetype:pdf director`
- `"company name" "project manager" OR "operations manager"`
- `"company name" "food and beverage" OR "F&B"`
- `site:theorg.com "company name" CEO OR Director`
- `site:linkedin.com/in "company name" director OR operations`
- `site:linkedin.com/in "company name" owner OR founder OR "general manager"`
- `site:linkedin.com/in "company name" "food and beverage" OR F&B OR procurement`

<!-- CODEx_END: enrichment_search_patterns -->

<!-- CODEx_START: company_page_scraping_strategy -->
*Updated: 2026-05-22*

## 公司页面抓取策略

当 Google 搜索 KP 姓名效率低下时（71 人搜索仅 1 个有效邮箱），直接抓取公司网站的 team/about/contact 页面更有效。

**路径优先级：**
1. `/about` 或 `/about-us` — 公司介绍，有时含团队信息
2. `/team` 或 `/our-team` — 团队页面，最可能有个人邮箱/手机
3. `/contact` 或 `/contact-us` — 联系页面，可能有个人联系方式
4. `/people` 或 `/staff` 或 `/leadership` — 备选路径

**工具选择：**
- Scrapling 优先（快速，覆盖大多数站点）
- Scrapling TLS 错误或 403 时降级到 CloakBrowser（如 Fink Group）
- `smart_fetch()` 自动处理降级和 cookie 传递

**有效性验证（2026-05-22 实测）：**
- 25 家公司页面抓取：发现 15 个联系方式（8 个有效人名邮箱 + 7 个手机号）
- 成功率最高的路径：`/contact` > `/about` > `/team`
- 大型餐饮集团（Merivale/Australian Venue Co/Oscars Group）官网不公开决策者直联
- 小型公司（BIM Stainless/Fast Fitouts/Blank Creatives）更容易找到个人联系方式

**代码示例：**
```python
from scripts.kp_pipeline.cloak_fetcher import smart_fetch
import re

EMAIL_RE = re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.I)
PHONE_RE = re.compile(r'04\d{2}\s?\d{3}\s?\d{3}')

for path in ['/about', '/team', '/contact', '/contact-us']:
    url = f'https://{domain}{path}'
    text, html, status, error, tool = smart_fetch(url, timeout=15)
    if error or not text:
        continue
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    # 过滤通用邮箱后保存
```

<!-- CODEx_END: company_page_scraping_strategy -->

<!-- CODEx_START: kp_acquisition_methods -->
*Updated: 2026-05-12 18:20*

## KP Acquisition Methods

Beyond manual LinkedIn checking, the project can improve KP discovery with these routes:

- Search-result automation: use Google Programmable Search / Custom Search JSON API for repeatable public queries such as `site:company.com director`, `site:company.com leadership`, `site:company.com filetype:pdf director`, and broader web queries combining company name with founder, operations, procurement, F&B, or general manager. This needs a Google API key and Programmable Search Engine ID; it has a small free daily quota and paid overage.
- Official-site deep extraction: extend the current Scrapling helper to prioritize `/about`, `/team`, `/people`, `/leadership`, `/media`, `/news`, `/press`, `/privacy`, PDFs, and venue pages, then parse person names near role words.
- PDF/news extraction: fetch official PDFs and press/news pages, then extract names, titles, emails, and phone numbers from text. Save results as `contacts.csv` candidates with source links and confidence notes.
- Email pattern inference: when a company has a known email domain and a verified KP name, generate likely patterns such as first.last, first, or first initial + last, then save only as Low confidence unless verified by source or email verification.
- Email discovery/verification API: if approved, use a service such as Hunter for domain search, email finder, and verifier workflows. This can help when the project already has a person name and company domain, but it uses API keys/credits and should be logged as a paid/account-based capability if enabled.
- Public profile/entity sources: use public The Org pages, official bios, Google snippets, public directories, and company press releases as candidate evidence. Save uncertainty in `contacts.csv`.

Do not automate LinkedIn login, scraping, messaging, connection export, or profile browsing without explicit approval. LinkedIn's own help pages describe crawlers, bots, scraping, and automated activity as prohibited. For this project, LinkedIn should remain a manual review/source-link route unless a separate approved and compliant access method is defined.

Current targeted KP search-task tool:

- `scripts/extraction/generate_kp_search_tasks.py` generates direct KP search tasks from existing lead rows.
- Default scope is Australia restaurant/hotel final-customer candidates with official websites.
- It prioritizes known KP names first, then official team/leadership, owner/director, operations/F&B, procurement, official PDF, broader web, and LinkedIn manual-review entry-point queries.
- Output goes to `reports/kp-search-tasks-*.csv` plus a Markdown summary. The search-task generator itself does not update `data/leads.csv` or `data/contacts.csv`; evidence found from those tasks may be registered directly when source, confidence, status, and uncertainty notes are present.
- Save KP results to `contacts.csv` when a person name or person-specific URL/email/phone has a source link, confidence, status, and uncertainty note. Pre-save human review is not required; review again before actual outreach.

Recommended next tooling step:

- Optional later step: add a Google Custom Search JSON API runner that consumes those tasks and writes compact result candidates to `reports/` or directly registers traceable pending-verification rows when source, confidence, status, and uncertainty notes are present.
- Optional paid/account step: add Hunter-style email finder/verifier integration only after the user approves API-key use, credit cost, rate limit, and output fields.

<!-- CODEx_END: kp_acquisition_methods -->

<!-- CODEx_START: local_extraction_helper_policy -->
*Updated: 2026-05-12 11:35*

## Local Extraction Helper Policy

Local extraction helpers may be used to reduce manual review time and token usage when they operate only on approved public sources and produce traceable candidate evidence.

For the current Australia form/KP workflow, a helper may extract from official company pages:

- visible email addresses
- visible phone numbers
- contact page and form URLs
- team/about/people page links
- visible LinkedIn profile/company URLs as manual review entry points
- visible key-person names and job titles
- short source-context snippets

The helper should output candidate rows for CSV registration. Company-level routes can be saved to `data/leads.csv` when the source is public and documented. KP candidates can be saved to `data/contacts.csv` as Low or Medium confidence pending-verification rows when they include a person name or a person-specific URL/email/phone plus a source link. Pre-save human review is not required for traceable public evidence; review again during outreach preparation. It should not directly mark a lead as complete unless the saved field has a source link, confidence value, and note.

Current registration rule clarification:

- Machine-generated public-source candidates may be written directly to `data/leads.csv` or `data/contacts.csv` when they include a reviewable source, confidence/status, and uncertainty notes.
- The required human exclusion/review checkpoint is before actual outreach, not before candidate CSV registration.
- Do not describe the current workflow as requiring manual pre-save verification. Historical reports that say "review before saving" describe older or narrower runs and do not override this rule.
- Search snippets, pure role words, fetch-status rows, and generic search-result URLs still should not become contact records by themselves; they need a person/company-specific source or usable route to be saved.

Scrapling is an acceptable candidate library for a limited test. Controlled use may include dynamic browser fetching, stealth browser settings, proxies, authenticated sessions, paid-source access, CAPTCHA handling, and platform-account automation when the user has approved that mode, has authorization to access the data/source, and the run remains limited by domain, batch size, rate limit, cooldown, account-safety stop conditions, and output-review boundaries.

For authenticated or platform-account runs, prioritize avoiding bans:

- use small batches first
- keep low concurrency
- apply cooldowns and human-like pacing
- stop on challenges, forced verification, account warnings, temporary blocks, or rate-limit errors
- save candidate evidence with clear confidence/status instead of pretending it is verified

Scrapling or similar tools should run only with user-authorized access. Do not use stolen cookies, unauthorized credential sharing, credential theft, unauthorized private/hidden data, or unpaid access-control bypass. Within authorized access, the main operating goal is preventing bans through small batches, low concurrency, cooldowns, and immediate stops on account-risk signals.

Recommended first test:

- Input: 5 to 10 URLs from `reports/au-form-kp-candidate-queue-20260512-continue.csv`.
- Output: candidate CSV plus traceable writes to `data/leads.csv` or `data/contacts.csv` when source, confidence, status, and uncertainty notes are present.
- Candidate fields: `lead_id`, `company_name`, `source_url`, `candidate_type`, `candidate_value`, `candidate_context`, `confidence_suggestion`, and `save_recommendation`.
- LinkedIn candidate rows should remain clearly labeled. The helper may output or save `key_person_linkedin_url` and `company_linkedin_url` with Low/Medium confidence and notes, but should not save `linkedin_search_url` as a contact field or open, scrape, message, export, or automate LinkedIn account actions without separate explicit approval.
- Expected benefit: reduce token use by passing compact candidate rows to CSV registration and later outreach review instead of full HTML or long page text.

Environment note from 2026-05-12 evaluation:

- Local Python: `3.14.4`.
- Scrapling installed/tested in project-local `.venv`: `scrapling 0.4.8`.
- Additional runtime dependencies installed during testing: `curl_cffi`, `playwright`, `browserforge`, `patchright`, and `msgspec`.
- Playwright Chromium browser installed in project-local `.ms-playwright` for dynamic/stealth testing.
- Static `Fetcher`, browser `DynamicFetcher`, and `StealthyFetcher` were verified against `https://example.com`.
- A 5-URL static extraction test generated `reports/au-public-contact-candidates-20260512-scrapling-test.*`.
- Follow-link extraction was tested on 3 queued companies and generated 62 candidate rows in `reports/au-public-contact-candidates-20260512-followlinks-test.*`.
- The extraction script now supports `--fetcher static|dynamic|stealth`; all three modes were tested on a queued company URL.

CloakBrowser + Scrapling deep integration (2026-05-20, fixed 2026-05-20 18:20):

- `cloakbrowser>=0.3.29` installed. Stealth Chromium with source-level fingerprint patches (30/30 bot detection tests passed).
- Uses **synchronous** `cloakbrowser.launch()` API (not `launch_async`) to avoid asyncio event loop lifecycle issues.
- `scripts/kp_pipeline/cloak_fetcher.py` — smart fetcher with:
  - **Domain routing memory** — `data/fetch_routes.json` remembers which tool works per domain
  - **Cookie handoff** — CloakBrowser fetches first → captures cookies/UA → passes to Scrapling via `headers` parameter (not `extra_headers`)
  - **Smart fallback** — Scrapling fails (403/429/TLS) → CloakBrowser → cookies back to Scrapling
  - Route expiry: 10 minutes (re-probes blocked domains periodically)
- Usage in `stage2_enrich.py`:
  - Google search → **always CloakBrowser directly** (calls `cloak_fetch()`, not `smart_fetch()`)
  - Company pages → Scrapling first, CloakBrowser fallback with cookie handoff
- Google search result extraction: supports both `/url?q=` (legacy) and direct href + `srsltid` (current) formats. Filters all `*.google.com` and `*.googleapis.com` domains.
- Config: `config/kp_pipeline.json` `fetch_strategy` section
- Known limits: Cloudflare challenge pages (e.g., Swillhouse) still return 403 even with CloakBrowser.
- **Do NOT use `nest_asyncio` or `asyncio.run()` with CloakBrowser** — always use sync API.

<!-- CODEx_END: local_extraction_helper_policy -->

<!-- CODEx_START: enrichment_stopping_rules -->
*Updated: 2026-05-08 12:05*

## Stopping Rules

Stop enrichment for a lead when:

- At least one usable contact method is found and the lead is sufficiently clear for review.
- 5 to 8 reasonable public-source checks have been attempted.
- 3 to 5 relevant sources have been checked.
- The remaining useful sources require account access that has not been approved or would create unacceptable account risk.

Do not search endlessly. If contact information still cannot be found, mark the lead clearly and move to the next one.

<!-- CODEx_END: enrichment_stopping_rules -->

<!-- CODEx_START: ready_vs_research_rules -->
*Updated: 2026-05-09 18:06*

## Ready to Contact vs Need More Research

Mark `Ready to Contact` only if at least one usable contact method is found:

- `company_email`
- `company_phone`
- `company_contact_page`
- `company_contact_form_url`
- `company_linkedin_url`
- `company_instagram_url`
- `key_contact_email`
- `key_contact_phone`
- `key_contact_linkedin_url`

If no usable contact method is found:

- Keep `follow_up_status` as `Need More Research`.
- Set `outreach_difficulty_level` to `Hard`.
- Set `estimated_follow_up_probability` to `Low` or `Unknown`.
- Set `contact_research_status` to `Manual Review Needed`.
- Set `contact_completeness_score` to `None` or `Low`.

If only a general email, phone, or contact form is found:

- `contact_completeness_score` is usually `Medium`.
- `follow_up_status` can be `Ready to Contact` if the company is relevant.
- Treat this as a secondary outreach path, especially for larger restaurant or hotel groups where general inboxes may have low reply probability.
- Do not treat a general company route as equal to a direct key-person email or phone.

If a direct decision-maker, job title, direct email, or LinkedIn profile is found:

- `contact_completeness_score` can be `High`.
- `outreach_difficulty_level` can be `Easy` or `Medium`.
- For the current workflow, prefer key-person email first, key-person phone second, and company-level contact paths after that.

`Priority Outreach` rules for the current Australia workflow:

- Highest priority: Australia restaurant or hotel final customer with a relevant key person and key-person email.
- Strong priority: Australia restaurant or hotel final customer with a relevant key person and direct phone.
- Medium priority: Australia restaurant or hotel final customer with department email, procurement email, events/F&B email, company phone, or official form.
- Lower priority: supplier/partner companies or company-only contacts unless the user explicitly asks for those directions.

`contact_data_level` rules:

- `No Contact Found`: No usable company or person contact method.
- `Company Contact Only`: Company contact exists, but no key person is identified.
- `Key Person Identified`: Key person name or title exists, but no direct personal contact method exists.
- `Direct Key Contact Found`: Key person exists and has direct email, direct phone, or personal LinkedIn.

If `next_action` says `Find official contact`, the enrichment process should continue later. Do not treat that lead as complete.

<!-- CODEx_END: ready_vs_research_rules -->

<!-- CODEx_START: missing_contact_handling -->
*Updated: 2026-05-08 12:05*

## Handling Missing Contact Information

When no contact information can be found:

- Leave missing fields blank.
- Fill `enrichment_attempts`.
- Explain searched sources in `enrichment_notes`.
- Use `Manual Review Needed`.
- Do not invent names, titles, emails, phone numbers, or LinkedIn URLs.

For news-only leads:

- Search for the official website first.
- Search for official social pages if the website cannot be found.
- Keep `verification_status` as `News Only` if no official source is found.

<!-- CODEx_END: missing_contact_handling -->
