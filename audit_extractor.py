from src.opportunity_sources.ashby_provider import AshbyProvider
from src.skill_extractor import extract_job_skills

jobs = AshbyProvider("replit").fetch()

print("TOTAL JOBS:", len(jobs))
print("\n--- AUDIT ---")

for i, job in enumerate(jobs, start=1):
    result = extract_job_skills(job["description"])

    print(f"\n{i}. {job['role']}")
    print("Required :", result["required_skills"])
    print("Preferred:", result["preferred_skills"])
    print("Mentioned:", result["mentioned_skills"])