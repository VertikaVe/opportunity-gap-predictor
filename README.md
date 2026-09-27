# Opportunity Gap Predictor — Web MVP

A working Streamlit application: upload a resume PDF (or enter skills
manually), see which internships/jobs you're actually eligible for, what
skills you're missing, and get a personalized learning roadmap.

> **Read this first:** this MVP ships with one real, working data
> source — clearly labeled **DEMO DATA** — and a genuine provider
> architecture for real sources (Unstop, LinkedIn, company career pages)
> that are honestly marked **unavailable** rather than faked. See
> [Section 6](#6-what-uses-demo-data-vs-real-data) for exactly what that
> means and why.

## 1. Quick Start

```bash
git clone <your-repo-url>
cd opportunity_gap_predictor
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows

pip install -r requirements.txt
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`) —
open it in your browser.

## 2. Test It With Your Real Resume

1. On the app's **Landing / Upload** page, choose the "Upload Resume
   (PDF)" tab.
2. Select your actual resume PDF and click **Analyze Resume**.
3. You'll see the extracted name, degree, graduation year, and skills.
   Check them — this is a heuristic parser (see
   [Section 7](#7-resume-parsing-how-it-works-and-its-limits)), not a
   perfect one.
4. If it missed something or your PDF has no extractable text (e.g. a
   scanned image), use the "Enter Skills Manually" tab instead.
5. Move to **Dashboard**, **Opportunities**, **Skill Gaps**, **Roadmap**,
   or **Alerts** in the sidebar to see the rest of the app.

## 3. Push to GitHub

```bash
git init
git add .
git commit -m "Initial working MVP"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

`.gitignore` already excludes `venv/`, `.env`, the local SQLite database
file, cache files, and anything under `data/uploads/` — no secrets or
personal data get committed.

## 4. Deploy It Live

The simplest path is **Streamlit Community Cloud** (free):
1. Push this repo to GitHub (Section 3).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in, and
   pick this repo + `app.py` as the entry point.
3. Deploy. No environment variables are required for the MVP as shipped
   (see `.env.example` for what you'd add if you later connect a real
   opportunity source that needs an API key).

Any other host that can run `streamlit run app.py` (Render, Railway, a
plain VM) works the same way — just make sure `requirements.txt` gets
installed first.

## 5. Run The Tests

```bash
pytest
```

25 tests cover skill normalization, skill-gap/preferred-skill logic,
TF-IDF similarity, the eligibility engine (including "possibly eligible"
and deadline-passed cases), opportunity deduplication/status logic, and
resume parsing against a sample fixture PDF (`tests/fixtures/`).

> **How this was verified:** the sandbox this project was built in has
> no internet access, so `pytest` couldn't be installed there to run it
> directly. All 25 test functions were executed manually (calling each
> one directly and checking for exceptions/assertion failures) and all
> passed. The test files themselves are standard pytest-discoverable
> files and will run normally with `pytest` on a machine with internet
> access. Every other module was also run directly end-to-end (see
> [Section 15](#15-what-was-actually-tested)).

## 6. What Uses Demo Data vs. Real Data

**Demo data (real, working, clearly labeled):**
- `src/opportunity_sources/demo_provider.py` — 12 hand-written sample
  opportunities. Every one carries `is_demo=True`, and the UI shows a
  **DEMO DATA** badge on each. Deadlines are set relative to today so
  the app genuinely exercises OPEN / CLOSING_SOON / EXPIRED statuses.

**Real, live application logic (not demo — this genuinely runs):**
- Resume PDF upload and parsing (`src/resume_parser.py`)
- The SQLite database, opportunity sync/update/expiry pipeline
  (`src/database.py`, `src/opportunity_manager.py`)
- Skill normalization, skill-gap analysis, TF-IDF similarity, the hybrid
  match score, the eligibility engine, the roadmap generator, and the
  alert feed (`src/skill_processing.py`, `src/skill_gap.py`,
  `src/similarity.py`, `src/recommendation.py`, `src/eligibility.py`,
  `src/roadmap.py`, `src/alerts.py`)
- The full Streamlit UI (`app.py`) — every page actually works against
  this real logic.

**Not implemented — honestly marked unavailable, not faked:**
- `src/opportunity_sources/unstop_provider.py` — Unstop has no public
  API; scraping it isn't confirmed to comply with its terms.
- `src/opportunity_sources/linkedin_provider.py` — covers LinkedIn,
  Wellfound, Internshala, and Indeed; none offer a public/permitted API
  for this use case, and scraping LinkedIn specifically violates its
  terms of service.
- `src/opportunity_sources/company_career_provider.py` — covers Google,
  Microsoft, Amazon, JPMorgan, NVIDIA, and other company career pages; no
  verified public endpoint has been wired up for any of them yet.

Each of these raises `SourceUnavailable` with a clear reason (visible in
the sidebar's "Data sources" panel), and `opportunity_manager.sync_all()`
logs that reason instead of inventing data. **This project will never
show you a fake Google/Microsoft/Amazon internship.** See each provider
file's docstring for exactly what a real integration would require.

## 7. Resume Parsing: How It Works, and Its Limits

`src/resume_parser.py` extracts text from the PDF with `pdfplumber`, then
uses regexes and keyword lists to pull out email, phone, name, degree,
branch, graduation year, semester, CGPA, skills (matched against a ~50
skill vocabulary), and best-effort "Projects"/"Certifications" sections.

This is a **heuristic parser, not a resume-understanding model**. It:
- will miss fields on resumes with unusual layouts, heavy use of tables
  or columns, or non-standard section headers,
- returns an empty profile (rather than guessing) for scanned/image-only
  PDFs with no text layer,
- never fabricates a field it can't find — everything is `None`/empty
  instead.

Always check the extracted profile on the **Profile** page and correct
anything wrong before relying on the results.

## 8. Eligibility Engine

For each opportunity, `src/eligibility.py` checks degree, branch,
graduation year, semester, CGPA, and deadline against the student's
profile, and returns one of three outcomes with plain-language reasons:

- **ELIGIBLE** — every criterion the listing actually states is met.
- **POSSIBLY ELIGIBLE** — nothing is clearly violated, but at least one
  stated criterion couldn't be checked because that field is missing
  from your profile (e.g. no CGPA found on your resume).
- **NOT ELIGIBLE** — at least one stated criterion is clearly violated,
  or the deadline has passed.

"Experience required" is shown as an informational note only — it never
decides eligibility, because reliably estimating years of experience
from an arbitrary resume isn't something this parser can do accurately.
The engine never invents a requirement a listing doesn't actually state;
where a listing is silent on something, that dimension is simply skipped
rather than assumed.

## 9. Matching Methodology (Skill Score)

```
match_score = 0.55 × required_skill_coverage
            + 0.15 × preferred_skill_coverage
            + 0.30 × TF-IDF_cosine_similarity
```

- **Required-skill coverage** (skill_gap.py) — the literal, most
  actionable signal: of the skills actually required, how many does the
  student have (after normalization/synonym-mapping, e.g. "ML" →
  "machine learning", while still keeping `java != javascript`)?
- **Preferred-skill coverage** — the same idea for "nice to have" skills,
  weighted lower since they're optional by definition.
- **TF-IDF + cosine similarity** (similarity.py) — a continuous measure
  of overall profile-to-requirement similarity that naturally
  down-weights ubiquitous skills (e.g. "python", if almost every posting
  wants it) and rewards rarer, more distinguishing overlap.

**Eligibility is deliberately kept separate from this score**, not
blended into it — the UI shows both side by side ("62% skill match, but
NOT ELIGIBLE: this role requires 8th semester") rather than letting a
categorical "you can't apply" get lost inside a slightly-lower
percentage. See `src/recommendation.py`'s module docstring for the full
reasoning.

Ranking (`rank_opportunities`) sorts ELIGIBLE first, then POSSIBLY
ELIGIBLE, then NOT_ELIGIBLE, and by match score within each tier — so the
top of any list is always something worth actually applying to.

## 10. Skill Gap & Roadmap

`recommend_skills_to_learn()` only counts a missing skill against
opportunities the student is ELIGIBLE or POSSIBLY_ELIGIBLE for — there's
no point telling a 2nd-semester student to learn a skill for a
final-year-only role they can never apply to anyway.

`build_roadmap()` (roadmap.py) then packs the highest-demand missing
skills into week-long phases using a small lookup table of rough
estimated learning durations per skill. **This is a simple demand-based
heuristic, not a curriculum-design AI** — it doesn't know that, say, SQL
joins require SQL basics first. See [Limitations](#13-limitations).

## 11. Database

SQLite (`data/opportunity_gap.db`, created automatically, git-ignored)
stores only **opportunities**, **alerts**, and an **update_log** audit
trail — never resumes or student profiles (see
[Privacy](#12-privacy--security) below). Migrating to Postgres later
means swapping `src/database.py`'s connection layer; every query is
plain SQL with no ORM-specific features.

## 12. Privacy & Security

- Uploaded resumes and parsed profiles live only in
  `st.session_state` for the current browser session — never written to
  disk or the database. Refreshing/closing the browser clears them.
- No API keys, passwords, or secrets are hard-coded anywhere;
  `.env.example` shows the pattern for adding one later if a real
  opportunity source needs credentials. `.env` itself is git-ignored.
- Demo opportunity data contains no real company postings, deadlines, or
  application links — every demo `source_url`/`application_url` points
  to an obviously fake `.invalid` domain so it can never be mistaken for
  a real link.

## 13. Limitations

- Only demo opportunity data is currently live (12 sample postings) —
  see [Section 6](#6-what-uses-demo-data-vs-real-data).
- No automated scheduled refresh yet — opportunities sync once at app
  startup and whenever "Refresh opportunities now" is clicked in the
  sidebar. A real deployment would run
  `python -m src.opportunity_manager` on a schedule (cron, or a
  scheduled task on whatever host you deploy to) — the sync logic itself
  is already schedule-ready, it's just not wired to a scheduler here.
- Resume parsing is heuristic and will miss fields on unusually
  formatted resumes (see [Section 7](#7-resume-parsing-how-it-works-and-its-limits)).
- The eligibility engine only checks what a listing explicitly states —
  it cannot infer unstated requirements, and "experience required" is
  informational only, not auto-verified.
- The roadmap generator sequences skills by demand only, not by
  prerequisite relationships between them.
- "Personalized" alerts are recomputed live each session rather than
  diffed against persisted history (since resume data is intentionally
  not persisted) — see `src/alerts.py`'s docstring for this trade-off.
- Duplicate detection currently only has one live source to exercise it
  against (demo data); the logic is unit-tested against synthetic
  cross-source duplicates (`tests/test_opportunity_manager.py`) but
  hasn't been exercised against two real, differently-formatted sources.

## 14. What to Improve Next

1. Implement one real opportunity source once a permitted API/feed is
   identified (most likely a company career page with a public JSON
   endpoint, or an official Unstop partner API if one becomes available).
2. Add real scheduled syncing (cron / hosted scheduler) calling
   `opportunity_manager.sync_all()`.
3. Expand the resume parser's section detection (e.g. handle two-column
   layouts, more header phrasings).
4. Add skill prerequisites to the roadmap generator so ordering reflects
   what actually needs to be learned first.
5. If real hiring-outcome data ever becomes available, evaluate the
   match score against it properly (precision/recall on real outcomes,
   not just the logic-level unit tests that exist today).
6. Add lightweight auth + persistent (opt-in) profiles if you want
   alerts to track a returning user's history over time.

## 15. What Was Actually Tested

Everything below was run for real while building this project (in a
sandbox with no internet access, so `streamlit`/`pytest` couldn't be
`pip install`-ed there — see the caveats noted inline):

- ✅ `src/database.py` — insert, update (upsert), and read, verified
  directly.
- ✅ `src/opportunity_sources/demo_provider.py` — fetches 12 opportunities.
- ✅ `src/opportunity_manager.py` — full `sync_all()` run: added 12,
  correctly logged 3 sources as `UNAVAILABLE` with reasons, computed
  OPEN/CLOSING_SOON/EXPIRED statuses correctly against real dates.
- ✅ `src/eligibility.py` — verified against real demo opportunities
  (e.g. correctly flagged semester/CGPA/graduation-year mismatches with
  accurate reasons).
- ✅ `src/recommendation.py` — ranking correctly prioritizes ELIGIBLE
  opportunities and produces accurate "why" explanations.
- ✅ `src/roadmap.py`, `src/alerts.py` — produced correct, sensible output
  against real demo data.
- ✅ `src/resume_parser.py` — tested against a synthetic sample resume
  PDF (`tests/fixtures/sample_resume.pdf`, generated with `reportlab` for
  testing purposes) and correctly extracted name, email, phone, degree,
  branch, graduation year, semester, CGPA, and skills.
- ✅ All 25 unit tests pass (run manually — see Section 5's note).
- ✅ **`app.py` — every one of its 7 pages was smoke-tested** using a
  minimal fake `streamlit` module that exercises the exact same
  `src/` function calls the real UI makes, confirming no page raises an
  exception with a real profile and real demo data loaded.
- ⚠️ **Not verified: the actual rendered Streamlit UI.** `streamlit`
  itself could not be installed in this offline sandbox, so the visual
  layout, CSS styling, and interactive widgets have not been visually
  confirmed — only the underlying logic every page calls. Please run
  `streamlit run app.py` locally as your first step to confirm the UI
  renders and looks right; if anything looks off, the fix is almost
  certainly in `app.py` only (all business logic underneath it is
  independently tested).

## 16. Project Structure

```
opportunity_gap_predictor/
├── app.py                              # Streamlit UI (all pages)
├── src/
│   ├── config.py                       # paths, DB location, scoring weights
│   ├── database.py                     # SQLite schema + CRUD
│   ├── resume_parser.py                # PDF -> StudentProfile
│   ├── profile.py                      # StudentProfile dataclass
│   ├── skill_processing.py             # normalization + synonyms
│   ├── skill_gap.py                    # matched/missing/coverage
│   ├── similarity.py                   # TF-IDF + cosine similarity
│   ├── eligibility.py                  # ELIGIBLE/POSSIBLY/NOT + reasons
│   ├── recommendation.py               # hybrid score, ranking, "why"
│   ├── roadmap.py                      # phased learning roadmap
│   ├── alerts.py                       # global + per-session alerts
│   ├── opportunity_manager.py          # sync, dedupe, status refresh
│   └── opportunity_sources/
│       ├── base.py                     # provider interface + helpers
│       ├── demo_provider.py            # REAL: demo data
│       ├── unstop_provider.py          # stub: honestly unavailable
│       ├── linkedin_provider.py        # stub: honestly unavailable
│       └── company_career_provider.py  # stub: honestly unavailable
├── data/
│   ├── opportunity_gap.db              # created at runtime, git-ignored
│   └── uploads/                        # empty, git-ignored (never used to persist resumes)
├── tests/                              # 25 tests, see Section 5
│   └── fixtures/sample_resume.pdf      # synthetic PDF for parser tests
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

## 17. License

MIT — see `LICENSE`.
