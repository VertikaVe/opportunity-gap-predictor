from src.opportunity_manager import deduplicate, _compute_status
from datetime import date, timedelta


def test_deduplicate_merges_same_company_and_role_across_sources():
    opportunities = [
        {"id": "a1", "company": "Acme", "role": "Intern", "source": "unstop", "description": ""},
        {"id": "b1", "company": "acme", "role": "intern", "source": "linkedin", "description": "Full description here"},
    ]
    result = deduplicate(opportunities)
    assert len(result) == 1
    assert "unstop" in result[0]["source"] and "linkedin" in result[0]["source"]


def test_deduplicate_keeps_distinct_roles_separate():
    opportunities = [
        {"id": "a1", "company": "Acme", "role": "Backend Intern", "source": "demo", "description": ""},
        {"id": "a2", "company": "Acme", "role": "Frontend Intern", "source": "demo", "description": ""},
    ]
    result = deduplicate(opportunities)
    assert len(result) == 2


def test_compute_status_expired_for_past_deadline():
    past = (date.today() - timedelta(days=1)).isoformat()
    assert _compute_status(past) == "EXPIRED"


def test_compute_status_closing_soon_within_window():
    soon = (date.today() + timedelta(days=3)).isoformat()
    assert _compute_status(soon) == "CLOSING_SOON"


def test_compute_status_open_for_far_deadline():
    far = (date.today() + timedelta(days=60)).isoformat()
    assert _compute_status(far) == "OPEN"


def test_compute_status_unknown_when_no_deadline():
    assert _compute_status(None) == "UNKNOWN"
