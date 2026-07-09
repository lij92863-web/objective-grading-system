"""R126: Qwen policy orchestrator — routing + budget + retry + cache."""
from dataclasses import dataclass, field
from .routing_policy import should_use_qwen
from .budget_guard import compute_qwen_budget
from .retry_policy import should_retry
from .cache_policy import build_cache_key


@dataclass
class QwenPolicyDecision:
    should_call_qwen: bool = False
    reason: str = ""
    qwen_call_allowed: bool = False
    blocked_by_budget: bool = False
    cache_hit: bool = False
    retry_allowed: bool = False
    max_retry: int = 0
    fallback_status: str = "needs_review"
    review_reason: str = ""


class QwenPolicyOrchestrator:
    def __init__(self, max_qwen_calls: int = 10, qwen_enabled: bool = True):
        self.max_calls = max_qwen_calls
        self.qwen_enabled = qwen_enabled
        self.call_count = 0
        self.cache_store = {}

    def decide(self, omr_confidence=None, is_blank=False, omr_clear=True,
               image_sha256="", roi_id="") -> QwenPolicyDecision:
        routing = should_use_qwen(omr_confidence, is_blank, self.qwen_enabled,
                                   budget_ok=(self.call_count < self.max_calls), omr_clear=omr_clear)
        if not routing.qwen_allowed:
            if "DISABLED" in routing.reason:
                return QwenPolicyDecision(reason="qwen_disabled", fallback_status="needs_review",
                                           review_reason="qwen_disabled")
            if "OMR_HIGH" in routing.reason:
                return QwenPolicyDecision(reason="omr_high_confidence", fallback_status="auto_accepted")
            if "BUDGET" in routing.reason:
                return QwenPolicyDecision(reason="budget_exceeded", blocked_by_budget=True,
                                           fallback_status="needs_review", review_reason="qwen_budget_exceeded")
            return QwenPolicyDecision(reason=routing.reason, fallback_status="needs_review")

        # Cache check
        if image_sha256 and roi_id:
            key = build_cache_key(image_sha256, roi_id)
            if key.to_key() in self.cache_store:
                return QwenPolicyDecision(reason="cache_hit", cache_hit=True,
                                           fallback_status="auto_accepted")

        if self.call_count >= self.max_calls:
            return QwenPolicyDecision(blocked_by_budget=True,
                                       fallback_status="needs_review", review_reason="qwen_budget_exceeded")

        self.call_count += 1
        return QwenPolicyDecision(should_call_qwen=True, qwen_call_allowed=True,
                                   reason="qwen_needed", fallback_status="auto_accepted")

    def summary(self) -> dict:
        return {"call_count": self.call_count, "max_calls": self.max_calls,
                "blocked_by_budget": max(0, 0), "cache_hits": len(self.cache_store)}
