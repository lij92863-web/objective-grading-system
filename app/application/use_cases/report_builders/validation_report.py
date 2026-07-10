"""Validation report builder — matches legacy ``build_validation_report``."""

from collections import Counter


def build_validation_report(answer_key: dict, submissions: list, results: list, profiles: list, question_bank: list = None) -> list:
    rows = []
    question_bank = question_bank or []
    bank_ids = {q.get("question_id", "") for q in question_bank}
    bank_tags = {t for q in question_bank for t in (q.get("tags", []) or [])}

    by_number = answer_key.get("by_number", {})
    answer_key_numbers = set(by_number)

    # Extra questions in submissions
    submitted_numbers = set()
    for sub in submissions:
        submitted_numbers.update(sub.get("answers", {}))
        for qnum in sub.get("extra_questions", []):
            rows.append(dict(severity="warning", scope="submission",
                            item=f"{sub.get('student_id','')}:Q{qnum}",
                            message="submissions.csv contains a question that is not in answer_key.csv"))

    # Questions in answer key but nobody answered
    for number in sorted(answer_key_numbers - submitted_numbers):
        rows.append(dict(severity="info", scope="submission", item=f"Q{number}",
                        message="answer_key.csv contains a question that no submission answered"))

    # Post-grade consistency/display observations only. Input blocking rules are
    # owned exclusively by ``run_grading_precheck``.
    questions = answer_key.get("questions", [])
    for spec in questions:
        qnum = spec.get("question", spec.get("number", 0))
        status = spec.get("status", "normal")
        points = spec.get("points", 0)
        if points <= 0:
            rows.append(dict(severity="warning", scope="answer_key", item=f"Q{qnum}",
                            message="question points should be positive"))
        if status == "cancelled":
            rows.append(dict(severity="info", scope="answer_key", item=f"Q{qnum}",
                            message="question was cancelled and does not count toward totals"))

    # Bank coverage warnings
    if bank_ids:
        for spec in questions:
            sid = spec.get("source_id", "")
            if sid and sid not in bank_ids:
                rows.append(dict(severity="warning", scope="answer_key",
                                item=f"Q{spec.get('question', spec.get('number', ''))}",
                                message=f"question_id {sid} not in question bank"))

    # Profile tags not in bank
    if bank_tags:
        tag_set = {p.get("tag") for p in profiles}
        for tag in sorted(tag_set - bank_tags):
            rows.append(dict(severity="warning", scope="knowledge_profile", item=tag,
                            message="knowledge point tag not in question bank"))

    if not rows:
        rows.append(dict(severity="ok", scope="all", item="", message="no validation issues found"))
    return rows
