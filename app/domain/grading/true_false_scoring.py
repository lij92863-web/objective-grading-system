"""Deterministic true/false answer handling."""

from typing import Optional

TRUE_VALUES = {"T", "TRUE", "1", "Y", "YES", "\u221a", "\u2713", "\u5bf9", "\u6b63\u786e", "\u662f"}
FALSE_VALUES = {"F", "FALSE", "0", "N", "NO", "X", "\u00d7", "\u2717", "\u9519", "\u9519\u8bef", "\u5426"}


def normalize_true_false(value: object) -> Optional[str]:
    text = str(value or "").strip().upper()
    if text in TRUE_VALUES:
        return "T"
    if text in FALSE_VALUES:
        return "F"
    return None
