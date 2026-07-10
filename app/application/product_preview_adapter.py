"""Compatibility adapter for the pre-existing JSON preview endpoint."""

from pathlib import Path

import objective_grader


def build_preview_data(
    answer_key_path: Path,
    submissions_path: Path,
    question_bank_path: Path | None,
) -> dict[str, object]:
    answer_key = objective_grader.load_answer_key(answer_key_path)
    submissions = objective_grader.load_submissions(submissions_path, answer_key)
    results = objective_grader.grade_all(answer_key, submissions)
    profiles = objective_grader.build_knowledge_profiles(answer_key, results)
    question_bank = (
        objective_grader.load_question_bank(question_bank_path)
        if question_bank_path and question_bank_path.exists()
        else None
    )
    validation_rows = objective_grader.build_validation_report(
        answer_key,
        submissions,
        results,
        profiles,
        question_bank,
    )
    return {
        "question_count": len(answer_key.questions),
        "student_count": len(submissions),
        "validation_rows": validation_rows,
    }
