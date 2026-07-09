import json
import unittest
from pathlib import Path

from app.recognition.single_image_manifest import SingleImageManifest, validate_single_image_manifest


FIXTURE = Path("tests/fixtures/recognition/single_image/demo_single_image_manifest.json")


class SingleImageManifestTests(unittest.TestCase):
    def data(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_valid_manifest(self):
        self.assertTrue(validate_single_image_manifest(SingleImageManifest.from_dict(self.data()))["valid"])

    def test_non_anonymous_fails(self):
        data = self.data()
        data["is_anonymous"] = False
        self.assertIn("IMAGE_NOT_ANONYMOUS", validate_single_image_manifest(SingleImageManifest.from_dict(data))["blockers"])

    def test_real_student_data_fails(self):
        data = self.data()
        data["contains_real_student_data"] = True
        self.assertIn("REAL_STUDENT_DATA_PRESENT", validate_single_image_manifest(SingleImageManifest.from_dict(data))["blockers"])

    def test_unsupported_mime_fails(self):
        data = self.data()
        data["mime_type"] = "image/gif"
        self.assertIn("UNSUPPORTED_MIME_TYPE", validate_single_image_manifest(SingleImageManifest.from_dict(data))["blockers"])

    def test_zero_size_fails(self):
        data = self.data()
        data["file_size_bytes"] = 0
        self.assertIn("INVALID_FILE_SIZE", validate_single_image_manifest(SingleImageManifest.from_dict(data))["blockers"])

    def test_base64_field_fails(self):
        data = self.data()
        data["image_base64"] = "abc"
        with self.assertRaises(ValueError):
            SingleImageManifest.from_dict(data)

    def test_json_round_trip(self):
        manifest = SingleImageManifest.from_dict(self.data())
        self.assertEqual(manifest.to_dict(), SingleImageManifest.from_dict(manifest.to_dict()).to_dict())

    def test_missing_template_and_roi_warn(self):
        data = self.data()
        data["template_id"] = ""
        data["roi_file"] = ""
        result = validate_single_image_manifest(SingleImageManifest.from_dict(data))
        self.assertIn("MISSING_TEMPLATE_ID", result["warnings"])
        self.assertIn("MISSING_ROI_FILE", result["warnings"])


if __name__ == "__main__":
    unittest.main()
