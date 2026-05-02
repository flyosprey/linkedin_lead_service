"""
Scraping and enrichment routines for LinkedIn leads.  Each function focuses on a
specific aspect: parsing search results, scraping profiles, enrichment, and
exporting.  Sleep calls are inserted between page interactions to mimic human
behaviour.
"""

import asyncio
import random
import logging
from pathlib import Path
from typing import List, Optional

from playwright.async_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from config import CONFIG
from models import RawLead, Profile, EnrichedLead
from helpers import validate_email, find_company_domain, find_work_email
from filters import pre_filter, final_filter


async def parse_search_results(page: Page) -> List[RawLead]:
    """
    Parse a LinkedIn search results page and return a list of RawLead objects.
    Relies on CSS selectors that may need updating when LinkedIn changes its DOM.
    """
    leads: List[RawLead] = []
    await page.wait_for_selector(".reusable-search__result-container", timeout=30000)
    cards = await page.query_selector_all(".reusable-search__result-container")
    for card in cards:
        name_el = await card.query_selector("span[dir='ltr']")
        title_el = await card.query_selector(".entity-result__primary-subtitle")
        link_el = await card.query_selector("a.app-aware-link")
        if not (name_el and title_el and link_el):
            continue
        name = (await name_el.inner_text()).strip()
        title = (await title_el.inner_text()).strip()
        href = await link_el.get_attribute("href")
        profile_url = href.split("?")[0] if href else ""
        leads.append(RawLead(name=name, title=title, profile_url=profile_url))
    return leads


async def parse_profile(page: Page, url: str) -> Optional[Profile]:
    """Scrape a single LinkedIn profile into a Profile instance."""
    try:
        await page.goto(url, timeout=45000)
        await page.wait_for_selector("h1", timeout=20000)
        name_el = await page.query_selector("h1")
        name = (await name_el.inner_text()).strip() if name_el else ""
        title_el = await page.query_selector(".text-body-medium")
        title = (await title_el.inner_text()).strip() if title_el else ""
        company_el = await page.query_selector(".pv-text-details__right-panel ul li span")
        company = (await company_el.inner_text()).strip() if company_el else ""
        location_el = await page.query_selector(".text-body-small.inline")
        location = (await location_el.inner_text()).strip() if location_el else ""
        # Delay to simulate reading time
        assert CONFIG is not None
        await asyncio.sleep(random.uniform(CONFIG.min_delay, CONFIG.max_delay))
        return Profile(name=name, title=title, company=company, location=location, profile_url=url)
    except PlaywrightTimeoutError:
        logging.warning("Timed out reading profile %s", url)
    except Exception as exc:
        logging.warning("Error scraping profile %s: %s", url, exc)
    return None


async def scrape_search_page(context: BrowserContext, search_url: str) -> List[RawLead]:
    """Return a list of pre-filtered leads from a search page."""
    page = await context.new_page()
    try:
        await page.goto(search_url, timeout=60000)
        raw_leads = await parse_search_results(page)
        filtered = [lead for lead in raw_leads if pre_filter(lead)]
        assert CONFIG is not None
        await asyncio.sleep(random.uniform(CONFIG.min_delay, CONFIG.max_delay))
        return filtered
    finally:
        await page.close()


async def scrape_profiles(context: BrowserContext, leads: List[RawLead], concurrency: int) -> List[Profile]:
    """Scrape detailed profiles concurrently and apply the final filter."""
    semaphore = asyncio.Semaphore(concurrency)
    results: List[Profile] = []

    async def worker(raw: RawLead) -> None:
        async with semaphore:
            page = await context.new_page()
            try:
                profile = await parse_profile(page, raw.profile_url)
                if profile and final_filter(profile):
                    results.append(profile)
            finally:
                await page.close()

    await asyncio.gather(*(worker(lead) for lead in leads))
    return results


async def enrich_profiles(profiles: List[Profile], concurrency: int) -> List[EnrichedLead]:
    """Enrich profiles with domain and email concurrently and return valid leads."""
    semaphore = asyncio.Semaphore(concurrency)
    enriched: List[EnrichedLead] = []

    async def worker(profile: Profile) -> None:
        async with semaphore:
            domain = await find_company_domain(profile.company)
            if not domain:
                return
            email = await find_work_email(profile.name, domain)
            if not email or not validate_email(email):
                return
            enriched.append(
                EnrichedLead(
                    name=profile.name,
                    role=profile.title,
                    company=profile.company,
                    email=email,
                    domain=domain,
                    location=profile.location,
                    profile_url=profile.profile_url,
                )
            )

    await asyncio.gather(*(worker(profile) for profile in profiles))
    return enriched


def export_to_csv(leads: List[EnrichedLead], output_path: Path) -> None:
    """Write enriched leads to a CSV file."""
    import csv
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "role", "company", "email", "domain", "location", "profile_url"])
        for lead in leads:
            writer.writerow([
                lead.name,
                lead.role,
                lead.company,
                lead.email,
                lead.domain,
                lead.location,
                lead.profile_url,
            ])
    logging.info("Exported %d leads to %s", len(leads), output_path)
