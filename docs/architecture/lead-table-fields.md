<!-- DOC_META
lifecycle:  long-term
audience:   agent
write_when: CSV 字段定义变更时更新
read_when:  需要了解字段含义或数据结构时读取
delete_when: 不删除
-->
# Lead Table Fields

<!-- CODEx_START: table_purpose -->
*Updated: 2026-05-08 17:50*

## Purpose of `data/leads.csv`

`data/leads.csv` stores company-level lead data, company-level contact channels, scoring, follow-up status, source links, and update notes.

Each row should represent one potential customer company or one source-specific company lead that may later be merged during manual review.

Person-level contacts should be stored in `data/contacts.csv`.

One company can have multiple contacts. Do not assume one company equals one contact.

<!-- CODEx_END: table_purpose -->

<!-- CODEx_START: required_fields -->
*Updated: 2026-05-08 17:50*

## Required Fields

Recommended required fields:

- `lead_id`
- `company_name`
- `website`
- `country`
- `city_or_region`
- `industry_type`
- `customer_type`
- `source_link`
- `customer_strength_level`
- `outreach_difficulty_level`
- `estimated_follow_up_probability`
- `follow_up_status`
- `last_researched_date`
- `next_action`
- `notes`
- `last_updated`
- `change_note`

<!-- CODEx_END: required_fields -->

<!-- CODEx_START: contact_and_enrichment_fields -->
*Updated: 2026-05-08 17:50*

## Contact and Enrichment Fields

Future collection and enrichment should use separated company-level lead fields and person-level contact rows.

Company-level contact fields kept in `leads.csv`:

- `company_email`: General company, department, reservation, sales, info, hello, enquiries, or contact email.
- `company_phone`: General company phone number.
- `company_linkedin_url`: Company LinkedIn page, not a personal profile.
- `company_instagram_url`: Official company or brand Instagram page.
- `company_contact_page`: Official contact page URL.
- `company_contact_form_url`: Official contact form URL.
- `company_general_contact_note`: Notes about general company contact quality or uncertainty.

Person-level contact fields should move to `data/contacts.csv`:

- `key_contact_name`: Relevant person, such as owner, founder, procurement manager, F&B manager, operations manager, project manager, director, or general manager.
- `key_contact_job_title`: Job title of the key contact person.
- `key_contact_email`: Direct email of the key contact person.
- `key_contact_phone`: Direct phone number of the key contact person.
- `key_contact_linkedin_url`: Personal LinkedIn profile of the key contact person.
- `key_contact_source_link`: Source URL where key contact information was found.
- `key_contact_confidence`: High, Medium, Low, or Unknown.
- `key_contact_note`: Notes about the key contact person, uncertainty, or missing information.

These `key_contact_*` fields are currently retained in `leads.csv` as legacy compatibility fields, but new person-level contact records should be written to `contacts.csv`.

Candidate registration rule:

- Public-source company contact routes may be saved directly to `leads.csv` with source and notes.
- Public-source KP candidates may be saved directly to `contacts.csv` even before outreach, as long as uncertainty is explicit.
- Use `contact_confidence` = `低` or `中`, `contact_status` = `待验证候选` or `已识别联系人`, and notes explaining the source and uncertainty.
- Machine-generated candidates from approved public-source tools may be registered directly under these same confidence/status rules. Human review is required before outreach use, not before candidate registration.
- Do not mark a candidate as `已找到直联`, `高`, or primary unless a person/company/source match and usable direct route are actually verified.
- Do not save pure role snippets, fetch status rows, or Google/LinkedIn search-result URLs as contact records.

`contacts.csv` suggested columns:

- `contact_id`
- `lead_id`
- `company_name`
- `contact_name`
- `job_title`
- `department`
- `contact_role_type`
- `email`
- `phone`
- `linkedin_url`
- `source_link`
- `source_type`
- `contact_confidence`
- `contact_status`
- `is_primary_contact`
- `contact_priority`
- `outreach_contact_type`
- `notes`
- `last_researched_date`
- `last_updated`
- `change_note`

