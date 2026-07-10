"""SRE945 §15.8 -- Synthetic (SRE121) v1 -> v2 compatibility tests.

These are CI guards: any change that breaks the synthetic layer or its fixtures
must be caught here (constitution: SRE121's 123 tests must stay green, and the
synthetic module/fixtures must NOT be modified by this stage).
"""

import unittest

from app.student_recognition.synthetic.ground_truth import GroundTruth
from app.student_recognition.synthetic.generator import SyntheticSheetGenerator
from app.student_recognition.synthetic.template_profile import build_default_template
from app.student_recognition.template.compatibility import adapt_synthetic_to_v2
from app.student_recognition.template.template_profile import TemplateProfile
from app.student_recognition.template.template_validator import TemplateValidator


class TestSyntheticCompat(unittest.TestCase):
    def test_synthetic_template_profile_still_valid(self):
        synth = build_default_template()
        profile = adapt_synthetic_to_v2(synth)
        self.assertIsInstance(profile, TemplateProfile)
        report = TemplateValidator().validate(profile)
        self.assertEqual(report.status, "valid", report.errors)

    def test_adapter_produces_normalized_coordinates(self):
        synth = build_default_template()
        profile = adapt_synthetic_to_v2(synth)
        for cell in profile.get_all_option_cells():
            roi = cell.roi
            for v in (roi["x"], roi["y"], roi["w"], roi["h"]):
                self.assertGreaterEqual(v, 0.0)
                self.assertLessEqual(v, 1.0)

    def test_synthetic_fixtures_still_generate(self):
        synth = build_default_template()
        gt = GroundTruth(
            sheet_id="blank",
            template_id="synthetic-v1",
            student={},
            answers=[],
            perturbation="clean",
            seed=1,
        )
        png, _ = SyntheticSheetGenerator.build(synth, gt, "clean")
        self.assertIsInstance(png, bytes)
        self.assertGreater(len(png), 0)

    def test_sre121_modules_remain_importable(self):
        # Normal discovery executes the synthetic suite once; never nest a runner.
        self.assertTrue(callable(SyntheticSheetGenerator))
        self.assertTrue(callable(GroundTruth))


if __name__ == "__main__":
    unittest.main()
