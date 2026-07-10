"""Canonical question-type parsing and conservative legacy inference."""

from typing import FrozenSet

from .models import QuestionType


QUESTION_TYPE_ALIASES = {
    "single_choice": QuestionType.SINGLE_CHOICE.value,
    "single": QuestionType.SINGLE_CHOICE.value,
    "\u5355\u9009": QuestionType.SINGLE_CHOICE.value,
    "\u5355\u9009\u9898": QuestionType.SINGLE_CHOICE.value,
    "\u5355\u9879\u9009\u62e9": QuestionType.SINGLE_CHOICE.value,
    "multiple_choice": QuestionType.MULTIPLE_CHOICE.value,
    "multiple": QuestionType.MULTIPLE_CHOICE.value,
    "\u591a\u9009": QuestionType.MULTIPLE_CHOICE.value,
    "\u591a\u9009\u9898": QuestionType.MULTIPLE_CHOICE.value,
    "\u591a\u9879\u9009\u62e9": QuestionType.MULTIPLE_CHOICE.value,
    "true_false": QuestionType.TRUE_FALSE.value,
    "judge": QuestionType.TRUE_FALSE.value,
    "judgement": QuestionType.TRUE_FALSE.value,
    "judgment": QuestionType.TRUE_FALSE.value,
    "tf": QuestionType.TRUE_FALSE.value,
    "truefalse": QuestionType.TRUE_FALSE.value,
    "\u5224\u65ad": QuestionType.TRUE_FALSE.value,
    "\u5224\u65ad\u9898": QuestionType.TRUE_FALSE.value,
    "blank": QuestionType.BLANK.value,
    "fill_blank": QuestionType.BLANK.value,
    "fill_in_blank": QuestionType.BLANK.value,
    "\u586b\u7a7a": QuestionType.BLANK.value,
    "\u586b\u7a7a\u9898": QuestionType.BLANK.value,
}


def resolve_question_type(
    explicit_value: object,
    answer_raw: str,
    answers: FrozenSet[str],
) -> str:
    explicit = str(explicit_value or "").strip().lower()
    if explicit:
        try:
            return QUESTION_TYPE_ALIASES[explicit]
        except KeyError as exc:
            raise ValueError(f"unknown question type: {explicit}") from exc
    if not str(answer_raw or "").strip() and not answers:
        raise ValueError("empty expected answer requires explicit question type")
    if answers and answers <= set("ABCDEFGH"):
        return QuestionType.MULTIPLE_CHOICE.value if len(answers) > 1 else QuestionType.SINGLE_CHOICE.value
    if str(answer_raw).strip().upper() in {"T", "F", "X"}:
        raise ValueError("ambiguous truth/choice marker requires explicit question type")
    return QuestionType.BLANK.value
