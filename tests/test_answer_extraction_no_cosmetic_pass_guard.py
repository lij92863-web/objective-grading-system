from __future__ import annotations

import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = TESTS_DIR / "fixtures" / "answer_extraction"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


class NoCosmeticPassGuardTests(unittest.TestCase):
    def test_real_bracket_paths_exist(self):
        paths = list(TESTS_DIR.rglob("*real*bracket*.py"))
        paths += list(FIXTURE_DIR.rglob("*real*bracket*"))
        self.assertTrue(len(paths) > 0, "Expected real bracket tests/fixtures to exist")

    def test_real_bracket_files_contain_real_marker(self):
        for path in list(TESTS_DIR.rglob("*real*bracket*.py")) + list(FIXTURE_DIR.rglob("*real*bracket*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".json", ".py"}:
                continue
            if "question" in path.name.lower():
                continue
            if ".expected." in path.name or "synthetic_docx_v3" in str(path):
                continue
            text = _read(path)
            self.assertIn("【答案】", text,
                          f"{path.name} claims real bracket coverage but lacks 【答案】")

    def test_non_compat_real_files_do_not_contain_compat_marker(self):
        for path in list(TESTS_DIR.rglob("*real*bracket*.py")) + list(FIXTURE_DIR.rglob("*real*bracket*")):
            if not path.is_file():
                continue
            if "compat" in path.name.lower():
                continue
            if "question" in path.name.lower():
                continue
            if ".expected." in path.name or "synthetic_docx_v3" in str(path):
                continue
            if "synthetic_docx" in path.name.lower():
                continue  # synthetic docx tests use assertNotIn for compat verification
            if path.suffix.lower() not in {".json", ".py"}:
                continue
            text = _read(path)
            self.assertNotIn("〖答案〗", text,
                             f"{path.name} claims real bracket coverage but contains compat marker 〖答案〗")


if __name__ == "__main__":
    unittest.main()
