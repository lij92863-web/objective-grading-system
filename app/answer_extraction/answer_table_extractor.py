from __future__ import annotations

from dataclasses import dataclass, field

from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool
from app.answer_extraction.answer_normalizer import normalize_answer
from app.answer_extraction.document_model import DocumentModel, DocumentTable, SourceSpan
from app.answer_extraction.student_answer_grid_detector import detect_student_answer_grid
from app.answer_extraction.table_normalizer import normalize_table
from app.answer_extraction.text_normalizer import normalize_text


@dataclass
class AnswerTableExtractionResult:
    candidate_pool: AnswerCandidatePool = field(default_factory=AnswerCandidatePool)
    ignored_tables: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "candidates": self.candidate_pool.to_dict(),
            "ignored_tables": list(self.ignored_tables),
            "warnings": list(self.warnings),
        }


def _make_candidate(question_no: int, raw: str, table: DocumentTable) -> AnswerCandidate | None:
    normalized = normalize_answer(raw)
    if not normalized.is_valid and raw and not any(ch.isdigit() for ch in raw):
        normalized = normalize_answer(raw, "blank")
    if not normalized.normalized_answer:
        return None
    return AnswerCandidate(
        question_no=question_no,
        raw_answer=raw,
        normalized_answer=normalized.normalized_answer,
        answer_type=normalized.answer_type,
        source_kind="answer_table",
        source_file=table.source_file,
        source_span=SourceSpan(table_id=table.table_id, page_index=table.page_index),
        evidence_text=f"题号 {question_no} 答案 {raw}",
        confidence=0.99 if normalized.is_valid else 0.4,
        warnings=normalized.warnings,
        blocking_errors=normalized.blocking_errors,
    )


def _extract_horizontal(table: DocumentTable) -> list[AnswerCandidate]:
    rows = normalize_table(table).rows
    candidates: list[AnswerCandidate] = []
    index = 0
    while index < len(rows) - 1:
        label = normalize_text(rows[index][0] if rows[index] else "")
        next_label = normalize_text(rows[index + 1][0] if rows[index + 1] else "")
        if "题号" in label and "答案" in next_label:
            question_values = rows[index][1:]
            answer_values = rows[index + 1][1:]
            for q_text, a_text in zip(question_values, answer_values):
                q_clean = normalize_text(q_text)
                if q_clean.isdigit():
                    candidate = _make_candidate(int(q_clean), a_text, table)
                    if candidate:
                        candidates.append(candidate)
            index += 2
            continue
        index += 1
    return candidates


def _extract_vertical(table: DocumentTable) -> list[AnswerCandidate]:
    rows = normalize_table(table).rows
    if not rows:
        return []
    header = [normalize_text(cell) for cell in rows[0]]
    if not ("题号" in header and "答案" in header):
        return []
    q_col = header.index("题号")
    a_col = header.index("答案")
    candidates: list[AnswerCandidate] = []
    for row in rows[1:]:
        if q_col >= len(row) or a_col >= len(row):
            continue
        q_text = normalize_text(row[q_col])
        if q_text.isdigit():
            candidate = _make_candidate(int(q_text), row[a_col], table)
            if candidate:
                candidates.append(candidate)
    return candidates


def extract_answer_tables(document: DocumentModel) -> AnswerTableExtractionResult:
    result = AnswerTableExtractionResult()
    for table in document.sorted_tables():
        if detect_student_answer_grid(table, document).is_student_answer_grid:
            result.ignored_tables.append(table.table_id)
            continue
        candidates = _extract_horizontal(table) + _extract_vertical(table)
        if not candidates:
            continue
        for candidate in candidates:
            result.candidate_pool.add(candidate)
    return result
