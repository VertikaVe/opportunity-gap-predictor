"""
Ashby public job-board provider.

Fetches publicly available job postings from an Ashby job board
and converts them into the project's standard opportunity format.
"""

from typing import Dict, List
import json
import urllib.request
import urllib.error

from src.opportunity_sources.base import (
    OpportunitySource,
    SourceUnavailable,
    make_opportunity_dict,
)

from src.skill_extractor import extract_job_skills


class AshbyProvider(OpportunitySource):
    name = "ashby"
    is_demo = False

    def __init__(self, board_name: str):
        self.board_name = board_name

    def fetch(self) -> List[Dict]:
        url = (
            f"https://api.ashbyhq.com/posting-api/"
            f"job-board/{self.board_name}"
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "OpportunityGapPredictor/1.0"
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=15
            ) as response:
                data = json.loads(
                    response.read().decode("utf-8")
                )

        except (
            urllib.error.URLError,
            urllib.error.HTTPError
        ) as exc:
            raise SourceUnavailable(
                f"Ashby board '{self.board_name}' unavailable: {exc}"
            ) from exc

        jobs = data.get("jobs", [])

        opportunities = []

        for job in jobs:
            title = job.get("title")

            # Skip invalid postings without a title
            if not title:
                continue

            # Full public job description
            description = job.get(
                "descriptionPlain",
                ""
            )

            # Extract required, preferred and mentioned skills
            skill_result = extract_job_skills(
                description
            )

            opportunity = make_opportunity_dict(
                source=self.name,
                is_demo=False,

                company=self.board_name,
                role=title,

                description=description,

                required_skills=skill_result[
                    "required_skills"
                ],
                preferred_skills=skill_result[
                    "preferred_skills"
                ],

                degree_allowed=None,
                branch_allowed=None,

                graduation_year_min=None,
                graduation_year_max=None,

                semester_min=None,
                semester_max=None,

                cgpa_min=None,
                experience_required=None,

                location=job.get("location"),
                work_mode=None,
                stipend=None,

                deadline=None,

                role_type=job.get(
                    "employmentType"
                ),

                source_url=job.get("jobUrl"),
                application_url=job.get("applyUrl"),
            )

            opportunities.append(
                opportunity
            )

        return opportunities