import argparse
import csv
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urlunparse

from scrapling.fetchers import DynamicFetcher, Fetcher, StealthyFetcher
from urllib.parse import unquote

# Import workflow checker for automatic rule enforcement
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))  # Add scripts directory to path
from workflow_checker import checker as workflow_checker


SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # Go up from scripts/extraction to project root
REPORTS = PROJECT_ROOT / "reports"
DATA = PROJECT_ROOT / "data"

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
# Binary file extensions to skip
BINARY_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico', '.pdf', '.zip', '.doc', '.docx', '.xls', '.xlsx'}


def load_existing_data():
    """Load existing contacts and leads data to avoid duplicates."""
    existing = {
        'emails': set(),
        'phones': set(),
        'contact_names': set(),  # (lead_id, name) pairs
        'contact_emails': set(),  # (lead_id, email) pairs
        'contact_phones': set(),  # (lead_id, phone) pairs
    }

    # Load contacts.csv
    contacts_path = DATA / "contacts.csv"
    if contacts_path.exists():
        try:
            for row in read_csv(str(contacts_path)):
                lead_id = row.get('lead_id', '')
                email = (row.get('email') or '').strip().lower()
                phone = normalized_phone(row.get('phone') or '')
                name = (row.get('contact_name') or '').strip()

                if email:
                    existing['emails'].add(email)
                    if lead_id:
                        existing['contact_emails'].add((lead_id, email))
                if phone:
                    existing['phones'].add(phone)
                    if lead_id:
                        existing['contact_phones'].add((lead_id, phone))
                if name and lead_id:
                    existing['contact_names'].add((lead_id, name.lower()))
        except Exception:
            pass

    # Load leads.csv - extract existing contact info
    leads_path = DATA / "leads.csv"
    if leads_path.exists():
        try:
            for row in read_csv(str(leads_path)):
                lead_id = row.get('lead_id', '')
                email = (row.get('email_address') or '').strip().lower()
                phone = normalized_phone(row.get('phone_number') or '')
                name = (row.get('contact_person') or '').strip()

                if email:
                    existing['emails'].add(email)
                    if lead_id:
                        existing['contact_emails'].add((lead_id, email))
                if phone:
                    existing['phones'].add(phone)
                    if lead_id:
                        existing['contact_phones'].add((lead_id, phone))
                if name and lead_id:
                    existing['contact_names'].add((lead_id, name.lower()))

                # Also check key contact fields
                key_email = (row.get('key_contact_email') or '').strip().lower()
                key_phone = normalized_phone(row.get('key_contact_phone') or '')
                key_name = (row.get('key_contact_name') or '').strip()

                if key_email:
                    existing['emails'].add(key_email)
                    if lead_id:
                        existing['contact_emails'].add((lead_id, key_email))
                if key_phone:
                    existing['phones'].add(key_phone)
                    if lead_id:
                        existing['contact_phones'].add((lead_id, key_phone))
                if key_name and lead_id:
                    existing['contact_names'].add((lead_id, key_name.lower()))

                # Company email and phone
                company_email = (row.get('company_email') or '').strip().lower()
                company_phone = normalized_phone(row.get('company_phone') or '')
                if company_email:
                    existing['emails'].add(company_email)
                if company_phone:
                    existing['phones'].add(company_phone)
        except Exception:
            pass

    return existing


def is_duplicate_candidate(lead_id, candidate_type, value, existing_data):
    """Check if a candidate already exists in the database."""
    if not existing_data:
        return False

    normalized_value = normalized_candidate_value(candidate_type, value)

    if candidate_type == 'email':
        email_lower = normalized_value.lower()
        # Check if this exact email already exists for this lead
        if (lead_id, email_lower) in existing_data['contact_emails']:
            return True
        # Check if email exists globally (might be from a different lead but same company)
        if email_lower in existing_data['emails']:
            return True

    elif candidate_type == 'phone':
        phone_norm = normalized_phone(normalized_value)
        if phone_norm and len(phone_norm) >= 8:
            if (lead_id, phone_norm) in existing_data['contact_phones']:
                return True
            if phone_norm in existing_data['phones']:
                return True

    elif candidate_type == 'key_person_name':
        name_lower = normalized_value.lower()
        if (lead_id, name_lower) in existing_data['contact_names']:
            return True

    return False


