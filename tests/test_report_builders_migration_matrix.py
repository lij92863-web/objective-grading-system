"""Report builders migration matrix — Stage E5G."""

import ast, unittest
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILDERS_DIR = PROJECT_ROOT/"app/application/use_cases/report_builders"

EXPECTED_MODULES = [
    "score_rows.py", "item_analysis.py", "knowledge_profiles.py",
    "class_report.py", "validation_report.py", "practice_recommendations.py",
]
EXPECTED_FUNCS = {
    "score_rows.py": "build_simple_score_rows",
    "item_analysis.py": "build_item_analysis_rows",
    "knowledge_profiles.py": "build_knowledge_profiles",
    "class_report.py": "build_class_report",
    "validation_report.py": "build_validation_report",
    "practice_recommendations.py": "build_practice_recommendations",
}

class ReportBuildersMigrationMatrixTests(unittest.TestCase):
    def test_all_modules_exist(self):
        for name in EXPECTED_MODULES:
            self.assertTrue((BUILDERS_DIR/name).exists(), f"Missing: {name}")
    def test_all_functions_exist(self):
        for fname, func in EXPECTED_FUNCS.items():
            tree = ast.parse((BUILDERS_DIR/fname).read_text(encoding="utf-8"))
            found = any(isinstance(n, ast.FunctionDef) and n.name == func for n in ast.walk(tree))
            self.assertTrue(found, f"{fname} missing {func}")
    def test_no_builder_imports_legacy(self):
        for f in BUILDERS_DIR.rglob("*.py"):
            if f.name == "__init__.py" or f.name == "contracts.py": continue
            for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
                if isinstance(n, (ast.Import, ast.ImportFrom)):
                    mod = getattr(n, "module", "") or ""
                    for a in n.names:
                        full = f"{mod}.{a.name}" if mod else a.name
                        self.assertFalse(full.startswith("legacy"), f"{f.name}: {full}")
    def test_no_builder_imports_exporters(self):
        for f in BUILDERS_DIR.rglob("*.py"):
            if f.name == "__init__.py" or f.name == "contracts.py": continue
            for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
                if isinstance(n, (ast.Import, ast.ImportFrom)):
                    mod = getattr(n, "module", "") or ""
                    for a in n.names:
                        full = f"{mod}.{a.name}" if mod else a.name
                        self.assertFalse(full.startswith("app.infrastructure.exporters"), f"{f.name}: {full}")

if __name__ == "__main__": unittest.main()
