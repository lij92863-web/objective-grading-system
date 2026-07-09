from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AnswerExtractionForbiddenImportGuardV3Tests(unittest.TestCase):
    def test_no_forbidden_imports(self) -> None:
        paths = list((ROOT / "app" / "answer_extraction").rglob("*.py")) + [
            ROOT / "scripts" / "extract_answer_key.py",
            ROOT / "scripts" / "classify_paper_files.py",
            ROOT / "scripts" / "run_local_answer_extraction_smoke.py",
            ROOT / "scripts" / "run_answer_extraction_synthetic_docx_smoke.py",
        ]
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        for token in ["legacy", "app.compat", "app.workflow", "objective_grader", "grade_all", "web_app"]:
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
