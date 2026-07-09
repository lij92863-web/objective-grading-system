"""R59: OMR candidate → EngineCandidate adapter."""
from .omr_metrics import ChoiceCellMetric
from .omr_choice_decision import decide_choice_from_cells, OMRDecisionConfig
from .contracts import EngineCandidate


def adapt_omr_to_candidate(cells: list, question_number: int,
                            config: OMRDecisionConfig = None) -> EngineCandidate:
    return decide_choice_from_cells(
        [ChoiceCellMetric(**c) if isinstance(c, dict) else c for c in cells],
        question_number, config)
