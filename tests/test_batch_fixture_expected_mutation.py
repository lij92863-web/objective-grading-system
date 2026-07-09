import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class BatchFixtureExpectedMutationTests(unittest.TestCase):
    def test_mutated_expected_fails_evaluator(self):
        source = PROJECT_ROOT / "tests/fixtures/recognition/synthetic_batches/batch_all_clear.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        data["expected"]["auto_accepted_items"] = 999
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as handle:
            json.dump(data, handle)
            path = handle.name
        try:
            result = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "scripts/evaluate_synthetic_batch.py"), "--fixture", path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertNotEqual(result.returncode, 0)
        finally:
            Path(path).unlink()


if __name__ == "__main__":
    unittest.main()
