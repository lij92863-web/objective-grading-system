import json
import unittest

from app.recognition.qwen_adapter import (
    QwenAdapterErrorCode,
    QwenRawResponse,
    parse_qwen_response,
    PROMPT_TYPE_NAME_FIELD,
    PROMPT_TYPE_CHOICE_CELL,
    PROMPT_TYPE_BLANK_ANSWER,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT,
)


class ParserTests(unittest.TestCase):
    # -- valid JSON ----------------------------------------------------------

    def test_name_field_valid(self):
        data = {"raw_text": "1李明", "confidence": 0.98}
        resp = QwenRawResponse(
            raw_text=json.dumps(data, ensure_ascii=False),
            parsed_json=data,
        )
        result = parse_qwen_response(resp, PROMPT_TYPE_NAME_FIELD)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.errors, [])

    def test_choice_cell_valid(self):
        data = {"answer": "AB", "confidence": 0.96}
        resp = QwenRawResponse(
            raw_text=json.dumps(data), parsed_json=data
        )
        result = parse_qwen_response(resp, PROMPT_TYPE_CHOICE_CELL)
        self.assertEqual(result.status, "ok")

    def test_blank_answer_valid(self):
        data = {
            "raw_text": "x+1",
            "latex": "x+1",
            "confidence": 0.92,
            "status": "recognized",
        }
        resp = QwenRawResponse(
            raw_text=json.dumps(data), parsed_json=data
        )
        result = parse_qwen_response(resp, PROMPT_TYPE_BLANK_ANSWER)
        self.assertEqual(result.status, "ok")

    def test_complex_judgment_valid(self):
        data = {
            "verdict": "correct",
            "confidence": 0.96,
            "reason": "equivalent",
            "normalized_standard": "x > 1",
            "normalized_student": "x > 1",
            "requires_review": False,
        }
        resp = QwenRawResponse(
            raw_text=json.dumps(data), parsed_json=data
        )
        result = parse_qwen_response(resp, PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT)
        self.assertEqual(result.status, "ok")

    # -- invalid JSON --------------------------------------------------------

    def test_non_json_returns_invalid_json_error(self):
        resp = QwenRawResponse(raw_text="{not json")
        result = parse_qwen_response(resp, PROMPT_TYPE_NAME_FIELD)
        self.assertEqual(result.status, "error")
        self.assertIn(QwenAdapterErrorCode.INVALID_JSON, result.errors)

    def test_empty_string(self):
        resp = QwenRawResponse(raw_text="")
        result = parse_qwen_response(resp, PROMPT_TYPE_NAME_FIELD)
        self.assertEqual(result.status, "error")

    # -- missing field -------------------------------------------------------

    def test_missing_raw_text_in_name_field(self):
        data = {"confidence": 0.9}
        resp = QwenRawResponse(
            raw_text=json.dumps(data), parsed_json=data
        )
        result = parse_qwen_response(resp, PROMPT_TYPE_NAME_FIELD)
        self.assertIn(
            QwenAdapterErrorCode.MISSING_REQUIRED_FIELD, result.errors
        )

    # -- invalid confidence --------------------------------------------------

    def test_confidence_above_1(self):
        data = {"raw_text": "x", "confidence": 1.2}
        resp = QwenRawResponse(
            raw_text=json.dumps(data), parsed_json=data
        )
        result = parse_qwen_response(resp, PROMPT_TYPE_BLANK_ANSWER)
        self.assertIn(
            QwenAdapterErrorCode.INVALID_CONFIDENCE, result.errors
        )

    def test_confidence_below_0(self):
        data = {"raw_text": "x", "confidence": -0.1}
        resp = QwenRawResponse(
            raw_text=json.dumps(data), parsed_json=data
        )
        result = parse_qwen_response(resp, PROMPT_TYPE_BLANK_ANSWER)
        self.assertIn(
            QwenAdapterErrorCode.INVALID_CONFIDENCE, result.errors
        )

    # -- invalid verdict -----------------------------------------------------

    def test_invalid_verdict_in_judgment(self):
        data = {
            "verdict": "maybe",
            "confidence": 0.9,
            "reason": "?",
            "normalized_standard": "x",
            "normalized_student": "x",
            "requires_review": False,
        }
        resp = QwenRawResponse(
            raw_text=json.dumps(data), parsed_json=data
        )
        result = parse_qwen_response(
            resp, PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT
        )
        self.assertIn(QwenAdapterErrorCode.INVALID_VERDICT, result.errors)

    # -- unsupported prompt type --------------------------------------------

    def test_unsupported_prompt_type(self):
        data = {"raw_text": "x"}
        resp = QwenRawResponse(
            raw_text=json.dumps(data), parsed_json=data
        )
        result = parse_qwen_response(resp, "unknown_type")
        self.assertIn(
            QwenAdapterErrorCode.UNSUPPORTED_PROMPT_TYPE, result.errors
        )

    # -- request_id propagation -----------------------------------------------

    def test_request_id_from_response(self):
        data = {"raw_text": "1李明", "confidence": 0.98}
        resp = QwenRawResponse(
            request_id="req-001",
            raw_text=json.dumps(data, ensure_ascii=False),
            parsed_json=data,
        )
        result = parse_qwen_response(resp, PROMPT_TYPE_NAME_FIELD)
        self.assertEqual(result.request_id, "req-001")

    def test_request_id_explicit_overrides_response(self):
        data = {"raw_text": "1李明", "confidence": 0.98}
        resp = QwenRawResponse(
            request_id="req-from-resp",
            raw_text=json.dumps(data, ensure_ascii=False),
            parsed_json=data,
        )
        result = parse_qwen_response(
            resp, PROMPT_TYPE_NAME_FIELD, request_id="explicit-001"
        )
        self.assertEqual(result.request_id, "explicit-001")

    def test_request_id_on_error_result(self):
        resp = QwenRawResponse(request_id="req-err", raw_text="{not json")
        result = parse_qwen_response(resp, PROMPT_TYPE_NAME_FIELD)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.request_id, "req-err")


if __name__ == "__main__":
    unittest.main()
