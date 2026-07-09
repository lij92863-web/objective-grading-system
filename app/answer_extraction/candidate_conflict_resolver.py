from __future__ import annotations

from dataclasses import dataclass, field

from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool


@dataclass
class ConflictResolutionResult:
    candidate_pool: AnswerCandidatePool
    warnings: list[str] = field(default_factory=list)
    blocking_errors: list[str] = field(default_factory=list)


def resolve_candidate_conflicts(pool: AnswerCandidatePool) -> ConflictResolutionResult:
    resolved = AnswerCandidatePool()
    warnings: list[str] = []
    blocking: list[str] = []
    for question_no, candidates in pool.candidates_by_question.items():
        non_llm = [candidate for candidate in candidates if candidate.source_kind != "llm_candidate"]
        if non_llm and len(non_llm) != len(candidates):
            warnings.append("llm_candidate_ignored_due_rule_candidate")
            candidates = non_llm
        by_answer: dict[str, list[AnswerCandidate]] = {}
        for candidate in candidates:
            by_answer.setdefault(candidate.normalized_answer, []).append(candidate)
        if len(by_answer) > 1:
            high = [candidate for candidate in candidates if candidate.confidence >= 0.9]
            if len({candidate.normalized_answer for candidate in high}) > 1:
                blocking.append("duplicate_conflicting_answer")
            table = [candidate for candidate in candidates if candidate.source_kind == "answer_table"]
            if table:
                resolved.add(sorted(table, key=lambda c: -c.confidence)[0])
                continue
        for same_answer in by_answer.values():
            merged = sorted(same_answer, key=lambda c: -c.confidence)[0]
            if len(same_answer) > 1:
                merged.warnings = sorted(set(merged.warnings + ["duplicate_same_answer"]))
            resolved.add(merged)
    return ConflictResolutionResult(resolved, sorted(set(warnings)), sorted(set(blocking)))
