<!-- DOC_META
lifecycle:  temporary
audience:   user
write_when: 历史批次完成后写入（已不再更新）
read_when:  一般不读取，仅归档参考
delete_when: 可随时归档到 docs/logs/archive/
-->

# Australia Direct Buyer Search Report - 2026-05-11 15:40

Batch ID: `BATCH-AU-DIRECTBUYER-20260511-154000`

## Scope

This pass continued the AU restaurant/hotel final-customer workflow.

It did not send outreach. It focused on existing Australia restaurant/hotel/hospitality final-customer leads and searched for procurement, F&B, operations, development, design, commercial, and venue-leadership buyer routes.

## Data Changes

- Leads reviewed/updated: 5
- New contact rows added: 17
- New leads collected: 0
- Outreach sent: 0

Current file counts after update:

- `data/leads.csv`: 183 rows
- `data/contacts.csv`: 110 rows

## Strongest Findings

### Official Source Findings

- `LEAD-0171` Applejack Hospitality
  - Official pages identify founders/directors, culinary, operations, beverage, and events leadership.
  - Added Hamish Watts, Ben Carroll, Patrick Friesen, Matthew Jenkins, and Chris Rolls.
  - Direct personal emails were not found. Use official `hello@applejackhospitality.com.au` route with role/person personalization.

### Public Professional / Directory Findings

- `LEAD-0170` Solotel
  - Public people sources identify Mark Sutherland as Group Procurement / Commercial Manager and Anna Solomon as Director of Design and Development.
  - Masked or third-party emails were not saved. Use official Solotel company routes unless a direct email is verified.

- `LEAD-0181` Crystalbrook Collection
  - The Org identifies Murray Gordon as Group Director, Development and lists F&B operations candidates.
  - Public job postings confirm a procurement function and Area Procurement Manager reporting line, but no named procurement manager/direct email was found.

- `LEAD-0172` Australian Venue Co.
  - The Org adds Yvette Neilson, Melise Connelly, and James Hay to the existing procurement/development map.
  - Official procurement mailbox remains the strongest outreach route.

### Low-Confidence Direct Route

- `LEAD-0121` Grill'd
  - The Org identifies supply chain, network development, and trade operations candidates.
  - A public directory lists Anthony Rahilly as General Manager of Supply with a direct email.
  - This was saved as Low confidence and Medium priority only. Verify before outreach because it is not official company evidence.

## Problems Found

- Direct key-person email remains the main bottleneck.
- Official restaurant/hotel pages often expose leadership names but not direct buyer contact details.
- Third-party databases frequently expose masked emails or guessed formats. These were not saved as outreach-ready contacts.
- Public org-chart sources are useful for personalization and buyer mapping, but they usually do not provide verified direct contact routes.

## Toolization Notes

Future direct-buyer tooling should separate:

- Officially verified direct contact.
- Public third-party direct contact requiring verification.
- Person identified only.
- Role/function evidence without a named person.

The tool should not upgrade a lead to high-priority outreach only because a third-party directory lists an email. It should keep a source-confidence gate before outreach prioritization.

## Recommended Next Step

Proceed to sample expansion for AU restaurant/hotel final customers.

Focus new collection on:

1. Restaurant groups and multi-location restaurants.
2. Hotel groups with F&B spaces.
3. Hospitality groups operating restaurants, bars, pubs, hotels, or event venues.
4. New opening, renovation, and expansion signals.

Avoid filling the next batch with fit-out/design/commercial kitchen suppliers unless explicitly needed.
