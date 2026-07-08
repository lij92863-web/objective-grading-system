import unittest

from app.recognition.exception_queue import build_exception_queue
from app.recognition.models import (
    ChoiceCellOutput,
    MockBlankOutput,
    QwenJudgmentMock,
    RecognizedAnswerDraft,
    StudentIdentityCandidate,
)
from app.recognition.choice_mock import normalize_choice_recognition
from app.recognition.blank_mock import normalize_blank_recognition
from app.recognition.qwen_judgment_mock import apply_qwen_judgment_mock


class ExceptionQueueTests(unittest.TestCase):
    def test_conflict_identity_in_queue(self):
        identity = StudentIdentityCandidate(
            raw_text="7李明",
            student_number="7",
            student_name="李明",
            status=StudentIdentityCandidate.STATUS_CONFLICT,
            message="姓名栏识别结果与学生名单不一致，请确认。",
        )
        queue = build_exception_queue([], identity=identity)
        self.assertTrue(any(e.code == "IDENTITY_CONFLICT" for e in queue))

    def test_invalid_identity_in_queue(self):
        identity = StudentIdentityCandidate(
            status=StudentIdentityCandidate.STATUS_INVALID,
            message="无法解析",
        )
        queue = build_exception_queue([], identity=identity)
        self.assertTrue(any(e.code == "IDENTITY_INVALID" for e in queue))

    def test_unclear_draft_in_queue(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("unclear", 0.50), 3)
        queue = build_exception_queue([draft])
        self.assertTrue(any(e.code == "DRAFT_UNCLEAR" for e in queue))

    def test_invalid_draft_in_queue(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("E", 0.80), 5)
        queue = build_exception_queue([draft])
        self.assertTrue(any(e.code == "DRAFT_INVALID" for e in queue))

    def test_low_confidence_draft_in_queue(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("A", 0.70), 7)
        queue = build_exception_queue([draft])
        self.assertTrue(
            any(e.code == "DRAFT_LOW_CONFIDENCE" for e in queue)
        )

    def test_blank_low_confidence_in_queue(self):
        output = MockBlankOutput(
            raw_text="x+1", confidence=0.60, status="recognized"
        )
        draft = normalize_blank_recognition(output, 12, low_confidence_threshold=0.80)
        queue = build_exception_queue([draft])
        self.assertTrue(
            any(e.code == "DRAFT_LOW_CONFIDENCE" for e in queue)
        )

    def test_needs_review_draft_in_queue(self):
        draft = RecognizedAnswerDraft(
            question_number=10,
            status=RecognizedAnswerDraft.STATUS_NEEDS_REVIEW,
            message="需要人工复核。",
        )
        queue = build_exception_queue([draft])
        self.assertTrue(
            any(e.code == "DRAFT_NEEDS_REVIEW" for e in queue)
        )

    def test_qwen_needs_review_in_queue(self):
        j = apply_qwen_judgment_mock(
            "x>1", "(1,+oo)", verdict="needs_review", confidence=0.80,
            reason="uncertain",
        )
        queue = build_exception_queue([], judgments=[j])
        self.assertTrue(any(e.code == "QWEN_NEEDS_REVIEW" for e in queue))

    def test_qwen_low_confidence_in_queue(self):
        j = apply_qwen_judgment_mock(
            "x>1", "(1,+oo)", verdict="correct", confidence=0.70,
            reason="same",
        )
        queue = build_exception_queue([], judgments=[j], judgment_threshold=0.90)
        self.assertTrue(
            any(e.code == "QWEN_LOW_CONFIDENCE" for e in queue)
        )

    def test_qwen_missing_reason_in_queue(self):
        j = QwenJudgmentMock(
            verdict="correct", confidence=0.95, reason="",
            normalized_standard="x>1", normalized_student="x>1",
        )
        queue = build_exception_queue([], judgments=[j])
        self.assertTrue(
            any(e.code == "QWEN_MISSING_REASON" for e in queue)
        )

    def test_message_is_natural_language(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("unclear", 0.50), 3)
        queue = build_exception_queue([draft])
        exc = queue[0]
        self.assertIn("识别不清", exc.message)
        self.assertIn("3", exc.message)

    def test_no_exceptions_for_clean_drafts(self):
        draft = normalize_choice_recognition(ChoiceCellOutput("A", 0.95), 1)
        queue = build_exception_queue([draft])
        self.assertEqual(len(queue), 0)

    def test_qwen_invalid_verdict_in_queue(self):
        j = apply_qwen_judgment_mock(
            "x>1", "???", verdict="invalid", confidence=0.50, reason="unparseable",
        )
        queue = build_exception_queue([], judgments=[j])
        self.assertTrue(any(e.code == "QWEN_INVALID" for e in queue))


if __name__ == "__main__":
    unittest.main()
