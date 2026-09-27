"""
config.py
=========
Central configuration: paths, DB location, scoring weights, and alert
thresholds. Kept in one file so nothing else hard-codes a path or a
magic number.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "opportunity_gap.db"
UPLOADS_DIR = DATA_DIR / "uploads"

# --------------------------------------------------------------------------
# Hybrid match-score weights
# --------------------------------------------------------------------------
# final_score = EXACT_WEIGHT * required_coverage
#             + PREFERRED_WEIGHT * preferred_coverage
#             + TFIDF_WEIGHT * tfidf_similarity
# Required-skill coverage is weighted highest because it's the most
# direct, literal signal of fit. Preferred skills matter but are, by
# definition, optional for the role, so they get a smaller weight.
# TF-IDF rewards overall profile similarity beyond exact skill presence.
EXACT_WEIGHT = 0.55
PREFERRED_WEIGHT = 0.15
TFIDF_WEIGHT = 0.30

# Opportunities within this many days of their deadline are flagged
# "closing soon" in the UI and trigger a deadline alert.
DEADLINE_SOON_DAYS = 7
DEADLINE_URGENT_DAYS = 3

# An opportunity is only shown as "newly added" (for the alerts feed) if
# it was added to the database within this many days.
NEW_OPPORTUNITY_WINDOW_DAYS = 14

DEFAULT_TOP_N = 10
