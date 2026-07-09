"""R1: Recognition baseline guard."""
import ast, unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RecognitionBaselineGuardTests(unittest.TestCase):
    def test_recognition_dir_exists(self):
        self.assertTrue((PROJECT_ROOT/"app/recognition").is_dir())
        self.assertTrue((PROJECT_ROOT/"app/recognition/qwen_adapter").is_dir())

    def test_real_qwen_client_default_disabled(self):
        from app.recognition.qwen_adapter.real_client import RealQwenClient
        c = RealQwenClient()
        self.assertFalse(c._is_enabled())

    def test_fake_qwen_client_available(self):
        from app.recognition.qwen_adapter.fake_client import FakeQwenClient
        self.assertTrue(FakeQwenClient)

    def test_no_real_api_in_tests(self):
        allowed = {"test_qwen_real_client_config.py", "test_qwen_real_client_safety.py",
                    "test_recognition_baseline_guard.py"}
        for p in (PROJECT_ROOT/"tests").rglob("test*.py"):
            if p.name in allowed: continue
            text = p.read_text(encoding="utf-8",errors="ignore")
            self.assertNotIn("QWEN_API_ENABLED", text,
                             f"{p.name} sets QWEN_API_ENABLED")

    def test_workflow_not_import_qwen(self):
        src = (PROJECT_ROOT/"app/workflow.py").read_text("utf-8")
        self.assertNotIn("qwen_adapter", src)
        self.assertNotIn("RealQwenClient", src)

    def test_objective_grader_not_import_qwen(self):
        src = (PROJECT_ROOT/"objective_grader.py").read_text("utf-8")
        self.assertNotIn("qwen_adapter", src)


if __name__ == "__main__": unittest.main()
