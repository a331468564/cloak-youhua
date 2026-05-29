"""
RunTimer — 自动记录脚本执行时间 + 跑前/跑后 lead stats，写入 JSON 供报告脚本读取。
"""

import csv
import json
from datetime import datetime
from pathlib import Path

TIMING_FILE = Path("data/.last_run_timing.json")
LEADS_CSV = Path("data/leads.csv")
CONTACTS_CSV = Path("data/contacts.csv")

CONTACT_FIELDS = [
    "email_address", "company_email", "phone_number", "company_phone",
    "company_contact_form_url", "contact_form_url",
    "contact_page_url", "official_contact_page", "company_contact_page",
]


def _load_lead_stats() -> dict:
    """Load lead stats from CSV (same logic as generate_run_report.load_lead_stats)."""
    if not LEADS_CSV.exists():
        return {}
    try:
        with open(LEADS_CSV, "r", encoding="utf-8-sig") as f:
            leads = list(csv.DictReader(f))
    except Exception:
        return {}
    has_any = sum(1 for l in leads if any(l.get(f, "").strip() for f in CONTACT_FIELDS))
    au_leads = [l for l in leads if l.get("country", "").strip() == "Australia"]
    au_no = sum(1 for l in au_leads if not any(l.get(f, "").strip() for f in CONTACT_FIELDS))
    stats = {
        "total_leads": len(leads),
        "has_any_contact": has_any,
        "au_no_contact": au_no,
        "has_email": sum(1 for l in leads if l.get("email_address", "").strip() or l.get("company_email", "").strip()),
        "has_phone": sum(1 for l in leads if l.get("phone_number", "").strip() or l.get("company_phone", "").strip()),
        "has_form": sum(1 for l in leads if l.get("company_contact_form_url", "").strip() or l.get("contact_form_url", "").strip()),
        "has_kc_email": sum(1 for l in leads if l.get("key_contact_email", "").strip()),
        "has_kc_phone": sum(1 for l in leads if l.get("key_contact_phone", "").strip()),
    }
    if CONTACTS_CSV.exists():
        try:
            with open(CONTACTS_CSV, "r", encoding="utf-8-sig") as f:
                stats["total_contacts"] = len(list(csv.DictReader(f)))
        except Exception:
            pass
    return stats


class RunTimer:
    """Context manager that records start/end/duration and writes to TIMING_FILE.

    On enter: captures lead stats as "before" snapshot.
    On exit: captures lead stats as "after" snapshot + timing data.
    """

    def __enter__(self):
        self.start = datetime.now()
        self.before_stats = _load_lead_stats()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = datetime.now()
        self.duration = self.end - self.start
        self.duration_seconds = self.duration.total_seconds()
        after_stats = _load_lead_stats()
        TIMING_FILE.parent.mkdir(parents=True, exist_ok=True)
        TIMING_FILE.write_text(
            json.dumps(
                {
                    "start": self.start.isoformat(timespec="seconds"),
                    "end": self.end.isoformat(timespec="seconds"),
                    "duration_seconds": round(self.duration_seconds, 1),
                    "leads_before": self.before_stats,
                    "leads_after": after_stats,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return False

    @staticmethod
    def load() -> dict | None:
        """Load the last timing record, or None if not available."""
        if not TIMING_FILE.exists():
            return None
        return json.loads(TIMING_FILE.read_text(encoding="utf-8"))
