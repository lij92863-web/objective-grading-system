import json
import tempfile
import unittest
from pathlib import Path

from app.recognition.batch_orchestrator import run_synthetic_batch


SOURCE = Path("tests/fixtures/recognition/synthetic_batches/batch_qwen_budget_exceeded.json")


class QwenBudgetExceededNotSimulatedTests(unittest.TestCase):
    def test_blocked_count_changes_with_max_calls(self):
        self.assertEqual(run_synthetic_batch("qwen_budget_exceeded")["batch_summary"]["blocked_by_budget_count"], 3)
        high = _run_with_max_calls(10)
        zero = _run_with_max_calls(0)
        self.assertEqual(high["batch_summary"]["blocked_by_budget_count"], 0)
        self.assertEqual(zero["batch_summary"]["blocked_by_budget_count"], 5)


def _run_with_max_calls(max_calls):
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    data["qwen_budget"]["max_calls"] = max_calls
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as handle:
        json.dump(data, handle)
        path = handle.name
    try:
        return run_synthetic_batch(fixture_path=path)
    finally:
        Path(path).unlink()


if __name__ == "__main__":
    unittest.main()
