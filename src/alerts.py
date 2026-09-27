"""
alerts.py
==========
Alert generation and retrieval.

Scope of what's implemented vs. deferred
-------------------------------------------
Two kinds of alerts are GLOBAL (not personal) and are generated for real,
stored in the database, and shown to every visitor:
  - "new_opportunity"  - written by opportunity_manager.sync_all() the
                          moment a genuinely new opportunity is added.
  - "deadline_soon"    - written by opportunity_manager.refresh_statuses()
                          when an opportunity newly crosses into the
                          CLOSING_SOON window.

A third kind is PERSONAL ("this newly matches your profile", "you just
became eligible for X") and would require persisting each student's
profile and their previous match results across visits to detect what
changed - which this project deliberately does NOT do, per its own
privacy rule against unnecessarily persisting resume data. Instead,
`personal_alerts_for_session()` below computes an equivalent view LIVE,
every time it's called, from the student's current in-session profile
against the current opportunity list - functionally similar ("here's
what's newly relevant to you right now"), but recomputed fresh each time
rather than diffed against history. See README.md "Limitations" for this
trade-off stated plainly.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List

from src import config, database
from src.recommendation import compute_match


def global_alerts(limit: int = 50) -> List[Dict]:
    """Return the stored, non-personal alert feed (new opportunities, deadlines)."""
    return database.get_alerts(limit=limit)


def personal_alerts_for_session(student, opportunities: List[Dict]) -> List[Dict]:
    """
    Compute a live, per-session view of what's currently most relevant to
    this student: opportunities they are ELIGIBLE for with a high match
    score, and opportunities with an imminent deadline that they are at
    least POSSIBLY_ELIGIBLE for. Not stored - recomputed on every call.
    """
    alerts = []
    today = date.today()

    for opp in opportunities:
        match = compute_match(student, opp)
        if match["eligibility_status"] == "NOT_ELIGIBLE":
            continue

        if match["match_score"] >= 60:
            alerts.append({
                "type": "good_match",
                "message": f"Strong match ({match['match_score']}%): {opp['role']} @ {opp['company']}",
                "opportunity_id": opp["id"],
            })

        if opp.get("deadline"):
            try:
                deadline = datetime.fromisoformat(opp["deadline"]).date()
                days_left = (deadline - today).days
                if 0 <= days_left <= config.DEADLINE_URGENT_DAYS:
                    alerts.append({
                        "type": "deadline_urgent",
                        "message": f"Only {days_left} day(s) left to apply: {opp['role']} @ {opp['company']}",
                        "opportunity_id": opp["id"],
                    })
                elif config.DEADLINE_URGENT_DAYS < days_left <= config.DEADLINE_SOON_DAYS:
                    alerts.append({
                        "type": "deadline_soon",
                        "message": f"{days_left} days left to apply: {opp['role']} @ {opp['company']}",
                        "opportunity_id": opp["id"],
                    })
            except ValueError:
                pass

        added_at = opp.get("added_at")
        if added_at:
            try:
                added_date = datetime.fromisoformat(added_at).date()
                if (today - added_date) <= timedelta(days=config.NEW_OPPORTUNITY_WINDOW_DAYS):
                    alerts.append({
                        "type": "new_and_relevant",
                        "message": f"New opportunity you may be eligible for: {opp['role']} @ {opp['company']}",
                        "opportunity_id": opp["id"],
                    })
            except ValueError:
                pass

    return alerts
