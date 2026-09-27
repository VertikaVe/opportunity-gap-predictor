from src.skill_gap import get_matched_skills, get_missing_skills, calculate_compatibility_score, get_skill_gap_report


def test_matched_and_missing():
    student = ["Python", "SQL", "Excel"]
    required = ["Python", "SQL", "Power BI"]
    assert get_matched_skills(student, required) == ["python", "sql"]
    assert get_missing_skills(student, required) == ["power bi"]


def test_compatibility_score_bounds():
    assert calculate_compatibility_score(["Python", "SQL"], ["Python", "SQL"]) == 100.0
    assert calculate_compatibility_score(["Java"], ["Python"]) == 0.0
    assert calculate_compatibility_score(["Python"], []) == 0.0


def test_skill_gap_report_includes_preferred_skills():
    report = get_skill_gap_report(["Python", "SQL"], ["Python", "SQL", "Excel"], preferred_skills=["Power BI", "SQL"])
    assert report["matched_preferred_skills"] == ["sql"]
    assert report["missing_preferred_skills"] == ["power bi"]
    assert report["missing_skills"] == ["excel"]
