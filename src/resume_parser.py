"""
resume_parser.py
==================
Best-effort extraction of a StudentProfile from an uploaded resume PDF.

Honesty about what this is
------------------------------
This is a HEURISTIC, regex/keyword-based parser - not a machine-learned
resume-understanding model. Resumes have no standard format, so this
parser:
  - looks for common patterns (email/phone regex, degree/branch keyword
    lists, a CGPA/GPA regex, a "Skills" section header, etc.),
  - always degrades gracefully: any field it can't confidently find is
    left as None/empty rather than guessed,
  - will work better on some resume layouts than others - a heavily
    graphical/columnar resume, or a scanned image PDF with no extractable
    text, will yield little or nothing.

If a stronger LLM-based extractor is ever added, it should be wired in as
an OPTIONAL alternative backend behind the same `parse_resume()`
function signature, per the project's "no paid API required for the
basic MVP" rule.

Privacy
--------
The uploaded PDF's bytes and extracted text are processed only in
memory for the duration of this call and are never written to disk or
the database - only the caller decides what to do with the resulting
StudentProfile (in this project: keep it in the Streamlit session only).
"""

import re
from typing import List, Optional

import pdfplumber

from src.profile import StudentProfile
from src.skill_processing import normalize_skill_list

# A reasonably broad vocabulary of skills to search for in resume text.
# This list intentionally overlaps with the demo opportunities' required
# skills so the matching pipeline has something to work with, but also
# includes many skills not required by any demo posting, since a real
# resume may mention things no demo opportunity asks for.
KNOWN_SKILLS = [
    "Python", "Java", "C", "C++", "JavaScript", "TypeScript", "SQL", "MySQL", "PostgreSQL",
    "MongoDB", "HTML", "CSS", "React", "Angular", "Vue", "Node.js", "Django", "Flask",
    "Spring Boot", "REST APIs", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch",
    "Machine Learning", "Deep Learning", "NLP", "Data Visualization", "Power BI", "Excel",
    "Tableau", "Statistics", "R", "Git", "Docker", "Kubernetes", "AWS", "Azure", "GCP",
    "Linux", "Data Structures", "Algorithms", "OOP", "Figma", "Firebase",
]

DEGREE_KEYWORDS = ["B.Tech", "B.E.", "BE", "BCA", "B.Sc", "BSc", "BBA", "M.Tech", "ME", "MCA", "M.Sc", "MSc", "MBA", "PhD"]
BRANCH_KEYWORDS = [
    "Computer Science", "CSE", "Information Technology", "IT", "Electronics", "ECE",
    "Electrical", "EEE", "Mechanical", "Civil", "AI", "Artificial Intelligence",
    "Data Science", "Statistics", "Economics",
]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s\-]?)?\d{10}")
CGPA_RE = re.compile(r"(?:CGPA|GPA)\s*[:\-]?\s*(\d\.\d{1,2})", re.IGNORECASE)
GRAD_YEAR_RE = re.compile(r"(20[2-3]\d)\s*(?:-|to|–)\s*(20[2-3]\d)")
SINGLE_YEAR_NEAR_GRAD_RE = re.compile(r"(?:graduat\w*|expected)\D{0,15}(20[2-3]\d)", re.IGNORECASE)
SEMESTER_RE = re.compile(r"(\d{1,2})(?:st|nd|rd|th)?\s*semester", re.IGNORECASE)
YEAR_OF_STUDY_RE = re.compile(r"(\d)(?:st|nd|rd|th)?\s*year", re.IGNORECASE)

SECTION_HEADERS = {
    "skills": ["skills", "technical skills", "core competencies"],
    "projects": ["projects", "academic projects"],
    "experience": ["experience", "work experience", "internships"],
    "certifications": ["certifications", "certificates", "licenses"],
}


def extract_text_from_pdf(file) -> str:
    """
    Extract plain text from a PDF given a file path or a file-like object
    (e.g. Streamlit's UploadedFile). Returns "" if no text could be
    extracted (e.g. a scanned/image-only PDF with no text layer).
    """
    text_parts: List[str] = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts)


def _extract_email(text: str) -> Optional[str]:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> Optional[str]:
    match = PHONE_RE.search(text)
    return match.group(0).strip() if match else None


