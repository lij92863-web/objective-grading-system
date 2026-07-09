from __future__ import annotations

ACCEPTED_STATUSES = {"accepted", "accepted_with_warnings"}


def answer_has_source(answer: dict[str, object]) -> bool:
    span = answer.get("source_span")
    if isinstance(span, dict):
        if any(span.get(key) for key in ("start_block", "end_block", "table_id")):
            return True
    return bool(answer.get("source_block_id") or answer.get("source_table_id"))


def validate_extraction_result_evidence(result: dict[str, object]) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    answers = result.get("answers", {})
    if not isinstance(answers, dict):
        return [{"type": "invalid_answers_container"}]
    for question_no, answer in answers.items():
        if not isinstance(answer, dict):
            continue
        status = answer.get("validation_status")
        if status not in ACCEPTED_STATUSES:
            continue
        missing: list[str] = []
        if not answer.get("evidence_text"):
            missing.append("evidence_text")
        if not answer.get("source_kind"):
            missing.append("source_kind")
        if not answer.get("source_file") and not answer.get("source_document_id"):
            missing.append("source_file")
        if not answer_has_source(answer):
            missing.append("source_span")
        if missing:
            violations.append({"type": "missing_evidence_for_accepted_answer", "question_no": question_no, "missing": missing})
    return violations


def enforce_result_evidence_invariant(result: dict[str, object]) -> dict[str, object]:
    violations = validate_extraction_result_evidence(result)
    if not violations:
        return result
    result = dict(result)
    answers = dict(result.get("answers", {}))
    for violation in violations:
        question_no = str(violation.get("question_no"))
        answer = dict(answers.get(question_no, {}))
        if answer.get("validation_status") in ACCEPTED_STATUSES:
            answer["validation_status"] = "needs_review"
            answers[question_no] = answer
    review_items = list(result.get("review_items", []))
    review_items.extend(violations)
    result["answers"] = answers
    result["review_items"] = review_items
    result["review_count"] = len(review_items)
    result["evidence_invariant_violations"] = violations
    if result.get("status") == "accepted":
        result["status"] = "needs_review"
    return result
