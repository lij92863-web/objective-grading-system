"""load_question_bank — mirrors legacy.load_question_bank exactly.

Uses only stdlib csv.  Returns SimpleNamespace objects matching
legacy.BankQuestion fields: question_id, stem, answer, tags, difficulty.
"""

import csv
from pathlib import Path
from types import SimpleNamespace
from typing import List

# Field aliases — same as legacy FIELD_ALIASES for question bank fields
_FIELD_ALIASES = {
    "bank_id": ("bank_id", "question_id", "id", "题目id"),
    "stem": ("stem", "question_text", "content", "题干"),
    "answer": ("answer", "答案", "correct", "key"),
    "tags": ("tags", "tag", "知识点"),
    "difficulty": ("difficulty", "level", "难度"),
}


def _first_present(row: dict, keys: tuple, default: str = "") -> str:
    """Return the first non-empty value matching any of *keys*."""
    folded = {k.strip().lower(): v for k, v in row.items() if k is not None}
    for k in keys:
        val = folded.get(k.lower())
        if val is not None and str(val).strip():
            return val
    return default


def _split_tags(value: str) -> tuple:
    """Split by ; , 、 into a tuple of stripped parts."""
    v = (value or "").replace("，", ";").replace(",", ";").replace("、", ";")
    return tuple(p.strip() for p in v.split(";") if p.strip())


def _parse_difficulty(value: object) -> int:
    text = str(value or "").strip().lower()
    if not text:
        return 0
    named = {"easy": 1, "medium": 3, "normal": 3, "hard": 5}
    if text in named:
        return named[text]
    try:
        n = int(float(text))
    except ValueError:
        return 0
    return max(1, min(5, n))


def load_question_bank(path: Path) -> List[SimpleNamespace]:
    """Read a CSV question bank and return BankQuestion-like objects.

    Matches legacy.load_question_bank behaviour: UTF-8-BOM encoding,
    alias-based column lookup, duplicate detection.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise ValueError(f"{path} does not contain a header row.")
        rows = list(reader)

    questions: List[SimpleNamespace] = []
    seen: set = set()
    for idx, row in enumerate(rows, start=2):
        qid = _first_present(row, _FIELD_ALIASES["bank_id"]).strip()
        if not qid:
            raise ValueError(f"Question bank row {idx}: missing question id.")
        if qid in seen:
            raise ValueError(
                f"Question bank row {idx}: duplicate question id {qid}.")
        questions.append(SimpleNamespace(
            question_id=qid,
            stem=_first_present(row, _FIELD_ALIASES["stem"]).strip(),
            answer=_first_present(row, _FIELD_ALIASES["answer"]).strip(),
            tags=_split_tags(_first_present(row, _FIELD_ALIASES["tags"])),
            difficulty=_parse_difficulty(
                _first_present(row, _FIELD_ALIASES["difficulty"])),
        ))
        seen.add(qid)
    return questions
