# src/app_logger.py
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.paths import APP_INTERACTIONS_FILE

def write_jsonl(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def log_app_interaction(record: Dict[str, Any]) -> None:
    record["ts_utc"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    write_jsonl(APP_INTERACTIONS_FILE, record)