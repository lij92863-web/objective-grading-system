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


def _collect(test, out):
    if isinstance(test, unittest.TestSuite):
        for sub in test:
            _collect(sub, out)
    else:
        out.append(test)


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

    def test_sre121_tests_still_pass(self):
        # Guard: run the full legacy (non-template) suite to prove no regression
        # in the existing SRE121 tests (must remain green).
        loader = unittest.TestLoader()
        discovered = loader.discover(
            "tests/student_recognition", pattern="test*.py", top_level_dir="."
        )
        all_tests = []
        _collect(discovered, all_tests)
        pruned = unittest.TestSuite()
        kept = 0
        for t in all_tests:
            mod = t.__class__.__module__ or ""
            if "template" in mod:
                continue
            pruned.addTest(t)
            kept += 1
        self.assertGreater(kept, 100, "expected to retain the legacy ~123 tests")
        result = unittest.TextTestRunner(verbosity=0).run(pruned)
        self.assertTrue(
            result.wasSuccessful(),
            f"legacy SRE121 regression: {len(result.errors)} errors, "
            f"{len(result.failures)} failures",
        )


if __name__ == "__main__":
    unittest.main()
