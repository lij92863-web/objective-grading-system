"""Pre-grading validation that separates blockers, warnings, and review items."""

import dataclasses
from collections import Counter
from typing import Iterable, List, Optional, Sequence

from .answer_draft import AnswerDraft, DraftAnswerItem, DraftStatus
from .models import AnswerKey, QuestionSpec, Submission
from .normalize import allowed_options, is_choice_answer


@dataclasses.dataclass(frozen=True)
class PrecheckIssue:
    severity: str
    scope: str
    item: str
    message: str


@dataclasses.dataclass(frozen=True)
class PrecheckReport:
    can_grade: bool
    blocking: tuple[PrecheckIssue, ...]
    warnings: tuple[PrecheckIssue, ...]
    review_required: tuple[PrecheckIssue, ...]


def _as_list(value: Optional[Iterable]) -> list:
    if value is None:
        return []
    return list(value)


def _questions(answer_key: Optional[AnswerKey], question_specs: Optional[Iterable[QuestionSpec]]) -> List[QuestionSpec]:
    if answer_key is not None:
        return list(answer_key.questions)
    return _as_list(question_specs)


def _students_from_submissions(submissions: Sequence[Submission]) -> List[str]:
    return [submission.student_id for submission in submissions if submission.student_id]


def _check_draft_item(item: DraftAnswerItem) -> Optional[PrecheckIssue]:
    if item.status in {DraftStatus.CONFIRMED, DraftStatus.BLANK}:
        return None
    messages = {
        DraftStatus.LOW_CONFIDENCE: "\u4f5c\u7b54\u7f6e\u4fe1\u5ea6\u8f83\u4f4e\uff0c\u9700\u8981\u8001\u5e08\u786e\u8ba4\u3002",
        DraftStatus.CONFLICT: "\u4f5c\u7b54\u5b58\u5728\u51b2\u7a81\uff0c\u9700\u8981\u8001\u5e08\u590d\u6838\u3002",
        DraftStatus.NEEDS_REVIEW: "\u4f5c\u7b54\u9700\u8981\u4eba\u5de5\u590d\u6838\u3002",
        DraftStatus.DRAFT: "\u4f5c\u7b54\u8fd8\u672a\u786e\u8ba4\uff0c\u4e0d\u5e94\u76f4\u63a5\u8fdb\u5165\u6b63\u5f0f\u6279\u6539\u3002",
    }
    return PrecheckIssue("review", "draft_answer", f"Q{item.question_number}", messages.get(item.status, "\u4f5c\u7b54\u72b6\u6001\u9700\u590d\u6838\u3002"))


def run_grading_precheck(
    *,
    students: Optional[Iterable[str]] = None,
    answer_key: Optional[AnswerKey] = None,
    submissions: Optional[Iterable[Submission]] = None,
    question_specs: Optional[Iterable[QuestionSpec]] = None,
    draft_answers: Optional[Iterable[AnswerDraft | DraftAnswerItem]] = None,
    strict_drafts: bool = True,
) -> PrecheckReport:
    blocking: List[PrecheckIssue] = []
    warnings: List[PrecheckIssue] = []
    review_required: List[PrecheckIssue] = []

    submission_list = _as_list(submissions)
    question_list = _questions(answer_key, question_specs)
    student_list = _as_list(students) or _students_from_submissions(submission_list)

    if not student_list:
        blocking.append(PrecheckIssue("error", "students", "-", "\u6ca1\u6709\u5b66\u751f\u540d\u5355\uff0c\u4e0d\u80fd\u5f00\u59cb\u6279\u6539\u3002"))
    if not question_list:
        blocking.append(PrecheckIssue("error", "answer_key", "-", "\u6ca1\u6709\u6807\u51c6\u7b54\u6848\uff0c\u4e0d\u80fd\u5f00\u59cb\u6279\u6539\u3002"))
    if not submission_list and not _as_list(draft_answers):
        blocking.append(PrecheckIssue("error", "submissions", "-", "\u6ca1\u6709\u5b66\u751f\u4f5c\u7b54\uff0c\u4e0d\u80fd\u5f00\u59cb\u6279\u6539\u3002"))

    duplicates = [student_id for student_id, count in Counter(student_list).items() if student_id and count > 1]
    for student_id in duplicates:
        warnings.append(PrecheckIssue("warning", "students", student_id, "\u5b66\u751f\u7f16\u53f7\u91cd\u590d\uff0c\u8bf7\u786e\u8ba4\u662f\u5426\u540c\u4e00\u4eba\u3002"))

    spec_by_number = {spec.number: spec for spec in question_list}
    for submission in submission_list:
        if not submission.student_id or not submission.name:
            warnings.append(PrecheckIssue("warning", "submission", f"row:{submission.row_number}", "\u5b66\u751f\u7f16\u53f7\u6216\u59d3\u540d\u7f3a\u5931\u3002"))
        for number, spec in spec_by_number.items():
            actual = submission.answers.get(number, frozenset())
            raw = submission.raw_answers.get(number, "")
            if not actual and not str(raw or "").strip():
                warnings.append(PrecheckIssue("warning", "answer", f"{submission.student_id}:Q{number}", "\u5b66\u751f\u4f5c\u7b54\u4e3a\u7a7a\u3002"))
            if is_choice_answer(spec.answers) and actual and not actual <= allowed_options(spec):
                warnings.append(PrecheckIssue("warning", "answer", f"{submission.student_id}:Q{number}", "\u4f5c\u7b54\u9009\u9879\u8d85\u51fa\u5141\u8bb8\u8303\u56f4\u3002"))

    for draft in _as_list(draft_answers):
        items = draft.items if isinstance(draft, AnswerDraft) else (draft,)
        for item in items:
            issue = _check_draft_item(item)
            if issue is not None:
                review_required.append(issue)

    can_grade = not blocking and (not strict_drafts or not review_required)
    return PrecheckReport(
        can_grade=can_grade,
        blocking=tuple(blocking),
        warnings=tuple(warnings),
        review_required=tuple(review_required),
    )
