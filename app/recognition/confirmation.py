"""Recognition draft → teacher confirmation → submission CSV boundary."""
import csv
from pathlib import Path
from .contracts import RecognizedSubmissionDraft, TeacherConfirmedSubmission


def confirm_recognition_draft(draft, reviewed_items, reviewer="teacher") -> TeacherConfirmedSubmission:
    """Confirm after review. Raises ValueError if not ready."""
    if not draft.ready_for_confirmation:
        raise ValueError("Draft not ready for confirmation")
    if draft.identity_status in ("missing", "conflict"):
        raise ValueError(f"Identity not confirmed: {draft.identity_status}")
    if draft.exceptions:
        raise ValueError("Blocking exceptions still present")
    unreviewed = [d for d in draft.decisions if d.needs_review and d.question_number not in reviewed_items]
    if unreviewed:
        raise ValueError(f"Unreviewed items: {[d.question_number for d in unreviewed]}")
    answers = {}
    for d in draft.decisions:
        qn = d.question_number
        if qn in reviewed_items:
            answers[qn] = reviewed_items[qn]
        else:
            answers[qn] = d.value
    return TeacherConfirmedSubmission(student_id=draft.student_id, name=draft.student_name,
                                       answers=answers, confirmed_by=reviewer,
                                       source_draft_id=draft.student_id)


def export_confirmed_submission_csv(confirmed, path):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["student_id", "name"] + [f"Q{q}" for q in sorted(confirmed.answers)])
        writer.writerow([confirmed.student_id, confirmed.name] +
                        [confirmed.answers.get(q, "") for q in sorted(confirmed.answers)])
