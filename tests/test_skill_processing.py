from src.skill_processing import normalize_skill, normalize_skill_list


def test_normalize_skill_lowercases_and_trims():
    assert normalize_skill("  Python  ") == "python"
    assert normalize_skill("PYTHON") == "python"


def test_synonym_mapping_maps_known_variants():
    assert normalize_skill_list(["ML"]) == ["machine learning"]


def test_does_not_merge_unrelated_skills():
    result = normalize_skill_list(["Java", "JavaScript"])
    assert "java" in result and "javascript" in result
    assert result.count("java") == 1
