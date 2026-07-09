import unittest
from pathlib import Path


PATHS = [
    "app/recognition/single_image_manifest.py",
    "app/recognition/manual_roi_schema.py",
    "app/recognition/single_image_trial_context.py",
    "app/recognition/single_image_dry_run.py",
    "app/recognition/single_image_trial_report.py",
    "scripts/validate_single_image_manifest.py",
    "scripts/validate_manual_roi.py",
    "scripts/run_single_image_dry_run.py",
    "scripts/check_single_image_qwen_readiness.py",
    "scripts/write_single_image_trial_report.py",
    "scripts/run_single_image_state_snapshot.py",
]


class SingleImageNoFormalReportGuardTests(unittest.TestCase):
    def test_no_forbidden_report_or_grading_imports(self):
        offenders = []
        forbidden = ("workflow", "objective_grader", "report_builders", "exporters", "grade_all")
        for file_path in PATHS:
            text = Path(file_path).read_text(encoding="utf-8")
            sanitized = text.replace("grade_all_called", "")
            for term in forbidden:
                if term in sanitized:
                    offenders.append(f"{file_path}:{term}")
        self.assertEqual(offenders, [])

    def test_no_formal_file_writes(self):
        offenders = []
        for file_path in PATHS:
            text = Path(file_path).read_text(encoding="utf-8")
            for suffix in (".csv", ".xlsx", ".html"):
                if suffix in text:
                    offenders.append(f"{file_path}:{suffix}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
