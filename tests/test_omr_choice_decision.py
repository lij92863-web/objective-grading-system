"""R36: OMR choice decision tests."""
import unittest
from app.recognition.omr_metrics import ChoiceCellMetric
from app.recognition.omr_choice_decision import decide_choice_from_cells, OMRDecisionConfig


class OMRChoiceDecisionTests(unittest.TestCase):
    def test_clear_single_choice(self):
        cells = [ChoiceCellMetric(option="A", dark_ratio=0.7, confidence=0.9),
                 ChoiceCellMetric(option="B", dark_ratio=0.1, confidence=0.1)]
        result = decide_choice_from_cells(cells, 1)
        self.assertEqual(result.value, "A")

    def test_ambiguous_cells(self):
        cells = [ChoiceCellMetric(option="A", dark_ratio=0.6),
                 ChoiceCellMetric(option="B", dark_ratio=0.55)]
        result = decide_choice_from_cells(cells, 1)
        self.assertEqual(result.status, "conflict")

    def test_all_blank(self):
        cells = [ChoiceCellMetric(option="A", dark_ratio=0.0),
                 ChoiceCellMetric(option="B", dark_ratio=0.05)]
        result = decide_choice_from_cells(cells, 1)
        self.assertEqual(result.status, "blank")

    def test_multiple_allowed(self):
        cfg = OMRDecisionConfig(allow_multiple=True, ambiguity_margin=0.05)
        cells = [ChoiceCellMetric(option="A", dark_ratio=0.8, confidence=0.9),
                 ChoiceCellMetric(option="D", dark_ratio=0.75, confidence=0.85)]
        result = decide_choice_from_cells(cells, 1, cfg)
        self.assertEqual(result.value, "AD")

    def test_no_valid_cells(self):
        cells = [ChoiceCellMetric(option="Z", dark_ratio=0.5)]
        result = decide_choice_from_cells(cells, 1)
        self.assertEqual(result.status, "blocking")


if __name__ == "__main__": unittest.main()
