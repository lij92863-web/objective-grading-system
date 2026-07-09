"""R98: Qwen routing policy."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class QwenRoutingResult:
    qwen_allowed: bool = False
    reason: str = ""


def should_use_qwen(omr_confidence: Optional[float], is_blank: bool = False,
                     qwen_enabled: bool = True, budget_ok: bool = True,
                     omr_clear: bool = True) -> QwenRoutingResult:
    if not qwen_enabled: return QwenRoutingResult(False, "QWEN_DISABLED")
    if not budget_ok: return QwenRoutingResult(False, "BUDGET_EXCEEDED")
    if is_blank: return QwenRoutingResult(True, "BLANK_QUESTION")
    if omr_confidence is None: return QwenRoutingResult(True, "NO_OMR_AVAILABLE")
    if omr_confidence >= 0.90 and omr_clear: return QwenRoutingResult(False, "OMR_HIGH_CONFIDENCE")
    if omr_confidence < 0.60: return QwenRoutingResult(True, "OMR_LOW_CONFIDENCE")
    return QwenRoutingResult(True, "OMR_AMBIGUOUS")
