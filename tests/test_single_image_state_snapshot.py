import unittest

from app.recognition.state_snapshot import RecognitionStateSnapshot


class SingleImageStateSnapshotTests(unittest.TestCase):
    def test_single_image_fields_are_safe(self):
        snapshot = RecognitionStateSnapshot(
            snapshot_type="single_image_trial",
            manifest_summary={"image_name": "demo.png"},
            roi_summary={"total_roi_count": 1},
            dry_run_summary={"real_api_called": False},
            readiness_summary={"ready_for_real_api": False},
        )
        data = snapshot.to_safe_dict()
        self.assertEqual(data["snapshot_type"], "single_image_trial")
        self.assertIn("manifest_summary", data)
        self.assertIn("roi_summary", data)


if __name__ == "__main__":
    unittest.main()
