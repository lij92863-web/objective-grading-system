"""Deterministic scoring engine for objective grading."""

from collections import Counter
from typing import FrozenSet, Iterable, List, Tuple

from .blank_scoring import blank_answer_matches, canonical_blank_text
from .models import AnswerKey, QuestionResult, QuestionSpec, SingleQuestionScore, StudentResult, Submission
from .normalize import allowed_options, format_answer, format_expected_answer, is_choice_answer, matches_text_answer, normalize_text_answer
from .true_false_scoring import normalize_true_false


def _question_type(spec: QuestionSpec) -> str:
    explicit = (spec.question_type or "").strip().lower()
    if explicit:
        if explicit in {"judge", "judgement", "judgment", "tf", "truefalse", "true_false", "\u5224\u65ad", "\u5224\u65ad\u9898"}:
            return "true_false"
        if explicit in {"blank", "fill_blank", "fill_in_blank", "\u586b\u7a7a", "\u586b\u7a7a\u9898"}:
            return "blank"
        if explicit in {"single", "single_choice", "\u5355\u9009", "\u5355\u9009\u9898"}:
            return "single_choice"
        if explicit in {"multiple", "multiple_choice", "\u591a\u9009", "\u591a\u9009\u9898"}:
            return "multiple_choice"
    expected_text = (spec.answer_text or format_answer(spec.answers)).strip()
    if normalize_true_false(expected_text) is not None or spec.answers <= {"T", "F", "\u221a", "\u00d7", "X"}:
        return "true_false"
    if is_choice_answer(spec.answers):
        return "multiple_choice" if len(spec.answers) > 1 else "single_choice"
    return "blank"


def _detail(spec: QuestionSpec, actual: FrozenSet[str], raw_actual: str, score: float, status: str, reason: str = "", needs_review: bool = False) -> SingleQuestionScore:
    expected_text = format_expected_answer(spec)
    normalized = format_answer(actual) if actual else canonical_blank_text(raw_actual)
    return SingleQuestionScore(
        question_number=spec.number,
        score=score,
        max_score=0.0 if spec.status in {"cancelled", "manual_review"} else spec.points,
        status=status,
        question_type=_question_type(spec),
        expected=spec.answers,
        actual=actual,
        raw_actual=raw_actual,
        student_answer=raw_actual,
        normalized_answer=normalized,
        correct_answer=expected_text,
        reason=reason or status,
        needs_review=needs_review,
    )


def score_answer_detail(spec: QuestionSpec, actual: FrozenSet[str], raw_actual: str = "") -> SingleQuestionScore:
    if spec.status == "cancelled":
        return _detail(spec, actual, raw_actual, 0.0, "cancelled")
    if spec.status == "manual_review":
        return _detail(spec, actual, raw_actual, 0.0, "manual_review", needs_review=True)
    if spec.status == "bonus_all":
        return _detail(spec, actual, raw_actual, spec.points, "bonus")
    if spec.status == "bonus_if_answered":
        return _detail(spec, actual, raw_actual, spec.points, "bonus") if actual or raw_actual.strip() else _detail(spec, actual, raw_actual, 0.0, "blank")
    if normalize_text_answer(raw_actual) in {"unrecognized", "__unrecognized__", "\u8bc6\u522b\u5931\u8d25"}:
        return _detail(spec, actual, raw_actual, 0.0, "unrecognized", needs_review=True)
    if not actual and not raw_actual.strip():
        return _detail(spec, actual, raw_actual, 0.0, "blank")

    question_type = _question_type(spec)
    if question_type == "true_false":
        expected = normalize_true_false(spec.answer_text or format_answer(spec.answers))
        student = normalize_true_false(raw_actual or format_answer(actual))
        if expected is None or student is None:
            return _detail(spec, actual, raw_actual, 0.0, "invalid", "true_false_not_recognized")
        return _detail(spec, actual, raw_actual, spec.points, "correct") if expected == student else _detail(spec, actual, raw_actual, 0.0, "wrong")

    if ((spec.answer_aliases or spec.tolerance is not None) or not is_choice_answer(spec.answers)) and matches_text_answer(spec, raw_actual):
        return _detail(spec, actual, raw_actual, spec.points, "correct")

    if question_type == "blank":
        expected_values = [spec.answer_text or format_answer(spec.answers)] + list(spec.answer_aliases)
        matched, needs_review = blank_answer_matches(expected_values, raw_actual)
        if matched:
            return _detail(spec, actual, raw_actual, spec.points, "correct")
        if needs_review:
            return _detail(spec, actual, raw_actual, 0.0, "needs_review", "blank_answer_needs_teacher_review", True)
        return _detail(spec, actual, raw_actual, 0.0, "wrong")

    if actual and actual == spec.answers:
        return _detail(spec, actual, raw_actual, spec.points, "correct")
    if is_choice_answer(spec.answers) and not actual <= allowed_options(spec):
        return _detail(spec, actual, raw_actual, 0.0, "invalid")
    if len(spec.answers) == 1:
        return _detail(spec, actual, raw_actual, 0.0, "wrong")
    if spec.partial_credit and len(spec.answers) > 1:
        wrong_selected = actual - spec.answers
        right_selected = actual & spec.answers
        if wrong_selected:
            return _detail(spec, actual, raw_actual, 0.0, "wrong")
        if right_selected:
            partial = spec.partial_points if spec.partial_points is not None else spec.points * len(right_selected) / len(spec.answers)
            return _detail(spec, actual, raw_actual, round(partial, 6), "partial")
    return _detail(spec, actual, raw_actual, 0.0, "wrong")


def score_answer(spec: QuestionSpec, actual: FrozenSet[str], raw_actual: str = "") -> Tuple[float, str]:
    detail = score_answer_detail(spec, actual, raw_actual)
    return detail.score, detail.status


def grade_submission(answer_key: AnswerKey, submission: Submission) -> StudentResult:
    details: List[QuestionResult] = []
    status_counts: Counter = Counter()
    score = 0.0
    for spec in answer_key.questions:
        actual = submission.answers.get(spec.number, frozenset())
        raw_actual = submission.raw_answers.get(spec.number, "")
        detail = score_answer_detail(spec, actual, raw_actual)
        status_counts[detail.status] += 1
        score += detail.score
        details.append(
            QuestionResult(
                number=spec.number,
                expected=spec.answers,
                actual=actual,
                raw_actual=raw_actual,
                score=detail.score,
                max_score=detail.max_score,
                status=detail.status,
                question_type=detail.question_type,
                student_answer=detail.student_answer,
                normalized_answer=detail.normalized_answer,
                correct_answer=detail.correct_answer,
                reason=detail.reason,
                needs_review=detail.needs_review,
            )
        )
    max_score = answer_key.total_points
    return StudentResult(
        student_id=submission.student_id,
        name=submission.name,
        score=round(score, 6),
        max_score=max_score,
        percent=round(score / max_score * 100, 2) if max_score else 0.0,
        correct_count=status_counts["correct"] + status_counts["bonus"],
        wrong_or_partial_count=status_counts["wrong"] + status_counts["partial"] + status_counts["needs_review"],
        blank_count=status_counts["blank"],
        invalid_count=status_counts["invalid"] + status_counts["unrecognized"],
        details=tuple(details),
    )


def grade_all(answer_key: AnswerKey, submissions: Iterable[Submission]) -> List[StudentResult]:
    return [grade_submission(answer_key, submission) for submission in submissions]
