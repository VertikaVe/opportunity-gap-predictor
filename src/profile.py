"""
profile.py
==========
The StudentProfile schema - a plain dataclass, not a database model,
because (per the project's own privacy rule) a student's parsed resume
data is kept only in the current session, never persisted.

Any field can be None/empty - resumes vary wildly in format and content,
and the parser (resume_parser.py) is explicitly built to degrade
gracefully rather than assume a field exists.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class StudentProfile:
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    college: Optional[str] = None
    degree: Optional[str] = None
    branch: Optional[str] = None
    graduation_year: Optional[int] = None
    semester: Optional[int] = None
    cgpa: Optional[float] = None
    skills: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    experience: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def is_empty(self) -> bool:
        """True if parsing found essentially nothing usable."""
        return not self.skills and not self.name and not self.email


def manual_profile(
    name: str,
    skills: List[str],
    degree: Optional[str] = None,
    branch: Optional[str] = None,
    graduation_year: Optional[int] = None,
    semester: Optional[int] = None,
    cgpa: Optional[float] = None,
) -> StudentProfile:
    """Build a StudentProfile from manual form input (no PDF involved)."""
    return StudentProfile(
        name=name, skills=skills, degree=degree, branch=branch,
        graduation_year=graduation_year, semester=semester, cgpa=cgpa,
    )
