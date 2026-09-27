"""
opportunity_sources/company_career_provider.py
==================================================
Provider interface for official company career pages (Google Careers,
Microsoft Careers, Amazon Jobs, JPMorgan Careers, NVIDIA Careers, etc.) -
currently UNAVAILABLE, by design.

Why this is not implemented yet
----------------------------------
Some large companies do expose structured career-page data (e.g. via a
careers-site JSON endpoint or an ATS like Greenhouse/Lever that offers a
public job-board API), but this varies company by company, changes
without notice, and would need to be verified and implemented
individually and carefully to stay within each site's terms of use. None
of that has been implemented or verified yet, so this provider is
intentionally a stub rather than a scraper returning unverified data.

How to make this real later
------------------------------
Turn this into a small registry of per-company fetchers, each checking
for a real, confirmed-public endpoint before returning anything:

    class CompanyCareerProvider(OpportunitySource):
        name = "company_career_pages"
        COMPANY_FETCHERS = {
            "google": _fetch_google_careers,     # implement once verified
            "microsoft": _fetch_microsoft_careers,
        }

Each per-company fetcher should map results through
`make_opportunity_dict()` from base.py, exactly like DemoDataProvider
does, so the rest of the app needs no changes.
"""

from typing import Dict, List

from src.opportunity_sources.base import OpportunitySource, SourceUnavailable


class CompanyCareerProvider(OpportunitySource):
    name = "company_career_pages"
    is_demo = False

    def fetch(self) -> List[Dict]:
        raise SourceUnavailable(
            "No verified, permitted public endpoint has been configured yet "
            "for any company career page (Google/Microsoft/Amazon/JPMorgan/"
            "NVIDIA/etc.). Add a per-company fetcher here once a real, "
            "confirmed-public data source is identified for that company."
        )