PHONE_RE = re.compile(
    r"(?:"
    r"(?:\+?61[\s().-]*(?:0)?[2378][\s().-]*\d{4}[\s().-]*\d{4})|"
    r"(?:\(?0[2378]\)?[\s().-]*\d{4}[\s().-]*\d{4})|"
    r"(?:\+?61[\s().-]*(?:0)?4\d{2}[\s().-]*\d{3}[\s().-]*\d{3})|"
    r"(?:04\d{2}[\s().-]*\d{3}[\s().-]*\d{3})|"
    r"(?:(?:1300|1800)[\s().-]*\d{3}[\s().-]*\d{3})"
    r")"
)

LINK_HINTS = {
    "contact_form_link": ["contact form", "enquiry form", "inquiry form", "request a quote"],
    "contact_link": ["contact", "enquiry", "enquiries", "inquiry", "quote", "book", "events", "functions"],
    "team_link": ["team", "people", "about", "leadership", "humans", "management"],
    "supplier_link": ["supplier", "procurement", "trade", "partner"],
}

ROLE_HINTS = [
    # Actual job titles — used for both role_context and key_person_name extraction
    "owner",
    "founder",
    "co-founder",
    "director",
    "managing director",
    "chief executive",
    "ceo",
    "operations",
    "procurement",
    "purchasing",
    "food and beverage",
    "f&b",
    "culinary",
    "events",
    "projects",
    "general manager",
    # Section headers — used ONLY for role_context snippets, NOT for name extraction
    # (they cause too many false positives when used in the name regex)
    "leadership",
    "management",
    "team",
    "people",
    "staff",
    "crew",
]

# Role hints that are valid for person name extraction (excludes section headers)
_ROLE_HINTS_FOR_NAMES = [
    "owner",
    "founder",
    "co-founder",
    "director",
    "managing director",
    "chief executive",
    "ceo",
    "operations",
    "procurement",
    "purchasing",
    "food and beverage",
    "f&b",
    "culinary",
    "events",
    "projects",
    "general manager",
]

# Sort roles by length (longest first) to match multi-word roles before single-word ones
_SORTED_ROLE_HINTS = sorted(_ROLE_HINTS_FOR_NAMES, key=len, reverse=True)

# Pattern for person names near role words (e.g., "John Smith, Director" or "Director: John Smith" or "John Smith CEO")
# Use non-greedy matching for name to avoid capturing part of multi-word roles
# Name part uses [^\S\n] to not span across newlines within the name
# But allow newlines between name and role (using \s+)
# Name part is case-sensitive (must start with uppercase), role part is case-insensitive
PERSON_NAME_NEAR_ROLE_RE = re.compile(
    r"([A-Z][a-z]+(?:[^\S\n]+[A-Z][a-z]+){1,2}?)\s+(?i:" + "|".join(re.escape(r) for r in _SORTED_ROLE_HINTS) + r")"
)

TYPE_PRIORITY = {
    "email": 100,
    "key_person_linkedin_url": 94,
    "phone": 90,
    "contact_form": 88,
    "contact_form_link": 86,
    "key_person_name": 85,
    "team_link": 76,
    "company_linkedin_url": 70,
    "contact_link": 68,
    "supplier_link": 62,
    "role_context": 50,
    "linkedin_search_url": 45,
    "fetch_status": 5,
}

EMAIL_LOW_VALUE_PREFIXES = (
    "careers",
    "jobs",
    "hr",
    "privacy",
    "media",
    "marketing",
    "noreply",
    "no-reply",
)

EMAIL_DEPARTMENT_EXACT = {
    "accounts.payable",
    "accounts.receivable",
    "admin",
    "media.enquiries",
}

EMAIL_DEPARTMENT_PREFIXES = (
    "accounts",
    "events",
    "functions",
    "sales",
    "enquiries",
    "enquiry",
    "hello",
    "info",
    "procurement",
    "reservations",
    "bookings",
)

def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def normalize_url(value):
    raw = (value or "").strip()
    if not raw:
        return ""
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw


def canonical_url(value):
    raw = normalize_url(value)
    if not raw:
        return ""
    parsed = urlparse(raw)
    netloc = parsed.netloc.lower().removeprefix("www.")
    path = re.sub(r"/+$", "", parsed.path or "/")
    return urlunparse((parsed.scheme.lower() or "https", netloc, path, "", "", ""))


def same_domain(base_url, candidate_url):
    base = urlparse(base_url).netloc.lower().removeprefix("www.")
    candidate = urlparse(candidate_url).netloc.lower().removeprefix("www.")
    return bool(base and candidate and (base == candidate or candidate.endswith("." + base)))


def is_noise_link(url):
    lowered = (url or "").lower()
    return "/cdn-cgi/l/email-protection" in lowered


