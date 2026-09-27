from src.similarity import get_tfidf_similarity


def test_identical_skills_high_similarity():
    skills = ["Python", "SQL", "Pandas"]
    assert get_tfidf_similarity(skills, skills) > 0.99


def test_disjoint_skills_zero_similarity():
    assert get_tfidf_similarity(["Java"], ["R", "Statistics"]) == 0.0


def test_empty_input_returns_zero():
    assert get_tfidf_similarity([], ["Python"]) == 0.0
