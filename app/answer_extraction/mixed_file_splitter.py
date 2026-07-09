from __future__ import annotations

from dataclasses import dataclass

from app.answer_extraction.document_model import DocumentBlock, DocumentModel


@dataclass(frozen=True)
class MixedFileSplit:
    question_blocks: list[DocumentBlock]
    answer_blocks: list[DocumentBlock]
    boundary_block_id: str = ""
    confidence: float = 0.0
    reasons: list[str] = None


ANSWER_MARKERS = ("参考答案", "答案解析", "参考解析", "详解", "【答案】", "〖答案〗", "[答案]", "故选", "故答案为", "答案为")


def split_mixed_document(document: DocumentModel) -> MixedFileSplit:
    blocks = document.sorted_blocks()
    best_index = -1
    best_score = 0
    best_reasons: list[str] = []
    for index, block in enumerate(blocks):
        text = block.text
        score = 0
        reasons: list[str] = []
        if any(marker in text for marker in ANSWER_MARKERS):
            score += 3
            reasons.append("answer marker")
        lookahead = "\n".join(b.text for b in blocks[index : index + 20])
        if "题号" in lookahead and "答案" in lookahead:
            score += 3
            reasons.append("answer table nearby")
        if any(marker in lookahead for marker in ("【答案】", "〖答案〗", "[答案]", "故选", "故答案为")):
            score += 3
            reasons.append("itemized evidence nearby")
        if sum(lookahead.count(label) for label in ("A.", "B.", "C.", "D.", "A、", "B、", "C、", "D、")) > 10:
            score -= 2
            reasons.append("question options still dense")
        if score > best_score:
            best_index = index
            best_score = score
            best_reasons = reasons
    if best_index < 0 or best_score < 3:
        return MixedFileSplit(blocks, [], "", 0.0, ["no answer boundary"])
    return MixedFileSplit(blocks[:best_index], blocks[best_index:], blocks[best_index].block_id, min(0.99, best_score / 9), best_reasons)