def is_binary_url(url):
    """Check if URL points to a binary/image file."""
    lowered = (url or "").lower()
    return any(lowered.endswith(ext) for ext in BINARY_EXTENSIONS)


def decode_email(email):
    """Decode URL-encoded email addresses."""
    decoded = unquote(email)
    # Re-validate after decoding
    if EMAIL_RE.match(decoded):
        return decoded.lower()
    return email.lower()


def extract_person_names(text):
    """Extract person names found near role words.

    Uses pattern: [Capitalized Words] + [space] + [role_word]
    Then filters through multiple layers to reduce false positives.
    """
    names = []

    # ---- Blacklist: words that should NEVER appear in a person name ----
    _BLACKLIST_WORDS = {
        # Common English function words
        'the', 'and', 'for', 'with', 'our', 'your', 'an', 'of', 'in', 'on', 'at',
        'to', 'by', 'from', 'through', 'or', 'a', 're', 'f',
        # UI / navigation
        'menu', 'open', 'close', 'skip', 'content', 'home', 'page', 'sign',
        'subscribe', 'newsletter', 'latest', 'news', 'articles', 'resources',
        'read', 'more', 'click', 'here', 'learn', 'find', 'out', 'get', 'touch',
        'contact', 'us', 'about', 'book', 'now', 'back', 'today', 'enquire',
        'gallery', 'log', 'cart', 'items', 'account',
        # Hospitality / business terms
        'hotel', 'restaurant', 'group', 'pty', 'ltd', 'hotels', 'restaurants',
        'venues', 'accommodation', 'spa', 'meetings', 'events', 'weddings',
        'conferences', 'functions', 'catering', 'hospitality', 'management',
        'leadership', 'team', 'people', 'staff', 'crew', 'personnel',
        'operations', 'procurement', 'purchasing', 'culinary', 'beverage',
        'asset', 'assets', 'fund', 'funds', 'wealth', 'credit', 'equity',
        'property', 'properties', 'portfolio', 'investors', 'investment',
        'advisory', 'board', 'company', 'companies', 'services', 'service',
        # Business descriptors
        'business', 'practices', 'respect', 'community', 'culture', 'integrity',
        'passion', 'excellence', 'dedication', 'innovative', 'customer',
        'satisfaction', 'values', 'focus', 'quality', 'food', 'dining',
        'experience', 'brand', 'premium', 'professional', 'specialists',
        # Navigation / section headers
        'destinations', 'story', 'careers', 'privacy', 'sustainability',
        'awards', 'media', 'subscribe', 'enquiry', 'enquiries',
        # Common place/region words in AU hospitality
        'australia', 'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide',
        'cairns', 'byron', 'gold', 'coast', 'queensland', 'victoria',
        'south', 'north', 'east', 'west', 'central', 'regional',
        # Country / region names that appear in navigation menus
        'hong', 'kong', 'indonesia', 'zealand', 'australia', 'kuta', 'bali',
        'japan', 'china', 'india', 'korea', 'singapore', 'thailand',
        # Business / brand names from false positives
        'coconut', 'bowl', 'cafe', 'bar', 'grill', 'bistro', 'pub', 'tavern',
        'lounge', 'kitchen', 'eatery', 'diner', 'bakery', 'pizzeria',
        'explore', 'art', 'scroll', 'discover', 'featured', 'spotlight',
        'highlight', 'showcase', 'gallery', 'studio', 'workshop', 'lab',
        'hub', 'space', 'place', 'room', 'house', 'shed', 'yard', 'park',
        # Number words that look like names (e.g., "Eleven Barrack Watermans")
        'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
        'nine', 'ten', 'eleven', 'twelve', 'first', 'second', 'third',
        # Indigenous acknowledgment terms
        'wurundjeri', 'woi', 'wurrung', 'whadjuk', 'nyoongar', 'kulin',
        'jagera', 'turrbal', 'aboriginal', 'torres', 'strait', 'islander',
        'traditional', 'owners', 'custodians', 'peoples', 'country', 'lands',
        'waters', 'acknowledges', 'pays', 'respect',
        # Business structure words
        'pty', 'ltd', 'limited', 'group', 'holdings', 'enterprises',
        'international', 'global', 'pacific', 'asia', 'portfolio',
        # Article / blog title words
        'building', 'stronger', 'through', 'inclusion', 'cultural', 'diversity',
        'week', 'operator', 'improves', 'motel', 'operations', 'aren',
        'more', 'motels', 'being', 'built', 'right', 'how', 'why',
        # Company name fragments from false positives
        'blanco', 'horner', 'white', 'top', 'trilogy', 'spinifex',
        'brave', 'statement', 'heavens', 'capella', 'aurora',
        'lancemore', 'ovolo', 'crystalbrook', 'meriton',
        # Event / package terms
        'elopement', 'package', 'corporate', 'private', 'celebrations',
        'conference', 'venue', 'hire', 'bundle', 'locks', 'love',
        'bio', 'packaging', 'hour', 'delivery', 'notice', 'buffets',
        'stations', 'canapes', 'curated', 'packages',
        # Navigation menu items
        'unmissable', 'live', 'featured', 'weekly', 'specials', 'happenings',
        'menus', 'order', 'online', 'pick', 'gift', 'cards', 'vouchers',
        'whats', 'whats-on', 'whatsnew',
        # Other noise
        'sample', 'logo', 'what', 'say', 'blogs', 'sustainable', 'cleaning',
        'starts', 'small', 'changes', 'recruit', 'global', 'staffing',
        'subsidiary', 'expansion', 'services', 'short', 'term', 'labour',
        'hire', 'reach', 'alliance', 'college', 'education', 'marion',
        'leadwell', 'resorts', 'causeway', 'paua',
    }

    # Section header words that can appear before person names (e.g., "Leadership Jayantha Warnakula CEO")
    _SECTION_HEADERS = {
        'leadership', 'management', 'team', 'people', 'staff', 'crew',
        'group', 'board', 'directors', 'executives', 'founders',
    }

    for match in PERSON_NAME_NEAR_ROLE_RE.finditer(text):
        name = match.group(1)
        if not name or len(name) <= 3 or len(name) >= 50:
            continue

        # Must start with uppercase letter
        if not name[0].isupper():
            continue

        words = name.split()

        # Strip section header prefix (e.g., "Leadership Jayantha Warnakula" -> "Jayantha Warnakula")
        if len(words) >= 3 and words[0].lower() in _SECTION_HEADERS:
            words = words[1:]
            name = ' '.join(words)

        # Strip section header suffix (e.g., "Shane Gross Group" -> "Shane Gross")
        if len(words) >= 3 and words[-1].lower() in _SECTION_HEADERS:
            words = words[:-1]
            name = ' '.join(words)

        # Must have 2-3 words (first + last [+ middle])
        if len(words) < 2 or len(words) > 3:
            continue

        # Each word must start with uppercase (proper noun pattern)
        if not all(w[0].isupper() for w in words if len(w) > 1):
            continue

        # No word should be in the blacklist
        if any(w.lower() in _BLACKLIST_WORDS for w in words):
            continue

        # No word should be all-uppercase (likely an acronym, not a name)
        if any(w.isupper() and len(w) > 2 for w in words):
            continue

        # No word should contain digits
        if any(c.isdigit() for w in words for c in w):
            continue

        # Reject if name looks like a phrase (all words are common English)
        # Heuristic: if 2+ words are very short (< 3 chars each), likely not a name
        if sum(1 for w in words if len(w) < 3) >= 2:
            continue

        # Strip job title prefixes if present (e.g., "Coordinator Calek Alshowaiheen" -> "Calek Alshowaiheen")
        cleaned_name = _strip_title_prefix(name)
        names.append(cleaned_name.strip())

    return list(set(names))


