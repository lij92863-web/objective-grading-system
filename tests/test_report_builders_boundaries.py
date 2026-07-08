import ast, unittest
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILDERS_DIR = PROJECT_ROOT/"app/application/use_cases/report_builders"

class ReportBuildersBoundaryTests(unittest.TestCase):
    def _check_no_import(self, prefix):
        for f in BUILDERS_DIR.rglob("*.py"):
            if f.name == "__init__.py": continue
            for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
                if isinstance(n, (ast.Import, ast.ImportFrom)):
                    mod = getattr(n, "module", "") or ""
                    for a in n.names:
                        full = f"{mod}.{a.name}" if mod else a.name
                        self.assertFalse(full.startswith(prefix), f"{f.name}: imports {prefix}: {full}")
    def test_no_legacy(self): self._check_no_import("legacy")
    def test_no_web(self): self._check_no_import("web")
    def test_no_exporters(self): self._check_no_import("app.infrastructure.exporters")

if __name__ == "__main__": unittest.main()
