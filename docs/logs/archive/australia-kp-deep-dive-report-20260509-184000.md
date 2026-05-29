<!-- DOC_META
lifecycle:  temporary
audience:   user
write_when: 历史批次完成后写入（已不再更新）
read_when:  一般不读取，仅归档参考
delete_when: 可随时归档到 docs/logs/archive/
-->

# Australia KP Deep-Dive Report - 20260509-184000

Batch ID: `BATCH-AU-KPDEEP-20260509-184000`
Run date: 2026-05-09

## Scope

This was a 20-candidate Australia restaurant/hotel final-customer KP enrichment pass.

The run did not collect new leads. It reviewed existing Australia leads, mostly `Company Contact Only`, and tried to upgrade them with public-source key-person evidence.

## Candidate Set

- Candidates reviewed: 20
- Strict `Company Contact Only` restaurant/hotel final-customer candidates: 18
- Additional restaurant group candidates with existing `Key Person Identified` but no direct personal route: 2
- Outreach sent: 0

## Summary

- New contact rows added: 23
- Leads upgraded to `Key Person Identified`: 10
- Leads still `Company Contact Only`: 8
- Leads moved to `Need More Research`: 1
- New direct contact rows: 3
- New direct key-person leads: 0

## Contact Quality

- High confidence contacts: 17
- Medium confidence contacts: 4
- Low confidence contacts: 2

Most high-confidence contacts came from official company about/team/story pages. Direct contact quality was still weak because most pages exposed names and titles but not personal email or phone.

## Best KP Sources

- Official team/about pages:
  - Australian Venue Co.
  - Odd Culture Group
  - Liquid & Larder
  - H&J Restaurants
  - Grossi Hospitality
- Official story/news pages:
  - Veriu Group
  - Hunter St. Hospitality
  - Bentley Restaurant Group
- Official careers/media pages:
  - Grill'd
  - TFE Hotels

## Notable Upgrades

- `LEAD-0172` Australian Venue Co.: Sam Lewis identified as GM Procurement, Projects & Analytics; Craig Ellison identified as COO.
- `LEAD-0173` Odd Culture Group: CEO, beverage, and operations contacts identified; one role mailbox found for Sabrina via official careers page.
- `LEAD-0174` Liquid & Larder: founder/director, growth/CFO, GM/accounts, and Head of Venues identified.
- `LEAD-0166` H&J Restaurants: CEO and Managing Director identified from official about page.
- `LEAD-0182` TFE Hotels: Group COO and media/brand contacts identified; one direct phone found for a brand manager.
- `LEAD-0183` Veriu Group: Group CEO identified from official Veriu article.

## Weak Spots

- Large hotel groups still expose central reservation, sales, media, or contact forms more often than procurement/F&B decision-makers.
- Public official pages often list role names but hide exact direct email addresses.
- Some candidate pages are useful for personalization but not enough for high-priority outreach.
- `LEAD-0164` Taverners Group appears to be investment/property/family-office oriented rather than an Australia restaurant/hotel final customer, so it was moved to manual review.

## Method Result

This method exceeded the KP identification target for a 20-candidate test:

- KP identification lift: 12 of 20 candidates now have `Key Person Identified`.
- Direct key-person contact: 0 of 20, below the 8% to 10% toolization target.

Conclusion: official-page KP search is strong for names/titles, but weak for direct key-person email/phone. It should become one stage in the tool, not the whole tool.

## Recommended Next Step

Run a second AU KP pass focused only on direct route discovery for the newly identified people:

- Australian Venue Co. - Sam Lewis
- Odd Culture Group - Rebecca Lines, Jordan Blackman, Sabrina Medcalf
- Liquid & Larder - Warren Burns, James Bradey, Dean Simpson, Emma McAlary
- TFE Hotels - Chris Sedgwick, Emily Hoare
- Veriu Group - Zed Sanjana
- H&J Restaurants - Jayantha Warnakula, Harsha Kumarasingha

Use public Google snippets, official PDFs, public LinkedIn-visible evidence, and The Org where available. Save third-party evidence only as Low or Medium confidence unless cross-checked by an official source.

