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
        self.total_items_seen = 0
        self.qwen_needed_count = 0
        self.qwen_call_allowed_count = 0
        self.qwen_call_skipped_count = 0
        self.blocked_by_budget_count = 0
        self.cache_hit_count = 0
        self.retry_allowed_count = 0
        self.retry_denied_count = 0
        self.disabled_count = 0

    def decide(self, omr_confidence=None, is_blank=False, omr_clear=True,
               image_sha256="", roi_id="") -> QwenPolicyDecision:
        self.total_items_seen += 1
        routing = should_use_qwen(omr_confidence, is_blank, self.qwen_enabled,
                                   budget_ok=(self.call_count < self.max_calls), omr_clear=omr_clear)
        if not routing.qwen_allowed:
            if "DISABLED" in routing.reason:
                self.disabled_count += 1
                return QwenPolicyDecision(reason="qwen_disabled", fallback_status="needs_review",
                                           review_reason="qwen_disabled")
            if "OMR_HIGH" in routing.reason:
                self.qwen_call_skipped_count += 1
                return QwenPolicyDecision(reason="omr_high_confidence", fallback_status="auto_accepted")
            if "BUDGET" in routing.reason:
                self.qwen_needed_count += 1
                self.blocked_by_budget_count += 1
                return QwenPolicyDecision(reason="budget_exceeded", blocked_by_budget=True,
                                           fallback_status="needs_review", review_reason="qwen_budget_exceeded")
            return QwenPolicyDecision(reason=routing.reason, fallback_status="needs_review")

        # Cache check
        self.qwen_needed_count += 1
        if image_sha256 and roi_id:
            key = build_cache_key(image_sha256, roi_id)
            if key.to_key() in self.cache_store:
                self.cache_hit_count += 1
                return QwenPolicyDecision(reason="cache_hit", cache_hit=True,
                                           fallback_status="auto_accepted")

        if self.call_count >= self.max_calls:
            self.blocked_by_budget_count += 1
            return QwenPolicyDecision(blocked_by_budget=True,
                                       fallback_status="needs_review", review_reason="qwen_budget_exceeded")

        self.call_count += 1
        self.qwen_call_allowed_count += 1
        return QwenPolicyDecision(should_call_qwen=True, qwen_call_allowed=True,
                                   reason="qwen_needed", fallback_status="auto_accepted")

    def summary(self) -> dict:
        return {
            "call_count": self.call_count,
            "max_calls": self.max_calls,
            "total_items_seen": self.total_items_seen,
            "qwen_needed_count": self.qwen_needed_count,
            "qwen_call_allowed_count": self.qwen_call_allowed_count,
            "qwen_call_skipped_count": self.qwen_call_skipped_count,
            "blocked_by_budget_count": self.blocked_by_budget_count,
            "cache_hit_count": self.cache_hit_count,
            "retry_allowed_count": self.retry_allowed_count,
            "retry_denied_count": self.retry_denied_count,
            "disabled_count": self.disabled_count,
            "blocked_by_budget": self.blocked_by_budget_count,
            "cache_hits": self.cache_hit_count,
        }
