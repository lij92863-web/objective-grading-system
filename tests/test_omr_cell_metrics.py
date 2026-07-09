"""R35: OMR cell metrics tests."""
import unittest
from app.recognition.omr_metrics import ChoiceCellMetric


class OMRCellMetricsTests(unittest.TestCase):
    def test_valid_cell(self):
        c = ChoiceCellMetric(question_id=1, option="A", dark_ratio=0.5, confidence=0.8)
        self.assertTrue(c.is_valid())

    def test_invalid_option(self):
        c = ChoiceCellMetric(option="Z")
        self.assertFalse(c.is_valid())

    def test_negative_dark_ratio(self):
        c = ChoiceCellMetric(option="A", dark_ratio=-0.1)
        self.assertFalse(c.is_valid())

    def test_dark_ratio_above_one(self):
        c = ChoiceCellMetric(option="A", dark_ratio=1.5)
        self.assertFalse(c.is_valid())

    def test_confidence_out_of_range(self):
        c = ChoiceCellMetric(option="A", confidence=1.5)
        self.assertFalse(c.is_valid())


if __name__ == "__main__": unittest.main()