# Job title prefixes to strip from person names
_TITLE_PREFIXES = [
    'coordinator', 'manager', 'director', 'executive', 'officer', 'chef',
    'supervisor', 'lead', 'head', 'senior', 'junior', 'assistant', 'associate',
    'principal', 'chief', 'vice', 'deputy', 'president', 'chairman', 'chairwoman',
]


def _strip_title_prefix(name):
    """Remove job title prefixes from person names.

    Examples:
        "Coordinator Calek Alshowaiheen" -> "Calek Alshowaiheen"
        "Manager John Smith" -> "John Smith"
        "Paul Salter" -> "Paul Salter" (no prefix, unchanged)
    """
    words = name.split()
    if len(words) < 3:
        return name  # Can't have a prefix with only 2 words

    # Check if first word is a known title prefix
    if words[0].lower() in _TITLE_PREFIXES:
        return ' '.join(words[1:])

    return name


def clean_value(value):
    return " ".join((value or "").split()).strip()


def normalized_phone(value):
    return re.sub(r"\D", "", value or "")


def normalized_candidate_value(candidate_type, value):
    cleaned = clean_value(value)
    if candidate_type in {
        "contact_link",
        "contact_form_link",
        "team_link",
        "supplier_link",
        "contact_form",
        "key_person_linkedin_url",
        "company_linkedin_url",
        "linkedin_search_url",
    }:
        return canonical_url(cleaned)
    if candidate_type == "email":
        return cleaned.lower()
    if candidate_type == "phone":
        return normalized_phone(cleaned)
    if candidate_type == "key_person_name":
        return cleaned.title()  # Normalize to Title Case
    if candidate_type == "role_context":
        return cleaned.lower()
    return cleaned.lower()


