"""R46: Qwen candidate normalizer."""
import re
from typing import List


def normalize_choice(value: str) -> str:
    v = value.strip().upper()
    v = re.sub(r'^(选|答案|选项|选择)\s*', '', v)
    v = re.sub(r'[^A-Z]', '', v)
    return "".join(sorted(v))


def normalize_multiple_choice(value) -> List[str]:
    if isinstance(value, list):
        return sorted(set(normalize_choice(v) for v in value if normalize_choice(v)))
    parts = re.split(r'[,，、\s]+', str(value))
    result = []
    for p in parts:
        n = normalize_choice(p)
        if n: result.append(n)
    return sorted(set(result))


def normalize_blank(raw_text: str, latex: str = "") -> dict:
    return {"raw_text": raw_text.strip(), "normalized_text": raw_text.strip().replace(" ", ""), "latex": latex}


def normalize_identity(raw: dict) -> dict:
    return {"student_number": str(raw.get("student_number", "")).strip(),
            "student_name": str(raw.get("student_name", "")).strip()}
