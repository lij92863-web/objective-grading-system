"""String / formatting helpers extracted from workflow.py.

No legacy, web, or business-logic imports.
"""
from typing import Any


def display_percent(value: object) -> str:
    """Format a value as percentage string, '0.00%' on failure."""
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def main_wrong_answer_from_distribution(
    distribution: object, expected: str = "",
) -> str:
    """Return the most common wrong option from a distribution dict."""
    if not isinstance(distribution, dict):
        return ""
    candidates = []
    for option, count in distribution.items():
        option_text = str(option)
        if option_text in {"", "(blank)", expected}:
            continue
        try:
            candidates.append((option_text, int(count)))
        except (TypeError, ValueError):
            continue
    if not candidates:
        return ""
    option, count = max(candidates, key=lambda item: item[1])
    return f"{option}（{count}人）"
