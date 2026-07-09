"""R36: OMR choice decision algorithm."""
from dataclasses import dataclass
from typing import List, Optional
from .omr_metrics import ChoiceCellMetric
from .contracts import EngineCandidate


@dataclass
class OMRDecisionConfig:
    min_mark_ratio: float = 0.30
    min_confidence: float = 0.50
    ambiguity_margin: float = 0.15
    allow_multiple: bool = False


def decide_choice_from_cells(cells: List[ChoiceCellMetric], question_number: int,
                              config: OMRDecisionConfig = None) -> EngineCandidate:
    config = config or OMRDecisionConfig()
    valid = [c for c in cells if c.is_valid()]
    if not valid:
        return EngineCandidate(question_number=question_number, engine="omr",
                               status="blocking", reason="no_valid_cells")
    # Filter by min_mark_ratio
    marked = [c for c in valid if c.dark_ratio >= config.min_mark_ratio]
    if not marked:
        return EngineCandidate(question_number=question_number, engine="omr",
                               status="blank", value="", confidence=0.0,
                               reason="no_cells_above_min_mark_ratio")
    marked.sort(key=lambda c: c.dark_ratio, reverse=True)
    best = marked[0]
    # Check for ambiguity
    if len(marked) > 1:
        second = marked[1]
        if best.dark_ratio - second.dark_ratio < config.ambiguity_margin:
            return EngineCandidate(question_number=question_number, engine="omr",
                                   status="conflict", confidence=best.confidence,
                                   reason="ambiguous_cells")
    # Multiple selection support
    if config.allow_multiple and len(marked) > 1:
        value = "".join(sorted(c.option for c in marked))
        confidence = sum(c.confidence for c in marked) / len(marked)
        return EngineCandidate(question_number=question_number, engine="omr",
                               value=value, confidence=confidence, status="ok")
    return EngineCandidate(question_number=question_number, engine="omr",
                           value=best.option, confidence=best.confidence, status="ok")
