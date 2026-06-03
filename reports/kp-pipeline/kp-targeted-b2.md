# Public Contact Candidate Extraction Test

Generated: 2026-06-01 10:39

## Scope

- Input queue: `reports/kp-targeted-queue.csv`
- Skip: 20
- Limit: 20
- Follow links per lead: 2
- Tool: Scrapling `static` mode
- Output type: candidate evidence only; no direct writes to data CSV files

## Candidate Counts

- `contact_link`: 189
- `role_context`: 75
- `fetch_status`: 43
- `phone`: 31
- `team_link`: 21
- `contact_form`: 17
- `key_person_name`: 14
- `company_linkedin_url`: 4
- `email`: 3
- `supplier_link`: 1

## Review Buckets

- `company_contact_page`: 153
- `kp_context_hint`: 75
- `technical_status`: 43
- `events_or_functions_contact`: 36
- `phone_candidate`: 31
- `team_or_about_page`: 21
- `possible_key_person`: 14
- `official_form_candidate`: 13
- `booking_form_candidate`: 4
- `company_linkedin`: 4
- `department_or_company_email`: 2
- `supplier_or_procurement_page`: 1
- `company_email`: 1

## Top Review Candidates

- AU-0282 `114` `department_or_company_email` email: info@laundy.com.au (https://laundy.com.au/contact)
- AU-0287 `114` `department_or_company_email` email: info@playersonlygon.com.au (https://pubcogroup.com.au)
- AU-0287 `108` `company_email` email: contact@pubcogroup.com.au (http://www.pubcogroup.com.au/contact-us)
- LEAD-0203 `102` `official_form_candidate` contact_form: https://order.yourprivatechef.com.au/quote/request (https://order.yourprivatechef.com.au/quote/request)
- LEAD-0204 `102` `official_form_candidate` contact_form: https://www.barbellaccino.com.au/franchising (https://www.barbellaccino.com.au/franchising)
- AU-0253 `102` `official_form_candidate` contact_form: https://georgesonwaymouth.com.au/contact/#wpcf7-f47-p14-o1 (https://georgesonwaymouth.com.au/contact/)
- AU-0268 `102` `official_form_candidate` contact_form: https://yarrahotelgroup.com.au/get-in-touch-today/#gf_1 (https://yarrahotelgroup.com.au/get-in-touch-today/)
- AU-0272 `102` `official_form_candidate` contact_form: https://trilogyhotels.com.au/ (https://trilogyhotels.com.au)
- AU-0272 `102` `official_form_candidate` contact_form: https://trilogyhotels.com.au/all-about-trilogy-hotels/ (https://trilogyhotels.com.au/about-us/)
- AU-0278 `102` `official_form_candidate` contact_form: https://reillygroup.com.au (https://reillygroup.com.au)
- AU-0278 `102` `official_form_candidate` contact_form: https://www.reillygroup.com.au/about (https://www.reillygroup.com.au/about)
- AU-0279 `102` `official_form_candidate` contact_form: https://www.thepubgroup.com.au/contact (https://www.thepubgroup.com.au/contact)
- AU-0280 `102` `official_form_candidate` contact_form: https://gmhotels.com.au/# (https://gmhotels.com.au)
- AU-0280 `102` `official_form_candidate` contact_form: https://gmhotels.com.au/our-team.php# (https://gmhotels.com.au/our-team.php)
- AU-0284 `102` `official_form_candidate` contact_form: https://rmh.com.au (https://rmh.com.au)

## Lead Review Summary

### 21. Yourprivatechef (LEAD-0203)
- `102` `official_form_candidate` contact_form: https://order.yourprivatechef.com.au/quote/request (https://order.yourprivatechef.com.au/quote/request)
- `88` `team_or_about_page` team_link: https://order.yourprivatechef.com.au/page/about-us (https://order.yourprivatechef.com.au/quote/request)
- `72` `company_contact_page` contact_link: https://order.yourprivatechef.com.au/items/category/dessert?returnurl=%2fquote%2frequest (https://order.yourprivatechef.com.au/quote/request)
- `72` `company_contact_page` contact_link: https://order.yourprivatechef.com.au/items/category/drinks?returnurl=%2fquote%2frequest (https://order.yourprivatechef.com.au/quote/request)
- `72` `company_contact_page` contact_link: https://order.yourprivatechef.com.au/items/category/grazing-menus?returnurl=%2fquote%2frequest (https://order.yourprivatechef.com.au/quote/request)

### 22. Barbellaccino (LEAD-0204)
- `102` `official_form_candidate` contact_form: https://www.barbellaccino.com.au/franchising (https://www.barbellaccino.com.au/franchising)
- `88` `team_or_about_page` team_link: https://www.barbellaccino.com.au/about-us (https://www.barbellaccino.com.au/franchising)
- `72` `company_contact_page` contact_link: https://www.barbellaccino.com.au (https://www.barbellaccino.com.au/franchising)
- `60` `kp_context_hint` role_context: founder (https://www.barbellaccino.com.au/about-us)
- `60` `kp_context_hint` role_context: owner (https://www.barbellaccino.com.au/franchising)

### 23. Georges on Waymouth | Mediterranean Restaurant Adelaide (AU-0253)
- `102` `official_form_candidate` contact_form: https://georgesonwaymouth.com.au/contact/#wpcf7-f47-p14-o1 (https://georgesonwaymouth.com.au/contact/)
- `72` `company_contact_page` contact_link: https://georgesonwaymouth.com.au/contact/ (https://georgesonwaymouth.com.au)
- `72` `events_or_functions_contact` contact_link: https://georgesonwaymouth.com.au/events/ (https://georgesonwaymouth.com.au)
- `72` `events_or_functions_contact` contact_link: https://georgesonwaymouth.com.au/functions/ (https://georgesonwaymouth.com.au)
- `50` `kp_context_hint` role_context: events (https://georgesonwaymouth.com.au)

### 24. La Vie Hospitality Group – The Life and Soul of Hospitality. (AU-0258)
- `94` `phone_candidate` phone: +61 29167 6666 (https://laviehospitalitygroup.com)
- `89` `possible_key_person` key_person_name: Alliance College Paro (https://laviehospitalitygroup.com)
- `89` `possible_key_person` key_person_name: Education Building (https://laviehospitalitygroup.com)
- `89` `possible_key_person` key_person_name: Hospitality Services (https://laviehospitalitygroup.com)
- `89` `possible_key_person` key_person_name: Jerry Xu (https://www.laviehospitalitygroup.com/about-us-2/)

### 25. Yarra Hotel Group | Hotel Developers | Melbourne (AU-0268)
- `102` `official_form_candidate` contact_form: https://yarrahotelgroup.com.au/get-in-touch-today/#gf_1 (https://yarrahotelgroup.com.au/get-in-touch-today/)
- `88` `team_or_about_page` team_link: https://yarrahotelgroup.com.au/about-us/ (https://yarrahotelgroup.com.au)
- `88` `team_or_about_page` team_link: https://yarrahotelgroup.com.au/projects/ (https://yarrahotelgroup.com.au/about-us/)
- `72` `company_contact_page` contact_link: https://yarrahotelgroup.com.au/get-in-touch-today/ (https://yarrahotelgroup.com.au)
- `50` `kp_context_hint` role_context: operations (https://yarrahotelgroup.com.au)

### 26. Oaks Hotels, Resorts &amp; Suites (AU-0270)
- `94` `phone_candidate` phone: +61 7 2100 0577 (https://oakshotels.com)
- `88` `team_or_about_page` team_link: https://www.oakshotels.com/en/about-oaks (https://oakshotels.com)
- `76` `booking_form_candidate` contact_form: https://www.oakshotels.com/en/contact-oaks-hotels#email (https://www.oakshotels.com/en/contact-oaks-hotels)
- `72` `company_contact_page` contact_link: https://www.oakshotels.com/en/al-najada-doha-hotel-apartments-by-oaks/contact (https://www.oakshotels.com/en/contact-oaks-hotels)
- `72` `company_contact_page` contact_link: https://www.oakshotels.com/en/auckland-harbour-suites/contact (https://www.oakshotels.com/en/contact-oaks-hotels)

### 27. Trilogy Hotels | Independent Hotel Management Company (AU-0272)
- `102` `official_form_candidate` contact_form: https://trilogyhotels.com.au/ (https://trilogyhotels.com.au)
- `102` `official_form_candidate` contact_form: https://trilogyhotels.com.au/all-about-trilogy-hotels/ (https://trilogyhotels.com.au/about-us/)
- `89` `possible_key_person` key_person_name: Do Asset (https://trilogyhotels.com.au/about-us/)
- `89` `possible_key_person` key_person_name: Scott Boyes (https://trilogyhotels.com.au)
- `89` `possible_key_person` key_person_name: Trilogy Hotels (https://trilogyhotels.com.au)

### 28. OUR PEOPLE (AU-0274)
- `88` `team_or_about_page` team_link: https://www.welcomehospitality.com.au/about-us (https://welcomehospitality.com.au)
- `88` `team_or_about_page` team_link: https://www.welcomehospitality.com.au/our-people (https://welcomehospitality.com.au)
- `72` `company_contact_page` contact_link: https://www.welcomehospitality.com.au/# (https://welcomehospitality.com.au)
- `72` `company_contact_page` contact_link: https://www.welcomehospitality.com.au/about-us# (https://www.welcomehospitality.com.au/about-us)
- `72` `company_contact_page` contact_link: https://www.welcomehospitality.com.au/contact-us (https://welcomehospitality.com.au)

### 30. Reilly Group (AU-0278)
- `102` `official_form_candidate` contact_form: https://reillygroup.com.au (https://reillygroup.com.au)
- `102` `official_form_candidate` contact_form: https://www.reillygroup.com.au/about (https://www.reillygroup.com.au/about)
- `88` `team_or_about_page` team_link: https://www.reillygroup.com.au/about (https://reillygroup.com.au)
- `60` `kp_context_hint` role_context: founder (https://www.reillygroup.com.au/about)
- `60` `kp_context_hint` role_context: owner (https://reillygroup.com.au)

### 31. The Pub Group (AU-0279)
- `102` `official_form_candidate` contact_form: https://www.thepubgroup.com.au/contact (https://www.thepubgroup.com.au/contact)
- `98` `phone_candidate` phone: +61267018400 (https://thepubgroup.com.au)
- `72` `company_contact_page` contact_link: https://www.thepubgroup.com.au/contact (https://thepubgroup.com.au)
- `72` `events_or_functions_contact` contact_link: https://www.thepubgroup.com.au/functions (https://thepubgroup.com.au)
- `50` `kp_context_hint` role_context: events (https://www.thepubgroup.com.au/functions)

### 32. GM Hotels Group | Australia (AU-0280)
- `102` `official_form_candidate` contact_form: https://gmhotels.com.au/# (https://gmhotels.com.au)
- `102` `official_form_candidate` contact_form: https://gmhotels.com.au/our-team.php# (https://gmhotels.com.au/our-team.php)
- `94` `phone_candidate` phone: (07) 3200 3777 (https://gmhotels.com.au)
- `94` `phone_candidate` phone: (07) 3252 4136 (https://gmhotels.com.au)
- `94` `phone_candidate` phone: (07) 3391 5022 (https://gmhotels.com.au)

### 33. Laundy Hotels | Award-Winning Hospitality Group (AU-0282)
- `114` `department_or_company_email` email: info@laundy.com.au (https://laundy.com.au/contact)
- `94` `phone_candidate` phone: (02) 9044 6133 (https://laundy.com.au/contact)
- `88` `team_or_about_page` team_link: https://laundy.com.au/about-us (https://laundy.com.au)
- `72` `company_contact_page` contact_link: https://laundy.com.au/contact (https://laundy.com.au)
- `72` `events_or_functions_contact` contact_link: https://laundy.com.au/corporate-functions (https://laundy.com.au)

### 34. RMH Functions | Melbourne Venue (AU-0284)
- `102` `official_form_candidate` contact_form: https://rmh.com.au (https://rmh.com.au)
- `94` `phone_candidate` phone: +61 3 9629 2400 (https://rmh.com.au)
- `89` `possible_key_person` key_person_name: Bourke St Courtyard (https://rmh.com.au)
- `88` `team_or_about_page` team_link: https://www.rmh.com.au/visit-us (https://rmh.com.au)
- `76` `booking_form_candidate` contact_form: https://www.rmh.com.au/book-a-table (https://www.rmh.com.au/book-a-table)

### 35. Venue | Legends Pub &amp; Bistro in Moonee Ponds | Legends (AU-0285)
- `98` `phone_candidate` phone: 03%209326%201277 (https://mvlegends.com.au)
- `72` `company_contact_page` contact_link: https://www.mvlegends.com.au/contact (https://www.mvlegends.com.au/functions)
- `72` `company_contact_page` contact_link: https://www.mvlegends.com.au/contact-us (https://mvlegends.com.au)
- `72` `events_or_functions_contact` contact_link: https://www.mvlegends.com.au/functions (https://mvlegends.com.au)
- `72` `events_or_functions_contact` contact_link: https://www.mvlegends.com.au/terms-conditions (https://www.mvlegends.com.au/contact-us)

### 37. PubCo Group (AU-0287)
- `114` `department_or_company_email` email: info@playersonlygon.com.au (https://pubcogroup.com.au)
- `108` `company_email` email: contact@pubcogroup.com.au (http://www.pubcogroup.com.au/contact-us)
- `94` `phone_candidate` phone: (03) 9663 8149 (https://pubcogroup.com.au)
- `72` `company_contact_page` contact_link: http://www.pubcogroup.com.au/contact-us (https://pubcogroup.com.au)
- `72` `company_contact_page` contact_link: https://www.pubcogroup.com.au/contact-us/ (https://pubcogroup.com.au)

### 38. Australia’s Trusted Corporate &amp; Event Caterers | Australian Catering Company (AU-0289)
- `102` `official_form_candidate` contact_form: https://australiancateringcompany.com.au (https://australiancateringcompany.com.au)
- `98` `phone_candidate` phone: %20412514741 (https://australiancateringcompany.com.au)
- `98` `phone_candidate` phone: 0412514741%20 (https://australiancateringcompany.com.au)
- `94` `phone_candidate` phone: 0412 514 741 (https://australiancateringcompany.com.au)
- `89` `possible_key_person` key_person_name: Time Fully Trained (https://australiancateringcompany.com.au)

### 39. Corporate Catering with Australia's #1 Platform | EatFirst (AU-0290)
- `13` `technical_status` fetch_status: https://eatfirst.com.au (https://eatfirst.com.au)

### 40. Corporate | Rydges Melbourne (CBD) (AU-0301)
- `88` `team_or_about_page` team_link: https://www.rydges.com/about-us/ (https://rydges.com)
- `88` `team_or_about_page` team_link: https://www.rydges.com/about-us/covid-safe-plan/ (https://www.rydges.com/about-us/)
- `76` `booking_form_candidate` contact_form: https://www.rydges.com/# (https://rydges.com)
- `76` `booking_form_candidate` contact_form: https://www.rydges.com/about-us/# (https://www.rydges.com/about-us/)
- `72` `company_contact_page` contact_link: https://www.rydges.com/cancel/ (https://rydges.com)


## Fetch Errors

- Marlow Hotel Group (https://marlowhotelgroup.com.au): CertificateVerifyError: Failed to perform, curl: (60) SSL: no alternative certificate subject name matches target hostname 'marlowhotelgroup.com.au'. See https://curl.se/libcurl/c/libcurl-errors.html first for more details.
- Function Room &amp; Event Venue Hire South Melbourne — Albion Rooftop &amp; Club (https://albionrooftop.com.au): Timeout: Failed to perform, curl: (28) Connection timed out after 20013 milliseconds. See https://curl.se/libcurl/c/libcurl-errors.html first for more details.

## Notes

- Candidate values must be reviewed before saving to `data/leads.csv` or `data/contacts.csv`.
- Emails and phones can be company-level or person-level; classify them before use.
- LinkedIn URLs are manual review entry points. Do not treat them as verified key-person contact until the person and company fit are confirmed.
- Role snippets are low-confidence hints until a person name/title is verified.
