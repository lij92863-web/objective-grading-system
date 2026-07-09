"""Decision fusion — normalize candidates, fuse, auto-accept/review/block."""
from .contracts import EngineCandidate, RecognitionDecision, RecognitionRunConfig


def normalize_choice_value(value: str) -> str:
    return "".join(sorted(c for c in value.upper() if c.isalpha()))


def normalize_blank_value(raw_text: str, latex: str = "") -> str:
    return latex or raw_text.strip()


def fuse_candidates(question_number, question_type, candidates, config) -> RecognitionDecision:
    if not candidates:
        return RecognitionDecision(question_number=question_number, status="blocking",
                                   blocking=True, reason="no_candidates", needs_review=True)
    if question_type == "choice":
        return _fuse_choice(question_number, candidates, config)
    return _fuse_blank(question_number, candidates, config)


def _fuse_choice(qn, candidates, config) -> RecognitionDecision:
    values = {normalize_choice_value(c.value) for c in candidates}
    max_conf = max(c.confidence for c in candidates)
    if len(values) > 1:
        return RecognitionDecision(question_number=qn, value=list(values)[0],
                                   confidence=max_conf, status="conflict",
                                   needs_review=True, reason="candidates_disagree",
                                   source_engines=[c.engine for c in candidates],
                                   candidates=candidates)
    best = max(candidates, key=lambda c: c.confidence)
    v = normalize_choice_value(best.value)
    if not v:
        return RecognitionDecision(question_number=qn, value="", confidence=0.0,
                                   status="blank", needs_review=True, reason="empty_answer",
                                   candidates=candidates)
    if any(c not in "ABCDEFGH" for c in v):
        return RecognitionDecision(question_number=qn, value=v, confidence=best.confidence,
                                   status="invalid", blocking=True, needs_review=True,
                                   reason="invalid_option", candidates=candidates)
    if max_conf >= config.auto_accept_threshold and not config.require_teacher_confirmation:
        return RecognitionDecision(question_number=qn, value=v, confidence=max_conf,
                                   status="auto_accepted", needs_review=False,
                                   source_engines=[c.engine for c in candidates],
                                   candidates=candidates)
    return RecognitionDecision(question_number=qn, value=v, confidence=max_conf,
                               status="needs_review", needs_review=True,
                               source_engines=[c.engine for c in candidates],
                               candidates=candidates)


def _fuse_blank(qn, candidates, config) -> RecognitionDecision:
    best = max(candidates, key=lambda c: c.confidence)
    v = normalize_blank_value(best.value, best.latex)
    if best.confidence >= config.auto_accept_threshold and not config.require_teacher_confirmation:
        return RecognitionDecision(question_number=qn, value=v, confidence=best.confidence,
                                   status="auto_accepted", needs_review=False,
                                   candidates=candidates)
    return RecognitionDecision(question_number=qn, value=v, confidence=best.confidence,
                               status="needs_review", needs_review=True, candidates=candidates)
