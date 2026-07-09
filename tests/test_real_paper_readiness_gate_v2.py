import unittest

from app.recognition.real_paper_readiness_gate import check_readiness


class RealPaperReadinessGateV2Tests(unittest.TestCase):
    def test_default_false(self):
        report = check_readiness()
        self.assertFalse(report.ready_for_single_real_qwen_trial)
        self.assertFalse(report.has_fixture_driven_batch)


if __name__ == "__main__":
    unittest.main()
