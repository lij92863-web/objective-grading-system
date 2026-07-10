import json
from pathlib import Path
from typing import Mapping


def write_finalization_audit(directory: Path, payload: Mapping[str, object]) -> Path:
    path = directory / "finalization_audit.json"
    path.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
