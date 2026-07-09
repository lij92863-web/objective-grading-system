from __future__ import annotations

import re
from dataclasses import dataclass

from app.answer_extraction.document_model import DocumentBlock
from app.answer_extraction.text_normalizer import normalize_text


@dataclass(frozen=True)
class AnswerItemBlock:
    question_no: int
    blocks: list[DocumentBlock]


START_RE = re.compile(r"^(\d{1,3})[\.\、]\s*(?:【答案】|〖答案〗|\[答案\]|答案|[A-Da-d]{1,4}\b|故选|故答案为)")


def segment_itemized_blocks(blocks: list[DocumentBlock], expected_questions: set[int] | None = None) -> list[AnswerItemBlock]:
    segments: list[AnswerItemBlock] = []
    current_no: int | None = None
    current_blocks: list[DocumentBlock] = []
    last_no = 0
    for block in blocks:
        text = normalize_text(block.text)
        if "①" in text or "②" in text or re.match(r"^20\d{2}[年\-.]", text):
            if current_no is not None:
                current_blocks.append(block)
            continue
        match = START_RE.match(text)
        next_no = int(match.group(1)) if match else None
        if next_no is not None and (expected_questions is None or next_no in expected_questions) and (not last_no or next_no >= last_no):
            if current_no is not None:
                segments.append(AnswerItemBlock(current_no, current_blocks))
            current_no = next_no
            current_blocks = [block]
            last_no = next_no
        elif current_no is not None:
            current_blocks.append(block)
    if current_no is not None:
        segments.append(AnswerItemBlock(current_no, current_blocks))
    return segments
