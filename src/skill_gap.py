"""
skill_gap.py
============
Set-based comparison between a student's skills and an opportunity's
required/preferred skills. See README.md "Skill Matching" for the full
reasoning (mechanical vs. synonym-based normalization, why exact matches
and normalized-only matches are reported separately).
"""

from typing import Dict, Iterable, List

from src.skill_processing import normalize_skill, normalize_skill_list


def get_matched_skills(student_skills: Iterable[str], required_skills: Iterable[str]) -> List[str]:
    student_set = set(normalize_skill_list(student_skills))
    required_set = set(normalize_skill_list(required_skills))
    return sorted(student_set & required_set)


def get_missing_skills(student_skills: Iterable[str], required_skills: Iterable[str]) -> List[str]:
    student_set = set(normalize_skill_list(student_skills))
    required_set = set(normalize_skill_list(required_skills))
    return sorted(required_set - student_set)


def calculate_compatibility_score(student_skills: Iterable[str], required_skills: Iterable[str]) -> float:
    """Percentage (0-100) of required skills the student already has."""
    required_set = set(normalize_skill_list(required_skills))
    if not required_set:
        return 0.0
    matched = set(normalize_skill_list(student_skills)) & required_set
    return round((len(matched) / len(required_set)) * 100, 2)


def _mechanically_normalized(skills: Iterable[str]) -> set:
    return {normalize_skill(s) for s in skills if normalize_skill(s)}


def get_skill_gap_report(
    student_skills: Iterable[str],
    required_skills: Iterable[str],
    preferred_skills: Iterable[str] = (),
) -> Dict:
    """
    Full skill-gap breakdown for one student/opportunity pair, including
    preferred (nice-to-have) skills separately from required ones, since
    an opportunity should never be scored down as heavily for missing a
    "preferred" skill as for missing a "required" one.
    """
    matched_required = get_matched_skills(student_skills, required_skills)
    missing_required = get_missing_skills(student_skills, required_skills)
    matched_preferred = get_matched_skills(student_skills, preferred_skills)
    missing_preferred = get_missing_skills(student_skills, preferred_skills)

    required_score = calculate_compatibility_score(student_skills, required_skills)
    preferred_score = calculate_compatibility_score(student_skills, preferred_skills) if preferred_skills else None

    student_mech = _mechanically_normalized(student_skills)
    required_mech = _mechanically_normalized(required_skills)
    exact_matches = sorted(student_mech & required_mech)
    normalized_only = sorted(set(matched_required) - set(exact_matches))

    total_required = len(set(normalize_skill_list(required_skills)))
    coverage = (len(matched_required) / total_required) if total_required else 0.0

    return {
        "matched_skills": matched_required,
        "missing_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "match_percentage": required_score,
        "preferred_match_percentage": preferred_score,
        "coverage": round(coverage, 4),
        "exact_matches": exact_matches,
        "normalized_only_matches": normalized_only,
    }
