from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool
from app.answer_extraction.answer_normalizer import normalize_answer
from app.answer_extraction.document_model import DocumentModel, SourceSpan
from app.answer_extraction.text_normalizer import normalize_text


@dataclass
class ItemizedAnswerExtractionResult:
    candidate_pool: AnswerCandidatePool = field(default_factory=AnswerCandidatePool)
    warnings: list[str] = field(default_factory=list)


PATTERNS = [
    ("explicit_answer", re.compile(r"^(\d{1,3})[\.\、]\s*(?:【答案】|〖答案〗|\[答案\])\s*(.+)$")),
    ("explicit_answer", re.compile(r"^(\d{1,3})[\.\、]\s*答案(?:为)?[:：]?\s*(.+)$")),
    ("short_itemized", re.compile(r"^(\d{1,3})[\.\、]\s*([A-Da-d]{1,4})\s*$")),
    ("guxuan", re.compile(r"^(\d{1,3})[\.\、].*故选[:：]?\s*([A-Da-d]{1,4})")),
    ("gu_daanwei", re.compile(r"^(\d{1,3})[\.\、].*故答案(?:为|是)?[:：]?\s*(.+)$")),
]

CONFIDENCE = {
    "explicit_answer": 0.97,
    "short_itemized": 0.95,
    "guxuan": 0.88,
    "gu_daanwei": 0.86,
}


def extract_itemized_answers(document: DocumentModel) -> ItemizedAnswerExtractionResult:
    result = ItemizedAnswerExtractionResult()
    for block in document.sorted_blocks():
        text = normalize_text(block.text)
        if not text or "①" in text or "②" in text:
            continue
        if re.match(r"^20\d{2}[年\-.]", text):
            continue
        for source_kind, pattern in PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            question_no = int(match.group(1))
            if question_no > 300:
                continue
            raw_answer = match.group(2).split("【", 1)[0].split("解析", 1)[0].strip()
            normalized = normalize_answer(raw_answer)
            if not normalized.is_valid and raw_answer:
                normalized = normalize_answer(raw_answer, "blank")
            candidate = AnswerCandidate(
                question_no=question_no,
                raw_answer=raw_answer,
                normalized_answer=normalized.normalized_answer,
                answer_type=normalized.answer_type,
                source_kind=source_kind,
                source_file=block.source_file,
                source_span=SourceSpan(start_block=block.block_id, end_block=block.block_id, page_index=block.page_index),
                evidence_text=block.text,
                confidence=CONFIDENCE[source_kind] if normalized.is_valid else 0.4,
                warnings=normalized.warnings,
                blocking_errors=normalized.blocking_errors,
            )
            result.candidate_pool.add(candidate)
            break
    return result
