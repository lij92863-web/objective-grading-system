import tempfile
import unittest
from pathlib import Path

from scripts.student_recognition.run_sre_algorithm_audit import run_audit


class TestAlgorithmAuditRepair(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
