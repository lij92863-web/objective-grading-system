import subprocess
import unittest
from pathlib import Path


class SingleImageArtifactGuardTests(unittest.TestCase):
    def test_no_tracked_real_image_in_single_image_fixtures(self):
        tracked = subprocess.run(["git", "ls-files", "tests/fixtures/recognition/single_image"],
                                 capture_output=True, text=True, timeout=10).stdout.splitlines()
        images = [path for path in tracked if Path(path).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
        self.assertEqual(images, [])

    def test_no_data_tmp_or_reports_tracked(self):
        tmp = subprocess.run(["git", "ls-files", "data/tmp"], capture_output=True, text=True, timeout=10).stdout.strip()
        reports = subprocess.run(["git", "ls-files", "data/reports"], capture_output=True, text=True, timeout=10).stdout.strip()
        self.assertEqual(tmp, "")
        self.assertEqual(reports, "")

    def test_no_raw_response_or_base64_payload(self):
        for path in Path("tests/fixtures/recognition/single_image").glob("*.json"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("raw_response", text)
            self.assertNotIn("data:image", text)


if __name__ == "__main__":
    unittest.main()
