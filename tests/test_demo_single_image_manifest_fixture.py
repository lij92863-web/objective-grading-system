import unittest
from pathlib import Path

from app.recognition.single_image_manifest import load_single_image_manifest, validate_single_image_manifest


class DemoSingleImageManifestFixtureTests(unittest.TestCase):
    def test_fixture_loadable_and_safe(self):
        manifest = load_single_image_manifest("tests/fixtures/recognition/single_image/demo_single_image_manifest.json")
        result = validate_single_image_manifest(manifest)
        self.assertTrue(result["valid"])
        self.assertTrue(manifest.is_anonymous)
        self.assertFalse(manifest.contains_real_student_data)
        self.assertTrue(manifest.image_path.startswith("data/tmp/"))
        self.assertFalse(Path(manifest.image_path).exists())
        self.assertNotIn("base64", str(manifest.to_dict()).lower())


if __name__ == "__main__":
    unittest.main()
