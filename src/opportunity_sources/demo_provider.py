"""
opportunity_sources/demo_provider.py
======================================
The ONLY provider in this project that currently returns data - and it is
hand-written sample data, clearly marked `is_demo=True` on every record.

Why this exists
-----------------
Per the project's data-honesty requirement, the application must never
pretend to show live opportunities from Google, Microsoft, LinkedIn, etc.
unless it genuinely has permitted access to real data from them (see
unstop_provider.py, company_career_provider.py, and linkedin_provider.py
for why those are NOT implemented yet). This provider exists so the
application has something real to run, test, and demo end-to-end while
those integrations are pending - every UI surface checks `is_demo` and
shows a "DEMO DATA" badge instead of implying live sourcing.

Deadlines below are set relative to "today" so that, whenever this is
run, the demo data naturally exercises every status the opportunity
manager assigns: OPEN, CLOSING_SOON, and (one intentionally past-dated
entry) EXPIRED.
"""

from datetime import date, timedelta
from typing import Dict, List

from src.opportunity_sources.base import OpportunitySource, make_opportunity_dict

_TODAY = date.today()


def _in_days(days: int) -> str:
    return (_TODAY + timedelta(days=days)).isoformat()


class DemoDataProvider(OpportunitySource):
    name = "demo"
    is_demo = True

    def fetch(self) -> List[Dict]:
        return [
            make_opportunity_dict(
                source=self.name, is_demo=True,
                company="Insight Analytics", role="Data Analyst Intern",
                description="Support the analytics team with dashboards and reporting on customer data.",
                required_skills=["Python", "SQL", "Excel", "Power BI"],
                preferred_skills=["Statistics", "Data Visualization"],
                degree_allowed=["B.Tech", "B.E.", "BBA", "B.Sc"], branch_allowed=None,
                graduation_year_min=2026, graduation_year_max=2028,
                semester_min=5, semester_max=8, cgpa_min=6.5,
                location="Bengaluru", work_mode="Hybrid", stipend="₹25,000/month",
                deadline=_in_days(21), role_type="Internship",
                source_url="https://example-demo-source.invalid/insight-analytics",
                application_url="https://example-demo-source.invalid/insight-analytics/apply",
            ),
            make_opportunity_dict(
                source=self.name, is_demo=True,
                company="NextGen AI", role="Machine Learning Engineer",
                description="Build and deploy deep learning models for computer vision products.",
                required_skills=["Python", "TensorFlow", "Deep Learning", "SQL"],
                preferred_skills=["PyTorch", "Docker"],
                degree_allowed=["B.Tech", "M.Tech"], branch_allowed=["CSE", "IT", "AI"],
                graduation_year_min=2025, graduation_year_max=2027,
                semester_min=7, semester_max=8, cgpa_min=7.5,
                location="Remote", work_mode="Remote", stipend=None,
                deadline=_in_days(45), role_type="Full-time",
                source_url="https://example-demo-source.invalid/nextgen-ai",
                application_url="https://example-demo-source.invalid/nextgen-ai/apply",
            ),
            make_opportunity_dict(
                source=self.name, is_demo=True,
                company="CodeCraft Systems", role="Backend Developer",
                description="Develop and maintain REST APIs for an e-commerce platform.",
                required_skills=["Java", "Spring Boot", "MySQL", "REST APIs"],
                preferred_skills=["Docker", "AWS"],
                degree_allowed=["B.Tech", "B.E."], branch_allowed=["CSE", "IT"],
                graduation_year_min=2025, graduation_year_max=2026,
                semester_min=8, semester_max=8, cgpa_min=6.0,
                location="Pune", work_mode="On-site", stipend="₹8,00,000/year",
                deadline=_in_days(5), role_type="Full-time",
                source_url="https://example-demo-source.invalid/codecraft",
                application_url="https://example-demo-source.invalid/codecraft/apply",
            ),
            make_opportunity_dict(
                source=self.name, is_demo=True,
                company="PixelWorks", role="Frontend Developer Intern",
                description="Build responsive UI components for a marketing website.",
                required_skills=["HTML", "CSS", "JavaScript", "React"],
                preferred_skills=["TypeScript", "Figma"],
                degree_allowed=None, branch_allowed=None,
                graduation_year_min=2027, graduation_year_max=2029,
                semester_min=3, semester_max=6, cgpa_min=None,
                location="Mumbai", work_mode="On-site", stipend="₹15,000/month",
                deadline=_in_days(2), role_type="Internship",
                source_url="https://example-demo-source.invalid/pixelworks",
                application_url="https://example-demo-source.invalid/pixelworks/apply",
            ),
            make_opportunity_dict(
                source=self.name, is_demo=True,
                company="QuantumEdge", role="Data Scientist",
                description="Analyze large datasets and build predictive models for finance clients.",
                required_skills=["Python", "Machine Learning", "SQL", "Statistics", "Pandas"],
                preferred_skills=["Scikit-learn", "Data Visualization"],
                degree_allowed=["B.Tech", "M.Tech", "M.Sc"], branch_allowed=["CSE", "IT", "Statistics"],
                graduation_year_min=2025, graduation_year_max=2027,
                semester_min=6, semester_max=8, cgpa_min=7.0,
                location="Hyderabad", work_mode="Hybrid", stipend="₹12,00,000/year",
                deadline=_in_days(30), role_type="Full-time",
                source_url="https://example-demo-source.invalid/quantumedge",
                application_url="https://example-demo-source.invalid/quantumedge/apply",
            ),
            make_opportunity_dict(
                source=self.name, is_demo=True,
                company="LinguaTech", role="NLP Engineer",
                description="Design NLP pipelines for a customer support chatbot.",
                required_skills=["Python", "NLP", "Pandas", "Scikit-learn", "Deep Learning"],
                preferred_skills=["Transformers", "spaCy"],
                degree_allowed=["B.Tech", "M.Tech"], branch_allowed=["CSE", "IT", "AI"],
                graduation_year_min=2025, graduation_year_max=2026,
                semester_min=7, semester_max=8, cgpa_min=7.0,
                location="Remote", work_mode="Remote", stipend=None,
                deadline=_in_days(60), role_type="Full-time",
                source_url="https://example-demo-source.invalid/linguatech",
                application_url="https://example-demo-source.invalid/linguatech/apply",
            ),
            make_opportunity_dict(
                source=self.name, is_demo=True,
                company="MarketPulse", role="Business Intelligence Analyst",
                description="Create BI reports and dashboards for retail sales performance.",
                required_skills=["SQL", "Power BI", "Excel", "Data Visualization"],
                preferred_skills=["Python", "Statistics"],
                degree_allowed=None, branch_allowed=None,
                graduation_year_min=2026, graduation_year_max=2028,
                semester_min=5, semester_max=8, cgpa_min=6.0,
                location="Delhi", work_mode="On-site", stipend="₹7,50,000/year",
                deadline=_in_days(14), role_type="Full-time",
                source_url="https://example-demo-source.invalid/marketpulse",
                application_url="https://example-demo-source.invalid/marketpulse/apply",
            ),
            make_opportunity_dict(
                source=self.name, is_demo=True,
                company="ByteForge", role="Software Engineer Intern",
                description="Work on core algorithms for a real-time trading system.",
                required_skills=["C++", "Data Structures", "Algorithms", "Git"],
                preferred_skills=["Multithreading"],
                degree_allowed=["B.Tech", "B.E."], branch_allowed=["CSE", "IT", "ECE"],
                graduation_year_min=2027, graduation_year_max=2028,
                semester_min=5, semester_max=6, cgpa_min=7.5,
                location="Chennai", work_mode="On-site", stipend="₹20,000/month",
                deadline=_in_days(10), role_type="Internship",
                source_url="https://example-demo-source.invalid/byteforge",
                application_url="https://example-demo-source.invalid/byteforge/apply",
            ),
            make_opportunity_dict(
                source=self.name, is_demo=True,
                company="WebNest", role="Full Stack Developer",
                description="Build and maintain a Django-based job listing platform.",
                required_skills=["Python", "Django", "REST APIs", "SQL", "JavaScript"],
                preferred_skills=["React", "Docker"],
                degree_allowed=["B.Tech", "B.E.", "BCA"], branch_allowed=None,
                graduation_year_min=2025, graduation_year_max=2026,
                semester_min=8, semester_max=8, cgpa_min=6.5,
                location="Bengaluru", work_mode="Hybrid", stipend="₹9,00,000/year",
                deadline=_in_days(40), role_type="Full-time",
                source_url="https://example-demo-source.invalid/webnest",
                application_url="https://example-demo-source.invalid/webnest/apply",
            ),
            make_opportunity_dict(
                source=self.name, is_demo=True,
                company="StatWorks", role="Data Analytics Trainee",
                description="Assist senior analysts with statistical reporting on survey data.",
                required_skills=["R", "Statistics", "Data Visualization", "Excel"],
                preferred_skills=["SQL"],
                degree_allowed=["B.Sc", "BBA"], branch_allowed=["Statistics", "Economics"],
                graduation_year_min=2026, graduation_year_max=2028,
                semester_min=5, semester_max=8, cgpa_min=None,
                location="Remote", work_mode="Remote", stipend="₹10,000/month",
                deadline=_in_days(-3), role_type="Internship",  # intentionally in the past -> EXPIRED
                source_url="https://example-demo-source.invalid/statworks",
                application_url="https://example-demo-source.invalid/statworks/apply",
            ),
            make_opportunity_dict(
                source=self.name, is_demo=True,
                company="CodeSprint", role="Junior Python Developer",
                description="Write automation scripts and simple backend services.",
                required_skills=["Python", "SQL", "Git"],
                preferred_skills=["Django", "Pandas"],
                degree_allowed=None, branch_allowed=None,
                graduation_year_min=2025, graduation_year_max=2027,
                semester_min=6, semester_max=8, cgpa_min=6.0,
                location="Pune", work_mode="Hybrid", stipend="₹6,50,000/year",
                deadline=_in_days(25), role_type="Full-time",
                source_url="https://example-demo-source.invalid/codesprint",
                application_url="https://example-demo-source.invalid/codesprint/apply",
            ),
            make_opportunity_dict(
                source=self.name, is_demo=True,
                company="DeepMind Labs (mock)", role="AI Research Intern",
                description="Assist researchers exploring deep learning and NLP techniques.",
                required_skills=["Python", "Deep Learning", "NLP", "Machine Learning"],
                preferred_skills=["PyTorch", "Transformers"],
                degree_allowed=["M.Tech", "M.Sc", "B.Tech"], branch_allowed=["CSE", "AI"],
                graduation_year_min=2025, graduation_year_max=2027,
                semester_min=6, semester_max=8, cgpa_min=8.0,
                location="Remote", work_mode="Remote", stipend="₹40,000/month",
                deadline=_in_days(6), role_type="Internship",
                source_url="https://example-demo-source.invalid/deepmind-labs-mock",
                application_url="https://example-demo-source.invalid/deepmind-labs-mock/apply",
            ),
        ]
