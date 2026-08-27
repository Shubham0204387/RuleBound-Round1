from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

CATALOG_FILE = DATA_DIR / "catalog.json"
FINISHES_FILE = DATA_DIR / "finishes.json"
RULES_FILE = DATA_DIR / "rules.yaml"
HISTORICAL_JOBS_FILE = DATA_DIR / "historical_jobs.json"

ROOMS_DIR = DATA_DIR / "rooms"
BRIEFS_DIR = DATA_DIR / "briefs"

OUTPUT_DIR = PROJECT_ROOT / "OUTPUT"