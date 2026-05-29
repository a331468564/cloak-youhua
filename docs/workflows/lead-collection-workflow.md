<!-- DOC_META
lifecycle:  long-term
audience:   agent
write_when: 采集流程、步骤、规则变更时更新
read_when:  执行线索采集时读取
delete_when: 不删除
-->
# Lead Collection Workflow

<!-- CODEx_START: lead_discovery_workflow -->
*Updated: 2026-05-08 12:05*

## Lead Discovery Workflow

Lead discovery means finding possible customer companies. It does not mean the lead is ready for outreach.

For each discovered lead, record:

- Company name
- Website, if available
- Country
- City or region
- Industry type
- Customer type
- Source link
- Project signal
- Notes

A discovered lead is valid when it appears relevant to Ron Group and has at least a public source that explains why it may be useful.

<!-- CODEx_END: lead_discovery_workflow -->

<!-- CODEx_START: current_collection_priority -->
*Updated: 2026-05-09 17:25*

## Current Collection Priority

For the current Australia workflow, prioritize restaurant and hotel final customers first.

Best-fit first-stage targets:

- Restaurant groups
- Multi-location restaurants
- Hotel groups
- Hotel F&B teams or hotel dining concepts
- Hospitality groups operating restaurants, bars, venues, or hotel F&B spaces

Fit-out, design, procurement, FF&E, OS&E, and commercial kitchen companies remain useful, but they are secondary unless the task explicitly asks for supplier or partner leads.

When choosing between two possible leads, prefer the company with stronger key-person potential over the company that only has a general contact form.

<!-- CODEx_END: current_collection_priority -->

<!-- CODEx_START: australia_first_collection_rule -->
*Updated: 2026-05-09 17:35*

## Australia-First Collection Rule

Until the Australia workflow is proven, do not start broad collection in other countries unless the user explicitly asks.

For new collection rounds, focus on Australia restaurant and hotel final customers with strong KP potential.

Recommended AU-first collection order:

1. Restaurant groups and multi-location restaurants.
2. Hotel groups and hotel F&B operators.
3. Hospitality groups with restaurants, bars, venues, or hotel dining concepts.
4. New opening, renovation, or expansion signals for Australia restaurants and hotels.

Do not treat general company forms as the main success metric. A lead is more valuable when the workflow can identify a relevant owner, founder, director, operations leader, F&B leader, procurement buyer, or project decision-maker.

<!-- CODEx_END: australia_first_collection_rule -->

<!-- CODEx_START: keyword_strategy -->
*Updated: 2026-05-08 18:11*

## Search Engine Keyword Strategy

Use `data/search_keywords.csv` as the starting keyword list.

Useful keyword patterns:

- `restaurant owner [city]`
- `new restaurant opening [city]`
- `restaurant group [country]`
- `multi-location restaurant company [city]`
- `hotel procurement manager [city]`
- `hotel purchasing manager [city]`
- `restaurant fit-out company [city]`
- `restaurant renovation contractor [city]`
- `restaurant design company [city]`
- `hospitality interior design [country]`
- `hospitality project management [city]`
- `hotel project developer [country]`

Search one customer type and one location at a time so the results remain easy to review.

Keyword intent types:

- `Discovery`: Find relevant companies.
- `Contact Finding`: Find company-level contact paths.
- `Decision Maker Finding`: Find owners, procurement managers, F&B managers, operations managers, project managers, or general managers.
- `Supplier / Partner Finding`: Find design firms, fit-out companies, procurement companies, and hospitality project partners.
- `Project Signal Finding`: Find new openings, renovations, expansions, and project signals.

Keyword status values:

- `New`: Not tested yet.
- `Testing`: Small batch test is in progress or recently completed.
- `Scale`: Performs well and can be used for larger batches.
- `Refine`: Relevant but too broad, noisy, duplicate-heavy, or weak for contact finding.
- `Pause`: Temporarily blocked due to cooldown, manual review, or quality concerns.
- `Retired`: Poor long-term performance; do not use unless manually reactivated.

Keyword quality should use two scores:

- `discovery_quality_score`: How well the keyword finds relevant companies.
- `contactability_score`: How well the keyword finds usable contact paths or key contacts.

<!-- CODEx_END: keyword_strategy -->

<!-- CODEx_START: keyword_control_and_batch_rules -->
*Updated: 2026-05-08 18:11*

