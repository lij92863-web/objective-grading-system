from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.answer_extraction.answer_candidate_pool import AnswerCandidatePool
from app.answer_extraction.answer_key_validator import validate_answer_key
from app.answer_extraction.answer_layout_classifier import classify_answer_layout
from app.answer_extraction.answer_table_extractor import extract_answer_tables
from app.answer_extraction.cross_file_aligner import align_by_question_no
from app.answer_extraction.candidate_conflict_resolver import resolve_candidate_conflicts
from app.answer_extraction.docx_native_parser import parse_docx
from app.answer_extraction.document_model import DocumentModel
from app.answer_extraction.document_model_loader import load_document_model_json
from app.answer_extraction.extraction_report import ExtractionReport
from app.answer_extraction.extraction_strategy_router import ExtractionStrategy, choose_strategy
from app.answer_extraction.file_role_classifier import FileRole, classify_file_role
from app.answer_extraction.itemized_answer_extractor import extract_itemized_answers
from app.answer_extraction.question_index_builder import QuestionIndex, build_question_index


@dataclass
class ExtractionResult:
    run_id: str
    strategy: str
    status: str
    questions: list[dict[str, Any]]
    answers: dict[str, dict[str, Any]]
    alignment_report: dict[str, Any]
    review_items: list[dict[str, Any]]
    report: dict[str, Any]

    @property
    def question_count(self) -> int:
        return len(self.questions)

    @property
    def answer_count(self) -> int:
        return len(self.answers)

    def to_safe_dict(self) -> dict[str, Any]:
        accepted_count = self.report.get("accepted_count", 0) if isinstance(self.report, dict) else 0
        evidence_summary = {
            question_no: {
                "source_kind": answer.get("source_kind", ""),
                "source_file": answer.get("source_file", ""),
                "source_span": answer.get("source_span", {}),
            }
            for question_no, answer in self.answers.items()
        }
        return {
            "run_id": self.run_id,
            "strategy": self.strategy,
            "status": self.status,
            "question_count": self.question_count,
            "answer_count": self.answer_count,
            "accepted_count": accepted_count,
            "review_count": len(self.review_items),
            "questions": self.questions,
            "answers": self.answers,
            "alignment_report": self.alignment_report,
            "missing_answers": self.alignment_report.get("missing_answers", []),
            "unexpected_answers": self.alignment_report.get("unexpected_answers", []),
            "blocking_errors": self.alignment_report.get("blocking_errors", []),
            "review_items": self.review_items,
            "evidence_summary": evidence_summary,
            "report": self.report,
        }


def load_document(path: str | Path) -> DocumentModel:
    file_path = Path(path)
    if file_path.suffix.lower() == ".json":
        return load_document_model_json(file_path).document
    if file_path.suffix.lower() == ".docx":
        return parse_docx(file_path)
    raise ValueError("unsupported input file type")


def _load_all(inputs: list[str] | list[DocumentModel]) -> list[DocumentModel]:
    documents: list[DocumentModel] = []
    for item in inputs:
        if isinstance(item, DocumentModel):
            documents.append(item)
        else:
            documents.append(load_document(item))
    return documents


def _answer_document_index(roles: list[Any]) -> int:
    for index, role in enumerate(roles):
        if role.role == FileRole.ANSWER_ONLY:
            return index
    return 0


def _question_document_index(roles: list[Any]) -> int:
    for index, role in enumerate(roles):
        if role.role == FileRole.QUESTION_ONLY:
            return index
    return 0


def _extract_candidates(strategy: ExtractionStrategy, documents: list[DocumentModel], roles: list[Any]) -> AnswerCandidatePool:
    answer_doc = documents[_answer_document_index(roles)]
    if strategy in {ExtractionStrategy.SAME_FILE_BOXED, ExtractionStrategy.SPLIT_FILE_BOXED}:
        return extract_answer_tables(answer_doc).candidate_pool
    if strategy in {ExtractionStrategy.SAME_FILE_ITEMIZED, ExtractionStrategy.SPLIT_FILE_ITEMIZED}:
        return extract_itemized_answers(answer_doc).candidate_pool
    return AnswerCandidatePool()


