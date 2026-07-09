import unittest

from app.recognition.small_batch_gate import check_small_batch_gate


class SmallBatchGateV2Tests(unittest.TestCase):
    def test_default_false(self):
        self.assertFalse(check_small_batch_gate().ready_for_small_batch)


if __name__ == "__main__":
    unittest.main()
