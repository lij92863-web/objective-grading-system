import unittest

from app.recognition.qwen_adapter.policy_orchestrator import QwenPolicyOrchestrator
from app.recognition.qwen_adapter.cache_policy import build_cache_key


class QwenPolicyOrchestratorCounterTests(unittest.TestCase):
    def test_initial_counters_zero(self):
        self.assertEqual(QwenPolicyOrchestrator().summary()["total_items_seen"], 0)

    def test_high_confidence_omr_increments_skipped(self):
        policy = QwenPolicyOrchestrator(qwen_enabled=True)
        policy.decide(omr_confidence=0.99, omr_clear=True)
        self.assertEqual(policy.summary()["qwen_call_skipped_count"], 1)

    def test_ambiguous_item_within_budget_increments_allowed(self):
        policy = QwenPolicyOrchestrator(max_qwen_calls=1, qwen_enabled=True)
        policy.decide(omr_confidence=0.50, omr_clear=False)
        self.assertEqual(policy.summary()["qwen_call_allowed_count"], 1)

    def test_budget_exceeded_increments_blocked(self):
        policy = QwenPolicyOrchestrator(max_qwen_calls=0, qwen_enabled=True)
        policy.decide(omr_confidence=0.50, omr_clear=False)
        self.assertEqual(policy.summary()["blocked_by_budget_count"], 1)

    def test_cache_hit_increments_cache_hit(self):
        policy = QwenPolicyOrchestrator(qwen_enabled=True)
        key = build_cache_key("abc", "q1").to_key()
        policy.cache_store[key] = {"answer": "A"}
        policy.decide(omr_confidence=0.50, omr_clear=False, image_sha256="abc", roi_id="q1")
        self.assertEqual(policy.summary()["cache_hit_count"], 1)

    def test_qwen_disabled_increments_disabled(self):
        policy = QwenPolicyOrchestrator(qwen_enabled=False)
        policy.decide(omr_confidence=0.50, omr_clear=False)
        self.assertEqual(policy.summary()["disabled_count"], 1)


if __name__ == "__main__":
    unittest.main()
