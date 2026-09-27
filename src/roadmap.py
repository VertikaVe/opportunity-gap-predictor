"""
roadmap.py
==========
Turns a student's prioritized skill gaps (from recommend_skills_to_learn)
into a phased, week-by-week learning roadmap, plus generic-but-relevant
suggestions for projects, OA/interview prep, and resume improvements.

How it works
-------------
1. Rank missing skills by how many opportunities the student could
   realistically apply to require them (reusing
   `recommendation.recommend_skills_to_learn`, which already excludes
   opportunities the student is flatly NOT_ELIGIBLE for).
2. Assign each skill an estimated learning duration from a small lookup
   table (`SKILL_DURATION_DAYS`), falling back to a default for anything
   not in the table.
3. Walk the ranked list, packing skills into week-long phases in
   priority order (highest-demand skill first) until the requested
   roadmap length is reached.

This is a deliberately simple heuristic scheduler, not a curriculum-
design AI - the durations are rough estimates, not measured learning
curves, and the ordering only reflects demand-across-opportunities, not
prerequisite relationships between skills (e.g. it doesn't know that
learning SQL joins requires SQL basics first) - see README.md
"Limitations" for this caveat stated plainly.
"""

from typing import Dict, List

from src.recommendation import recommend_skills_to_learn

SKILL_DURATION_DAYS = {
    "sql": 5,
    "python": 7,
    "excel": 4,
    "power bi": 5,
    "statistics": 6,
    "machine learning": 10,
    "deep learning": 12,
    "nlp": 10,
    "pandas": 4,
    "scikit-learn": 5,
    "data visualization": 4,
    "javascript": 6,
    "react": 6,
    "html": 3,
    "css": 3,
    "java": 8,
    "spring boot": 7,
    "mysql": 4,
    "rest apis": 4,
    "git": 2,
    "docker": 4,
    "c": 6,  # "c++" is normalized to "c" by the current skill cleanup (see skill_processing.py)
}
DEFAULT_DURATION_DAYS = 5


def build_roadmap(student, opportunities: List[Dict], max_weeks: int = 6) -> Dict:
    """
    Build a phased roadmap for `student` based on skill gaps against
    `opportunities`. Returns a dict with `phases` (list of week-labeled
    dicts with a list of skills to learn that week) plus generic-but-
    targeted suggestions for projects, OA prep, and resume improvements.
    """
    ranked_gaps = recommend_skills_to_learn(student, opportunities, top_n=20)

    phases = []
    current_week_skills: List[str] = []
    current_week_days = 0
    week_number = 1

    for item in ranked_gaps:
        skill = item["skill"]
        duration = SKILL_DURATION_DAYS.get(skill, DEFAULT_DURATION_DAYS)

        if current_week_days + duration > 7 and current_week_skills:
            phases.append({
                "week": week_number,
                "skills": current_week_skills,
                "focus": ", ".join(s.title() for s in current_week_skills),
            })
            week_number += 1
            current_week_skills = []
            current_week_days = 0

            if week_number > max_weeks:
                break

        current_week_skills.append(skill)
        current_week_days += duration

    if current_week_skills and week_number <= max_weeks:
        phases.append({
            "week": week_number,
            "skills": current_week_skills,
            "focus": ", ".join(s.title() for s in current_week_skills),
        })

    remaining_weeks = max_weeks - len(phases)
    suggestions = {
        "projects": [
            f"Build a small project that uses {phases[0]['skills'][0].title()}" if phases else
            "Build a project using your current strongest skills to showcase them.",
            "Add the project to your resume and GitHub with a clear README.",
        ],
        "oa_interview_prep": [
            "Practice data-structures-and-algorithms problems relevant to the roles you're targeting.",
            "Review your resume out loud - be ready to explain every project and skill listed.",
        ],
        "resume_improvements": [
            "Quantify project impact where possible (e.g. 'reduced query time by 30%').",
            "Move your most in-demand/matched skills near the top of the skills section.",
        ],
    }

    if remaining_weeks > 0:
        phases.append({
            "week": len(phases) + 1,
            "skills": [],
            "focus": "Apply, build a portfolio project, and prepare for OA/interviews with what you've learned so far.",
        })

    return {"phases": phases, **suggestions}
