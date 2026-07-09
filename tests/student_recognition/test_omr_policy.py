"""OMR policy stub tests (constitution §7 placeholder)."""

import unittest

from app.student_recognition.omr_policy import (
    STRONG_MARK_DARK_RATIO,
    default_policy,
)


class TestOMRPolicy(unittest.TestCase):
    def test_default_policy_has_thresholds(self):
        p = default_policy()
        self.assertGreater(p.strong_mark_dark_ratio, p.weak_mark_dark_ratio)
        self.assertGreater(p.weak_mark_dark_ratio, p.empty_mark_dark_ratio)
        self.assertEqual(p.strong_mark_dark_ratio, STRONG_MARK_DARK_RATIO)
        self.assertIn("strong_mark_dark_ratio", p.as_dict())


if __name__ == "__main__":
    unittest.main()
