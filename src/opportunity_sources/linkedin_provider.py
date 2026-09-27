"""
opportunity_sources/linkedin_provider.py
===========================================
Provider interface for LinkedIn Jobs (and, by the same reasoning,
Wellfound, Internshala, Indeed, and other third-party job boards) -
currently UNAVAILABLE, by design.

Why this is not implemented yet
----------------------------------
LinkedIn's job search/listings are not available through a public,
unauthenticated API for this kind of use, and LinkedIn's terms of
service explicitly restrict automated scraping of its site. Building a
scraper against those terms is exactly what this project's own data
honesty rules forbid ("respect website terms, robots rules, API
restrictions and rate limits"). The same reasoning currently applies to
Wellfound, Internshala, and Indeed - each would need its own verified,
permitted integration (an official partner API, if one exists) before
this project shows anything from it as live data.

How to make this real later
------------------------------
If LinkedIn (or Wellfound/Internshala/Indeed) ever offers a partner/API
program this application is approved for, implement `fetch()` to call
that official API using credentials from `.env`, and map results through
`make_opportunity_dict()` - no other module needs to change.
"""

from typing import Dict, List

from src.opportunity_sources.base import OpportunitySource, SourceUnavailable


class LinkedInProvider(OpportunitySource):
    name = "linkedin"
    is_demo = False

    def fetch(self) -> List[Dict]:
        raise SourceUnavailable(
            "LinkedIn Jobs has no public API for this use case, and "
            "scraping LinkedIn is against its terms of service. This "
            "provider (and the same reasoning applies to Wellfound, "
            "Internshala, and Indeed) stays unavailable until an official, "
            "permitted integration exists."
        )
