from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", text or "")
    value = value.replace("。", ".").replace("．", ".").replace("：", ":")
    value = value.replace("，", ",").replace("、", ",").replace("；", ";")
    value = re.sub(r"[\u200b-\u200f\ufeff]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_evidence_text(text: str) -> str:
    return normalize_text(text)


def compact_choice_text(text: str) -> str:
    return re.sub(r"[\s,;:/\\|]+", "", normalize_text(text)).upper()
