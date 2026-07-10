import tempfile
import unittest
from pathlib import Path

from scripts.student_recognition.run_sre_algorithm_audit import run_audit


class TestAlgorithmAuditRepair(unittest.TestCase):
    def _temporary_source(self, source):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        template = root / "app" / "student_recognition" / "template"
        omr = root / "app" / "student_recognition" / "omr"
        template.mkdir(parents=True)
        omr.mkdir(parents=True)
        (template / "anchor_layout.py").write_text("VALUE = 1\n", encoding="utf-8")
        (omr / "single_choice_recognizer.py").write_text(source, encoding="utf-8")
        return temporary, root

    def test_algorithm_audit_fails_on_silent_clamp(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            template = root / "app" / "student_recognition" / "template"
            template.mkdir(parents=True)
            (template / "anchor_layout.py").write_text(
                "def _clamp_roi(roi):\n    return roi\n",
                encoding="utf-8",
            )
            result = run_audit(root)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(
            any(item["check"] == "silent_clamp" for item in result["findings"])
        )

    def test_algorithm_audit_fails_on_ground_truth_leak(self):
        temporary, root = self._temporary_source("ground_truth = {}\n")
        with temporary:
            result = run_audit(root)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(item["check"] == "gt_leak" for item in result["findings"]))

    def test_algorithm_audit_fails_on_magic_threshold_outside_policy(self):
        temporary, root = self._temporary_source(
            "def recognize(score):\n    return score > 0.65\n"
        )
        with temporary:
            result = run_audit(root)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(
            any(item["check"] == "magic_threshold" for item in result["findings"])
        )


if __name__ == "__main__":
    unittest.main()
