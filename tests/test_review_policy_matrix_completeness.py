import unittest

from app.recognition.error_codes import all_codes
from app.recognition.review_policy_matrix import lookup_policy


class ReviewPolicyMatrixCompletenessTests(unittest.TestCase):
    def test_every_known_error_code_has_complete_policy(self):
        for code in all_codes():
            policy = lookup_policy(code)
            self.assertNotEqual(policy["item_type"], "unknown", code)
            self.assertIn("severity", policy)
            self.assertIn("allowed_actions", policy)


if __name__ == "__main__":
    unittest.main()
