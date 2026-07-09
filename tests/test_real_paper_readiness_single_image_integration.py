import unittest

from app.recognition.real_paper_readiness_gate import check_readiness


class RealPaperReadinessSingleImageIntegrationTests(unittest.TestCase):
    def test_all_single_image_preconditions_true_allows_single_trial_only(self):
        report = check_readiness(
            has_anonymous_image=True,
            manifest_valid=True,
            roi_valid=True,
            identity_roi_present=True,
            single_image_dry_run_passed=True,
            qwen_check_only_passed=True,
            artifact_policy_passed=True,
        )
        self.assertTrue(report.ready_for_single_real_qwen_trial)
        self.assertFalse(report.ready_for_small_batch_trial)

    def test_manifest_only_false(self):
        self.assertFalse(check_readiness(has_anonymous_image=True, manifest_valid=True).ready_for_single_real_qwen_trial)


if __name__ == "__main__":
    unittest.main()
