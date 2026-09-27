from src.profile import StudentProfile
from src.eligibility import evaluate_eligibility, ELIGIBLE, POSSIBLY_ELIGIBLE, NOT_ELIGIBLE


def _opportunity(**overrides):
    base = {
        "degree_allowed": None, "branch_allowed": None,
        "graduation_year_min": None, "graduation_year_max": None,
        "semester_min": None, "semester_max": None,
        "cgpa_min": None, "experience_required": None, "deadline": None,
    }
    base.update(overrides)
    return base


def test_eligible_when_all_criteria_pass():
    student = StudentProfile(degree="B.Tech CSE", branch="CSE", graduation_year=2027, semester=5, cgpa=8.0)
    opp = _opportunity(degree_allowed=["B.Tech"], branch_allowed=["CSE"], graduation_year_min=2026, graduation_year_max=2028, cgpa_min=6.0)
    result = evaluate_eligibility(student, opp)
    assert result.status == ELIGIBLE


def test_not_eligible_when_graduation_year_out_of_range():
    student = StudentProfile(graduation_year=2030)
    opp = _opportunity(graduation_year_min=2025, graduation_year_max=2026)
    result = evaluate_eligibility(student, opp)
    assert result.status == NOT_ELIGIBLE
    assert any("graduation year" in r for r in result.reasons)


def test_not_eligible_when_deadline_passed():
    student = StudentProfile()
    opp = _opportunity(deadline="2020-01-01")
    result = evaluate_eligibility(student, opp)
    assert result.status == NOT_ELIGIBLE


def test_possibly_eligible_when_info_missing():
    student = StudentProfile()  # no cgpa on file
    opp = _opportunity(cgpa_min=7.0)
    result = evaluate_eligibility(student, opp)
    assert result.status == POSSIBLY_ELIGIBLE


def test_eligible_when_nothing_specified():
    student = StudentProfile()
    opp = _opportunity()
    result = evaluate_eligibility(student, opp)
    assert result.status == POSSIBLY_ELIGIBLE
