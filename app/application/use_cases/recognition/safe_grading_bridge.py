"""Safe grading bridge — R12. Confirmed submission → grading without legacy.

Does NOT import legacy, compat, workflow, or web.
Only validates that a TeacherConfirmedSubmission can be converted to
submission-compatible rows acceptable by the existing grading core.
"""
import csv, io
from pathlib import Path
from typing import Any, Dict, List

from app.recognition.contracts import TeacherConfirmedSubmission, RecognizedSubmissionDraft


def validate_draft_safe_for_grading(draft: RecognizedSubmissionDraft) -> List[str]:
    """Return list of blockers; empty = safe."""
    blockers = []
    if not draft.ready_for_confirmation:
        blockers.append("DRAFT_NOT_READY_FOR_CONFIRMATION")
    if draft.ready_for_grading:
        blockers.append("DRAFT_ALREADY_READY_FOR_GRADING_WITHOUT_CONFIRMATION")
    if draft.identity_status in ("missing", "conflict"):
        blockers.append(f"IDENTITY_{draft.identity_status.upper()}")
    if draft.exceptions:
        blockers.append("BLOCKING_EXCEPTIONS_PRESENT")
    unreviewed = [d for d in draft.decisions if d.needs_review]
    if unreviewed:
        blockers.append(f"UNREVIEWED_ITEMS:{len(unreviewed)}")
    return blockers


def convert_confirmed_to_submission_rows(confirmed: TeacherConfirmedSubmission) -> List[Dict[str, str]]:
    """Convert confirmed submission to rows compatible with csv.DictReader."""
    row = {"student_id": confirmed.student_id, "name": confirmed.name}
    for qn in sorted(confirmed.answers):
        row[f"Q{qn}"] = confirmed.answers[qn]
    return [row]


def write_submission_csv(rows: List[Dict[str, str]], path: Path) -> None:
    """Write submission-compatible CSV rows."""
    if not rows:
        raise ValueError("No rows to write")
    fields = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def safe_dry_run_grading(confirmed: TeacherConfirmedSubmission, answer_key_path, submissions_path) -> Dict[str, Any]:
    """Dry-run grading with existing domain core. No legacy, no workflow, no reports."""
    rows = convert_confirmed_to_submission_rows(confirmed)
    write_submission_csv(rows, Path(submissions_path))
    from app.infrastructure.loaders.csv_loaders import load_answer_key, load_submissions
    from app.domain.grading import grade_all
    ak = load_answer_key(Path(answer_key_path))
    subs = load_submissions(Path(submissions_path), ak)
    results = grade_all(ak, subs)
    return {
        "student_count": len(results),
        "total_score": sum(r.score for r in results),
        "max_score": results[0].max_score if results else 0,
        "passed": True,
    }
