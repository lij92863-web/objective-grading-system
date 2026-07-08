"""Legacy entrypoint import smoke — Stage 6.

Verifies that key entrypoints can be imported without errors.
"""

import unittest


class LegacyEntrypointImportTests(unittest.TestCase):
    def test_import_objective_grader(self):
        try:
            import objective_grader  # noqa: F401
        except ImportError as exc:
            self.fail(f"objective_grader import failed: {exc}")

    def test_import_app_core(self):
        try:
            import app.core  # noqa: F401
        except ImportError as exc:
            self.fail(f"app.core import failed: {exc}")

    def test_import_legacy(self):
        try:
            import legacy.objective_grader_legacy  # noqa: F401
        except ImportError as exc:
            self.fail(f"legacy.objective_grader_legacy import failed: {exc}")

    def test_import_web_app_module(self):
        """web_app.py can be imported as a module (without starting server)."""
        # Import the module — do NOT call run()
        try:
            import web_app  # noqa: F401
        except ImportError as exc:
            self.fail(f"web_app import failed: {exc}")

    def test_import_roster_manager(self):
        try:
            import roster_manager  # noqa: F401
        except ImportError as exc:
            self.fail(f"roster_manager import failed: {exc}")

    def test_import_exam_recognizer(self):
        try:
            import exam_recognizer  # noqa: F401
        except ImportError as exc:
            self.fail(f"exam_recognizer import failed: {exc}")


if __name__ == "__main__":
    unittest.main()
