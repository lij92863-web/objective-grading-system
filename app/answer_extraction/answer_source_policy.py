from __future__ import annotations

CONFIDENCE_BY_SOURCE = {
    "answer_table": 0.99,
    "explicit_bracket_answer": 0.98,
    "explicit_answer": 0.97,
    "explicit_answer_colon": 0.96,
    "short_itemized": 0.95,
    "guxuan": 0.88,
    "gu_daanwei": 0.86,
    "llm_candidate": 0.70,
    "unknown": 0.0,
}


def confidence_for_source(source_kind: str) -> float:
    return CONFIDENCE_BY_SOURCE.get(source_kind, 0.0)
