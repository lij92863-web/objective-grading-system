"""Basic score statistics builder."""

import statistics
from typing import Dict, List


def _value(item: object, name: str, default: object = 0) -> object:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def basic_stats(results: List[object]) -> Dict[str, object]:
    scores = [_value(result, "score", 0) for result in results]
    if not scores:
        return {
            "average": 0,
            "highest": 0,
            "lowest": 0,
            "pass_rate": 0,
            "excellent_rate": 0,
        }
    return {
        "average": round(statistics.mean(scores), 2),
        "highest": round(max(scores), 2),
        "lowest": round(min(scores), 2),
        "pass_rate": round(
            sum(1 for result in results if _value(result, "percent", 0) >= 60)
            / len(results)
            * 100,
            2,
        ),
        "excellent_rate": round(
            sum(1 for result in results if _value(result, "percent", 0) >= 90)
            / len(results)
            * 100,
            2,
        ),
    }
