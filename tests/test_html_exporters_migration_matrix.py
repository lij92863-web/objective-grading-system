"""HTML exporters migration matrix — E4H."""

import ast
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"
DEMO_SUB = PROJECT_ROOT / "samples/demo_exam/submissions_sample.csv"


class HtmlExportersMigrationMatrixTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not DEMO_KEY.exists():
            raise unittest.SkipTest("No demo answer key")

    def test_simple_report_exporter_exists(self):
        from app.infrastructure.exporters.simple_report_html_exporter \
            import SimpleReportHtmlExporter
        self.assertTrue(SimpleReportHtmlExporter)

    def test_advanced_dashboard_exporter_exists(self):
        from app.infrastructure.exporters.advanced_dashboard_html_exporter \
            import AdvancedDashboardHtmlExporter
        self.assertTrue(AdvancedDashboardHtmlExporter)

    def test_report_index_exporter_exists(self):
        from app.infrastructure.exporters.report_index_html_exporter \
            import ReportIndexHtmlExporter
        self.assertTrue(ReportIndexHtmlExporter)

    def test_all_three_no_legacy_import(self):
        for mod in ["simple_report_html_exporter",
                     "advanced_dashboard_html_exporter",
                     "report_index_html_exporter"]:
            src = (PROJECT_ROOT / "app" / "infrastructure" / "exporters"
                   / f"{mod}.py").read_text(encoding="utf-8")
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        self.assertNotIn("legacy", a.name,
                                         f"{mod} imports legacy")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.assertNotIn("legacy", node.module,
                                         f"{mod} imports legacy")

    def test_all_three_no_web_import(self):
        for mod in ["simple_report_html_exporter",
                     "advanced_dashboard_html_exporter",
                     "report_index_html_exporter"]:
            src = (PROJECT_ROOT / "app" / "infrastructure" / "exporters"
                   / f"{mod}.py").read_text(encoding="utf-8")
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        self.assertNotIn("web", a.name, f"{mod} imports web")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.assertNotIn("web", node.module,
                                         f"{mod} imports web")

    def test_all_three_return_export_result(self):
        """Verifies that all exporters return ExportResult."""
        import shutil
        import legacy.objective_grader_legacy as leg
        from app.infrastructure.exporters.contracts import ExportRequest

        ak = leg.load_answer_key(DEMO_KEY)
        subs = leg.load_submissions(DEMO_SUB, ak)
        results = leg.grade_all(ak, subs)
        profiles = leg.build_knowledge_profiles(ak, results)
        item_rows = leg.item_stats(ak, results)
        simple_rows = leg.simple_score_rows(results)
        val_rows = leg.build_validation_report(ak, subs, results, profiles)
        meta = {"exam_name": "d", "class_name": "c",
                "subject": "s", "exam_date": "2026-07-09"}

        t = tempfile.mkdtemp(prefix="e4h_", dir=PROJECT_ROOT / "data")
        try:
            out = Path(t) / "out"
            out.mkdir()
            req = ExportRequest(output_dir=out)

            from app.infrastructure.exporters.simple_report_html_exporter \
                import SimpleReportHtmlExporter
            r1 = SimpleReportHtmlExporter().export(
                req, meta, results, simple_rows, item_rows)
            self.assertEqual(r1.status, "ok")

            from app.infrastructure.exporters.advanced_dashboard_html_exporter \
                import AdvancedDashboardHtmlExporter
            r2 = AdvancedDashboardHtmlExporter().export(
                req, meta, results, profiles, val_rows, item_rows)
            self.assertEqual(r2.status, "ok")

            (out / "simple_report.html").touch()
            (out / "advanced_dashboard.html").touch()
            (out / "simple_score_report.xlsx").touch()
            from app.infrastructure.exporters.report_index_html_exporter \
                import ReportIndexHtmlExporter
            r3 = ReportIndexHtmlExporter().export(
                req, meta,
                out / "simple_report.html",
                out / "advanced_dashboard.html",
                out / "simple_score_report.xlsx")
            self.assertEqual(r3.status, "ok")
        finally:
            shutil.rmtree(t, ignore_errors=True)

    def test_workflow_has_no_legacy_html(self):
        wf = (PROJECT_ROOT / "app" / "workflow.py").read_text(
            encoding="utf-8")
        for name in ["write_simple_report", "write_advanced_dashboard",
                      "write_report_index"]:
            self.assertNotIn(
                name, wf,
                f"workflow still references legacy HTML: {name}")

    def test_html_legacy_behavior_tests_still_baseline(self):
        from tests.test_html_legacy_behavior import HtmlLegacyBehaviorTests
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(HtmlLegacyBehaviorTests)
        runner = unittest.TextTestRunner(verbosity=0)
        result = runner.run(suite)
        self.assertTrue(result.wasSuccessful(),
                        "HTML legacy behavior baseline tests failed")

    def test_old_cli_smoke(self):
        t = tempfile.mkdtemp(prefix="e4h_cli_", dir=PROJECT_ROOT / "data")
        try:
            r = subprocess.run([
                sys.executable,
                str(PROJECT_ROOT / "objective_grader.py"),
                "--answer-key", str(DEMO_KEY),
                "--submissions", str(DEMO_SUB),
                "--out-dir", str(Path(t) / "out"),
                "--no-archive",
            ], capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
