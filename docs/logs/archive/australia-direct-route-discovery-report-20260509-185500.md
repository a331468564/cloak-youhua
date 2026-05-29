<!-- DOC_META
lifecycle:  temporary
audience:   user
write_when: 历史批次完成后写入（已不再更新）
read_when:  一般不读取，仅归档参考
delete_when: 可随时归档到 docs/logs/archive/
-->

# Australia Direct Route Discovery Report - 2026-05-09 18:55

Batch ID: `BATCH-AU-DIRECTROUTE-20260509-185500`

## Scope

This pass did not collect new leads and did not perform outreach.

The purpose was to improve existing Australia restaurant/hotel final-customer leads by checking whether already identified key people had usable direct routes, especially email or phone.

## Data Changes

- Leads reviewed/updated: 5
- Contact rows changed: 3
- New contact rows added: 2
- Existing contact rows upgraded: 1
- New leads collected: 0
- Outreach sent: 0

Current file counts after update:

- `data/leads.csv`: 183 rows
- `data/contacts.csv`: 92 rows

Integrity check:

- Duplicate `contact_id`: 0
- Contact rows linked to missing `lead_id`: 0

## Results

### Direct Contact Found

- `LEAD-0182` TFE Hotels
  - Updated contact: Jodi Clark, Director of Communications
  - Official direct email and phone found on TFE Hotels press page.
  - Lead upgraded to `Direct Key Contact Found`.
  - Important limitation: this is a communications route, not a procurement, F&B, operations, or fit-out buyer route.

### Procurement Candidates Added

- `LEAD-0172` Australian Venue Co.
  - Added Fonda Kourmadias, Head of Food Procurement.
  - Added Manish Baisoya, Senior Analyst - Procurement.
  - Source is The Org, so both are Medium confidence candidates only.
  - No official personal direct email was found.
  - Recommended route remains the official AVC procurement mailbox until a direct email is verified.

### No Usable Direct Route Found

- `LEAD-0173` Odd Culture Group
  - Official role mailbox retained.
  - No new official personal direct route found for Rebecca Lines, Jordan Blackman, or Sabrina Medcalf.

- `LEAD-0174` Liquid & Larder
  - No official personal direct route found.
  - Third-party guessed email patterns were not saved.

- `LEAD-0183` Veriu Group
  - Compliance/whistleblower-only contact routes were found but not saved for sales outreach.
  - These routes do not match the source purpose and should not be used for normal business development.

## Sources Checked

- Australian Venue Co. official team page: https://www.ausvenueco.com.au/our-team/
- Australian Venue Co. The Org page: https://theorg.com/org/avc-pty-ltd/offices/hq
- TFE Hotels senior appointments press page: https://www.tfehotels.com/en/press/tfe-announces-senior-appointments-to-help-deliver-robust-hotel-pipeline/
- Odd Culture Group official about page: https://www.oddculture.group/about-us/
- Liquid & Larder official about page: https://www.liquidandlarder.com.au/about/
- Veriu Group official expansion article: https://veriu.com.au/blog/veriu-group-to-launch-four-new-properties-in-victoria-and-nsw/

## Pending Issues

- AU restaurant/hotel target quality is improving, but direct key-person email remains the main bottleneck.
- Large hotel and venue groups often expose media, careers, events, or company mailboxes more readily than procurement/F&B buyer emails.
- Some direct contacts exist in pages with a restricted purpose, such as compliance or whistleblower reporting. These should be excluded from outreach use unless the user explicitly approves a different rule.
- The current CSV does not have a separate source-purpose field, so purpose-sensitive exclusions must be documented in `change_note`, `enrichment_notes`, or `notes`.

## Toolization Lessons

A successful AU tool should include these filters before writing contacts:

- Prioritize official sources, then approved public professional profiles and reputable org-chart sources.
- Separate "person identified" from "usable direct route".
- Reject contacts from compliance, whistleblower, privacy, investor complaint, legal notice, or unrelated support contexts for sales outreach.
- Save guessed third-party emails only after verification, not as outreach-ready data.
- Preserve company-level routes as fallback, but do not count them as priority outreach unless no better route exists.

## Recommended Next Step

Continue the AU plan with a focused direct-buyer search round:

1. Start with Australia restaurant/hotel groups already marked `Key Person Identified`.
2. Look specifically for procurement, F&B, operations, development, projects, openings, and venue leadership contacts.
3. Use official source pages first, then public LinkedIn/The Org-style evidence as Low/Medium confidence candidates.
4. Only upgrade to `Priority Outreach` when the lead has an AU restaurant/hotel final-customer fit plus a relevant key person with a usable email, preferably phone.
