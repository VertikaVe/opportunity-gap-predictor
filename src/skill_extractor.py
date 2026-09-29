"""
skill_extractor.py

Extract skills from job descriptions.

The extractor distinguishes between:
- required skills
- preferred / bonus skills
- all mentioned skills

It uses explicit section headings when available and avoids
treating every technology mentioned in a job description as required.
"""

import re
from typing import Dict, List

from src.skill_processing import normalize_skill_list


SKILL_VOCABULARY = [
    "python",
    "java",
    "c++",
    "javascript",
    "typescript",
    "react",
    "angular",
    "node.js",
    "node",
    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "redis",
    "rest apis",
    "rest api",
    "graphql",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "git",
    "github",
    "linux",
    "machine learning",
    "deep learning",
    "nlp",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "data science",
    "data analysis",
    "data visualization",
    "pandas",
    "numpy",
    "statistics",
    "artificial intelligence",
    "llm",
    "large language models",
    "generative ai",
    "natural language processing",
    "computer vision",
    "system design",
    "distributed systems",
    "data structures",
    "algorithms",
    "data structures and algorithms",
    "object oriented programming",
    "api development",
    "authentication",
    "authorization",
    "cybersecurity",
    "networking",
    "agile",
    "ci/cd",
    "jenkins",
    "dbt",
    "bigquery",
    "snowflake",
    "fivetran",
    "amplitude",
    "mixpanel",
    "segment",
    "a/b testing",
    "causal inference",
    "accessibility",
    "html",
    "css",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "statsmodels",
    "data science",
]


REQUIRED_HEADINGS = [
    r"required skills",
    r"required skills and experience",
    r"required skills & experience",
    r"required qualifications",
    r"qualifications required",
    r"what you bring",
]


PREFERRED_HEADINGS = [
    r"preferred qualifications",
    r"preferred skills",
    r"preferred experience",
    r"nice to have",
    r"nice-to-have",
    r"bonus qualifications",
    r"bonus points",
    r"bonus",
]


def _contains_skill(text: str, skill: str) -> bool:
    """Check whether a skill occurs as a separate term."""

    if not isinstance(text, str) or not text.strip():
        return False

    normalized_text = text.lower()
    normalized_skill = skill.lower()

    skill_pattern = re.escape(normalized_skill).replace(
        r"\ ",
        r"[\s\-]+"
    )

    pattern = rf"(?<![a-z0-9]){skill_pattern}(?![a-z0-9])"

    return re.search(pattern, normalized_text) is not None


def _extract_from_text(text: str) -> List[str]:
    """Extract known skills from a text section."""

    if not isinstance(text, str) or not text.strip():
        return []

    found = []

    for skill in SKILL_VOCABULARY:
        if _contains_skill(text, skill):
            found.append(skill)

    return normalize_skill_list(found)


def _find_heading_positions(text: str, headings: List[str]) -> List[int]:
    """Find positions of section headings."""

    positions = []
    lower_text = text.lower()

    for heading in headings:
        match = re.search(
            rf"(?m)^\s*{heading}\s*:?\s*$",
            lower_text,
        )

        if match:
            positions.append(match.start())

    return sorted(set(positions))


def _extract_section(text: str, start: int, end_positions: List[int]) -> str:
    """
    Extract text from a section heading until the next recognised
    section heading.
    """

    if start < 0:
        return ""

    end = len(text)

    for position in end_positions:
        if position > start:
            end = position
            break

    return text[start:end]


def _extract_sections(
    text: str,
    headings: List[str],
    all_heading_positions: List[int],
) -> List[str]:
    """Extract all sections matching the supplied heading group."""

    positions = _find_heading_positions(text, headings)

    sections = []

    for position in positions:
        sections.append(
            _extract_section(
                text,
                position,
                all_heading_positions,
            )
        )

    return sections


def extract_job_skills(text: str) -> Dict[str, List[str]]:
    """
    Extract required, preferred and mentioned skills.

    Explicit required sections are treated as required.
    Explicit preferred/bonus sections are treated as preferred.

    Skills appearing only in normal descriptive text are returned
    separately as mentioned_skills and are NOT automatically
    considered required.
    """

    if not isinstance(text, str) or not text.strip():
        return {
            "required_skills": [],
            "preferred_skills": [],
            "mentioned_skills": [],
        }

    all_heading_patterns = REQUIRED_HEADINGS + PREFERRED_HEADINGS

    all_positions = []

    for heading in all_heading_patterns:
        matches = re.finditer(
            rf"(?m)^\s*{heading}\s*:?\s*$",
            text.lower(),
        )

        for match in matches:
            all_positions.append(match.start())

    all_positions = sorted(set(all_positions))

    required_sections = _extract_sections(
        text,
        REQUIRED_HEADINGS,
        all_positions,
    )

    preferred_sections = _extract_sections(
        text,
        PREFERRED_HEADINGS,
        all_positions,
    )

    required_skills = set()

    for section in required_sections:
        required_skills.update(
            _extract_from_text(section)
        )

    preferred_skills = set()

    for section in preferred_sections:
        preferred_skills.update(
            _extract_from_text(section)
        )

    mentioned_skills = set(
        _extract_from_text(text)
    )

    # Skills explicitly required should not also be classified
    # as preferred-only.
    preferred_skills -= required_skills

    # Skills that appear anywhere in the JD but were not classified
    # by an explicit required/preferred section.
    mentioned_only = (
        mentioned_skills
        - required_skills
        - preferred_skills
    )

    return {
        "required_skills": sorted(required_skills),
        "preferred_skills": sorted(preferred_skills),
        "mentioned_skills": sorted(mentioned_only),
    }


def extract_skills_from_text(text: str) -> List[str]:
    """
    Backward-compatible helper.

    Existing code can continue using this function.
    It returns all detected skills.
    """

    result = extract_job_skills(text)

    return normalize_skill_list(
        result["required_skills"]
        + result["preferred_skills"]
        + result["mentioned_skills"]
    )