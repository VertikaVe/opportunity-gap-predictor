"""
eligibility.py
===============
Checks whether a student profile actually qualifies for an opportunity's
stated eligibility criteria - degree, branch, graduation year, semester,
CGPA, and deadline - and always attaches a plain-language reason to the
result, per the project's requirement to "never invent eligibility
requirements" and to say "Not specified" rather than assume.

Three possible outcomes
-------------------------
- ELIGIBLE          : every criterion the opportunity actually states is
                       satisfied by the student's profile.
- NOT_ELIGIBLE      : at least one stated criterion is clearly violated
                       (e.g. opportunity requires 2025-2026 graduates,
                       student graduates in 2029), OR the deadline has
                       passed.
- POSSIBLY_ELIGIBLE : no criterion is clearly violated, but at least one
                       criterion the opportunity states could not be
                       checked because the student's profile is missing
                       that field (e.g. CGPA wasn't found on the resume).

What is intentionally NOT auto-decided
------------------------------------------
"Experience required" is reported as an informational note only, never
used to fail or pass a candidate, because reliably extracting "years of
relevant experience" from an arbitrary resume is not something this
project's simple parser can do accurately - see resume_parser.py's
docstring. Location/work-mode preferences are shown to the student but
are a personal preference, not an eligibility gate.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Optional

ELIGIBLE = "ELIGIBLE"
POSSIBLY_ELIGIBLE = "POSSIBLY_ELIGIBLE"
NOT_ELIGIBLE = "NOT_ELIGIBLE"


@dataclass
class EligibilityResult:
    status: str
    reasons: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)  # informational, non-deciding


def _contains_ci(haystack: Optional[str], needle: str) -> bool:
    if not haystack:
        return False
    return needle.strip().lower() in haystack.strip().lower()


def _check_degree(student_degree: Optional[str], allowed: Optional[List[str]]) -> Optional[tuple]:
    if not allowed:
        return None  # not specified -> not checked
    if not student_degree:
        return ("possibly", f"Opportunity requires one of {allowed}, but no degree was found in your profile.")
    match = any(_contains_ci(student_degree, deg) for deg in allowed)
    if match:
        return ("pass", f"Your degree ({student_degree}) matches the required degree(s).")
    return ("fail", f"This opportunity requires one of {allowed}; your profile shows '{student_degree}'.")


def _check_branch(student_branch: Optional[str], allowed: Optional[List[str]]) -> Optional[tuple]:
    if not allowed:
        return None
    if not student_branch:
        return ("possibly", f"Opportunity requires branch in {allowed}, but no branch was found in your profile.")
    match = any(_contains_ci(student_branch, br) for br in allowed)
    if match:
        return ("pass", f"Your branch ({student_branch}) matches the required branch(es).")
    return ("fail", f"This opportunity requires branch in {allowed}; your profile shows '{student_branch}'.")


def _check_range(value: Optional[float], min_v: Optional[float], max_v: Optional[float], label: str) -> Optional[tuple]:
    if min_v is None and max_v is None:
        return None
    if value is None:
        bound_text = f"{min_v}-{max_v}" if (min_v and max_v) else str(min_v or max_v)
        return ("possibly", f"Opportunity requires {label} in range {bound_text}, but this wasn't found in your profile.")
    if min_v is not None and value < min_v:
        return ("fail", f"This opportunity requires {label} >= {min_v}; your profile shows {value}.")
    if max_v is not None and value > max_v:
        return ("fail", f"This opportunity requires {label} <= {max_v}; your profile shows {value}.")
    return ("pass", f"Your {label} ({value}) is within the required range.")


def _check_cgpa(student_cgpa: Optional[float], min_cgpa: Optional[float]) -> Optional[tuple]:
    if min_cgpa is None:
        return None
    if student_cgpa is None:
        return ("possibly", f"Opportunity requires CGPA >= {min_cgpa}, but no CGPA was found in your profile.")
    if student_cgpa < min_cgpa:
        return ("fail", f"This opportunity requires CGPA >= {min_cgpa}; your profile shows {student_cgpa}.")
    return ("pass", f"Your CGPA ({student_cgpa}) meets the required minimum ({min_cgpa}).")


def _check_deadline(deadline_str: Optional[str]) -> Optional[tuple]:
    if not deadline_str:
        return None
    try:
        deadline = datetime.fromisoformat(deadline_str).date()
    except ValueError:
        return None
    if deadline < date.today():
        return ("fail", f"This opportunity's deadline ({deadline_str}) has already passed.")
    return None


def evaluate_eligibility(student, opportunity: Dict) -> EligibilityResult:
    """
    `student` is a StudentProfile (or any object with the same attribute
    names). `opportunity` is a dict as returned by database.get_opportunity
    / get_all_opportunities.
    """
    checks = [
        _check_degree(getattr(student, "degree", None), opportunity.get("degree_allowed")),
        _check_branch(getattr(student, "branch", None), opportunity.get("branch_allowed")),
        _check_range(
            getattr(student, "graduation_year", None),
            opportunity.get("graduation_year_min"), opportunity.get("graduation_year_max"),
            "graduation year",
        ),
        _check_range(
            getattr(student, "semester", None),
            opportunity.get("semester_min"), opportunity.get("semester_max"),
            "semester",
        ),
        _check_cgpa(getattr(student, "cgpa", None), opportunity.get("cgpa_min")),
        _check_deadline(opportunity.get("deadline")),
    ]

    fail_reasons = []
    possibly_reasons = []
    pass_reasons = []

    for check in checks:
        if check is None:
            continue
        kind, message = check
        if kind == "fail":
            fail_reasons.append(message)
        elif kind == "possibly":
            possibly_reasons.append(message)
        else:
            pass_reasons.append(message)

    notes = []
    if opportunity.get("experience_required"):
        notes.append(
            f"Experience requirement stated: '{opportunity['experience_required']}'. "
            f"This is not automatically verified - please review it yourself."
        )
    if not any([opportunity.get("degree_allowed"), opportunity.get("branch_allowed"),
                opportunity.get("graduation_year_min"), opportunity.get("graduation_year_max"),
                opportunity.get("semester_min"), opportunity.get("semester_max"),
                opportunity.get("cgpa_min")]):
        notes.append("This listing does not specify degree/branch/year/semester/CGPA requirements.")

    if fail_reasons:
        return EligibilityResult(status=NOT_ELIGIBLE, reasons=fail_reasons, notes=notes)
    if possibly_reasons:
        return EligibilityResult(status=POSSIBLY_ELIGIBLE, reasons=possibly_reasons, notes=notes)
    if pass_reasons:
        return EligibilityResult(status=ELIGIBLE, reasons=pass_reasons, notes=notes)
    return EligibilityResult(
        status=POSSIBLY_ELIGIBLE,
        reasons=["This listing does not specify eligibility criteria that could be checked."],
        notes=notes,
    )
