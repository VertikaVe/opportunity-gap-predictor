from pathlib import Path

from src.resume_parser import parse_resume

FIXTURE = Path(__file__).parent / "fixtures" / "sample_resume.pdf"


def test_parse_resume_extracts_email_and_name():
    profile = parse_resume(str(FIXTURE))
    assert profile.email == "ananya.rao@example.com"
    assert profile.name == "Ananya Rao"


def test_parse_resume_extracts_skills():
    profile = parse_resume(str(FIXTURE))
    assert "python" in profile.skills
    assert "sql" in profile.skills


def test_parse_resume_extracts_graduation_year_and_semester():
    profile = parse_resume(str(FIXTURE))
    assert profile.graduation_year == 2027
    assert profile.semester == 5


def test_parse_resume_extracts_cgpa():
    profile = parse_resume(str(FIXTURE))
    assert profile.cgpa == 8.1


def test_parse_resume_handles_empty_pdf_gracefully(tmp_path):
    from reportlab.pdfgen import canvas
    blank_pdf = tmp_path / "blank.pdf"
    c = canvas.Canvas(str(blank_pdf))
    c.save()
    profile = parse_resume(str(blank_pdf))
    assert profile.is_empty()