def _extract_name(text: str, email: Optional[str]) -> Optional[str]:
    """
    Heuristic: the name is usually the first non-empty line that isn't an
    email/phone/URL and looks like a short "Title Case" line.
    """
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) > 60:
            continue
        if email and email in line:
            continue
        if EMAIL_RE.search(line) or PHONE_RE.search(line):
            continue
        if any(char.isdigit() for char in line):
            continue
        words = line.split()
        if 1 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
            return line
    return None


def _extract_degree(text: str) -> Optional[str]:
    for keyword in DEGREE_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE):
            # Grab a short surrounding snippet (e.g. "B.Tech Computer Science
            # Engineering") if possible, trimmed back to a whole word so it
            # never ends mid-word.
            match = re.search(rf"({re.escape(keyword)}[\w.\s]{{0,40}})", text, re.IGNORECASE)
            if not match:
                return keyword
            snippet = match.group(1).split("\n")[0].strip()
            # If the snippet was cut off mid-word (no trailing space in the
            # original match window), drop the trailing partial word.
            if len(snippet) == len(match.group(1)) and not text[match.end():match.end() + 1].isspace():
                snippet = snippet.rsplit(" ", 1)[0] if " " in snippet else snippet
            return snippet
    return None


def _extract_branch(text: str) -> Optional[str]:
    for keyword in BRANCH_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE):
            return keyword
    return None


def _extract_graduation_year(text: str) -> Optional[int]:
    match = GRAD_YEAR_RE.search(text)
    if match:
        return int(match.group(2))  # the later year in a range is the graduation year
    match = SINGLE_YEAR_NEAR_GRAD_RE.search(text)
    if match:
        return int(match.group(1))
    return None


def _extract_semester(text: str) -> Optional[int]:
    match = SEMESTER_RE.search(text)
    if match:
        return int(match.group(1))
    match = YEAR_OF_STUDY_RE.search(text)
    if match:
        year_of_study = int(match.group(1))
        if 1 <= year_of_study <= 5:
            return year_of_study * 2  # rough estimate: "3rd year" -> ~semester 6
    return None


def _extract_cgpa(text: str) -> Optional[float]:
    match = CGPA_RE.search(text)
    return float(match.group(1)) if match else None


def _extract_skills(text: str) -> List[str]:
    found = []
    for skill in KNOWN_SKILLS:
        if re.search(rf"\b{re.escape(skill)}\b", text, re.IGNORECASE):
            found.append(skill)
    return normalize_skill_list(found)


def _extract_section(text: str, section: str) -> List[str]:
    """
    Grab lines under a section header (e.g. "PROJECTS") until the next
    recognized header or the end of the text. Best-effort only - resumes
    that don't clearly label sections will yield an empty list here.
    """
    headers = SECTION_HEADERS[section]
    all_headers = [h for headers_list in SECTION_HEADERS.values() for h in headers_list]

    lines = text.splitlines()
    collected = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower().rstrip(":")
        if lower in headers:
            in_section = True
            continue
        if lower in all_headers and lower not in headers:
            in_section = False
            continue
        if in_section and stripped:
            collected.append(stripped)
    return collected[:10]  # cap to avoid pulling in an entire mis-parsed document


def parse_resume(file) -> StudentProfile:
    """
    Parse a resume PDF (path or file-like object) into a StudentProfile.
    Never raises on a resume it can't fully understand - fields it can't
    find are left as None/empty.
    """
    text = extract_text_from_pdf(file)
    if not text.strip():
        return StudentProfile()  # e.g. a scanned/image PDF with no text layer

    email = _extract_email(text)
    return StudentProfile(
        name=_extract_name(text, email),
        email=email,
        phone=_extract_phone(text),
        degree=_extract_degree(text),
        branch=_extract_branch(text),
        graduation_year=_extract_graduation_year(text),
        semester=_extract_semester(text),
        cgpa=_extract_cgpa(text),
        skills=_extract_skills(text),
        projects=_extract_section(text, "projects"),
        experience=_extract_section(text, "experience"),
        certifications=_extract_section(text, "certifications"),
    )
