"""Utility functions for authentication, email handling and domain inference."""

import json
import re
import asyncio
from pathlib import Path
from typing import Optional
import logging

from playwright.async_api import BrowserContext

from config import CONFIG


async def load_cookies(context: BrowserContext, cookie_file: str) -> None:
    """
    Load cookies from a JSON file into the provided browser context.  If the file
    does not exist or cannot be parsed, this function logs a warning and
    continues without loading cookies.
    """
    path = Path(cookie_file)
    if not path.exists():
        logging.warning("Cookie file %s not found; proceeding without cookies.", cookie_file)
        return
    try:
        cookies = json.loads(path.read_text())
        await context.add_cookies(cookies)
        logging.info("Loaded %d cookies from %s", len(cookies), cookie_file)
    except Exception as exc:
        logging.warning("Failed to load cookies: %s", exc)


def validate_email(email: str) -> bool:
    """Return True if the email address appears syntactically valid and is not a generic inbox."""
    blocked_prefixes = ["info", "no-reply", "noreply"]
    local = email.split("@")[0].lower()
    if any(local.startswith(prefix) for prefix in blocked_prefixes):
        return False
    pattern = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    return bool(pattern.match(email))


async def find_company_domain(company_name: str) -> Optional[str]:
    """
    Heuristically generate a domain name from a company name.  This implementation
    simply removes non-alphanumeric characters and appends `.com`.  Replace with
    an API call to a company database for production use.
    """
    if not company_name:
        return None
    slug = re.sub(r"[^A-Za-z0-9]", "", company_name).lower()
    if not slug:
        return None
    return f"{slug}.com"


async def find_work_email(name: str, domain: str) -> Optional[str]:
    """
    Generate plausible professional email patterns from a person's name and domain.
    Real systems should integrate with email enrichment services.  Returns the
    first syntactically valid email pattern.
    """
    if not name or not domain:
        return None
    parts = [p.strip() for p in name.lower().split() if p.strip()]
    if not parts:
        return None
    first, *rest = parts
    last = rest[-1] if rest else ""
    patterns = [
        f"{first}@{domain}",
        f"{first}{last[0] if last else ''}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first[0]}.{last}@{domain}",
    ]
    for email in patterns:
        if validate_email(email):
            return email
    return None
