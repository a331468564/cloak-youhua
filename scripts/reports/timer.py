"""
RunTimer — 自动记录脚本执行时间 + 跑前/跑后 lead stats，写入 JSON 供报告脚本读取。

用法：
  with RunTimer():          # A/B 共用（向后兼容）
  with RunTimer("a"):       # A区专用 → data/.last_run_timing_a.json
  with RunTimer("b"):       # B区专用 → data/.last_run_timing_b.json
"""

import csv
import json
from datetime import datetime
from pathlib import Path

_BASE_TIMING = Path("data/.last_run_timing")
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
    """Context manager that records start/end/duration and writes to a timing JSON file.

    On enter: captures lead stats as "before" snapshot.
    On exit: captures lead stats as "after" snapshot + timing data.

    Args:
        tag: "a" for A区, "b" for B区, None for shared (backward compatible).
    """

    def __init__(self, tag: str = None):
        suffix = f"_{tag}" if tag else ""
        self.timing_file = Path(f"{_BASE_TIMING}{suffix}.json")

    def __enter__(self):
        self.start = datetime.now()
        self.before_stats = _load_lead_stats()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = datetime.now()
        self.duration = self.end - self.start
        self.duration_seconds = self.duration.total_seconds()
        after_stats = _load_lead_stats()
        self.timing_file.parent.mkdir(parents=True, exist_ok=True)
        self.timing_file.write_text(
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
    def load(tag: str = None) -> dict | None:
        """Load the last timing record, or None if not available.

        Args:
            tag: "a" for A区, "b" for B区, None for shared.
        """
        suffix = f"_{tag}" if tag else ""
        timing_file = Path(f"{_BASE_TIMING}{suffix}.json")
        if not timing_file.exists():
            return None
        return json.loads(timing_file.read_text(encoding="utf-8"))
