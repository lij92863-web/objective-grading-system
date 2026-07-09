import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

WORKFLOW_FORBIDDEN_CALLS = {
    "write_summary",
    "write_detail",
    "write_item_analysis",
    "write_knowledge_profiles",
    "write_practice_recommendations",
    "write_class_report",
    "write_validation_report",
    "write_student_report",
    "write_workbook",
    "write_simple_score_workbook",
    "write_enhanced_workbook",
    "write_simple_report",
    "write_advanced_dashboard",
    "write_report_index",
    "simple_score_rows",
    "item_stats",
    "load_answer_key",
    "load_submissions",
    "grade_all",
    "build_validation_report",
    "build_knowledge_profiles",
    "basic_stats",
}
WORKFLOW_ALLOWED_CALLS = {"ExamMeta", "load_question_bank"}
OBJECTIVE_ALLOWED_LEGACY_CALLS: set = set()  # all legacy calls migrated
APPLICATION_EXPORTER_IMPORT_EXCEPTIONS = {"csv_report_pipeline.py"}


def py_files(root: str):
    return sorted((PROJECT_ROOT / root).rglob("*.py"))


def import_names(tree):
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def legacy_calls(tree):
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "legacy"
        ):
            calls.append((func.attr, node.lineno))
    return calls


class LegacyDependencyGuardMatrixTests(unittest.TestCase):
    def test_workflow_forbidden_legacy_calls_are_absent(self):
        source_path = PROJECT_ROOT / "app/workflow.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        violations = [
            (name, line)
            for name, line in legacy_calls(tree)
            if name in WORKFLOW_FORBIDDEN_CALLS
        ]
        self.assertEqual([], violations)

    def test_workflow_legacy_calls_are_known(self):
        source_path = PROJECT_ROOT / "app/workflow.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        calls = {name for name, _line in legacy_calls(tree)}
        self.assertTrue(calls <= WORKFLOW_ALLOWED_CALLS, calls)

    def test_application_layer_import_boundaries(self):
        violations = []
        for source_path in py_files("app/application"):
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
            for name in import_names(tree):
                exporter_import_allowed = (
                    source_path.name in APPLICATION_EXPORTER_IMPORT_EXCEPTIONS
                    and name.startswith("app.infrastructure.exporters")
                )
                if (
                    name == "legacy"
                    or name.startswith("legacy.")
                    or name == "web"
                    or name.startswith("web.")
                    or (
                        name.startswith("app.infrastructure.exporters")
                        and not exporter_import_allowed
                    )
                ):
                    violations.append((source_path.relative_to(PROJECT_ROOT).as_posix(), name))
        self.assertEqual([], violations)

    def test_infrastructure_layer_import_boundaries(self):
        violations = []
        for source_path in py_files("app/infrastructure"):
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
            for name in import_names(tree):
                if (
                    name == "legacy"
                    or name.startswith("legacy.")
                    or name == "web"
                    or name.startswith("web.")
                    or name.startswith("web.static")
                ):
                    violations.append((source_path.relative_to(PROJECT_ROOT).as_posix(), name))
        self.assertEqual([], violations)

    def test_domain_layer_import_boundaries(self):
        violations = []
        for source_path in py_files("app/domain"):
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
            for name in import_names(tree):
                if (
                    name == "legacy"
                    or name.startswith("legacy.")
                    or name == "web"
                    or name.startswith("web.")
                    or name.startswith("app.infrastructure")
                ):
                    violations.append((source_path.relative_to(PROJECT_ROOT).as_posix(), name))
        self.assertEqual([], violations)

    def test_objective_grader_legacy_boundary(self):
        source_path = PROJECT_ROOT / "objective_grader.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "legacy.objective_grader_legacy":
                self.assertFalse(any(alias.name == "*" for alias in node.names))
        calls = {name for name, _line in legacy_calls(tree)}
        self.assertTrue(calls <= OBJECTIVE_ALLOWED_LEGACY_CALLS, calls)


if __name__ == "__main__":
    unittest.main()
