import unittest
from pathlib import Path


SCRIPTS = [
    "scripts/validate_single_image_manifest.py",
    "scripts/validate_manual_roi.py",
    "scripts/run_single_image_dry_run.py",
    "scripts/check_single_image_qwen_readiness.py",
    "scripts/write_single_image_trial_report.py",
]


class SingleImageNoRealApiGuardTests(unittest.TestCase):
    def test_scripts_do_not_read_env_or_call_real_client(self):
        offenders = []
        for script in SCRIPTS:
            text = Path(script).read_text(encoding="utf-8")
            for forbidden in ("dotenv", ".env", "QWEN_API_KEY", "RealQwenClient", "requests.post", "Authorization"):
                if forbidden in text:
                    offenders.append(f"{script}:{forbidden}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