def _build_question_index(strategy: ExtractionStrategy, documents: list[DocumentModel], roles: list[Any]) -> QuestionIndex:
    if strategy in {ExtractionStrategy.SPLIT_FILE_BOXED, ExtractionStrategy.SPLIT_FILE_ITEMIZED}:
        return build_question_index(documents[_question_document_index(roles)])
    return build_question_index(documents[0])


def _answers_dict(question_index: QuestionIndex, candidate_pool: AnswerCandidatePool, statuses: dict[int, str]) -> dict[str, dict[str, Any]]:
    answers: dict[str, dict[str, Any]] = {}
    valid_question_numbers = set(question_index.question_numbers())
    for question_no in sorted(valid_question_numbers & set(candidate_pool.question_numbers())):
        candidate = candidate_pool.highest_confidence_candidate(question_no)
        if not candidate:
            continue
        answers[str(question_no)] = {
            "answer": candidate.normalized_answer,
            "raw_answer": candidate.raw_answer,
            "normalized_answer": candidate.normalized_answer,
            "source_kind": candidate.source_kind,
            "source_file": Path(candidate.source_file).name if candidate.source_file else "",
            "source_span": candidate.source_span.to_dict(),
            "evidence_text": candidate.evidence_text,
            "confidence": candidate.confidence,
            "validation_status": statuses.get(question_no, "needs_review"),
        }
    return answers


def extract_answer_key(files: list[str] | list[DocumentModel]) -> ExtractionResult:
    documents = _load_all(files)
    run_id = "ae_run_001"
    if not documents:
        report = ExtractionReport(run_id, "mixed_or_unknown", blocking_errors=["empty_input"])
        return ExtractionResult(run_id, "mixed_or_unknown", "failed", [], {}, {"missing_answers": [], "unexpected_answers": [], "duplicate_answers": [], "warnings": [], "blocking_errors": ["empty_input"]}, [], report.to_safe_dict())
    roles = [classify_file_role(document) for document in documents]
    layouts = [classify_answer_layout(document) for document in documents]
    strategy_result = choose_strategy(roles, layouts)
    question_index = _build_question_index(strategy_result.strategy, documents, roles)
    candidate_pool = resolve_candidate_conflicts(_extract_candidates(strategy_result.strategy, documents, roles)).candidate_pool
    alignment = align_by_question_no(question_index, candidate_pool)
    validation = validate_answer_key(question_index, candidate_pool, alignment)
    answers = _answers_dict(question_index, candidate_pool, validation.answer_statuses)
    file_roles = {document.source_file: role.role.value for document, role in zip(documents, roles)}
    answer_layouts = {document.source_file: layout.layout.value for document, layout in zip(documents, layouts)}
    accepted_count = sum(1 for value in answers.values() if value["validation_status"] == "accepted")
    report = ExtractionReport(
        run_id=run_id,
        strategy=strategy_result.strategy.value,
        file_roles=file_roles,
        answer_layouts=answer_layouts,
        question_count=len(question_index.questions),
        answer_count=len(answers),
        accepted_count=accepted_count,
        missing_answers=alignment.missing_answers,
        unexpected_answers=alignment.unexpected_answers,
        duplicate_answers=alignment.duplicate_answers,
        warnings=validation.warnings,
        blocking_errors=validation.blocking_errors,
        review_items=validation.review_items,
    )
    return ExtractionResult(
        run_id=run_id,
        strategy=strategy_result.strategy.value,
        status=validation.status,
        questions=question_index.to_dict(),
        answers=answers,
        alignment_report=alignment.to_dict(),
        review_items=validation.review_items,
        report=report.to_safe_dict(),
    )
