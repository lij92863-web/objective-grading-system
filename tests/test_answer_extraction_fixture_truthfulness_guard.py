from __future__ import annotations

import unittest
from pathlib import Path


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "answer_extraction"
TESTS_ROOT = Path(__file__).resolve().parent


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


class FixtureTruthfulnessGuardTests(unittest.TestCase):
    def test_real_chinese_bracket_fixtures_use_real_marker(self):
        paths = list(FIXTURE_ROOT.rglob("*real_chinese_brackets*"))
        paths += list(FIXTURE_ROOT.rglob("*real_brackets*"))
        self.assertTrue(len(paths) > 0, "Expected real bracket fixtures to exist")
        for path in paths:
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".json", ".txt", ".py"}:
                continue
            if "question" in path.name.lower():
                continue  # question-only files don't contain answer markers
            if ".expected." in path.name or path.parent.name == "expected_v3" or "synthetic_docx_v3" in str(path):
                continue  # expected result and synthetic docx companion files
            text = _read(path)
            self.assertIn("【答案】", text,
                          f"{path.relative_to(FIXTURE_ROOT)} named real_chinese_brackets but lacks 【答案】")
            self.assertNotIn("〖答案〗", text,
                             f"{path.relative_to(FIXTURE_ROOT)} named real_chinese_brackets but uses compat marker 〖答案〗")

    def test_real_chinese_bracket_tests_assert_real_marker(self):
        paths = list(TESTS_ROOT.rglob("*real_chinese_brackets*.py"))
        self.assertTrue(len(paths) > 0, "Expected real bracket tests to exist")
        for path in paths:
            text = _read(path)
            self.assertIn("【答案】", text,
                          f"{path.name} must directly assert or use 【答案】")

    def test_real_bracket_tests_do_not_assert_compat_marker(self):
        paths = list(TESTS_ROOT.rglob("*real_chinese_bracket*.py"))
        for path in paths:
            if "compat" in path.name:
                continue
            text = _read(path)
            has_compat_assert = 'assertIn("〖答案〗"' in text or 'assert "〖答案〗"' in text
            self.assertFalse(has_compat_assert,
                             f"{path.name} should not assert compat marker 〖答案〗")

    def test_matrix_real_brackets_use_real_marker(self):
        matrix_dir = FIXTURE_ROOT / "matrix_v3"
        if not matrix_dir.exists():
            self.skipTest("matrix_v3 dir not found")
        for path in matrix_dir.rglob("*real_brackets*"):
            if not path.is_file() or path.suffix != ".json":
                continue
            if "question" in path.name.lower():
                continue
            text = _read(path)
            self.assertIn("【答案】", text,
                          f"Matrix {path.name} named real_brackets but lacks 【答案】")


if __name__ == "__main__":
    unittest.main()
