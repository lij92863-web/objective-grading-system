"""Tests for the GroundTruth serialization and mark-type validation."""

import unittest

from app.student_recognition.synthetic.ground_truth import (
    MARK_TYPES,
    AnswerRecord,
    GroundTruth,
)


class TestGroundTruthRoundTrip(unittest.TestCase):
    def _sample_gt(self) -> GroundTruth:
        return GroundTruth(
            sheet_id="sheet-000",
            template_id="synthetic-v1",
            student={"student_id": "20240001", "name": "学生01"},
            answers=[
                AnswerRecord(question=0, selected="A", mark_type="strong", expected_option="A"),
                AnswerRecord(question=1, selected=None, mark_type="none", expected_option="B"),
                AnswerRecord(question=2, selected="C", mark_type="multi", expected_option="C"),
                AnswerRecord(question=3, selected="D", mark_type="erased", expected_option="D"),
                AnswerRecord(question=4, selected="B", mark_type="weak", expected_option="B"),
            ],
            perturbation="clean",
            seed=12345,
        )

    def test_to_dict_from_dict_roundtrip(self):
        gt = self._sample_gt()
        gt2 = GroundTruth.from_dict(gt.to_dict())
        self.assertEqual(gt.to_dict(), gt2.to_dict())

    def test_name_only_student_allowed(self):
        gt = GroundTruth(
            sheet_id="sheet-001",
            template_id="synthetic-v1",
            student={"name": "无名01"},
            answers=[AnswerRecord(question=0, selected="A", mark_type="strong", expected_option="A")],
            perturbation="clean",
            seed=1,
        )
        gt2 = GroundTruth.from_dict(gt.to_dict())
        self.assertEqual(gt2.student, {"name": "无名01"})


class TestMarkTypeValidation(unittest.TestCase):
    def test_invalid_mark_type_rejected(self):
        bad = {
            "sheet_id": "x",
            "template_id": "synthetic-v1",
            "student": {"name": "n"},
            "answers": [
                {"question": 0, "selected": "A", "mark_type": "bogus", "expected_option": "A"}
            ],
            "perturbation": "clean",
            "seed": 0,
        }
        with self.assertRaises(ValueError):
            GroundTruth.from_dict(bad)

    def test_all_valid_mark_types_accepted(self):
        for mt in MARK_TYPES:
            rec = AnswerRecord.from_dict(
                {
                    "question": 0,
                    "selected": "A" if mt != "none" else None,
                    "mark_type": mt,
                    "expected_option": "A",
                }
            )
            self.assertEqual(rec.mark_type, mt)

    def test_none_mark_has_no_selected(self):
        rec = AnswerRecord.from_dict(
            {"question": 0, "selected": None, "mark_type": "none", "expected_option": "A"}
        )
        self.assertIsNone(rec.selected)
        self.assertEqual(rec.mark_type, "none")


if __name__ == "__main__":
    unittest.main()
