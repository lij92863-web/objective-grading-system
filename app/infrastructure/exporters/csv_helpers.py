"""CSV helpers — standalone, no legacy / web / grading dependencies.

Matches the behaviour of ``legacy.write_dicts`` for compatibility:
- UTF-8 with BOM (``utf-8-sig``)
- platform-default newlines (``newline=""``)
- fieldnames taken from first row keys (order-preserving in Python 3.7+)
- empty rows → writes an empty file (no header)
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional


def write_dict_rows_csv(
    path: Path,
    rows: List[Dict[str, object]],
    fieldnames: Optional[List[str]] = None,
    encoding: str = "utf-8-sig",
) -> None:
    """Write *rows* as CSV to *path* using the same conventions as legacy.

    Parameters
    ----------
    path:
        Output file path.  Parent directories are created if needed.
    rows:
        List of homogeneous dicts.  Field names are taken from the first
        row unless *fieldnames* is provided explicitly.
    fieldnames:
        Explicit column order.  If ``None`` the order of keys in the
        first row is used.
    encoding:
        File encoding (default ``utf-8-sig`` to match legacy).
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        if fieldnames:
            # Write header only
            with path.open("w", encoding=encoding, newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
        else:
            # Legacy behaviour: empty file
            path.write_text("", encoding=encoding)
        return

    if fieldnames is None:
        fieldnames = list(rows[0])

    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
