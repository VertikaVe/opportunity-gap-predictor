"""
opportunity_sources/base.py
=============================
The provider interface every opportunity source implements, plus shared
helpers (deterministic IDs, the "source unavailable" exception).

What problem this solves
-------------------------
The spec requires supporting many possible sources (Unstop, company
career pages, LinkedIn, Internshala, ...) without hard-coding the rest of
the application to any one of them, and WITHOUT inventing fake data for
sources that can't actually be reached. This file defines the contract:

    class SomeProvider(OpportunitySource):
        def fetch(self) -> List[dict]: ...

`fetch()` either returns a list of opportunity dicts, or raises
`SourceUnavailable` with a human-readable reason. It never returns
invented data pretending to be real.

Only `DemoDataProvider` (see demo_provider.py) currently returns data -
it is clearly labeled `is_demo=True` everywhere so the UI can show
"DEMO DATA" instead of implying these are real live postings. Every other
provider file in this package (unstop_provider.py, etc.) implements this
same interface but currently raises `SourceUnavailable`, documenting
exactly why (no public API, scraping would violate the site's terms,
etc.) - see each file's docstring.

Adding a new real source later means writing one new file that
implements `OpportunitySource.fetch()` and registering it in
`opportunity_manager.py`'s provider list - nothing else needs to change.
"""

import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List


class SourceUnavailable(Exception):
    """
    Raised by a provider's fetch() when it cannot honestly return real
    data (no API access, scraping not permitted, credentials not
    configured, etc.). The opportunity_manager catches this, logs it,
    and moves on without touching the database - it never falls back to
    inventing data.
    """


class OpportunitySource(ABC):
    """Base interface every opportunity provider must implement."""

    #: Short machine-readable name used as the `source` field in the DB
    #: and in update_log rows, e.g. "demo", "unstop", "linkedin".
    name: str = "unknown"

    #: True only for providers that return clearly-labeled sample data,
    #: never for anything claiming to be a real live posting.
    is_demo: bool = False

    @abstractmethod
    def fetch(self) -> List[Dict]:
        """
        Return a list of opportunity dicts (see make_opportunity_dict
        below for the expected shape), or raise SourceUnavailable.
        """
        raise NotImplementedError


def make_opportunity_id(source: str, company: str, role: str) -> str:
    """
    Build a deterministic ID from (source, company, role) so re-fetching
    the same posting always maps to the same database row (an UPDATE)
    instead of creating a duplicate. Cross-source duplicate DETECTION
    (the same real posting appearing on two different sites) is handled
    separately in opportunity_manager.deduplicate(), since that requires
    comparing content across different source-specific IDs.
    """
    key = f"{source}::{company}::{role}".strip().lower()
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def make_opportunity_dict(
    *,
    source: str,
    company: str,
    role: str,
    description: str = "",
    required_skills=None,
    preferred_skills=None,
    degree_allowed=None,
    branch_allowed=None,
    graduation_year_min=None,
    graduation_year_max=None,
    semester_min=None,
    semester_max=None,
    cgpa_min=None,
    experience_required=None,
    location=None,
    work_mode=None,
    stipend=None,
    deadline=None,
    role_type=None,
    source_url=None,
    application_url=None,
    is_demo=False,
) -> Dict:
    """
    Build one opportunity dict in the exact shape database.upsert_opportunity
    expects. Every provider should build its results through this helper
    so the shape stays consistent across sources.
    """
    from datetime import datetime

    now = datetime.utcnow().isoformat()
    return {
        "id": make_opportunity_id(source, company, role),
        "company": company,
        "role": role,
        "description": description,
        "required_skills": required_skills or [],
        "preferred_skills": preferred_skills or [],
        "degree_allowed": degree_allowed,
        "branch_allowed": branch_allowed,
        "graduation_year_min": graduation_year_min,
        "graduation_year_max": graduation_year_max,
        "semester_min": semester_min,
        "semester_max": semester_max,
        "cgpa_min": cgpa_min,
        "experience_required": experience_required,
        "location": location,
        "work_mode": work_mode,
        "stipend": stipend,
        "deadline": deadline,
        "role_type": role_type,
        "source": source,
        "source_url": source_url,
        "application_url": application_url,
        "last_checked": now,
        "added_at": now,
        "status": "UNKNOWN",
        "is_demo": is_demo,
    }
