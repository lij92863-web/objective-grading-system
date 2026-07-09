"""R26: Qwen response → EngineCandidate parser."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.recognition.contracts import EngineCandidate, RecognitionDecision, RecognitionRunConfig


@dataclass
class QwenParsedResult:
    candidates: List[EngineCandidate] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    status: str = "ok"


def parse_choice_response(response: dict, question_number: int) -> EngineCandidate:
    value = str(response.get("answer", response.get("value", ""))).strip().upper()
    confidence = float(response.get("confidence", 0.0))
    if not value:
        return EngineCandidate(question_number=question_number, engine="qwen",
                               status="engine_error", reason="empty_response")
    return EngineCandidate(question_number=question_number, engine="qwen",
                           value=value, confidence=confidence, status="ok")


def parse_blank_response(response: dict, question_number: int) -> EngineCandidate:
    value = str(response.get("answer", response.get("value", ""))).strip()
    latex = str(response.get("latex", ""))
    confidence = float(response.get("confidence", 0.0))
    if not value and not latex:
        return EngineCandidate(question_number=question_number, engine="qwen",
                               status="engine_error", reason="empty_blank_response")
    return EngineCandidate(question_number=question_number, engine="qwen",
                           value=value, latex=latex, confidence=confidence, status="ok")


def parse_qwen_response(response: dict) -> QwenParsedResult:
    if not isinstance(response, dict):
        return QwenParsedResult(errors=["MALFORMED_RESPONSE"], status="engine_error")
    results = QwenParsedResult()
    for key, val in response.items():
        try:
            qn = int(key)
            if isinstance(val, dict):
                qtype = val.get("question_type", "choice")
                if qtype == "blank":
                    results.candidates.append(parse_blank_response(val, qn))
                else:
                    results.candidates.append(parse_choice_response(val, qn))
        except (ValueError, TypeError):
            results.errors.append(f"INVALID_QUESTION_KEY:{key}")
    if not results.candidates:
        results.errors.append("NO_CANDIDATES_PARSED")
        results.status = "engine_error"
    return results
