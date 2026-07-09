import unittest

from app.recognition.small_batch_gate import check_small_batch_gate


class SmallBatchGateAfterSingleImagePrepTests(unittest.TestCase):
    def test_single_image_prep_does_not_open_small_batch(self):
        report = check_small_batch_gate(
            single_anonymous_image_trial_passed=True,
            fixture_driven_batch_passed=True,
            model_driven_summary_passed=True,
            qwen_budget_truth_passed=True,
            identity_policy_passed=True,
            review_queue_policy_passed=True,
            no_real_data_leak=True,
        )
        self.assertFalse(report.ready_for_small_batch)
        self.assertIn("THREE_IMAGE_TRIAL_NOT_PASSED", report.blockers)


if __name__ == "__main__":
    unittest.main()
