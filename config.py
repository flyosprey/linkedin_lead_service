"""Configuration and logging utilities for the LinkedIn scraping pipeline."""

from __future__ import annotations

import logging
import os
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class Config:
    """
    Centralised configuration for the scraping pipeline.  Adjust these values
    based on your target persona and infrastructure.  Most settings can be
    overridden via environment variables (see run_pipeline for details).
    """

    search_urls: List[str] = field(default_factory=list)
    cookie_file: str = "cookies.json"
    output_csv: str = "enriched_leads.csv"
    headless: bool = False
    proxy_servers: List[str] = field(default_factory=list)
    user_agents: List[str] = field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0",
    ])
    locale: str = "en-US"
    concurrency_profiles: int = 3
    concurrency_enrichment: int = 5
    min_delay: float = 1.0
    max_delay: float = 3.0
    target_keywords: List[str] = field(default_factory=lambda: ["Founder", "CEO", "Head", "Owner", "Co-Founder", "Co‑Founder"])
    allowed_locations: List[str] = field(default_factory=lambda: ["United States"])
    forbidden_company_terms: List[str] = field(default_factory=lambda: ["stealth", "freelance", "self‑employed"])

    def pick_proxy(self) -> Optional[Dict[str, str]]:
        """Return a proxy configuration for Playwright if any proxies are defined."""
        if not self.proxy_servers:
            return None
        return {"server": random.choice(self.proxy_servers)}

    def pick_user_agent(self) -> str:
        """Return a random user agent from the configured list."""
        return random.choice(self.user_agents)


# Global configuration instance (set in pipeline.run_pipeline)
CONFIG: Optional[Config] = None


def init_logging() -> None:
    """Initialise logging to stdout.  The level can be set via LOG_LEVEL env variable."""
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s")
