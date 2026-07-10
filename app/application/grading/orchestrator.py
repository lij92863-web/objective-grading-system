"""Canonical load/precheck/grade orchestration without report concerns."""

from datetime import datetime

from app.domain.grading.precheck import PrecheckReport, run_grading_precheck
from app.domain.grading.scoring import grade_all
from app.infrastructure.loaders.csv_loaders import load_answer_key, load_submissions

from .contracts import (
    GradingRunRequest, GradingRunResult, GradingRunStatus, GradingStats,
)


def _new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def run_grading_orchestrator(request: GradingRunRequest) -> GradingRunResult:
    if not isinstance(request, GradingRunRequest):
        raise TypeError("request must be GradingRunRequest")
    answer_key = load_answer_key(request.answer_key_path)
    submissions = tuple(load_submissions(request.submissions_path, answer_key))
    precheck = run_grading_precheck(
        answer_key=answer_key,
        submissions=submissions,
        strict_drafts=request.validation_policy.strict_drafts,
    )
    external = request.validation_policy.external_issues
    if external:
        blocking = tuple(issue for issue in external if issue.severity == "error")
        warnings = tuple(issue for issue in external if issue.severity == "warning")
        review = tuple(issue for issue in external if issue.severity == "review")
        precheck = PrecheckReport(
            can_grade=precheck.can_grade and not blocking and not review,
            blocking=precheck.blocking + blocking,
            warnings=precheck.warnings + warnings,
            review_required=precheck.review_required + review,
        )
    run_id = request.run_id or _new_run_id()
    audit_warnings = ()
    if request.override is not None:
        override = request.override
        audit_warnings = (
            "override_audit: actor={actor}; codes={codes}; reason={reason}; created_at={created}".format(
                actor=override.actor,
                codes=",".join(override.allowed_issue_codes),
                reason=override.reason,
                created=override.created_at,
            ),
        )
    if not precheck.can_grade:
        return GradingRunResult(
            status=GradingRunStatus.BLOCKED,
            run_id=run_id,
            precheck=precheck,
            warnings=audit_warnings,
            answer_key=answer_key,
            submissions=submissions,
        )
    results = tuple(grade_all(answer_key, submissions))
    return GradingRunResult(
        status=GradingRunStatus.GRADED,
        run_id=run_id,
        precheck=precheck,
        warnings=audit_warnings,
        stats=GradingStats(len(submissions), len(answer_key.questions), answer_key.total_points),
        answer_key=answer_key,
        submissions=submissions,
        student_results=results,
    )
