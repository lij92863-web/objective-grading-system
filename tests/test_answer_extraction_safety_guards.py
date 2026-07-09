from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCANNED = [
    ROOT / "app" / "answer_extraction",
    ROOT / "scripts" / "extract_answer_key.py",
    ROOT / "scripts" / "classify_paper_files.py",
    ROOT / "scripts" / "run_local_answer_extraction_smoke.py",
]


class AnswerExtractionSafetyGuardTests(unittest.TestCase):
    def iter_text(self) -> str:
        chunks = []
        for path in SCANNED:
            if path.is_dir():
                for file_path in path.rglob("*.py"):
                    chunks.append(file_path.read_text(encoding="utf-8"))
            else:
                chunks.append(path.read_text(encoding="utf-8"))
        return "\n".join(chunks)

    def test_no_forbidden_import_or_integration_terms(self) -> None:
        text = self.iter_text()
        forbidden = ["legacy", "app.compat", "app.workflow", "objective_grader", "grade_all", "web_app", "web.", "exporters"]
        for token in forbidden:
            self.assertNotIn(token, text)

    def test_no_real_api_secret_or_raw_payload_terms(self) -> None:
        text = self.iter_text()
        forbidden = ["QWEN_API_KEY", "Authorization", "Bearer", "data:image", "raw_response", ".env"]
        for token in forbidden:
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