Link rule:

- Use `lead_id` to connect each row in `contacts.csv` back to the matching company row in `leads.csv`.
- Multiple rows in `contacts.csv` can use the same `lead_id`.

Contact classification fields:

- `contact_data_level`: No Contact Found, Company Contact Only, Key Person Identified, or Direct Key Contact Found.
- `primary_contact_method`: Best current contact path.
- `outreach_contact_type`: General Company Contact, Department Contact, Key Person Contact, Social Contact, Contact Form, or No Contact.
- `contact_priority`: High, Medium, Low, or Manual Review Needed.

Enrichment tracking fields:

- `keyword_source_query`: Search keyword that found the lead.
- `source_type`: Official Website, News Article, Directory, Social Media, Search Result, or Mixed.
- `contact_research_status`: Not Started, In Progress, Contact Found, No Contact Found, or Manual Review Needed.
- `verification_status`: Official Site Verified, News Only, Directory Only, or Needs Verification.
- `contact_completeness_score`: High, Medium, Low, or None.
- `enrichment_attempts`: Number of public-source checks attempted.
- `enrichment_notes`: What was searched and what is still missing.

Legacy deprecated fields:

- `email_address`: Deprecated because it may contain company email or person email.
- `phone_number`: Deprecated because it may contain company phone or person phone.
- `linkedin_url`: Deprecated because it may contain company page or personal profile.
- `contact_person`: Deprecated; use `key_contact_name`.
- `job_title`: Deprecated; use `key_contact_job_title`.
- `official_contact_page`: Deprecated; use `company_contact_page`.
- `contact_form_url`: Deprecated; use `company_contact_form_url`.

<!-- CODEx_END: contact_and_enrichment_fields -->

<!-- CODEx_START: optional_fields -->
*Updated: 2026-05-08 15:41*

## Optional Fields

Optional or future fields:

- `company_size`
- `project_signal`
- `product_service_fit`
- `duplicate_status`
- `email_status`
- `contact_type`
- `review_priority`

These fields can improve filtering and review, but they should not be filled with guesses.

<!-- CODEx_END: optional_fields -->

<!-- CODEx_START: scoring_rules -->
*Updated: 2026-05-09 18:06*

## Scoring Rules

`customer_strength_level`:

- `High`: Strong fit, clear project or procurement potential, multiple locations, hotel group, chain restaurant, restaurant group, hotel F&B operator, or high-value hospitality group. Fit-out, design, and commercial kitchen companies can be High for supplier/partner tasks, but are secondary in the current Australia restaurant/hotel final-customer workflow.
- `Medium`: Possible fit, active company, but project size or purchasing need is unclear.
- `Low`: Weak fit, small or unclear business, no visible purchasing signal.

`outreach_difficulty_level`:

- `Easy`: Relevant key person found with direct email, direct phone, or another strong direct route.
- `Medium`: Company email, company phone, department email, contact page, contact form, or key person identified without direct contact.
- `Hard`: No usable contact method found.

`contact_data_level`:

- `No Contact Found`: No usable company or person contact method.
- `Company Contact Only`: Company email, phone, contact page, contact form, company LinkedIn, or Instagram exists, but no key person is identified.
- `Key Person Identified`: Person name or job title exists, but no direct personal email, phone, or LinkedIn is available.
- `Direct Key Contact Found`: Key person plus direct email, direct phone, or personal LinkedIn is available.

`contact_priority`:

- `High`: Direct key contact found, especially key-person email or phone.
- `Medium`: Company contact only, department contact, contact form, or key person identified without direct contact.
- `Low`: Weak or uncertain contact path.
- `Manual Review Needed`: No contact found or unclear data.

`estimated_follow_up_probability`:

- `High`: Strong customer fit and direct key-person contact.
- `Medium`: Strong or possible fit with company-level contact, department contact, contact form, or key person identified without direct contact.
- `Low`: Weak fit or no usable contact method.
- `Unknown`: Not enough information.

`priority_outreach_candidate` rule:

