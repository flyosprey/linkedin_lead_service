"""Filtering functions for LinkedIn leads and profiles."""

from typing import Optional
from models import RawLead, Profile
from config import CONFIG


def pre_filter(raw_lead: RawLead) -> bool:
    """Return True if the lead's title matches one of the configured keywords."""
    assert CONFIG is not None, "CONFIG must be initialised"
    title_lower = raw_lead.title.lower()
    return any(keyword.lower() in title_lower for keyword in CONFIG.target_keywords)


def final_filter(profile: Profile) -> bool:
    """Return True if the profile matches allowed locations and excludes forbidden terms."""
    assert CONFIG is not None, "CONFIG must be initialised"
    if not profile.location:
        return False
    if not any(loc.lower() in profile.location.lower() for loc in CONFIG.allowed_locations):
        return False
    company_lower = profile.company.lower() if profile.company else ""
    if any(term in company_lower for term in CONFIG.forbidden_company_terms):
        return False
    return True
