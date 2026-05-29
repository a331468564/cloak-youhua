# Public Contact Candidate Extraction Test

Generated: 2026-05-29 15:32

## Scope

- Input queue: `reports/auto-queue.csv`
- Skip: 0
- Limit: 1
- Follow links per lead: 0
- Tool: Scrapling `static` mode
- Output type: candidate evidence only; no direct writes to data CSV files

## Candidate Counts

- `email`: 1
- `linkedin_search_url`: 1
- `fetch_status`: 1

## Review Buckets

- `possible_person_email`: 1
- `manual_linkedin_search`: 1
- `technical_status`: 1

## Top Review Candidates

- TEST-002 `120` `possible_person_email` email: a.khaled@mathaqat.com.sa (https://www.lucasrestaurants.com)
- TEST-002 `45` `manual_linkedin_search` linkedin_search_url: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%22Lucas+Restaurants%22+Australia+director+OR+operations+OR+procurement (queue_public_linkedin_query)
- TEST-002 `13` `technical_status` fetch_status: https://www.lucasrestaurants.com (https://www.lucasrestaurants.com)

## Lead Review Summary

### 1. Lucas Restaurants (TEST-002)
- `120` `possible_person_email` email: a.khaled@mathaqat.com.sa (https://www.lucasrestaurants.com)
- `45` `manual_linkedin_search` linkedin_search_url: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%22Lucas+Restaurants%22+Australia+director+OR+operations+OR+procurement (queue_public_linkedin_query)
- `13` `technical_status` fetch_status: https://www.lucasrestaurants.com (https://www.lucasrestaurants.com)


## Notes

- Candidate values must be reviewed before saving to `data/leads.csv` or `data/contacts.csv`.
- Emails and phones can be company-level or person-level; classify them before use.
- LinkedIn URLs are manual review entry points. Do not treat them as verified key-person contact until the person and company fit are confirmed.
- Role snippets are low-confidence hints until a person name/title is verified.
