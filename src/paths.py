from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

# Data & Storage
DATA_DIR = BASE_DIR / "data"

DOCS_DIR = DATA_DIR / "docs"
INDEX_DIR = DATA_DIR / "index_faiss"

LOGS_DIR = DATA_DIR / "logs"
APP_LOGS_DIR = LOGS_DIR / "app"
AUDIT_LOGS_DIR = LOGS_DIR / "audit"

REPORTS_DIR = BASE_DIR / "reports"
AUDIT_REPORTS_DIR = REPORTS_DIR / "audit"
APP_REPORTS_DIR = REPORTS_DIR / "app"

# Files (raw logs)
AUDIT_RUNS_FILE = AUDIT_LOGS_DIR / "audit_runs.jsonl"
APP_INTERACTIONS_FILE = APP_LOGS_DIR / "app_interactions.jsonl"

# Defaults (models)
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_EMBEDDINGS = "BAAI/bge-m3"

# Ensure directories
for d in [
    DATA_DIR,
    DOCS_DIR,
    INDEX_DIR,
    LOGS_DIR,
    APP_LOGS_DIR,
    AUDIT_LOGS_DIR,
    REPORTS_DIR,
    AUDIT_REPORTS_DIR,
    APP_REPORTS_DIR,
]:
    d.mkdir(parents=True, exist_ok=True)