## Keyword Control and Batch Rules

Use `data/search_keywords.csv` to control whether a keyword can be used.

Before running a keyword, check:

- `keyword_status`
- `used_recently`
- `last_used_at`
- `next_allowed_at`
- `cooldown_days`
- `blocked_reason`
- `manual_review_required`

Do not run a keyword if:

- `used_recently` is `Yes`
- Current date is before `next_allowed_at`
- `manual_review_required` is `Yes`
- `blocked_reason` is not empty
- `keyword_status` is `Pause` or `Retired`

Reasonable cooldowns:

- Discovery: 14 days
- Contact Finding: 14 to 30 days
- Decision Maker Finding: 30 days
- Supplier / Partner Finding: 14 days
- Project Signal Finding: 7 days

Batch size rules:

- New keyword test: 10 to 20 leads
- Form/KP focused test: 20 company form or key-person candidates before judging the method
- Australia toolization test: at least 80 Australia candidates across several repeatable keyword/query patterns before treating the method as stable
- Good keyword scaling: 30 to 50 leads
- Early total batch size: 50 to 100 leads

Stop collecting for a keyword when:

- Target count is reached
- Results become unrelated
- Duplicate ratio becomes too high
- News-only ratio becomes too high
- No-contact ratio becomes too high
- Manual review is required

Each collection run should be recorded in `data/keyword_runs.csv` with `batch_id`, `run_id`, `keyword_id`, `keyword_source_query`, and `collection_round`.

<!-- CODEx_END: keyword_control_and_batch_rules -->

<!-- CODEx_START: acceptable_sources -->
*Updated: 2026-05-12 11:35*

## Source and Tool Access Policy

Default acceptable sources:

- Search engine results
- Official company websites
- Official contact pages
- Official service or portfolio pages
- Public news articles
- Public business directories
- Public social media pages that do not require login
- Public LinkedIn company pages when visible without login

Additional tool access is allowed when it is reviewable, account-safe, and appropriate for the platform:

- Free/open-source query builders and enrichment helpers that operate on search results, official pages, and CSV files.
- Official APIs or platform-approved integrations when available.
- User-authorized accounts only after account-risk review and explicit approval.
- Public org-chart or business databases such as The Org when records are cross-checked or marked with confidence.
- Manual LinkedIn or Sales Navigator review for KP verification.
- Controlled high-capability public-page extraction tools, including dynamic browsers, stealth browser settings, and proxies, when the user explicitly approves the mode and the run is limited by domain, batch size, rate, and output registration rules.
- Controlled authenticated or paid-source extraction when the user explicitly provides or authorizes the account/tool access and defines anti-ban limits.

Controlled high-capability mode rules:

- Use it to improve access reliability and reduce manual/token cost, not to obtain data the user is not authorized to access.
- Set clear scope before running: target domains or URLs, maximum pages, rate limit, output file, and stop conditions.
- For authenticated, paid, or platform-account access, set account owner, allowed actions, daily/page limits, cooldown, concurrency, proxy/browser mode, and ban-risk stop conditions before running.
- Prefer official company domains first; use third-party public directories only as Low or Medium confidence unless independently verified.
- Save extracted public evidence with source, confidence, status, and notes. Company routes and KP candidates may be written directly to `data/leads.csv` or `data/contacts.csv` as pending-verification records; human review can happen during outreach preparation. Do not bulk-write unsourced, status-only, or unclear extracted data.
- Stop if the target site or account shows ban-risk signals such as repeated challenges, temporary blocks, forced verification, unusual-activity warnings, account locks, or rate-limit errors.

Still not allowed unless the user gives a separate explicit approval after risk review:

- Automated LinkedIn browsing, connection, messaging, or profile export from a user-authorized account.
- CAPTCHA handling, paid-source access, login-only access, or platform-account automation.
- Treating black-box enrichment data as high confidence without a public source link.

Authorization boundary:

- Stolen cookies, credential sharing without authorization, credential theft, or accessing hidden/private data that the user is not authorized to access.
- Bypassing payment or access controls for content/tools the user has not paid for or been granted access to.

Operational priority:

- Within user-authorized access, prioritize preventing bans through low concurrency, conservative pacing, cooldowns, small batches, and immediate stop on account-risk signals.

