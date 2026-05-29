<!-- DOC_META
lifecycle:  temporary
audience:   user
write_when: 历史批次完成后写入（已不再更新）
read_when:  一般不读取，仅归档参考
delete_when: 可随时归档到 docs/logs/archive/
-->

# Australia Restaurant/Hotel Sample Expansion Report - 2026-05-11 16:00

Batch ID: `BATCH-AU-RHSAMPLE-20260511-160000`

## Scope

This pass expanded the Australia restaurant/hotel final-customer sample after the direct-buyer search pass.

It prioritized restaurant groups, hotel groups, hospitality venue groups, and multi-venue operators. It did not add fit-out, interior design, commercial kitchen, FF&E, OS&E, or supplier/partner companies.

Outreach sent: 0.

## Data Changes

- New AU final-customer leads added: 12
- New contact rows added: 11
- New keyword rows added: 3
- New keyword run rows added: 3

Current file counts after update:

- `data/leads.csv`: 195 rows
- `data/contacts.csv`: 121 rows
- `data/search_keywords.csv`: 33 rows
- `data/keyword_runs.csv`: 23 rows

## New Leads Added

- `LEAD-0184` The Speakeasy Group
- `LEAD-0185` Swillhouse
- `LEAD-0186` Kickon Group
- `LEAD-0187` Lancemore Hotels
- `LEAD-0188` EVT
- `LEAD-0189` Dedes Waterfront Group
- `LEAD-0190` House Made Hospitality
- `LEAD-0191` Lucas Collective
- `LEAD-0192` Merivale
- `LEAD-0193` Meriton Suites
- `LEAD-0194` Ovolo Hotels Australia
- `LEAD-0195` Oscars Group

## Useful Sources

- Official contact/about/team/venue pages were used first.
- Official protected emails displayed as `[email protected]` in search snippets were not copied as real email values.
- Where official pages exposed named leaders, contacts were added as `Person Identified`; direct personal email was not assumed.

## Results

- Official source coverage: 12 of 12 new leads.
- Ready to Contact: 12 of 12 new leads, mostly through official company contact pages, forms, phone numbers, or general mailboxes.
- Direct key-person contact: 0 new high-confidence direct buyer emails.
- Key-person identification improved for companies with official named founders/executives, such as Speakeasy, Swillhouse, Kickon, Lucas Collective, Merivale, and Oscars Group.

## Problems Found

- The added sample improves final-customer coverage but does not solve the direct buyer email bottleneck.
- Hotel groups and large hospitality groups usually expose reservations, events, careers, head office, or general forms before procurement/F&B buyer routes.
- Some strong target companies have reputational or compliance context in public news. These should be reviewed before outreach tone is finalized.

## Toolization Impact

This pass reaches the minimum Australia sample target by bringing Australia leads to 80.

However, the workflow is still not fully tool-ready because the strongest success metric is direct key-person contact, not only sample count or general contactability.

The next toolization work should measure:

- Australia final-customer count separately from supplier/partner count.
- Company contact only vs key-person identified vs direct key contact.
- Official-source direct buyer yield.
- Third-party candidate yield requiring verification.

## Recommended Next Step

Before building broader automation, run a quality review over the 80 Australia leads and tag which are true restaurant/hotel final customers versus secondary supplier/partner leads.

Then build the first local tool layer around:

1. Candidate selection.
2. Query generation.
3. Manual review checklist.
4. CSV update helper.
5. Batch report generation.
