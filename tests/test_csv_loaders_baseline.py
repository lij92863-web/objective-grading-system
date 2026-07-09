"""CSV loaders baseline — fixture-based (B5)."""
import os, tempfile, unittest
from pathlib import Path
from app.infrastructure.loaders.csv_loaders import load_answer_key, load_submissions

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"


class CsvLoadersBaselineTests(unittest.TestCase):
    def test_load_answer_key_reads_correctly(self):
        ak = load_answer_key(DEMO_KEY)
        self.assertIsNotNone(ak)
        self.assertGreater(len(ak.questions), 0)

    def test_load_submissions_reads_correctly(self):
        ak = load_answer_key(DEMO_KEY)
        subs = load_submissions(DEMO_SUB, ak)
        self.assertGreater(len(subs), 0)

    def test_load_answer_key_missing_file(self):
        with self.assertRaises((FileNotFoundError, ValueError, OSError)):
            load_answer_key(Path("/nonexistent/key.csv"))

    def test_no_legacy_import(self):
        import ast
        src = Path(__file__).read_text("utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names: self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module: self.assertNotIn("legacy", node.module)


if __name__ == "__main__":
    unittest.main()
