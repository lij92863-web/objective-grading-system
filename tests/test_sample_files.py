"""Tests for sample_files — L14B."""
import ast
import shutil
import tempfile
import unittest
from pathlib import Path

from app.infrastructure.samples.sample_files import create_sample_files

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class SampleFilesTests(unittest.TestCase):
    def test_creates_three_files(self):
        t = tempfile.mkdtemp(prefix="l14b_", dir=PROJECT_ROOT / "data")
        try:
            create_sample_files(Path(t))
            self.assertTrue((Path(t) / "answer_key_sample.csv").exists())
            self.assertTrue((Path(t) / "submissions_sample.csv").exists())
            self.assertTrue((Path(t) / "question_bank_sample.csv").exists())
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_csv_content_stable(self):
        t = tempfile.mkdtemp(prefix="l14b_", dir=PROJECT_ROOT / "data")
        try:
            create_sample_files(Path(t))
            key = (Path(t) / "answer_key_sample.csv").read_text("utf-8-sig")
            self.assertIn("question_id", key)
            self.assertIn("B001", key)
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        src = (PROJECT_ROOT / "app" / "infrastructure" / "samples"
               / "sample_files.py").read_text("utf-8")
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
