"""Tests for ExamMeta contract — D2."""

import unittest

from app.application.contracts.exam_metadata import ExamMeta as NewExamMeta


class ExamMetaContractTests(unittest.TestCase):
    def test_fields_match_legacy(self):
        legacy_fields = {"exam_name", "class_name", "subject", "exam_date"}
        new_fields = {f.name for f in NewExamMeta.__dataclass_fields__.values()}
        self.assertEqual(legacy_fields, new_fields)

    def test_defaults_match_legacy(self):
        m = NewExamMeta()
        self.assertEqual(m.exam_name, "")
        self.assertEqual(m.class_name, "")
        self.assertEqual(m.subject, "")
        self.assertEqual(m.exam_date, "")

    def test_construct_and_access(self):
        m = NewExamMeta(exam_name="test", class_name="c",
                        subject="s", exam_date="2026-07-09")
        self.assertEqual(m.exam_name, "test")
        self.assertEqual(m.exam_date, "2026-07-09")

    def test_no_legacy_import(self):
        import ast
        from pathlib import Path
        src = (Path(__file__).parents[1] / "app" / "application"
               / "contracts" / "exam_metadata.py").read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("legacy", node.module)


if __name__ == "__main__":
    unittest.main()
