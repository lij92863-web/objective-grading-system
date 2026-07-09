from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.answer_extraction.answer_candidate_pool import AnswerCandidate, AnswerCandidatePool
from app.answer_extraction.answer_markers import ANSWER_MARKER_RE
from app.answer_extraction.answer_normalizer import normalize_answer
from app.answer_extraction.answer_source_policy import confidence_for_source
from app.answer_extraction.document_model import DocumentModel, SourceSpan
from app.answer_extraction.itemized_block_segmenter import segment_itemized_blocks
from app.answer_extraction.status_model import STATUS_ACCEPTED, STATUS_BLOCKED
from app.answer_extraction.text_normalizer import normalize_text


@dataclass
class ItemizedAnswerExtractionResult:
    candidate_pool: AnswerCandidatePool = field(default_factory=AnswerCandidatePool)
    warnings: list[str] = field(default_factory=list)


ANSWER_MARKER_PATTERN = ANSWER_MARKER_RE.pattern

PATTERNS = [
    ("explicit_bracket_answer", re.compile(rf"^(\d{{1,3}})[\.\、,]\s*{ANSWER_MARKER_PATTERN}[:：]?\s*(.+?)\s*$")),
    ("explicit_answer", re.compile(r"^(\d{1,3})[\.\、,]\s*答案(?:为)?[:：]?\s*(.+)$")),
    ("short_itemized", re.compile(r"^(\d{1,3})[\.\、,]\s*([A-Da-d]{1,4})\s*$")),
    ("guxuan", re.compile(r"^(\d{1,3})[\.\、,].*故选[:：]?\s*([A-Da-d]{1,4})")),
    ("gu_daanwei", re.compile(r"^(\d{1,3})[\.\、,].*故答案(?:为|是)?[:：]?\s*(.+)$")),
]

CONFIDENCE = {
    "explicit_bracket_answer": 0.98,
    "explicit_answer": 0.97,
    "short_itemized": 0.95,
    "guxuan": 0.88,
    "gu_daanwei": 0.86,
}

INLINE_WITHOUT_QNO = [
    ("explicit_bracket_answer", re.compile(rf"^\s*{ANSWER_MARKER_PATTERN}\s*[:：]?\s*(.+?)\s*$")),
    ("explicit_answer_colon", re.compile(r"答案(?:为)?[:：]\s*(.+)$")),
    ("guxuan", re.compile(r"故选[:：]?\s*([A-Da-d]{1,4})")),
    ("gu_daanwei", re.compile(r"故答案(?:为|是)?[:：]?\s*(.+)$")),
]


def extract_itemized_answers(document: DocumentModel) -> ItemizedAnswerExtractionResult:
    result = ItemizedAnswerExtractionResult()
    consumed_blocks: set[str] = set()
    blocks = document.sorted_blocks()
    for index, block in enumerate(blocks[:-1]):
        text = normalize_text(block.text)
        next_text = normalize_text(blocks[index + 1].text)
        q_only = re.match(r"^(\d{1,3})[\.\、,]\s*$", text)
        marker = next((item for item in INLINE_WITHOUT_QNO if item[1].search(next_text)), None)
        if not q_only or marker is None:
            continue
        source_kind, pattern = marker
        match = pattern.search(next_text)
        raw_answer = match.group(1).splitlines()[0].split("[object]", 1)[0].split("【", 1)[0].split("解析", 1)[0].strip()
        normalized = normalize_answer(raw_answer)
        if not normalized.is_valid and raw_answer:
            normalized = normalize_answer(raw_answer, "blank")
        result.candidate_pool.add(
            AnswerCandidate(
                question_no=int(q_only.group(1)),
                raw_answer=raw_answer,
                normalized_answer=normalized.normalized_answer,
                answer_type=normalized.answer_type,
                source_kind=source_kind,
                source_file=block.source_file,
                source_span=SourceSpan(start_block=block.block_id, end_block=blocks[index + 1].block_id, page_index=block.page_index),
                evidence_text=f"{block.text}\n{blocks[index + 1].text}",
                confidence=confidence_for_source(source_kind) if normalized.is_valid else 0.4,
                warnings=normalized.warnings,
                blocking_errors=normalized.blocking_errors,
            )
        )
        consumed_blocks.add(block.block_id)
        consumed_blocks.add(blocks[index + 1].block_id)
    for segment in segment_itemized_blocks(document.sorted_blocks()):
        if any(block.block_id in consumed_blocks for block in segment.blocks):
            continue
        evidence = "\n".join(block.text for block in segment.blocks)
        normalized_evidence = normalize_text(evidence)
        for source_kind, pattern in INLINE_WITHOUT_QNO:
            match = pattern.search(normalized_evidence)
            if not match:
                continue
            raw_answer = match.group(1).splitlines()[0].split("[object]", 1)[0].split("【", 1)[0].split("解析", 1)[0].strip()
            normalized = normalize_answer(raw_answer)
            if not normalized.is_valid and raw_answer:
                normalized = normalize_answer(raw_answer, "blank")
            result.candidate_pool.add(
                AnswerCandidate(
                    question_no=segment.question_no,
                    raw_answer=raw_answer,
                    normalized_answer=normalized.normalized_answer,
                    answer_type=normalized.answer_type,
                    source_kind=source_kind,
                    source_file=segment.blocks[0].source_file,
                    source_span=SourceSpan(start_block=segment.blocks[0].block_id, end_block=segment.blocks[-1].block_id, page_index=segment.blocks[0].page_index),
                    evidence_text=evidence,
                    confidence=confidence_for_source(source_kind) if normalized.is_valid else 0.4,
                    warnings=normalized.warnings,
                    blocking_errors=normalized.blocking_errors,
                )
            )
            consumed_blocks.update(block.block_id for block in segment.blocks)
            break
    for block in document.sorted_blocks():
        if block.block_id in consumed_blocks:
            continue
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
            raw_answer = match.group(2).splitlines()[0].split("[object]", 1)[0].split("【", 1)[0].split("解析", 1)[0].strip()
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
                confidence=confidence_for_source(source_kind) if normalized.is_valid else 0.4,
                warnings=normalized.warnings,
                blocking_errors=normalized.blocking_errors,
            )
            result.candidate_pool.add(candidate)
            break
    return result
