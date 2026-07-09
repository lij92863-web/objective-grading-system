"""Tests for the SyntheticSheetGenerator: determinism and self-consistency.

These tests prove the generator is *self-consistent* (strong marks are darker
than empty ones, same seed -> same bytes). They do NOT perform OMR recognition
and never reference ``omr_policy`` thresholds (constitution boundary lock).
"""

import unittest

from app.student_recognition.synthetic.generator import SyntheticSheetGenerator
from app.student_recognition.synthetic.ground_truth import AnswerRecord, GroundTruth
from app.student_recognition.synthetic.raster import read_png_bytes
from app.student_recognition.synthetic.template_profile import build_default_template


def _gt_with(answers, perturbation="clean", seed=42):
    return GroundTruth(
        sheet_id="sheet-test",
        template_id="synthetic-v1",
        student={"name": "t"},
        answers=answers,
        perturbation=perturbation,
        seed=seed,
    )


class TestGeneratorDeterminism(unittest.TestCase):
    def test_same_seed_produces_identical_bytes(self):
        tp = build_default_template()
        answers = [
            AnswerRecord(question=0, selected="A", mark_type="strong", expected_option="A"),
            AnswerRecord(question=1, selected="B", mark_type="weak", expected_option="B"),
        ]
        gt = _gt_with(answers)
        b1, _ = SyntheticSheetGenerator.build(tp, gt)
        b2, _ = SyntheticSheetGenerator.build(tp, gt)
        self.assertEqual(b1, b2)

    def test_different_seed_produces_different_bytes_for_noisy_perturbation(self):
        tp = build_default_template()
        answers = [
            AnswerRecord(question=0, selected="A", mark_type="strong", expected_option="A"),
        ]
        gt_a = _gt_with(answers, perturbation="add_gaussian_noise", seed=1)
        gt_b = _gt_with(answers, perturbation="add_gaussian_noise", seed=2)
        b_a, _ = SyntheticSheetGenerator.build(tp, gt_a, gt_a.perturbation)
        b_b, _ = SyntheticSheetGenerator.build(tp, gt_b, gt_b.perturbation)
        self.assertNotEqual(b_a, b_b)

    def test_build_returns_bytes_and_echoed_gt(self):
        tp = build_default_template()
        gt = _gt_with([AnswerRecord(question=0, selected="A", mark_type="none", expected_option="A")])
        data, out_gt = SyntheticSheetGenerator.build(tp, gt)
        self.assertIsInstance(data, bytes)
        self.assertIs(out_gt, gt)


class TestGeneratorSelfConsistency(unittest.TestCase):
    def test_strong_center_darker_than_none_center(self):
        tp = build_default_template()
        # Question 0 strongly filled at A; question 1 left empty (none).
        answers = [
            AnswerRecord(question=0, selected="A", mark_type="strong", expected_option="A"),
            AnswerRecord(question=1, selected=None, mark_type="none", expected_option="B"),
        ]
        gt = _gt_with(answers)
        data, _ = SyntheticSheetGenerator.build(tp, gt, "clean")
        width, height, pixels = read_png_bytes(data)

        ax, ay = tp.cell_center(0, 0)  # strong
        bx, by = tp.cell_center(1, 0)  # none

        strong_intensity = pixels[(ay * width + ax) * 3]
        none_intensity = pixels[(by * width + bx) * 3]

        self.assertLess(strong_intensity, 100, "strong mark centre should be dark")
        self.assertGreater(none_intensity, 200, "empty bubble centre should be white")

    def test_unknown_perturbation_raises(self):
        tp = build_default_template()
        gt = _gt_with([AnswerRecord(question=0, selected="A", mark_type="strong", expected_option="A")])
        with self.assertRaises(ValueError):
            SyntheticSheetGenerator.build(tp, gt, "not_a_real_perturbation")


if __name__ == "__main__":
    unittest.main()
