"""
opportunity_manager.py
========================
Coordinates every OpportunitySource provider, syncs their results into
the database, updates statuses (OPEN/CLOSING_SOON/CLOSED/EXPIRED), and
detects likely duplicate postings across sources.

How it works
-------------
1. `sync_all()` calls `.fetch()` on every registered provider.
   - If a provider raises SourceUnavailable, that is logged to
     `update_log` as an "UNAVAILABLE" run and skipped - the database is
     never touched with invented data for that source.
   - If a provider returns data, each opportunity is deduplicated
     against everything fetched so far, then upserted into the database.
2. `refresh_statuses()` recomputes OPEN / CLOSING_SOON / EXPIRED for
   every stored opportunity based on today's date vs. its deadline. This
   is the "automatic update" mechanism described in the spec; in this
   MVP it runs on demand (a button in the UI, or every time the app
   starts) rather than on a background schedule - see README.md
   "Future Improvements" for how to add real scheduling (e.g. a cron job
   calling `python -m src.opportunity_manager`).

Deduplication
---------------
Two opportunities are considered likely duplicates if they normalize to
the same (company, role) pair, even if they come from different sources
with different source-specific IDs. When a duplicate is found, the
opportunities are merged: the entry with the more complete data (more
non-empty fields) is kept, and its `source` field records both sources
so the UI can show "Also listed on: X, Y".
"""

from datetime import date, datetime
from typing import Dict, List

from src import database
from src.opportunity_sources.base import SourceUnavailable
from src.opportunity_sources.demo_provider import DemoDataProvider
from src.opportunity_sources.unstop_provider import UnstopProvider
from src.opportunity_sources.company_career_provider import CompanyCareerProvider
from src.opportunity_sources.linkedin_provider import LinkedInProvider
from src.opportunity_sources.ashby_provider import AshbyProvider
from src.skill_processing import normalize_skill

# Every registered provider. Adding a real source later means adding one
# line here - see each provider's own docstring for what "real" requires.
PROVIDERS = [
    DemoDataProvider(),
    UnstopProvider(),
    CompanyCareerProvider(),
    LinkedInProvider(),
    AshbyProvider("replit"),
]


def _normalize_key(company: str, role: str) -> str:
    return f"{normalize_skill(company)}::{normalize_skill(role)}"


def deduplicate(opportunities: List[Dict]) -> List[Dict]:
    """
    Merge opportunities that share a normalized (company, role) key,
    keeping the record with more populated fields and recording every
    source that listed it.
    """
    merged: Dict[str, Dict] = {}

    def completeness(opp: Dict) -> int:
        return sum(1 for v in opp.values() if v not in (None, "", [], {}))

    for opp in opportunities:
        key = _normalize_key(opp["company"], opp["role"])
        if key not in merged:
            opp = dict(opp)
            opp["_sources"] = {opp["source"]}
            merged[key] = opp
            continue

        existing = merged[key]
        existing_sources = existing.get("_sources", {existing["source"]})
        existing_sources.add(opp["source"])

        if completeness(opp) > completeness(existing):
            opp = dict(opp)
            opp["_sources"] = existing_sources
            merged[key] = opp
        else:
            existing["_sources"] = existing_sources

    results = []
    for opp in merged.values():
        sources = sorted(opp.pop("_sources", {opp["source"]}))
        opp["source"] = ", ".join(sources)
        results.append(opp)
    return results


def sync_all() -> Dict[str, int]:
    """
    Fetch from every provider, deduplicate, and upsert into the database.
    Returns a summary dict: {"added": n, "updated": n, "unavailable_sources": [...]}.
    """
    all_fetched: List[Dict] = []
    unavailable = []

    for provider in PROVIDERS:
        try:
            results = provider.fetch()
            all_fetched.extend(results)
            database.log_update_run(
                source=provider.name, status="SUCCESS",
                message=f"Fetched {len(results)} opportunities.",
            )
        except SourceUnavailable as e:
            unavailable.append({"source": provider.name, "reason": str(e)})
            database.log_update_run(source=provider.name, status="UNAVAILABLE", message=str(e))

    deduped = deduplicate(all_fetched)

    added = updated = 0
    for opp in deduped:
        result = database.upsert_opportunity(opp)
        if result == "added":
            added += 1
            database.add_alert(
                alert_type="new_opportunity",
                message=f"New opportunity added: {opp['role']} @ {opp['company']}",
                opportunity_id=opp["id"],
            )
        else:
            updated += 1

    expired = refresh_statuses()

    return {"added": added, "updated": updated, "expired": expired, "unavailable_sources": unavailable}


def _compute_status(deadline_str: str, days_soon: int = 7) -> str:
    if not deadline_str:
        return "UNKNOWN"
    try:
        deadline = datetime.fromisoformat(deadline_str).date()
    except ValueError:
        return "UNKNOWN"

    today = date.today()
    if deadline < today:
        return "EXPIRED"
    if (deadline - today).days <= days_soon:
        return "CLOSING_SOON"
    return "OPEN"


def refresh_statuses() -> int:
    """
    Recompute status for every opportunity based on today's date. Returns
    the number of opportunities newly marked EXPIRED in this run (used
    for the sync summary and to avoid spamming duplicate alerts).
    """
    expired_count = 0
    for opp in database.get_all_opportunities():
        new_status = _compute_status(opp["deadline"])
        if new_status != opp["status"]:
            if new_status == "EXPIRED" and opp["status"] != "EXPIRED":
                expired_count += 1
            database.update_opportunity_status(opp["id"], new_status)
            if new_status == "CLOSING_SOON":
                database.add_alert(
                    alert_type="deadline_soon",
                    message=f"Deadline approaching for {opp['role']} @ {opp['company']} ({opp['deadline']}).",
                    opportunity_id=opp["id"],
                )
    return expired_count


if __name__ == "__main__":
    database.init_db()
    summary = sync_all()
    print("Sync summary:", summary)
