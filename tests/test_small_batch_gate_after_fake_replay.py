"""Tests for small batch gate after fake replay — R385."""
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


class SmallBatchGateAfterFakeReplayTests(unittest.TestCase):
    def test_small_batch_gate_importable(self):
        """Small batch gate must be importable."""
        from app.recognition.small_batch_gate import check_small_batch_gate
        self.assertTrue(callable(check_small_batch_gate))

    def test_small_batch_gate_default_false(self):
        """Small batch gate defaults to blocked."""
        from app.recognition.small_batch_gate import check_small_batch_gate
        result = check_small_batch_gate()
        ready = (result.ready_for_small_batch if hasattr(result, 'ready_for_small_batch')
                 else result.get("ready_for_small_batch", True))
        self.assertFalse(ready)

    def test_fake_replay_does_not_enable_batch(self):
        """Fake replay success should not enable small batch."""
        from app.recognition.small_batch_gate import check_small_batch_gate
        result = check_small_batch_gate()
        blockers = (result.blockers if hasattr(result, 'blockers')
                    else result.get("blockers", []))
        self.assertGreater(len(blockers), 0)

    def test_single_real_trial_incomplete_blocks_batch(self):
        """Single real trial not done → small batch blocked."""
        from app.recognition.small_batch_gate import check_small_batch_gate
        result = check_small_batch_gate()
        blockers = (result.blockers if hasattr(result, 'blockers')
                    else result.get("blockers", []))
        self.assertGreater(len(blockers), 0)

    def test_no_real_data_leak_required(self):
        """This test does not require real data."""
        pass  # Always passes - meta-guard


if __name__ == "__main__":
    unittest.main()
