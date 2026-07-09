import unittest

from app.recognition.manual_roi_schema import load_manual_roi_file
from app.recognition.single_image_manifest import load_single_image_manifest
from app.recognition.single_image_trial_context import build_single_image_trial_context


MANIFEST = "tests/fixtures/recognition/single_image/demo_single_image_manifest.json"
ROI = "tests/fixtures/recognition/single_image/demo_manual_roi.json"


class SingleImageTrialContextTests(unittest.TestCase):
    def test_valid_context_ready_for_check_only(self):
        context = build_single_image_trial_context(load_single_image_manifest(MANIFEST), load_manual_roi_file(ROI))
        self.assertTrue(context.ready_for_qwen_check_only)
        self.assertFalse(context.ready_for_real_api)

    def test_missing_manifest_blocks(self):
        self.assertIn("MISSING_MANIFEST", build_single_image_trial_context(None, load_manual_roi_file(ROI)).blockers)

    def test_missing_roi_blocks(self):
        self.assertIn("MISSING_ROI_FILE", build_single_image_trial_context(load_single_image_manifest(MANIFEST), None).blockers)

    def test_non_anonymous_blocks(self):
        manifest = load_single_image_manifest(MANIFEST)
        manifest.is_anonymous = False
        self.assertIn("IMAGE_NOT_ANONYMOUS", build_single_image_trial_context(manifest, load_manual_roi_file(ROI)).blockers)

    def test_real_student_data_blocks(self):
        manifest = load_single_image_manifest(MANIFEST)
        manifest.contains_real_student_data = True
        self.assertIn("REAL_STUDENT_DATA_PRESENT", build_single_image_trial_context(manifest, load_manual_roi_file(ROI)).blockers)

    def test_missing_identity_blocks(self):
        roi_file = load_manual_roi_file(ROI)
        roi_file.identity_rois = []
        self.assertIn("MISSING_IDENTITY_ROI", build_single_image_trial_context(load_single_image_manifest(MANIFEST), roi_file).blockers)

    def test_allow_real_api_still_blocks_this_stage(self):
        context = build_single_image_trial_context(load_single_image_manifest(MANIFEST), load_manual_roi_file(ROI), allow_real_api=True, api_key_present=True)
        self.assertFalse(context.ready_for_real_api)
        self.assertIn("REAL_API_NOT_ALLOWED_IN_THIS_STAGE", context.blockers)

    def test_counts(self):
        context = build_single_image_trial_context(load_single_image_manifest(MANIFEST), load_manual_roi_file(ROI))
        self.assertGreater(context.roi_count, 0)
        self.assertEqual(context.blank_question_count, 2)


if __name__ == "__main__":
    unittest.main()
