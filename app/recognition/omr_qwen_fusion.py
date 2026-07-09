"""R40A: OMR + Qwen candidate fusion."""
from dataclasses import dataclass, field
from typing import List, Optional
from .contracts import EngineCandidate, RecognitionDecision, RecognitionRunConfig
from .decision import fuse_candidates


@dataclass
class FusionResult:
    candidates: List[EngineCandidate] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    omr_qwen_conflict: bool = False
    omr_qwen_agree: bool = False
    engine_errors: List[str] = field(default_factory=list)


def fuse_omr_qwen(question_number: int, question_type: str,
                   omr_candidate: Optional[EngineCandidate] = None,
                   qwen_candidate: Optional[EngineCandidate] = None,
                   config: RecognitionRunConfig = None) -> FusionResult:
    config = config or RecognitionRunConfig()
    result = FusionResult()
    candidates = []
    if omr_candidate:
        if omr_candidate.status in ("blocking", "invalid"):
            return FusionResult(candidates=[omr_candidate], engine_errors=[],
                                 omr_qwen_conflict=False)
        candidates.append(omr_candidate)
    if qwen_candidate:
        if qwen_candidate.status == "engine_error":
            result.engine_errors.append("QWEN_ENGINE_ERROR")
            if omr_candidate:
                return FusionResult(candidates=[omr_candidate],
                                     engine_errors=["QWEN_ENGINE_ERROR"],
                                     omr_qwen_conflict=False)
            return FusionResult(engine_errors=["QWEN_ENGINE_ERROR"])
        if qwen_candidate.status == "malformed":
            result.engine_errors.append("QWEN_MALFORMED")
            if omr_candidate:
                return FusionResult(candidates=[omr_candidate],
                                     engine_errors=["QWEN_MALFORMED"])
            return FusionResult(engine_errors=["QWEN_MALFORMED"])
        candidates.append(qwen_candidate)
    if not candidates:
        return FusionResult()

    if omr_candidate and qwen_candidate:
        omr_v = omr_candidate.value.upper()
        qwen_v = qwen_candidate.value.upper()
        if omr_v == qwen_v:
            result.omr_qwen_agree = True
            boosted = EngineCandidate(question_number=question_number, engine="fusion",
                                       value=omr_v,
                                       confidence=max(omr_candidate.confidence, qwen_candidate.confidence),
                                       status="ok")
            result.candidates = [boosted]
        else:
            result.omr_qwen_conflict = True
            result.candidates = [omr_candidate, qwen_candidate]
    else:
        result.candidates = candidates
    return result
