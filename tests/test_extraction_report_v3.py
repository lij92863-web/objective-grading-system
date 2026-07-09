from __future__ import annotations

import unittest

from app.answer_extraction.extraction_report import ExtractionReport


class ExtractionReportV3Tests(unittest.TestCase):
    def _report(self, **overrides) -> ExtractionReport:
        defaults = dict(
            run_id="r1", strategy="same_file_boxed",
            file_roles={}, answer_layouts={},
            question_count=5, answer_count=5, accepted_count=5,
            missing_answers=[], unexpected_answers=[], duplicate_answers=[],
            warnings=[], blocking_errors=[], review_items=[],
        )
        defaults.update(overrides)
        return ExtractionReport(**defaults)

    def test_ignored_student_answer_grid_count_default(self):
        r = self._report()
        self.assertEqual(r.ignored_student_answer_grid_count, 0)

    def test_ignored_student_answer_grid_count_set(self):
        r = self._report(ignored_student_answer_grid_count=3)
        self.assertEqual(r.ignored_student_answer_grid_count, 3)

    def test_explicit_bracket_answer_count(self):
        r = self._report(explicit_bracket_answer_count=5)
        self.assertEqual(r.explicit_bracket_answer_count, 5)

    def test_answer_table_count(self):
        r = self._report(answer_table_count=10)
        self.assertEqual(r.answer_table_count, 10)

    def test_itemized_answer_count(self):
        r = self._report(itemized_answer_count=8)
        self.assertEqual(r.itemized_answer_count, 8)

    def test_blank_answer_count(self):
        r = self._report(blank_answer_count=2)
        self.assertEqual(r.blank_answer_count, 2)

    def test_conflict_count(self):
        r = self._report(conflict_count=1)
        self.assertEqual(r.conflict_count, 1)

    def test_evidence_missing_count_default(self):
        r = self._report()
        self.assertEqual(r.evidence_missing_count, 0)

    def test_review_and_blocked_counts(self):
        r = self._report(accepted_count=3, review_items=[{"type": "x"}] * 2, blocking_errors=["e1"])
        self.assertEqual(r.accepted_count, 3)
        self.assertEqual(len(r.review_items), 2)
        self.assertEqual(len(r.blocking_errors), 1)

    def test_to_safe_dict_includes_all_fields(self):
        r = self._report(ignored_student_answer_grid_count=1, explicit_bracket_answer_count=3,
                          answer_table_count=2, itemized_answer_count=3, blank_answer_count=1,
                          conflict_count=0, evidence_missing_count=0)
        d = r.to_safe_dict()
        for key in ("ignored_student_answer_grid_count", "explicit_bracket_answer_count",
                     "answer_table_count", "itemized_answer_count", "blank_answer_count",
                     "conflict_count", "evidence_missing_count"):
            self.assertIn(key, d)

    def test_file_roles_and_answer_layouts_serialized(self):
        r = self._report(file_roles={"a.json": "mixed"}, answer_layouts={"a.json": "boxed_table"})
        d = r.to_safe_dict()
        self.assertEqual(d["file_roles"], {"a.json": "mixed"})
        self.assertEqual(d["answer_layouts"], {"a.json": "boxed_table"})


if __name__ == "__main__":
    unittest.main()
