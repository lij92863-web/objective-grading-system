import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests/fixtures/recognition/single_image/demo_single_image_manifest.json"


class ValidateSingleImageManifestCliTests(unittest.TestCase):
    def test_valid_fixture_returncode_zero(self):
        result = _run([str(MANIFEST), "--json"])
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_non_anonymous_returncode_nonzero(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        data["is_anonymous"] = False
        result = _run([_tmp_json(data), "--json"])
        self.assertNotEqual(result.returncode, 0)

    def test_real_student_data_returncode_nonzero(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        data["contains_real_student_data"] = True
        result = _run([_tmp_json(data), "--json"])
        self.assertNotEqual(result.returncode, 0)

    def test_json_parseable_and_no_api(self):
        result = _run([str(MANIFEST), "--json"])
        output = json.loads(result.stdout)
        self.assertIn("manifest_summary", output)
        self.assertNotIn("api", result.stdout.lower())


def _run(args):
    return subprocess.run([sys.executable, str(ROOT / "scripts/validate_single_image_manifest.py"), "--manifest", *args],
                          capture_output=True, text=True, timeout=10)


def _tmp_json(data):
    handle = tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8")
    json.dump(data, handle)
    handle.close()
    return handle.name


if __name__ == "__main__":
    unittest.main()
