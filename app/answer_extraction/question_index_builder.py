from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from app.answer_extraction.document_model import DocumentModel, SourceSpan
from app.answer_extraction.text_normalizer import normalize_text


@dataclass
class QuestionIndexItem:
    question_no: int
    question_type: str = "unknown"
    section: str = ""
    has_options: bool = False
    option_labels: list[str] = field(default_factory=list)
    source_file: str = ""
    source_span: SourceSpan = field(default_factory=SourceSpan)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_span"] = self.source_span.to_dict()
        return data


@dataclass
class QuestionIndex:
    questions: list[QuestionIndexItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocking_errors: list[str] = field(default_factory=list)

    def question_numbers(self) -> list[int]:
        return [item.question_no for item in self.questions]

    def by_number(self) -> dict[int, QuestionIndexItem]:
        return {item.question_no: item for item in self.questions}

    def to_dict(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.questions]


def _question_type_from_section(section: str) -> str:
    if "单选" in section:
        return "single_choice"
    if "多选" in section:
        return "multi_choice"
    if "填空" in section:
        return "blank"
    if "解答" in section:
        return "solution"
    return "unknown"


def build_question_index(document: DocumentModel) -> QuestionIndex:
    result = QuestionIndex()
    current_section = ""
    seen: set[int] = set()
    last_no = 0
    blocks = document.sorted_blocks()
    pending: list[QuestionIndexItem] = []
    for index, block in enumerate(blocks):
        if block.block_type == "table":
            continue
        text = normalize_text(block.text)
        if any(token in text for token in ("参考答案", "答案解析", "【答案】", "故选")):
            break
        if re.match(r"^[一二三四五六七八九十]+[、,].*(单选|多选|填空|解答)", text):
            current_section = block.text
            continue
        if re.match(r"^20\d{2}年", text):
            continue
        match = re.match(r"^(\d{1,3})[\.\、]\s*(?!【答案】)(.+)", text)
        if not match:
            continue
        question_no = int(match.group(1))
        if question_no in seen:
            result.blocking_errors.append("duplicate_question_number")
            continue
        if last_no and question_no < last_no:
            result.blocking_errors.append("question_number_rewind")
        seen.add(question_no)
        last_no = question_no
        nearby = "\n".join(b.text for b in blocks[index : index + 4])
        labels = sorted(set(re.findall(r"([A-D])[\.\、]", nearby)))
        end_block = block.block_id
        for following in blocks[index + 1 :]:
            f_text = normalize_text(following.text)
            if following.block_type == "table":
                continue
            if re.match(r"^[一二三四五六七八九十]+[、,].*(单选|多选|填空|解答)", f_text):
                break
            if re.match(r"^(\d{1,3})[\.\、]\s*(?!【答案】)(.+)", f_text) or any(token in f_text for token in ("参考答案", "答案解析", "【答案】", "故选")):
                break
            end_block = following.block_id
        pending.append(
            QuestionIndexItem(
                question_no=question_no,
                question_type=_question_type_from_section(current_section),
                section=current_section,
                has_options=bool(labels),
                option_labels=labels,
                source_file=block.source_file,
                source_span=SourceSpan(start_block=block.block_id, end_block=end_block, page_index=block.page_index),
                confidence=0.95 if current_section else 0.75,
            )
        )
    result.questions = pending
    return result
