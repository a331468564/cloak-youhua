<!-- DOC_META
lifecycle:  long-term
audience:   agent
write_when: 技能定义、触发条件、执行步骤变更时更新
read_when:  Agent 加载技能时读取
delete_when: 不删除
-->
---
name: australia-lead-kp-research
description: Use for Ron Group Australia lead research, official form discovery, key-person enrichment, Google dork query generation, and CSV/report updates for restaurant and hospitality B2B leads.
---

# Australia Lead KP Research

Use this skill for Ron Group Australia lead discovery and enrichment work.

## Core Workflow

1. Read the current lead workflow docs:
   - `docs/architecture/project-overview.md`
   - `docs/workflows/lead-collection-workflow.md`
   - `docs/workflows/lead-enrichment-workflow.md`
   - `docs/architecture/lead-table-fields.md`
   - `docs/guides/cli-operating-rules.md`
2. Follow `docs/guides/iteration-setup.md` for key-checkpoint backups. Do not create backups for every routine task; create them before direction/rule/schema changes, large data updates, or other important checkpoints.
3. Prefer official company pages, official contact forms, official team/about pages, PDFs, public org charts, and reviewable public search results.
4. Use a 20-candidate minimum for form/KP method testing unless results are clearly unrelated, duplicate-heavy, or account-risky.
5. Never fill `data/outreach_log.csv` unless outreach is actually planned or sent.
6. Ask for clarification before changing project direction, account-access assumptions, quality thresholds, or outreach-readiness standards. If evidence is too weak to classify a company or KP confidently, ask or mark it for manual review rather than guessing.
7. For important user requirements or handling decisions that future sessions should remember, add a short entry to `docs/request-solution-log.md`.

## Current Business Priorities

- Australia is the current primary market. Do not expand broad collection to other countries unless explicitly requested.
- Prioritize key-person discovery over raw lead volume or general form collection.
- First-stage outreach should focus on restaurant and hotel final customers.
- Treat fit-out, design, procurement, FF&E, OS&E, and commercial kitchen companies as secondary unless the task explicitly asks for supplier or partner leads.
- Public The Org pages and publicly visible LinkedIn/search-result evidence may be saved as Low or Medium confidence KP candidates when the source and uncertainty are recorded.
- The strongest contact is a relevant key person with at least an email address, preferably with phone as well.
- Company email, phone, and contact form are secondary paths because general company inboxes often have lower reply probability, especially at larger companies.

## Toolization Goal

The purpose of this workflow is to win Australia first and then convert the successful process into a repeatable local tool.

Before treating the workflow as tool-ready:
- Test at least 80 Australia restaurant/hotel final-customer candidates.
- Keep duplicate rate below 25%.
- Reach at least 60% Ready to Contact.
- Reach at least 25% key-person identification.
- Reach at least 8% to 10% direct key-person contact.
- Save source links, confidence, notes, and change notes for every lead/contact update.
- Produce repeatable query patterns, scoring rules, CSV update rules, and batch reports.

Historical batch reports are evidence from earlier runs. They do not override current AU-first, restaurant/hotel final-customer, KP-first rules.

## Tool Access

Allowed by default:
- Search engine queries.
- Official company websites and official PDFs.
- Public The Org pages as candidate KP evidence.
- Manual LinkedIn/Sales Navigator review as candidate KP evidence.
- Free/open-source local tools that operate on search queries, official pages, and CSV files.

Use only after explicit account-risk approval:
- User-authorized platform accounts.
- Official APIs or platform-approved integrations.
- Any automated social-platform search or enrichment.

Do not treat a black-box enrichment result as high-confidence without a saved public source link.

## Query Generation

Use `scripts/extraction/generate_kp_form_queries.py` to generate repeatable query batches:

```bash
python scripts/extraction/generate_kp_form_queries.py --limit 20
```

For known company domains:

```bash
python scripts/extraction/generate_kp_form_queries.py --limit 20 --domains "example.com.au,example2.com.au"
```

## KP Confidence

- `High`: Official company page identifies the person and title, or official page lists direct personal email/phone.
- `Medium`: Official PDF/news/company source identifies person or role, but direct route is company-level.
- `Low`: First name, named mailbox, The Org, LinkedIn snippet, or third-party source only.

## Record Rules

Save company-level data in `data/leads.csv`.
Save person-level records in `data/contacts.csv`.
Use `lead_id` to link contacts to leads.
Record all relevant contacts on one official page; do not keep only one.

Each saved record needs:
- `source_link`
- `last_updated`
- `change_note`
- contact confidence and notes when KP data is not direct.
