# audit/looger.py
from datetime import datetime
import json
from src.paths import LOG_DIR, LOG_FILE

LOG_DIR = LOG_DIR
LOG_FILE = LOG_FILE

LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_interaction(record: dict):
    record["timestamp"] = datetime.utcnow().isoformat()

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
