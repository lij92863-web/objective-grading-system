import unittest

from app.recognition.models import (
    ChoiceCellOutput,
    MockBlankOutput,
    QwenJudgmentMock,
    StudentIdentityCandidate,
)
from app.recognition.qwen_judgment_mock import apply_qwen_judgment_mock
from app.recognition.pipeline import process_mock_recognition_batch


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.roster = {"1": "李明", "2": "张三", "3": "王强"}

    def test_complete_mock_scenario(self):
        """Full pipeline run matching the CODEX_TASK scenario."""

        result = process_mock_recognition_batch(
            identity_raw_text="1李明",
            roster=self.roster,
            choice_cell_outputs={
                1: ChoiceCellOutput("A", 0.95),       # high-conf, draft
                2: ChoiceCellOutput("BA", 0.92),      # → AB
                3: ChoiceCellOutput("unclear", 0.50), # → exception
            },
            blank_outputs={
                12: MockBlankOutput(
                    raw_text="1/2", latex="\\frac{1}{2}",
                    confidence=0.92, status="recognized",
                ),
                13: MockBlankOutput(
                    raw_text="x>1", latex="x > 1",
                    confidence=0.88, status="recognized",
                ),
                14: MockBlankOutput(
                    raw_text="unclear", confidence=0.40, status="unclear",
                ),
            },
            qwen_judgments={
                13: apply_qwen_judgment_mock(
                    "x>1", "x>1", verdict="correct", confidence=0.96,
                    reason="两者表示同一解集",
                ),
            },
        )

        # identity
        self.assertEqual(
            result.identity.status, StudentIdentityCandidate.STATUS_CONFIRMED
        )
        self.assertEqual(result.identity.matched_student_id, "1")

        # draft count: 3 choice + 3 blank = 6
        self.assertEqual(result.total_drafts, 6)

        # choice drafts
        choice_drafts = [d for d in result.drafts if d.question_type != "blank"]
        self.assertEqual(len(choice_drafts), 3)

        q1 = next(d for d in choice_drafts if d.question_number == 1)
        self.assertEqual(q1.normalized_text, "A")
        self.assertEqual(q1.status, "draft")

        q2 = next(d for d in choice_drafts if d.question_number == 2)
        self.assertEqual(q2.normalized_text, "AB")

        q3 = next(d for d in choice_drafts if d.question_number == 3)
        self.assertEqual(q3.status, "unclear")
        self.assertTrue(q3.needs_review)

        # blank drafts
        blank_drafts = [d for d in result.drafts if d.question_type == "blank"]
        self.assertEqual(len(blank_drafts), 3)

        q12 = next(d for d in blank_drafts if d.question_number == 12)
        self.assertEqual(q12.raw_text, "1/2")
        self.assertEqual(q12.status, "draft")

        q13 = next(d for d in blank_drafts if d.question_number == 13)
        self.assertEqual(q13.status, "auto_accepted")
        self.assertFalse(q13.needs_review)

        q14 = next(d for d in blank_drafts if d.question_number == 14)
        self.assertEqual(q14.status, "unclear")
        self.assertTrue(q14.needs_review)

        # auto-accept
        self.assertEqual(result.auto_accepted_count, 1)

        # exceptions: Q3 unclear + Q14 unclear = 2 drafts + any identity/judgment
        self.assertGreaterEqual(result.exception_count, 2)

        # verify unclear items in exception queue
        unclear_exceptions = [
            e for e in result.exceptions if "识别不清" in e.message
        ]
        self.assertGreaterEqual(len(unclear_exceptions), 2)

        # summary
        self.assertEqual(result.total_drafts, 6)
        self.assertEqual(result.auto_accepted_count, 1)
        self.assertGreaterEqual(result.exception_count, 2)

    def test_pipeline_no_roster(self):
        result = process_mock_recognition_batch(
            identity_raw_text="1李明",
            choice_cell_outputs={
                1: ChoiceCellOutput("A", 0.95),
            },
        )
        self.assertEqual(result.identity.status, "draft")
        self.assertEqual(result.total_drafts, 1)

    def test_pipeline_empty_inputs(self):
        result = process_mock_recognition_batch(identity_raw_text="")
        self.assertEqual(result.total_drafts, 0)
        self.assertEqual(result.auto_accepted_count, 0)
        self.assertGreaterEqual(result.exception_count, 1)  # identity invalid

    def test_student_info_attached_when_confirmed(self):
        result = process_mock_recognition_batch(
            identity_raw_text="1李明",
            roster=self.roster,
            choice_cell_outputs={
                1: ChoiceCellOutput("A", 0.95),
            },
        )
        draft = result.drafts[0]
        self.assertEqual(draft.student_id, "1")
        self.assertEqual(draft.student_name, "李明")

    def test_auto_accepted_count_matches(self):
        result = process_mock_recognition_batch(
            identity_raw_text="1李明",
            roster=self.roster,
            blank_outputs={
                12: MockBlankOutput(
                    raw_text="x>1", latex="x>1",
                    confidence=0.95, status="recognized",
                ),
            },
            qwen_judgments={
                12: apply_qwen_judgment_mock(
                    "x>1", "x>1", verdict="correct", confidence=0.96,
                    reason="等价",
                ),
            },
        )
        self.assertEqual(result.auto_accepted_count, 1)

    def test_low_confidence_count(self):
        result = process_mock_recognition_batch(
            identity_raw_text="1李明",
            roster=self.roster,
            choice_cell_outputs={
                1: ChoiceCellOutput("A", 0.70),  # below 0.80 threshold
                2: ChoiceCellOutput("B", 0.95),
            },
        )
        self.assertEqual(result.low_confidence_count, 1)

    def test_needs_review_count(self):
        result = process_mock_recognition_batch(
            identity_raw_text="1李明",
            roster=self.roster,
            choice_cell_outputs={
                1: ChoiceCellOutput("unclear", 0.50),
            },
            blank_outputs={
                12: MockBlankOutput(
                    raw_text="unclear", confidence=0.40, status="unclear",
                ),
            },
        )
        self.assertEqual(result.needs_review_count, 2)


if __name__ == "__main__":
    unittest.main()
