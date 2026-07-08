import unittest

from app.recognition.qwen_adapter import (
    PROMPT_TYPE_BLANK_ANSWER,
    PROMPT_TYPE_CHOICE_CELL,
    PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT,
    PROMPT_TYPE_NAME_FIELD,
    QwenAdapterError,
    QwenRequest,
)
from app.recognition.qwen_adapter.prompt_builder import build_prompt


class RequestBuildingTests(unittest.TestCase):
    # -- name_field prompt --------------------------------------------------

    def test_name_field_prompt(self):
        req = QwenRequest(prompt_type=PROMPT_TYPE_NAME_FIELD, prompt="")
        prompt = build_prompt(req)
        self.assertIn("姓名栏", prompt)
        self.assertIn("JSON", prompt)

    # -- choice_cell prompt -------------------------------------------------

    def test_choice_cell_prompt(self):
        req = QwenRequest(prompt_type=PROMPT_TYPE_CHOICE_CELL, prompt="")
        prompt = build_prompt(req)
        self.assertIn("A、B、C、D", prompt)
        self.assertIn("JSON", prompt)

    # -- blank_answer prompt ------------------------------------------------

    def test_blank_answer_prompt(self):
        req = QwenRequest(prompt_type=PROMPT_TYPE_BLANK_ANSWER, prompt="")
        prompt = build_prompt(req)
        self.assertIn("LaTeX", prompt)
        self.assertIn("JSON", prompt)

    # -- complex_blank_judgment prompt --------------------------------------

    def test_complex_blank_judgment_prompt(self):
        req = QwenRequest(
            prompt_type=PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT,
            prompt="",
            metadata={
                "standard_answer": "x>1",
                "student_answer": "(1,+oo)",
                "question_text": "解不等式",
                "points": "5",
                "ocr_confidence": "0.92",
                "format_required": "否",
            },
        )
        prompt = build_prompt(req)
        self.assertIn("x>1", prompt)
        self.assertIn("(1,+oo)", prompt)
        self.assertIn("解不等式", prompt)
        self.assertIn("verdict", prompt)

    def test_complex_blank_judgment_prompt_without_metadata(self):
        req = QwenRequest(
            prompt_type=PROMPT_TYPE_COMPLEX_BLANK_JUDGMENT, prompt=""
        )
        prompt = build_prompt(req)
        # Template is filled with defaults (empty strings)
        self.assertIn("verdict", prompt)

    # -- unsupported prompt type --------------------------------------------

    def test_unsupported_prompt_type_raises(self):
        req = QwenRequest(prompt_type="unknown_type", prompt="")
        with self.assertRaises(QwenAdapterError):
            build_prompt(req)

    # -- request_id preservation --------------------------------------------

    def test_request_id_preserved_in_request(self):
        req = QwenRequest(
            request_id="req-abc",
            prompt_type=PROMPT_TYPE_NAME_FIELD,
            prompt="",
        )
        self.assertEqual(req.request_id, "req-abc")


if __name__ == "__main__":
    unittest.main()