def candidate_key(lead, candidate_type, value):
    if candidate_type == "fetch_status":
        return (
            lead.get("lead_id", ""),
            candidate_type,
            canonical_url(value),
        )
    return (
        lead.get("lead_id", ""),
        candidate_type,
        normalized_candidate_value(candidate_type, value),
    )


def email_review_bucket(email):
    local = email.split("@", 1)[0].lower()
    if local in EMAIL_DEPARTMENT_EXACT:
        return "department_or_company_email"
    if any(local.startswith(prefix) for prefix in EMAIL_LOW_VALUE_PREFIXES):
        return "low_value_company_email"
    if any(local.startswith(prefix) for prefix in EMAIL_DEPARTMENT_PREFIXES):
        return "department_or_company_email"
    if "." in local or "_" in local:
        return "possible_person_email"
    return "company_email"


def review_bucket(candidate_type, value, context):
    lowered = f"{value} {context}".lower()
    if candidate_type == "email":
        return email_review_bucket(value)
    if candidate_type == "phone":
        return "phone_candidate"
    if candidate_type == "key_person_linkedin_url":
        return "possible_key_person_linkedin"
    if candidate_type == "company_linkedin_url":
        return "company_linkedin"
    if candidate_type == "linkedin_search_url":
        return "manual_linkedin_search"
    if candidate_type == "contact_form":
        if "booking_form" in lowered:
            return "booking_form_candidate"
        return "official_form_candidate"
    if candidate_type == "contact_form_link":
        return "official_form_link_candidate"
    if candidate_type == "team_link":
        return "team_or_about_page"
    if candidate_type == "contact_link":
        if "event" in lowered or "function" in lowered:
            return "events_or_functions_contact"
        return "company_contact_page"
    if candidate_type == "supplier_link":
        return "supplier_or_procurement_page"
    if candidate_type == "role_context":
        return "kp_context_hint"
    if candidate_type == "key_person_name":
        return "possible_key_person"
    return "technical_status"


def priority_score(candidate_type, value, context, confidence):
    score = TYPE_PRIORITY.get(candidate_type, 0)
    bucket = review_bucket(candidate_type, value, context)
    if confidence == "High":
        score += 8
    elif confidence == "Medium":
        score += 4
    if bucket == "possible_person_email":
        score += 12
    elif bucket == "possible_key_person_linkedin":
        score += 10
    elif bucket in {"department_or_company_email", "official_form_candidate", "official_form_link_candidate"}:
        score += 6
    elif bucket == "booking_form_candidate":
        score -= 20
    elif bucket == "low_value_company_email":
        score -= 60
    elif bucket == "team_or_about_page":
        score += 8
    elif bucket == "kp_context_hint" and any(role in context.lower() for role in ("owner", "founder", "director", "manager")):
        score += 10
    return max(score, 0)


def int_value(value, default=999999):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def sort_key(row):
    return (
        int_value(row.get("queue_rank")),
        -int_value(row.get("priority_score"), 0),
        row.get("review_bucket", ""),
        row.get("candidate_type", ""),
        row.get("candidate_value", "").lower(),
    )


def top_review_key(row):
    return (
        -int_value(row.get("priority_score"), 0),
        int_value(row.get("queue_rank")),
        row.get("review_bucket", ""),
        row.get("candidate_type", ""),
        row.get("candidate_value", "").lower(),
    )


def context_for(text, value, width=90):
    if not text or not value:
        return ""
    idx = text.lower().find(value.lower())
    if idx < 0:
        return ""
    start = max(0, idx - width)
    end = min(len(text), idx + len(value) + width)
    return clean_value(text[start:end])


def looks_like_valid_phone(phone, page_text):
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 8 or len(digits) > 13:
        return False
    cleaned = clean_value(phone)
    if re.match(r"^\d{4}\s+1[38]00", cleaned):
        return False
    if len(digits) >= 11 and "1800" in digits and not digits.startswith(("61", "1800")):
        return False
    context = context_for(page_text, phone, width=14)
    if context and digits not in re.sub(r"\D", "", context):
        return False
    return True


def form_bucket(form_evidence):
    lowered = form_evidence.lower()
    if any(hint in lowered for hint in ("booking", "check availability", "select destination", "select guests", "rooms")):
        return "booking_form"
    if any(hint in lowered for hint in ("contact", "enquiry", "inquiry", "message", "phone", "event", "function", "quote", "collaboration", "consultation")):
        return "contact_form"
    return ""


