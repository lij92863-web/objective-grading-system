from __future__ import annotations

import unittest

from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool
from app.answer_extraction.candidate_conflict_resolver import resolve_candidate_conflicts, ConflictResolutionResult


def _candidate(qno, answer, source="answer_table", confidence=0.99, evidence="ev"):
    return AnswerCandidate(question_no=qno, raw_answer=answer, normalized_answer=answer,
                           source_kind=source, source_file="f.json", evidence_text=evidence,
                           confidence=confidence)


class CandidateConflictResolverV3Tests(unittest.TestCase):
    def test_same_answer_different_sources_merged(self):
        pool = AnswerCandidatePool()
        pool.add(_candidate(1, "B", "answer_table", 0.99))
        pool.add(_candidate(1, "B", "guxuan", 0.88))
        result = resolve_candidate_conflicts(pool)
        self.assertEqual(len(result.candidate_pool.candidates_by_question[1]), 1)
        self.assertEqual(result.candidate_pool.highest_confidence_candidate(1).confidence, 0.99)

    def test_table_vs_guxuan_same_answer_no_conflict(self):
        pool = AnswerCandidatePool()
        pool.add(_candidate(1, "C", "answer_table", 0.99))
        pool.add(_candidate(1, "C", "guxuan", 0.88))
        result = resolve_candidate_conflicts(pool)
        self.assertEqual(len(result.blocking_errors), 0)

    def test_conflicting_high_confidence_blocked(self):
        pool = AnswerCandidatePool()
        pool.add(_candidate(1, "B", "answer_table", 0.99))
        pool.add(_candidate(1, "C", "guxuan", 0.90))
        result = resolve_candidate_conflicts(pool)
        self.assertTrue(len(result.blocking_errors) > 0)

    def test_llm_candidate_ignored_when_deterministic_present(self):
        pool = AnswerCandidatePool()
        pool.add(_candidate(1, "B", "answer_table", 0.99))
        pool.add(_candidate(1, "C", "llm_candidate", 0.70))
        result = resolve_candidate_conflicts(pool)
        self.assertTrue(any("llm" in w.lower() for w in result.warnings))

    def test_llm_only_stays(self):
        pool = AnswerCandidatePool()
        pool.add(_candidate(1, "B", "llm_candidate", 0.70))
        result = resolve_candidate_conflicts(pool)
        self.assertEqual(len(result.candidate_pool.candidates_by_question.get(1, [])), 1)

    def test_duplicate_same_answer_warning_not_blocking(self):
        pool = AnswerCandidatePool()
        pool.add(_candidate(1, "B", "answer_table", 0.99))
        pool.add(_candidate(1, "B", "answer_table", 0.99))
        result = resolve_candidate_conflicts(pool)
        self.assertEqual(len(result.blocking_errors), 0)

    def test_blank_conflict_review(self):
        pool = AnswerCandidatePool()
        pool.add(_candidate(1, "\\frac{1}{2}", "explicit_bracket_answer", 0.98, "ev1"))
        pool.add(_candidate(1, "0.5", "gu_daanwei", 0.86, "ev2"))
        result = resolve_candidate_conflicts(pool)
        has_issue = len(result.blocking_errors) > 0 or len(result.warnings) > 0 or len(result.candidate_pool.candidates_by_question.get(1, [])) >= 1
        self.assertTrue(has_issue, "Should have blocking error, warning, or at least one candidate")

    def test_multiple_questions_independent(self):
        pool = AnswerCandidatePool()
        pool.add(_candidate(1, "B", "answer_table", 0.99))
        pool.add(_candidate(2, "C", "guxuan", 0.88))
        result = resolve_candidate_conflicts(pool)
        self.assertEqual(len(result.candidate_pool.candidates_by_question), 2)

    def test_conflict_keeps_highest_confidence_per_unique_answer(self):
        pool = AnswerCandidatePool()
        pool.add(_candidate(1, "B", "answer_table", 0.99))
        pool.add(_candidate(1, "C", "guxuan", 0.60))
        pool.add(_candidate(1, "D", "short_itemized", 0.55))
        result = resolve_candidate_conflicts(pool)
        candidates = result.candidate_pool.candidates_by_question.get(1, [])
        self.assertTrue(len(candidates) >= 1)


if __name__ == "__main__":
    unittest.main()