The practical rule is: tools may increase coverage, but every saved lead/contact still needs a traceable source, confidence level, and reviewable note.

<!-- CODEx_END: acceptable_sources -->

<!-- CODEx_START: source_handling_rules -->
*Updated: 2026-05-08 12:05*

## Source Handling Rules

Official websites:

- Prefer official websites over third-party summaries.
- Use official contact pages for verification when available.

News articles:

- Use news articles as discovery sources, not final contact sources.
- If a lead came from news, search for the official company website next.
- Set `source_type` to `News Article` or `Mixed`.
- If no official website is found, set `verification_status` to `News Only`.

Directories:

- Use directories only when official data is limited.
- Try to verify the company with its own website.
- Set `source_type` to `Directory` or `Mixed`.

Social media:

- Use only publicly visible pages.
- Do not require login or scrape private content.
- Use social media mainly to confirm activity or find official links.

<!-- CODEx_END: source_handling_rules -->

<!-- CODEx_START: discovered_lead_definition -->
*Updated: 2026-05-08 12:05*

## What Counts as a Discovered Lead

A company can be added as a discovered lead if:

- It appears to match Ron Group target customer types.
- It is related to restaurants, hotels, cafes, bars, hospitality projects, design, fit-out, or procurement.
- It has a public source link.
- There is a possible product or service fit for Ron Group.

A discovered lead is not automatically ready to contact. Contact readiness is decided during lead enrichment.

<!-- CODEx_END: discovered_lead_definition -->

<!-- CODEx_START: entity_dedup_rule -->
*Updated: 2026-05-25*

## Entity-Level Dedup Rule

入库去重必须基于公司实体，不能只靠当前记录的 URL 或公司名精确匹配。

Before adding a new lead to `data/leads.csv`, check for existing entries that represent the same company:

1. **域名归一化** — 提取 website 域名，去掉 `www.`，比较根域名（如 `bargroup.au` 和 `bargroup.com.au` 是同一公司）
2. **公司名归一化** — `.strip().lower()` 后比较，注意缩写和变体（如 "Fink" vs "Fink Group"）
3. **邮箱域匹配** — 如果新候选的邮箱域名与已有线索的邮箱域名相同，可能是同一公司

命中任一检查时：合并到已有条目，不新建行。合并时保留信息更完整的那条，把另一条的独有字段（如 `keyword_source_query`、`enrichment_notes`）追加过去。

同一家公司可能从不同 URL、不同域名、不同关键词被多次发现。每次入库都要重新检查，不能假设「这批数据内部没有重复」就够了。

<!-- CODEx_END: entity_dedup_rule -->

<!-- CODEx_START: b_to_a_auto_flow -->
*Updated: 2026-05-28*

## Discovery-to-Enrichment Auto-Flow

Approved companies from keyword discovery are automatically eligible for form collection.

Rules:

- AU leads with `customer_type` matching `Final Customer` or hospitality/restaurant terms are auto-included in the form collection queue.
- Before each form collection run, build the queue with `build_form_kp_candidate_queue.py`. The queue must include all AU leads with missing contact fields.
- No manual approval is needed between discovery and enrichment. Approved discovery leads enter the queue on the next run.

<!-- CODEx_END: b_to_a_auto_flow -->

<!-- CODEx_START: enrichment_threshold_rule -->
*Updated: 2026-05-28*

## Enrichment Threshold Rule

After each form collection run, calculate AU contact coverage rate. Coverage = AU leads with at least one contact field (company email / phone / contact page / contact form) / total AU leads.

| Coverage | Status | Action |
|----------|--------|--------|
| >= 90% | Healthy | Continue filling remaining gaps |
| 75%–89% | Warning | Signal that new companies are needed from discovery |
| < 75% | Critical | **Discovery must run before more form collection** |

Trigger:

- Calculate coverage after every form collection run.
- If coverage < 90%, add a warning in the run report.
- If coverage < 75%, write "needs discovery batch" in `current-progress.md` A zone next steps.

Inline check:

```python
au_leads = [r for r in leads if r.get('country') == 'Australia']
has_contact = [r for r in au_leads if any(r.get(f,'').strip() for f in ['company_email','company_phone','company_contact_page','company_contact_form_url'])]
rate = len(has_contact) / len(au_leads) * 100 if au_leads else 0
```

<!-- CODEx_END: enrichment_threshold_rule -->
