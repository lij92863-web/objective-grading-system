"""CSV exporters migration matrix — Stage E2I.

Verifies all migrated CSV exporters exist, meet the contract,
and don't import legacy/web.
"""

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORTERS_DIR = PROJECT_ROOT / "app" / "infrastructure" / "exporters"

ALL_EXPORTERS = [
    "summary_csv_exporter.py",
    "detail_csv_exporter.py",
    "item_analysis_csv_exporter.py",
    "knowledge_profiles_csv_exporter.py",
    "practice_recommendations_csv_exporter.py",
    "class_report_csv_exporter.py",
    "validation_report_csv_exporter.py",
    "student_report_csv_exporter.py",
]


class CsvExportersMigrationMatrixTests(unittest.TestCase):

    def test_all_exporters_exist(self):
        for name in ALL_EXPORTERS:
            f = EXPORTERS_DIR / name
            self.assertTrue(f.exists(), f"Missing: {name}")

    def test_no_exporter_imports_legacy(self):
        for name in ALL_EXPORTERS:
            f = EXPORTERS_DIR / name
            if not f.exists():
                continue
            tree = ast.parse(f.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    mod = getattr(node, "module", "") or ""
                    for alias in node.names:
                        full = f"{mod}.{alias.name}" if mod else alias.name
                        self.assertFalse(
                            full.startswith("legacy"),
                            f"{name} imports legacy: {full}",
                        )

    def test_no_exporter_imports_web(self):
        for name in ALL_EXPORTERS:
            f = EXPORTERS_DIR / name
            if not f.exists():
                continue
            tree = ast.parse(f.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    mod = getattr(node, "module", "") or ""
                    for alias in node.names:
                        full = f"{mod}.{alias.name}" if mod else alias.name
                        self.assertFalse(
                            full.startswith("web"),
                            f"{name} imports web: {full}",
                        )

    def test_all_exporters_have_fieldnames(self):
        """Each exporter module defines *_FIELDNAMES."""
        expected = {
            "summary_csv_exporter.py": "SUMMARY_FIELDNAMES",
            "detail_csv_exporter.py": "DETAIL_FIELDNAMES",
            "item_analysis_csv_exporter.py": "ITEM_ANALYSIS_FIELDNAMES",
            "knowledge_profiles_csv_exporter.py": "KNOWLEDGE_PROFILES_FIELDNAMES",
            "practice_recommendations_csv_exporter.py": "PRACTICE_RECOMMENDATIONS_FIELDNAMES",
            "class_report_csv_exporter.py": "CLASS_REPORT_FIELDNAMES",
            "validation_report_csv_exporter.py": "VALIDATION_REPORT_FIELDNAMES",
            "student_report_csv_exporter.py": "STUDENT_REPORT_FIELDNAMES",
        }
        for fname, varname in expected.items():
            f = EXPORTERS_DIR / fname
            if not f.exists():
                continue
            tree = ast.parse(f.read_text(encoding="utf-8"))
            found = False
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == varname:
                            found = True
            self.assertTrue(found, f"{fname} missing {varname}")

    def test_all_exporters_implement_report_exporter(self):
        """Each exporter class subclasses ReportExporter."""
        classes = {
            "summary_csv_exporter.py": "SummaryCsvExporter",
            "detail_csv_exporter.py": "DetailCsvExporter",
            "item_analysis_csv_exporter.py": "ItemAnalysisCsvExporter",
            "knowledge_profiles_csv_exporter.py": "KnowledgeProfilesCsvExporter",
            "practice_recommendations_csv_exporter.py": "PracticeRecommendationsCsvExporter",
            "class_report_csv_exporter.py": "ClassReportCsvExporter",
            "validation_report_csv_exporter.py": "ValidationReportCsvExporter",
            "student_report_csv_exporter.py": "StudentReportCsvExporter",
        }
        for fname, clsname in classes.items():
            f = EXPORTERS_DIR / fname
            if not f.exists():
                continue
            tree = ast.parse(f.read_text(encoding="utf-8"))
            found = False
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == clsname:
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == "ReportExporter":
                            found = True
            self.assertTrue(
                found, f"{fname}: {clsname} does not extend ReportExporter"
            )

    def test_all_empty_rows_return_export_result_with_warning(self):
        """Each exporter handles empty rows gracefully."""
        import tempfile, shutil
        from app.infrastructure.exporters.contracts import ExportRequest

        exporters = [
            ("summary_csv_exporter", "SummaryCsvExporter"),
            ("detail_csv_exporter", "DetailCsvExporter"),
            ("item_analysis_csv_exporter", "ItemAnalysisCsvExporter"),
            ("knowledge_profiles_csv_exporter", "KnowledgeProfilesCsvExporter"),
            ("practice_recommendations_csv_exporter", "PracticeRecommendationsCsvExporter"),
            ("class_report_csv_exporter", "ClassReportCsvExporter"),
            ("validation_report_csv_exporter", "ValidationReportCsvExporter"),
            ("student_report_csv_exporter", "StudentReportCsvExporter"),
        ]
        for modname, clsname in exporters:
            mod = __import__(
                f"app.infrastructure.exporters.{modname}", fromlist=[clsname]
            )
            cls = getattr(mod, clsname)
            t = tempfile.mkdtemp(prefix="e2i_", dir=PROJECT_ROOT / "data")
            try:
                result = cls().export(ExportRequest(output_dir=Path(t)), [])
                self.assertEqual(result.status, "ok", f"{clsname} empty rows failed")
                self.assertGreater(len(result.generated_files), 0,
                                   f"{clsname} generated_files empty")
            finally:
                shutil.rmtree(t, ignore_errors=True)

    def test_legacy_behavior_still_passes(self):
        import tempfile, shutil
        from app.workflow import run_grading
        DEMO_KEY = PROJECT_ROOT/"samples/demo_exam/answer_key_sample.csv"
        DEMO_SUB = PROJECT_ROOT/"samples/demo_exam/submissions_sample.csv"
        if not DEMO_KEY.exists():
            self.skipTest("No demo samples")
        t = tempfile.mkdtemp(prefix="e2i_", dir=PROJECT_ROOT/"data")
        try:
            r = run_grading(DEMO_KEY, DEMO_SUB, Path(t), no_archive=True, exam_name="e2i")
            self.assertTrue(r["ok"])
        finally:
            shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
