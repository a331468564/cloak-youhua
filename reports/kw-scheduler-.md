# Public Contact Candidate Extraction Test

Generated: 2026-05-29 14:50

## Scope

- Input queue: `D:\TestProject-v3\reports\kw-scheduler-queue.csv`
- Skip: 0
- Limit: 10
- Follow links per lead: 2
- Tool: Scrapling `static` mode
- Output type: candidate evidence only; no direct writes to data CSV files

## Candidate Counts


## Review Buckets


## Notes

- Candidate values must be reviewed before saving to `data/leads.csv` or `data/contacts.csv`.
- Emails and phones can be company-level or person-level; classify them before use.
- LinkedIn URLs are manual review entry points. Do not treat them as verified key-person contact until the person and company fit are confirmed.
- Role snippets are low-confidence hints until a person name/title is verified.