- Treat a lead as a top outreach candidate only when it is an Australia restaurant or hotel final customer and has a relevant key person with at least an email address, preferably with phone as well.
- Company email, company phone, and company contact form can make a lead `Ready to Contact`, but they should normally be reviewed after direct key-person contacts.

<!-- CODEx_END: scoring_rules -->

<!-- CODEx_START: status_rules -->
*Updated: 2026-05-09 18:06*

## Status Rules

`follow_up_status` values:

- `New`
- `Reviewed`
- `Need More Research`
- `Ready to Contact`
- `Contacted`
- `Replied`
- `Not Suitable`

Rules:

- Use `Ready to Contact` only when at least one usable contact method exists.
- `Ready to Contact` is a broad operational status, not the same as highest-priority outreach.
- Use `Need More Research` when contact data is missing or weak.
- Use `Not Suitable` when the company does not match Ron Group's target customer profile.
- Prefer direct key contact information over general company contact information.
- If `contact_data_level` is `No Contact Found`, `follow_up_status` must be `Need More Research`.
- If `contact_data_level` is `Key Person Identified`, keep `Need More Research` unless a usable company contact path is also available.
- If `contact_data_level` is `Direct Key Contact Found`, the lead can usually be `Ready to Contact`.
- For the current Australia workflow, review `Direct Key Contact Found` restaurant/hotel final customers before `Company Contact Only` leads.

`contact_research_status` values:

- `Not Started`
- `In Progress`
- `Contact Found`
- `No Contact Found`
- `Manual Review Needed`

`verification_status` values:

- `Official Site Verified`
- `News Only`
- `Directory Only`
- `Needs Verification`

<!-- CODEx_END: status_rules -->

<!-- CODEx_START: filtering_fields -->
*Updated: 2026-05-08 12:05*

## Recommended Filter Fields

Useful filter fields:

- `country`
- `city_or_region`
- `customer_type`
- `customer_strength_level`
- `outreach_difficulty_level`
- `follow_up_status`
- `contact_research_status`
- `verification_status`
- `contact_completeness_score`
- `product_service_fit`
- `next_action`

<!-- CODEx_END: filtering_fields -->

<!-- CODEx_START: keyword_runs_and_outreach_log_fields -->
*Updated: 2026-05-08 18:11*

## Keyword Runs and Outreach Log Fields

`data/keyword_runs.csv` records each keyword collection batch.

Purpose:

- Track which keyword was used
- Track when it was used
- Track how many leads were collected
- Track quality metrics for the run
- Avoid repeating the same keyword without review

Important fields:

- `batch_id`: Batch identifier for one collection batch.
- `run_id`: Unique identifier for one keyword run.
- `keyword_id`: Links the run back to `data/search_keywords.csv`.
- `keyword_source_query`: Exact search query used.
- `collection_round`: Round number for repeated use of the same keyword.
- `target_leads_count`: Intended number of leads.
- `actual_leads_collected`: Actual number collected.
- `discovery_quality_score`: Company discovery quality.
- `contactability_score`: Contact finding quality.
- `run_status`: Planned, Completed, Paused, Failed, or Needs Review.

`data/outreach_log.csv` is an empty future tracking template.

Purpose:

- Prevent contacting the same company multiple times.
- Prevent contacting the same person multiple times.
- Prevent different batches from creating outreach conflicts.

Important fields:

- `outreach_id`: Unique outreach record ID.
- `lead_id`: Company lead ID.
- `contact_id`: Contact person ID.
- `canonical_domain`: Company domain used for conflict checks.
- `email`: Email used for outreach.
- `linkedin_url`: LinkedIn used for outreach.
- `outreach_date`: Date contacted.
- `outreach_status`: Planned, Sent, Replied, Bounced, Paused, or Blocked.
- `blocked_reason`: Reason outreach should not proceed.

Do not fill `outreach_log.csv` with existing leads until outreach is actually planned or performed.

<!-- CODEx_END: keyword_runs_and_outreach_log_fields -->
