import dataclasses
import sqlite3


IDENTITY_TYPES = {
    "IDENTITY_MISSING",
    "IDENTITY_CONFLICT",
    "IDENTITY_DUPLICATE",
}


@dataclasses.dataclass(frozen=True)
class PresentedReviewIssue:
    issue_id: str
    issue_type: str
    teacher_message: str
    question_number: int | None
    evidence_path: str
    state: str


def present_issue(row: sqlite3.Row) -> PresentedReviewIssue:
    return PresentedReviewIssue(
        issue_id=row["id"],
        issue_type=row["issue_type"],
        teacher_message=row["teacher_message"],
        question_number=row["question_number"],
        evidence_path=row["evidence_path"],
        state=row["state"],
    )


def review_sort_key(issue: PresentedReviewIssue) -> tuple[int, int, str]:
    priority = 0 if issue.issue_type in IDENTITY_TYPES else 1
    return (priority, issue.question_number or 0, issue.issue_id)
