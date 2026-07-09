"""Tests for readiness gate with fake replay integration — R384."""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


class ReadinessGateFakeReplayIntegrationTests(unittest.TestCase):
    def test_readiness_gate_importable(self):
        from app.recognition.real_paper_readiness_gate import check_readiness
        self.assertTrue(callable(check_readiness))

    def test_readiness_gate_default_blocked(self):
        from app.recognition.real_paper_readiness_gate import check_readiness
        result = check_readiness()
        self.assertFalse(result.ready_for_single_real_qwen_trial)

    def test_readiness_gate_no_fake_replay_disables_real(self):
        from app.recognition.real_paper_readiness_gate import check_readiness
        result = check_readiness()
        self.assertGreater(len(result.blockers), 0)

    def test_readiness_gate_has_checks(self):
        from app.recognition.real_paper_readiness_gate import check_readiness
        result = check_readiness()
        self.assertFalse(result.ready_for_single_real_qwen_trial)


if __name__ == "__main__":
    unittest.main()