def google_search_url(query):
    query = clean_value(query)
    if not query:
        return ""
    return "https://www.google.com/search?q=" + quote_plus(query)


def linkedin_candidate_type(url):
    lowered = url.lower()
    if "linkedin.com/in/" in lowered:
        return "key_person_linkedin_url"
    if "linkedin.com/company/" in lowered or "linkedin.com/school/" in lowered:
        return "company_linkedin_url"
    if "linkedin.com/" in lowered:
        return "key_person_linkedin_url"
    return ""


def add_candidate(rows, seen, lead, source_url, candidate_type, value, context, confidence, recommendation, existing_data=None):
    value = clean_value(value)
    if not value:
        return

    # Check if this candidate already exists in the database using workflow checker
    lead_id = lead.get("lead_id", "")
    if existing_data and workflow_checker.is_duplicate(lead_id, candidate_type, value):
        return  # Skip duplicate

    key = candidate_key(lead, candidate_type, value)
    if key in seen:
        row = rows[seen[key]]
        sources = [source for source in row.get("additional_source_urls", "").split(" | ") if source]
        if source_url != row["source_url"] and source_url not in sources:
            sources.append(source_url)
        row["additional_source_urls"] = " | ".join(sources[:6])
        row["source_count"] = str(int(row.get("source_count") or "1") + 1)
        if len(clean_value(context)) > len(row.get("candidate_context", "")):
            row["candidate_context"] = clean_value(context)[:500]
        return
    score = priority_score(candidate_type, value, context, confidence)
    seen[key] = len(rows)
    rows.append({
        "priority_score": str(score),
        "review_bucket": review_bucket(candidate_type, value, context),
        "queue_rank": lead.get("queue_rank", ""),
        "lead_id": lead.get("lead_id", ""),
        "company_name": lead.get("company_name", ""),
        "source_url": source_url,
        "source_count": "1",
        "additional_source_urls": "",
        "candidate_type": candidate_type,
        "candidate_value": value,
        "candidate_context": clean_value(context)[:500],
        "confidence_suggestion": confidence,
        "save_recommendation": recommendation,
    })


def fetch_page(url, fetcher_mode):
    if fetcher_mode == "dynamic":
        return DynamicFetcher.fetch(url, headless=True, timeout=30000)
    if fetcher_mode == "stealth":
        return StealthyFetcher.fetch(url, headless=True, timeout=30000)
    return Fetcher.get(url, timeout=20, retries=1)


