# Public Contact Candidate Extraction Test

Generated: 2026-05-29 14:17

## Scope

- Input queue: `reports/test-queue.csv`
- Skip: 0
- Limit: 3
- Follow links per lead: 2
- Tool: Scrapling `static` mode
- Output type: candidate evidence only; no direct writes to data CSV files

## Candidate Counts

- `linkedin_search_url`: 3
- `fetch_status`: 3
- `email`: 1
- `role_context`: 1

## Review Buckets

- `manual_linkedin_search`: 3
- `technical_status`: 3
- `possible_person_email`: 1
- `kp_context_hint`: 1

## Top Review Candidates

- TEST-002 `120` `possible_person_email` email: a.khaled@mathaqat.com.sa (https://www.lucasrestaurants.com)
- TEST-003 `60` `kp_context_hint` role_context: owner (https://www.rockpool.com)
- TEST-002 `45` `manual_linkedin_search` linkedin_search_url: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%22Lucas+Restaurants%22+Australia+director+OR+operations+OR+procurement (queue_public_linkedin_query)
- TEST-001 `45` `manual_linkedin_search` linkedin_search_url: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%22Merivale+Group%22+Australia+director+OR+operations+OR+procurement (queue_public_linkedin_query)
- TEST-003 `45` `manual_linkedin_search` linkedin_search_url: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%22Rockpool+Dining+Group%22+Australia+director+OR+operations+OR+procurement (queue_public_linkedin_query)
- TEST-002 `13` `technical_status` fetch_status: https://www.lucasrestaurants.com (https://www.lucasrestaurants.com)
- TEST-001 `13` `technical_status` fetch_status: https://www.merivale.com (https://www.merivale.com)
- TEST-003 `5` `technical_status` fetch_status: https://www.rockpool.com (https://www.rockpool.com)

## Lead Review Summary

### 1. Lucas Restaurants (TEST-002)
- `120` `possible_person_email` email: a.khaled@mathaqat.com.sa (https://www.lucasrestaurants.com)
- `45` `manual_linkedin_search` linkedin_search_url: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%22Lucas+Restaurants%22+Australia+director+OR+operations+OR+procurement (queue_public_linkedin_query)
- `13` `technical_status` fetch_status: https://www.lucasrestaurants.com (https://www.lucasrestaurants.com)

### 2. Merivale Group (TEST-001)
- `45` `manual_linkedin_search` linkedin_search_url: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%22Merivale+Group%22+Australia+director+OR+operations+OR+procurement (queue_public_linkedin_query)
- `13` `technical_status` fetch_status: https://www.merivale.com (https://www.merivale.com)

### 3. Rockpool Dining Group (TEST-003)
- `60` `kp_context_hint` role_context: owner (https://www.rockpool.com)
- `45` `manual_linkedin_search` linkedin_search_url: https://www.google.com/search?q=site%3Alinkedin.com%2Fin+%22Rockpool+Dining+Group%22+Australia+director+OR+operations+OR+procurement (queue_public_linkedin_query)
- `5` `technical_status` fetch_status: https://www.rockpool.com (https://www.rockpool.com)


## Notes

- Candidate values must be reviewed before saving to `data/leads.csv` or `data/contacts.csv`.
- Emails and phones can be company-level or person-level; classify them before use.
- LinkedIn URLs are manual review entry points. Do not treat them as verified key-person contact until the person and company fit are confirmed.
- Role snippets are low-confidence hints until a person name/title is verified.
