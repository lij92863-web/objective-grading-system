import csv
import json
from pathlib import Path
from typing import Mapping, Sequence


FINAL_FIELDS = (
    "student_no", "student_name", "score", "max_score", "percent", "status",
    "unresolved_count", "manual_review_count",
)


def write_final_scores(
    directory: Path,
    rows: Sequence[Mapping[str, object]],
) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    csv_path = directory / "final_scores.csv"
    json_path = directory / "final_scores.json"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FINAL_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(
        json.dumps(list(rows), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return csv_path, json_path
