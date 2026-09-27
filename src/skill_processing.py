"""
skill_processing.py
====================
Skill normalization utilities (mechanical cleanup + explicit synonym
mapping). See README.md "Skill Matching" for the reasoning; this module
is functionally the same approach used in the project's earlier baseline,
carried forward unchanged so prior understanding/tests transfer directly.
"""

import re
from typing import Iterable, List

SKILL_SYNONYMS = {
    "ml": "machine learning",
    "machine-learning": "machine learning",
    "python programming": "python",
    "python3": "python",
    "python 3": "python",
    "nlp": "nlp",
    "natural language processing": "nlp",
    "dl": "deep learning",
    "deep-learning": "deep learning",
    "sql server": "sql",
    "mysql database": "mysql",
    "js": "javascript",
    "reactjs": "react",
    "react.js": "react",
    "tensor flow": "tensorflow",
    "power-bi": "power bi",
    "powerbi": "power bi",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "data viz": "data visualization",
    "oop": "object oriented programming",
    "restful apis": "rest apis",
    "rest api": "rest apis",
    "oa": "online assessment",
    "dsa": "data structures and algorithms",
    "data structures": "data structures and algorithms",
    "algorithms": "data structures and algorithms",
}


def normalize_skill(text: str) -> str:
    """Lowercase, trim, collapse whitespace, strip stray punctuation (keeps hyphens)."""
    if not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s\-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def apply_synonym_mapping(skill: str) -> str:
    return SKILL_SYNONYMS.get(skill, skill)


def normalize_skill_list(skills: Iterable[str]) -> List[str]:
    """Full normalization + synonym mapping, de-duplicated, order-preserving."""
    normalized = []
    for skill in skills:
        cleaned = normalize_skill(skill)
        if not cleaned:
            continue
        normalized.append(apply_synonym_mapping(cleaned))

    seen = set()
    result = []
    for skill in normalized:
        if skill not in seen:
            seen.add(skill)
            result.append(skill)
    return result
