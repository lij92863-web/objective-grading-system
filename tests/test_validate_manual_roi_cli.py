import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROI = ROOT / "tests/fixtures/recognition/single_image/demo_manual_roi.json"


class ValidateManualROICliTests(unittest.TestCase):
    def test_valid_roi_returncode_zero(self):
        result = _run(str(ROI))
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_missing_identity_fails(self):
        data = json.loads(ROI.read_text(encoding="utf-8"))
        data["identity_rois"] = []
        self.assertNotEqual(_run(_tmp_json(data)).returncode, 0)

    def test_out_of_bounds_fails(self):
        data = json.loads(ROI.read_text(encoding="utf-8"))
        data["question_rois"][0]["x"] = 9999
        self.assertNotEqual(_run(_tmp_json(data)).returncode, 0)

    def test_negative_coordinate_fails(self):
        data = json.loads(ROI.read_text(encoding="utf-8"))
        data["question_rois"][0]["x"] = -1
        self.assertNotEqual(_run(_tmp_json(data)).returncode, 0)

    def test_zero_size_fails(self):
        data = json.loads(ROI.read_text(encoding="utf-8"))
        data["question_rois"][0]["width"] = 0
        self.assertNotEqual(_run(_tmp_json(data)).returncode, 0)


def _run(path):
    return subprocess.run([sys.executable, str(ROOT / "scripts/validate_manual_roi.py"), "--roi", path, "--json"],
                          capture_output=True, text=True, timeout=10)


def _tmp_json(data):
    handle = tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8")
    json.dump(data, handle)
    handle.close()
    return handle.name


if __name__ == "__main__":
    unittest.main()
