"""
similarity.py
=============
TF-IDF + cosine similarity between a student's skill profile and an
opportunity's requirements - see README.md "Skill Matching" for the full
explanation of why TF-IDF/cosine similarity is used and what it adds
beyond exact/normalized matching.
"""

from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.skill_processing import normalize_skill_list


def _skills_to_document(skills: Iterable[str]) -> str:
    normalized = normalize_skill_list(skills)
    return " ".join(skill.replace(" ", "_").replace("-", "_") for skill in normalized)


def get_tfidf_similarity(student_skills: Iterable[str], required_skills: Iterable[str]) -> float:
    """TF-IDF + cosine similarity between two skill lists, in [0.0, 1.0]."""
    student_doc = _skills_to_document(student_skills)
    required_doc = _skills_to_document(required_skills)

    if not student_doc or not required_doc:
        return 0.0

    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([student_doc, required_doc])
    except ValueError:
        return 0.0

    similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
    return round(float(similarity), 4)
