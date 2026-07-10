"""Last-line invariants for records about to become official."""

import math
from typing import Mapping


class FinalScoreInvariantError(ValueError):
    pass


def validate_final_score(row: Mapping[str, object]) -> None:
    try:
        score = float(row["score"])
        max_score = float(row["max_score"])
        percent = float(row["percent"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise FinalScoreInvariantError("final score fields must be numeric") from exc
    if not all(math.isfinite(value) for value in (score, max_score, percent)):
        raise FinalScoreInvariantError("final score fields must be finite")
    if max_score < 0:
        raise FinalScoreInvariantError("max_score cannot be below zero")
    if score < 0 or score > max_score:
        raise FinalScoreInvariantError("score must be within [0, max_score]")
    if percent < 0 or percent > 100:
        raise FinalScoreInvariantError("percent must be within [0, 100]")
    if max_score == 0 and (score != 0 or percent != 0):
        raise FinalScoreInvariantError(
            "zero-max score requires score=0 and percent=0"
        )
