"""HTML shadow parity — fixture baseline (T3)."""
import json, shutil, tempfile, unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"
FIXTURES = Path(__file__).resolve().parent/"fixtures"/"baseline"/"html_structures"


class HtmlShadowParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists(): raise unittest.SkipTest("No demo")

    def test_html_structure_matches_fixtures(self):
        from app.workflow import run_grading
        t = tempfile.mkdtemp(prefix="t3_", dir=PROJECT_ROOT/"data")
        try:
            run_grading(DEMO_KEY, DEMO_SUB, Path(t), no_archive=True, exam_name="p")
            for fname in ["simple_report.html","advanced_dashboard.html","index.html"]:
                fp = Path(t)/fname
                self.assertTrue(fp.exists())
                self.assertGreater(fp.stat().st_size, 500)
                fix = FIXTURES/fname.replace(".html",".json")
                if fix.exists():
                    expected = json.loads(fix.read_text("utf-8"))
                    html = fp.read_text("utf-8")
                    for section in expected.get("sections",[]):
                        self.assertIn(section, html,
                                      f"{fname}: missing section '{section}'")
                    for link in expected.get("links",[]):
                        self.assertIn(link, html)
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        import ast; src = Path(__file__).read_text("utf-8")
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                for a in node.names: self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module: self.assertNotIn("legacy", node.module)


if __name__ == "__main__": unittest.main()
