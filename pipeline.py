"""
Entry point for running the LinkedIn scraping pipeline.  This module
coordinates configuration, logging, scraping and enrichment.
"""

import asyncio
import os
import logging
from typing import Set

from playwright.async_api import async_playwright, Browser

import config as cfg
from config import Config
from helpers import load_cookies
from scraping import scrape_search_page, scrape_profiles, enrich_profiles, export_to_csv
from models import RawLead


async def run_pipeline() -> None:
    """Configure and run the end-to-end scraping pipeline."""
    cfg.init_logging()
    # Build configuration and allow environment overrides
    config = Config()
    if not config.search_urls:
        config.search_urls = [
            "https://www.linkedin.com/search/results/people/?keywords=founder%20saas&geoUrn=103644278",
            "https://www.linkedin.com/search/results/people/?keywords=ecommerce%20CEO&geoUrn=103644278",
        ]
    if "HEADLESS" in os.environ:
        value = os.environ["HEADLESS"].lower()
        config.headless = value not in ("0", "false", "no")
    if "PROXY_SERVERS" in os.environ:
        config.proxy_servers = [s.strip() for s in os.environ["PROXY_SERVERS"].split(";") if s.strip()]
    # Set global config for other modules
    cfg.CONFIG = config
    logging.info("Starting pipeline with %d search URLs", len(config.search_urls))
    async with async_playwright() as p:
        proxy_config = config.pick_proxy()
        browser: Browser = await p.chromium.launch(headless=config.headless, proxy=proxy_config)
        context = await browser.new_context(user_agent=config.pick_user_agent(), locale=config.locale)
        await load_cookies(context, config.cookie_file)
        raw_leads: list[RawLead] = []
        seen: Set[str] = set()
        # Scrape search pages sequentially
        for url in config.search_urls:
            logging.info("Processing search page: %s", url)
            leads = await scrape_search_page(context, url)
            logging.info("Found %d pre-filtered leads", len(leads))
            for lead in leads:
                if lead.profile_url not in seen:
                    seen.add(lead.profile_url)
                    raw_leads.append(lead)
        logging.info("Collected %d unique raw leads", len(raw_leads))
        # Scrape detailed profiles
        profiles = await scrape_profiles(context, raw_leads, concurrency=config.concurrency_profiles)
        logging.info("Profiles after final filtering: %d", len(profiles))
        # Enrich profiles
        enriched = await enrich_profiles(profiles, concurrency=config.concurrency_enrichment)
        logging.info("Enriched leads: %d", len(enriched))
        # Export
        export_to_csv(enriched, os.path.abspath(config.output_csv))
        await context.storage_state(path="state.json")
        await browser.close()
    logging.info("Pipeline finished")


if __name__ == "__main__":
    asyncio.run(run_pipeline())