def extract_from_page(lead, url, rows, seen, fetcher_mode, existing_data=None):
    page = fetch_page(url, fetcher_mode)
    status = getattr(page, "status", "")
    text = page.get_all_text(separator=" ") if hasattr(page, "get_all_text") else page.text
    text = clean_value(text)

    add_candidate(
        rows,
        seen,
        lead,
        url,
        "fetch_status",
        url,
        getattr(page, "reason", "") or "",
        "High" if str(status).startswith("2") else "Low",
        f"Fetch status: {status}. Use only if page fetched successfully.",
        existing_data,
    )

    for email in sorted(set(EMAIL_RE.findall(text))):
        # Decode URL-encoded emails
        decoded_email = decode_email(email)
        add_candidate(
            rows,
            seen,
            lead,
            url,
            "email",
            decoded_email,
            context_for(text, email),
            "High",
            "Review whether this is company, department, or person email before saving.",
            existing_data,
        )

    for phone in sorted(set(PHONE_RE.findall(text))):
        if not looks_like_valid_phone(phone, text):
            continue
        add_candidate(
            rows,
            seen,
            lead,
            url,
            "phone",
            phone,
            context_for(text, phone),
            "Medium",
            "Review whether this is company or person phone before saving.",
            existing_data,
        )

    discovered_links = []
    for element in page.css("form"):
        action = element.attrib.get("action", "")
        method = element.attrib.get("method", "")
        form_url = page.urljoin(action) if action else url
        form_text = clean_value(element.get_all_text(separator=" ") if hasattr(element, "get_all_text") else element.text)
        form_evidence = f"{action} {method} {form_text}".lower()
        bucket = form_bucket(form_evidence)
        if same_domain(url, form_url) and bucket:
            discovered_links.append(form_url)
            add_candidate(
                rows,
                seen,
                lead,
                url,
                "contact_form",
                form_url,
                f"{bucket} form method={method or 'unknown'} action={action or 'current page'} {form_text}",
                "High",
                "Official page contains a form; save as company_contact_form_url only if it is a contact/enquiry form, not only a booking widget.",
                existing_data,
            )

    for element in page.css("a"):
        href = element.attrib.get("href", "")
        if not href or href.startswith(("mailto:", "tel:")):
            if href.startswith("mailto:"):
                add_candidate(rows, seen, lead, url, "email", href.replace("mailto:", "").split("?")[0], element.text, "High", "Mailto link; save with source/confidence note and review again before outreach.", existing_data)
            if href.startswith("tel:"):
                add_candidate(rows, seen, lead, url, "phone", href.replace("tel:", ""), element.text, "High", "Tel link; save with source/confidence note and review again before outreach.", existing_data)
            continue
        full_url = page.urljoin(href)
        if is_noise_link(full_url) or is_binary_url(full_url):
            continue
        linkedin_type = linkedin_candidate_type(full_url)
        if linkedin_type:
            add_candidate(
                rows,
                seen,
                lead,
                url,
                linkedin_type,
                full_url,
                element.text or href,
                "Medium" if linkedin_type == "key_person_linkedin_url" else "Low",
                "Use as a manual LinkedIn review URL; do not treat as verified direct contact until person/company fit is confirmed.",
                existing_data,
            )
            continue
        if not same_domain(url, full_url):
            continue
        label = clean_value(element.text or href).lower()
        combined = f"{label} {href}".lower()
        for candidate_type, hints in LINK_HINTS.items():
            if any(hint in combined for hint in hints):
                discovered_links.append(full_url)
                add_candidate(
                    rows,
                    seen,
                    lead,
                    url,
                    candidate_type,
                    full_url,
                    element.text or href,
                    "Medium",
                    "Review linked page for contact/form/KP details.",
                    existing_data,
                )
                break

    lowered = text.lower()
    role_snippets = []
    for role in ROLE_HINTS:
        idx = lowered.find(role)
        if idx >= 0:
            snippet = clean_value(text[max(0, idx - 120): min(len(text), idx + 180)])
            role_snippets.append((role, snippet))
            add_candidate(
                rows,
                seen,
                lead,
                url,
                "role_context",
                role,
                snippet,
                "Low",
                "Use as a page-level KP hint; confirm person name/title before saving.",
                existing_data,
            )

    # Extract person names near role words — from both full text and role_context snippets
    # Snippets are cleaner (single-line, trimmed) so they catch names the full text misses
    person_names = set(extract_person_names(text))
    for role, snippet in role_snippets:
        for name in extract_person_names(snippet):
            person_names.add(name)
    for name in person_names:
        # Find the role associated with this name
        name_idx = text.find(name)
        if name_idx >= 0:
            context = clean_value(text[max(0, name_idx - 50): min(len(text), name_idx + len(name) + 100)])
            # Check if any role word is in the context
            role_found = next((r for r in ROLE_HINTS if r in context.lower()), "unknown")
            add_candidate(
                rows,
                seen,
                lead,
                url,
                "key_person_name",
                name,
                f"{role_found}: {context}",
                "Medium",
                f"Person name found near '{role_found}' role. Verify person/company fit before saving to contacts.",
                existing_data,
            )

    unique_links = {}
    for link in discovered_links:
        unique_links.setdefault(canonical_url(link), link)
    return [unique_links[key] for key in sorted(unique_links)]


def add_lead_level_candidates(lead, rows, seen, existing_data=None):
    query = lead.get("public_linkedin_query", "")
    search_url = google_search_url(query)
    if search_url:
        add_candidate(
            rows,
            seen,
            lead,
            "queue_public_linkedin_query",
            "linkedin_search_url",
            search_url,
            query,
            "Low",
            "Manual search URL for public LinkedIn result review; save only a matched personal/company URL with confidence notes.",
            existing_data,
        )


