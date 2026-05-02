# LinkedIn Lead Service

This repository contains a Python-based service for scraping and enriching leads from LinkedIn. The service uses Playwright to automate LinkedIn searches, parse profile pages, and collect structured data about potential leads. It includes modules for configuration, data models, helper functions, filtering logic, scraping routines, and a pipeline orchestrator.

## Features

- Generate and execute LinkedIn search queries using Playwright.
- Parse search result pages and extract key fields such as name, title, company, location, and profile URL.
- Fetch individual profile pages only for relevant leads based on pre-filter keywords.
- Enrich profiles with company domains and email addresses using external APIs and heuristics.
- Validate email addresses, remove duplicates, and apply custom filters to retain high-quality leads.
- Rotate proxies and user agents and add randomized delays to mimic human browsing.
- Export validated leads to CSV for further use.

## Project Structure

- `config.py` – central configuration and logging setup, including search queries, proxy lists, user agents, and filter criteria.
- `models.py` – dataclass definitions for `RawLead`, `Profile`, and `EnrichedLead`.
- `helpers.py` – utilities for loading cookies, validating emails, and generating candidate domains and addresses.
- `filters.py` – pre_filter and final_filter functions to narrow results based on job titles, geography, and company terms.
- `scraping.py` – scraping logic for search pages and profile pages, enrichment functions, and CSV export routine.
- `pipeline.py` – entry point that orchestrates the entire scraping and enrichment process using the other modules.

## Prerequisites

- Python 3.9 or newer
- Playwright installed with browsers (run `playwright install` after installation).
- A valid LinkedIn session cookie stored in a `cookies.json` file located in the project root. The cookie is used to authenticate scraping sessions; do not share it publicly.

## Installation

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
playwright install
```

## Usage

Update the configuration in `config.py` with your desired search queries, proxy settings, user agents, and filtering keywords. Ensure you have a `cookies.json` file with your LinkedIn session cookies.

Run the pipeline from the project root:

```bash
python pipeline.py
```

The script will scrape LinkedIn search results, parse relevant profiles, enrich them with additional data, and export the final list of leads to a CSV file.

## Disclaimer

This project is provided for educational purposes only. Scraping LinkedIn or using collected data may violate LinkedIn’s Terms of Service and data privacy laws. Use this code responsibly and ensure compliance with all applicable terms and regulations.
