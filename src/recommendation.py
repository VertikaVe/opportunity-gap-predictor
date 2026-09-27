"""
recommendation.py
==================
Combines skill-gap analysis, TF-IDF similarity, and eligibility into one
transparent match score and a human-readable "why" explanation, plus
ranking/skill-demand utilities. See README.md "Matching Methodology" for
the full reasoning behind the formula and weights (src/config.py).

Design choice: eligibility is NOT baked into the numeric score
------------------------------------------------------------------
The spec asks for a transparent score built from skill coverage +
similarity + eligibility + deadline relevance. Mixing a categorical
eligibility outcome into one blended number tends to hide the most
important fact ("you are not eligible") behind a merely-lower percentage.
Instead, this module keeps skill-based compatibility as its own
transparent 0-100 score, and eligibility as an explicit separate label
with its own reasons (src/eligibility.py) - the UI shows both side by
side ("82% skill match, but NOT ELIGIBLE: <reason>"), which is more
honest than compressing "you can't apply" into a slightly-lower score.
"""

from typing import Dict, List

import pandas as pd

from src import config
from src.eligibility import evaluate_eligibility, ELIGIBLE
from src.skill_gap import get_skill_gap_report
from src.similarity import get_tfidf_similarity


def compute_match(student, opportunity: Dict) -> Dict:
    """
    Full match breakdown for one student/opportunity pair: skill-gap
    report, TF-IDF score, blended skill-match score, eligibility result,
    and a list of plain-language "why" bullet points for the UI.
    """
    student_skills = getattr(student, "skills", [])
    required = opportunity.get("required_skills", [])
    preferred = opportunity.get("preferred_skills", [])

    gap = get_skill_gap_report(student_skills, required, preferred)
    tfidf_score = get_tfidf_similarity(student_skills, required) * 100
    preferred_score = gap["preferred_match_percentage"] or 0.0

    match_score = (
        config.EXACT_WEIGHT * gap["match_percentage"]
        + config.PREFERRED_WEIGHT * preferred_score
        + config.TFIDF_WEIGHT * tfidf_score
    )

    eligibility = evaluate_eligibility(student, opportunity)

    why = []
    n_required = len(set(required)) or 1
    why.append(f"{len(gap['matched_skills'])}/{len(set(gap['matched_skills']) | set(gap['missing_skills'])) or n_required} required skills matched")
    if gap["missing_skills"]:
        why.append(f"Missing required: {', '.join(gap['missing_skills'])}")
    if gap["matched_preferred_skills"]:
        why.append(f"Also has {len(gap['matched_preferred_skills'])} preferred skill(s): {', '.join(gap['matched_preferred_skills'])}")
    why.extend(eligibility.reasons)
    why.extend(eligibility.notes)

    return {
        "opportunity_id": opportunity["id"],
        "company": opportunity["company"],
        "role": opportunity["role"],
        "match_score": round(match_score, 2),
        "matched_skills": gap["matched_skills"],
        "missing_skills": gap["missing_skills"],
        "matched_preferred_skills": gap["matched_preferred_skills"],
        "missing_preferred_skills": gap["missing_preferred_skills"],
        "tfidf_score": round(tfidf_score, 2),
        "eligibility_status": eligibility.status,
        "eligibility_reasons": eligibility.reasons,
        "eligibility_notes": eligibility.notes,
        "why": why,
        "opportunity": opportunity,
    }


def rank_opportunities(student, opportunities: List[Dict], top_n: int = config.DEFAULT_TOP_N) -> List[Dict]:
    """
    Rank opportunities for a student. Eligible/possibly-eligible
    opportunities are ranked above clearly-ineligible ones (regardless of
    skill score), and within each eligibility tier, ranked by match_score
    descending - so the top of the list is always something worth
    actually applying to.
    """
    results = [compute_match(student, opp) for opp in opportunities]

    tier = {ELIGIBLE: 0, "POSSIBLY_ELIGIBLE": 1, "NOT_ELIGIBLE": 2}
    results.sort(key=lambda r: (tier.get(r["eligibility_status"], 3), -r["match_score"]))
    return results[:top_n]


def recommend_skills_to_learn(student, opportunities: List[Dict], top_n: int = config.DEFAULT_TOP_N) -> List[Dict]:
    """
    Rank missing skills by how many opportunities the student is
    ELIGIBLE or POSSIBLY_ELIGIBLE for require them - i.e. skills worth
    learning because they'd unlock opportunities the student could
    actually apply to, not opportunities they're excluded from anyway.
    """
    from src.skill_gap import get_missing_skills

    skill_frequency: Dict[str, int] = {}
    for opp in opportunities:
        eligibility = evaluate_eligibility(student, opp)
        if eligibility.status == "NOT_ELIGIBLE":
            continue
        for skill in get_missing_skills(getattr(student, "skills", []), opp.get("required_skills", [])):
            skill_frequency[skill] = skill_frequency.get(skill, 0) + 1

    ranked = sorted(skill_frequency.items(), key=lambda item: item[1], reverse=True)
    return [{"skill": skill, "opportunity_count": count} for skill, count in ranked[:top_n]]


def top_demanded_skills(opportunities: List[Dict], top_n: int = config.DEFAULT_TOP_N) -> List[Dict]:
    from src.skill_processing import normalize_skill_list

    skill_frequency: Dict[str, int] = {}
    for opp in opportunities:
        for skill in normalize_skill_list(opp.get("required_skills", [])):
            skill_frequency[skill] = skill_frequency.get(skill, 0) + 1
    ranked = sorted(skill_frequency.items(), key=lambda item: item[1], reverse=True)
    return [{"skill": skill, "opportunity_count": count} for skill, count in ranked[:top_n]]