def write_markdown(path, rows, errors, input_path, skip, limit, follow_links, fetcher_mode):
    counts = Counter(row["candidate_type"] for row in rows)
    bucket_counts = Counter(row["review_bucket"] for row in rows)
    top_rows = sorted(rows, key=top_review_key)[:15]
    lines = [
        "# Public Contact Candidate Extraction Test",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Scope",
        "",
        f"- Input queue: `{input_path}`",
        f"- Skip: {skip}",
        f"- Limit: {limit}",
        f"- Follow links per lead: {follow_links}",
        f"- Tool: Scrapling `{fetcher_mode}` mode",
        "- Output type: candidate evidence only; no direct writes to data CSV files",
        "",
        "## Candidate Counts",
        "",
    ]
    for key, value in counts.most_common():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Review Buckets", ""])
    for key, value in bucket_counts.most_common():
        lines.append(f"- `{key}`: {value}")
    if top_rows:
        lines.extend(["", "## Top Review Candidates", ""])
        for row in top_rows:
            lines.append(
                f"- {row['lead_id']} `{row['priority_score']}` `{row['review_bucket']}` "
                f"{row['candidate_type']}: {row['candidate_value']} ({row['source_url']})"
            )
    if rows:
        lines.extend(["", "## Lead Review Summary", ""])
        lead_rows = {}
        for row in rows:
            lead_rows.setdefault((row["queue_rank"], row["lead_id"], row["company_name"]), []).append(row)
        for (queue_rank, lead_id, company_name), grouped_rows in sorted(
            lead_rows.items(),
            key=lambda item: int_value(item[0][0]),
        ):
            lines.append(f"### {queue_rank}. {company_name} ({lead_id})")
            for row in sorted(grouped_rows, key=top_review_key)[:5]:
                lines.append(
                    f"- `{row['priority_score']}` `{row['review_bucket']}` "
                    f"{row['candidate_type']}: {row['candidate_value']} ({row['source_url']})"
                )
            lines.append("")
    if errors:
        lines.extend(["", "## Fetch Errors", ""])
        for error in errors:
            lines.append(f"- {error}")
    lines.extend([
        "",
        "## Notes",
        "",
        "- Candidate values must be reviewed before saving to `data/leads.csv` or `data/contacts.csv`.",
        "- Emails and phones can be company-level or person-level; classify them before use.",
        "- LinkedIn URLs are manual review entry points. Do not treat them as verified key-person contact until the person and company fit are confirmed.",
        "- Role snippets are low-confidence hints until a person name/title is verified.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Extract public contact candidates from queued official websites.")
    parser.add_argument("--input", default="reports/au-form-kp-candidate-queue-20260512-continue.csv")
    parser.add_argument("--skip", type=int, default=0, help="Number of input queue rows to skip before applying --limit.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--follow-links", type=int, default=0, help="Number of discovered same-domain links to fetch per lead.")
    parser.add_argument("--fetcher", choices=["static", "dynamic", "stealth"], default="static")
    parser.add_argument("--output-prefix", default="")
    parser.add_argument("--skip-existing", action="store_true", default=True, help="Skip candidates that already exist in data files.")
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    prefix = Path(args.output_prefix) if args.output_prefix else REPORTS / f"au-public-contact-candidates-{ts}"
    rows = []
    errors = []
    seen = {}

    # Load existing data to avoid duplicates using workflow checker
    existing_data = None
    if args.skip_existing:
        existing_data = workflow_checker.load_existing_data()
        print(f"Loaded existing data: {len(existing_data['emails'])} emails, {len(existing_data['phones'])} phones, {len(existing_data['contact_names'])} contact names")

    input_rows = read_csv(args.input)
    if args.skip < 0:
        raise SystemExit("--skip must be zero or greater")
    for lead in input_rows[args.skip:args.skip + args.limit]:
        add_lead_level_candidates(lead, rows, seen, existing_data)
        url = normalize_url(lead.get("website"))
        if not url:
            continue
        try:
            links = extract_from_page(lead, url, rows, seen, args.fetcher, existing_data)
            for link in links[:args.follow_links]:
                time.sleep(args.delay)
                try:
                    extract_from_page(lead, link, rows, seen, args.fetcher, existing_data)
                except Exception as exc:
                    errors.append(f"{lead.get('company_name')} ({link}): {exc.__class__.__name__}: {exc}")
        except Exception as exc:
            errors.append(f"{lead.get('company_name')} ({url}): {exc.__class__.__name__}: {exc}")
        time.sleep(args.delay)

    rows = sorted(rows, key=sort_key)
    fields = [
        "priority_score",
        "review_bucket",
        "queue_rank",
        "lead_id",
        "company_name",
        "source_url",
        "source_count",
        "additional_source_urls",
        "candidate_type",
        "candidate_value",
        "candidate_context",
        "confidence_suggestion",
        "save_recommendation",
    ]
    write_csv(prefix.with_suffix(".csv"), rows, fields)
    write_markdown(prefix.with_suffix(".md"), rows, errors, args.input, args.skip, args.limit, args.follow_links, args.fetcher)
    print(f"Wrote {len(rows)} candidates to {prefix.with_suffix('.csv')} and {prefix.with_suffix('.md')}")
    if errors:
        print(f"Errors: {len(errors)}")


if __name__ == "__main__":
    main()
