"""
opportunity_sources/unstop_provider.py
=========================================
Provider interface for Unstop - currently UNAVAILABLE, by design.

Why this is not implemented yet
----------------------------------
Unstop does not offer a public, documented API for third-party
applications to pull listings from. The only way to get data from it
today would be scraping its website, which:
  1. is not confirmed to be permitted under Unstop's terms of service,
  2. would be fragile (breaks whenever their page structure changes),
  3. cannot be verified as "safe/reliable" from inside this project.

Per the project's own data-honesty rule ("if a source does not provide a
usable API/feed or permitted access, do not pretend that we have live
data from it"), this provider therefore raises `SourceUnavailable`
instead of scraping or returning invented listings.

How to make this real later
------------------------------
If Unstop ever publishes an official partner/API program:
  1. Add credentials to `.env` (see `.env.example`).
  2. Implement `fetch()` to call that API and map each result through
     `make_opportunity_dict()` (see base.py) - the rest of the
     application (database, eligibility, matching, UI) needs no changes.
"""

from typing import Dict, List

from src.opportunity_sources.base import OpportunitySource, SourceUnavailable


class UnstopProvider(OpportunitySource):
    name = "unstop"
    is_demo = False

    def fetch(self) -> List[Dict]:
        raise SourceUnavailable(
            "Unstop has no public API for third-party listing access. "
            "Scraping its site is not implemented here because it is not "
            "confirmed to comply with Unstop's terms of service. "
            "This provider will return real data automatically once an "
            "official API/partner integration is available."
        )
