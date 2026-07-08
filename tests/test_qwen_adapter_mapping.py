import json
import unittest

from app.recognition.qwen_adapter import (
    FakeQwenClient,
    QwenParsedResult,
    QwenRequest,
    PROMPT_TYPE_BLANK_ANSWER,
    PROMPT_TYPE_CHOICE_CELL,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT,
    PROMPT_TYPE_NAME_FIELD,
    parse_qwen_response,
    parse_blank_response_to_draft,
    parse_choice_response_to_draft,
    parse_complex_judgment_response,
    parse_name_field_to_identity_candidate,
)
from app.recognition.models import (
    QwenJudgmentMock,
    RecognizedAnswerDraft,
    StudentIdentityCandidate,
)
from app.recognition.qwen_judgment_mock import should_auto_accept_qwen_judgment


class MappingTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeQwenClient()

    # -- name field → StudentIdentityCandidate -------------------------------

    def test_name_field_to_identity_candidate(self):
        req = QwenRequest(prompt_type=PROMPT_TYPE_NAME_FIELD, prompt="test")
        resp = self.client.recognize_name_field(req)
        result = parse_qwen_response(resp, PROMPT_TYPE_NAME_FIELD)
        self.assertEqual(result.status, "ok")

        candidate = parse_name_field_to_identity_candidate(result)
        self.assertIsInstance(candidate, StudentIdentityCandidate)
        self.assertEqual(candidate.raw_text, "1李明")
        self.assertEqual(candidate.student_number, "1")

    def test_name_field_to_identity_with_roster(self):
        roster = {"1": "李明"}
        req = QwenRequest(prompt_type=PROMPT_TYPE_NAME_FIELD, prompt="test")
        resp = self.client.recognize_name_field(req)
        result = parse_qwen_response(resp, PROMPT_TYPE_NAME_FIELD)
        candidate = parse_name_field_to_identity_candidate(result, roster=roster)
        self.assertEqual(
            candidate.status, StudentIdentityCandidate.STATUS_CONFIRMED
        )
        self.assertEqual(candidate.matched_student_id, "1")

    # -- choice cell → RecognizedAnswerDraft ---------------------------------

    def test_choice_response_to_draft(self):
        self.client.inject_custom_payload({"answer": "BA", "confidence": 0.92})
        req = QwenRequest(prompt_type=PROMPT_TYPE_CHOICE_CELL, prompt="test")
        resp = self.client.recognize_choice_cell(req)
        result = parse_qwen_response(resp, PROMPT_TYPE_CHOICE_CELL)
        draft = parse_choice_response_to_draft(result, question_number=2)
        self.assertIsInstance(draft, RecognizedAnswerDraft)
        self.assertEqual(draft.normalized_text, "AB")
        self.assertEqual(draft.question_number, 2)

    def test_choice_response_blank(self):
        self.client.inject_custom_payload({"answer": "blank", "confidence": 0.99})
        req = QwenRequest(prompt_type=PROMPT_TYPE_CHOICE_CELL, prompt="test")
        resp = self.client.recognize_choice_cell(req)
        result = parse_qwen_response(resp, PROMPT_TYPE_CHOICE_CELL)
        draft = parse_choice_response_to_draft(result, question_number=5)
        self.assertEqual(draft.status, RecognizedAnswerDraft.STATUS_BLANK)

    # -- blank answer → RecognizedAnswerDraft --------------------------------

    def test_blank_response_to_draft(self):
        self.client.inject_custom_payload(
            {
                "raw_text": "x^2+1",
                "latex": "x^{2}+1",
                "confidence": 0.94,
                "status": "recognized",
            }
        )
        req = QwenRequest(prompt_type=PROMPT_TYPE_BLANK_ANSWER, prompt="test")
        resp = self.client.recognize_blank_answer(req)
        result = parse_qwen_response(resp, PROMPT_TYPE_BLANK_ANSWER)
        draft = parse_blank_response_to_draft(result, question_number=12)
        self.assertIsInstance(draft, RecognizedAnswerDraft)
        self.assertEqual(draft.raw_text, "x^2+1")
        self.assertEqual(draft.latex, "x^{2}+1")
        self.assertEqual(draft.question_type, "blank")

    def test_blank_response_unclear(self):
        self.client.inject_custom_payload(
            {"raw_text": "unclear", "confidence": 0.40, "status": "unclear"}
        )
        req = QwenRequest(prompt_type=PROMPT_TYPE_BLANK_ANSWER, prompt="test")
        resp = self.client.recognize_blank_answer(req)
        result = parse_qwen_response(resp, PROMPT_TYPE_BLANK_ANSWER)
        draft = parse_blank_response_to_draft(result, question_number=14)
        self.assertEqual(draft.status, RecognizedAnswerDraft.STATUS_UNCLEAR)
        self.assertTrue(draft.needs_review)

    # -- complex judgment → QwenJudgmentMock ---------------------------------

    def test_complex_judgment_to_mock(self):
        req = QwenRequest(
            prompt_type=PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT, prompt="test"
        )
        resp = self.client.judge_complex_blank(req)
        result = parse_qwen_response(
            resp, PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT
        )
        judgment = parse_complex_judgment_response(result)
        self.assertIsInstance(judgment, QwenJudgmentMock)
        self.assertEqual(judgment.verdict, "correct")
        self.assertEqual(judgment.confidence, 0.96)

    def test_high_confidence_can_auto_accept(self):
        req = QwenRequest(
            prompt_type=PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT, prompt="test"
        )
        resp = self.client.judge_complex_blank(req)
        result = parse_qwen_response(
            resp, PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT
        )
        judgment = parse_complex_judgment_response(result)
        self.assertTrue(should_auto_accept_qwen_judgment(judgment))

    def test_low_confidence_cannot_auto_accept(self):
        self.client.inject_custom_payload(
            {
                "verdict": "correct",
                "confidence": 0.70,
                "reason": "same",
                "normalized_standard": "x > 1",
                "normalized_student": "x > 1",
                "requires_review": False,
            }
        )
        req = QwenRequest(
            prompt_type=PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT, prompt="test"
        )
        resp = self.client.judge_complex_blank(req)
        result = parse_qwen_response(
            resp, PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT
        )
        judgment = parse_complex_judgment_response(result)
        self.assertFalse(
            should_auto_accept_qwen_judgment(judgment, threshold=0.90)
        )

    def test_needs_review_response_mapping(self):
        self.client.inject_error("needs_review_true")
        req = QwenRequest(
            prompt_type=PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT, prompt="test"
        )
        resp = self.client.judge_complex_blank(req)
        result = parse_qwen_response(
            resp, PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT
        )
        judgment = parse_complex_judgment_response(result)
        self.assertEqual(judgment.verdict, "needs_review")
        self.assertTrue(judgment.requires_review)


if __name__ == "__main__":
    unittest.main()
