"""
Workflow Checker Module

This module enforces the workflow rules defined in config/workflow_rules.json.
Import this module in extraction scripts to automatically apply thresholds.

Usage:
    from workflow_checker import WorkflowChecker

    checker = WorkflowChecker()
    if checker.should_stop_company_search(lead_id, pages_searched, found_items):
        print("Stopping company search")
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "workflow_rules.json"


class WorkflowChecker:
    def __init__(self, config_path=None):
        self.config_path = config_path or CONFIG_PATH
        self.config = self._load_config()
        self._existing_data = None

    def _load_config(self):
        """Load workflow rules from config file."""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def load_existing_data(self, data_dir=None):
        """Load existing contacts and leads data."""
        data_dir = data_dir or PROJECT_ROOT / "data"
        self._existing_data = {
            'emails': set(),
            'phones': set(),
            'contact_names': set(),
            'lead_ids_with_contact': set(),
            'lead_ids_with_kp': set(),
        }

        # Load contacts.csv
        contacts_path = data_dir / "contacts.csv"
        if contacts_path.exists():
            try:
                import csv
                with open(contacts_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        lead_id = row.get('lead_id', '')
                        email = (row.get('email') or '').strip().lower()
                        phone = self._normalize_phone(row.get('phone') or '')
                        name = (row.get('contact_name') or '').strip()

                        if email:
                            self._existing_data['emails'].add(email)
                        if phone:
                            self._existing_data['phones'].add(phone)
                        if name and lead_id:
                            self._existing_data['contact_names'].add((lead_id, name.lower()))
                        if lead_id:
                            self._existing_data['lead_ids_with_contact'].add(lead_id)
            except Exception:
                pass

        # Load leads.csv
        leads_path = data_dir / "leads.csv"
        if leads_path.exists():
            try:
                import csv
                with open(leads_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        lead_id = row.get('lead_id', '')

                        # Check various email fields
                        for field in ['email_address', 'company_email', 'key_contact_email']:
                            email = (row.get(field) or '').strip().lower()
                            if email:
                                self._existing_data['emails'].add(email)

                        # Check various phone fields
                        for field in ['phone_number', 'company_phone', 'key_contact_phone']:
                            phone = self._normalize_phone(row.get(field) or '')
                            if phone:
                                self._existing_data['phones'].add(phone)

                        # Check key contact
                        key_name = (row.get('key_contact_name') or '').strip()
                        if key_name and lead_id:
                            self._existing_data['contact_names'].add((lead_id, key_name.lower()))
                            self._existing_data['lead_ids_with_kp'].add(lead_id)

                        # Check contact person
                        contact_person = (row.get('contact_person') or '').strip()
                        if contact_person and lead_id:
                            self._existing_data['contact_names'].add((lead_id, contact_person.lower()))
            except Exception:
                pass

        return self._existing_data

    def _normalize_phone(self, phone):
        """Normalize phone number to digits only."""
        import re
        return re.sub(r'\D', '', phone or '')

    def should_skip_lead(self, lead_id):
        """Check if lead should be skipped entirely."""
        if not self._existing_data:
            return False

        # Skip if already has key contact
        if lead_id in self._existing_data['lead_ids_with_kp']:
            return True

        # Skip if already has contact
        if lead_id in self._existing_data['lead_ids_with_contact']:
            return True

        return False

    def should_stop_company_search(self, lead_id, pages_searched, found_items):
        """
        Check if company info search should stop.

        Args:
            lead_id: The lead ID
            pages_searched: Number of pages already searched
            found_items: Dict with keys 'contact_page', 'email', 'phone', 'linkedin'

        Returns:
            tuple: (should_stop: bool, reason: str)
        """
        thresholds = self.config.get('thresholds', {}).get('company_info', {})

        # Check stop conditions
        if found_items.get('contact_page'):
            return True, "found_contact_page"
        if found_items.get('email'):
            return True, "found_email"
        if found_items.get('phone'):
            return True, "found_phone"
        if found_items.get('linkedin'):
            return True, "found_linkedin_company"

        # Check max pages
        max_pages = thresholds.get('max_pages_to_search', 3)
        if pages_searched >= max_pages:
            return True, "max_pages_reached"

        return False, ""

    def should_start_kp_search(self, lead_id, company_info_complete, has_team_page):
        """
        Check if key person search should start.

        Returns:
            tuple: (should_start: bool, reason: str)
        """
        if not self._existing_data:
            return True, "no_existing_data"

        # Skip if already has key contact
        if lead_id in self._existing_data['lead_ids_with_kp']:
            return False, "already_has_kp"

        # Skip if already has contact
        if lead_id in self._existing_data['lead_ids_with_contact']:
            return False, "already_has_contact"

        # Only start if company info is complete
        if not company_info_complete:
            return False, "company_info_incomplete"

        # Prefer searching if has team page
        if has_team_page:
            return True, "has_team_page"

        return True, "kp_search_allowed"

    def should_abandon_kp_search(self, start_time, pages_searched, unhelpful_pages, found_kp_name):
        """
        Check if key person search should be abandoned.

        Returns:
            tuple: (should_abandon: bool, reason: str)
        """
        thresholds = self.config.get('thresholds', {}).get('key_person_search', {})

        # Check time limit
        max_minutes = thresholds.get('max_time_minutes', 5)
        if start_time:
            elapsed = datetime.now() - start_time
            if elapsed > timedelta(minutes=max_minutes):
                return True, "timeout_reached"

        # Check page limit
        max_pages = thresholds.get('max_pages_to_search', 3)
        if pages_searched >= max_pages:
            return True, "max_pages_reached"

        # Check unhelpful page ratio
        max_ratio = thresholds.get('max_unhelpful_page_ratio', 0.7)
        if pages_searched > 0 and (unhelpful_pages / pages_searched) > max_ratio:
            return True, "too_many_unhelpful_pages"

        return False, ""

    def is_duplicate(self, lead_id, candidate_type, value):
        """Check if candidate already exists in database."""
        if not self._existing_data:
            return False

        if candidate_type == 'email':
            return value.lower() in self._existing_data['emails']

        if candidate_type == 'phone':
            phone_norm = self._normalize_phone(value)
            return phone_norm in self._existing_data['phones']

        if candidate_type == 'key_person_name':
            return (lead_id, value.lower()) in self._existing_data['contact_names']

        return False

    def get_review_priority(self, candidate_type, score):
        """Get review priority for a candidate."""
        priorities = self.config.get('review_priority', [])
        for p in priorities:
            if p['type'] == candidate_type:
                score_range = p.get('score_range', [0, 999])
                if score_range[0] <= score <= score_range[1]:
                    return p.get('priority', 99)
        return 99  # Low priority if not matched


# Singleton instance for easy import
checker = WorkflowChecker()


def should_stop_company_search(lead_id, pages_searched, found_items):
    """Module-level function for easy import."""
    return checker.should_stop_company_search(lead_id, pages_searched, found_items)


def should_start_kp_search(lead_id, company_info_complete, has_team_page):
    """Module-level function for easy import."""
    return checker.should_start_kp_search(lead_id, company_info_complete, has_team_page)


def should_abandon_kp_search(start_time, pages_searched, unhelpful_pages, found_kp_name=False):
    """Module-level function for easy import."""
    return checker.should_abandon_kp_search(start_time, pages_searched, unhelpful_pages, found_kp_name)


def is_duplicate(lead_id, candidate_type, value):
    """Module-level function for easy import."""
    return checker.is_duplicate(lead_id, candidate_type, value)
