from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.answer_extraction.document_model import DocumentModel
from app.answer_extraction.student_answer_grid_detector import detect_student_answer_grid


class FileRole(str, Enum):
    QUESTION_ONLY = "question_only"
    ANSWER_ONLY = "answer_only"
    MIXED_QUESTION_ANSWER = "mixed_question_answer"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FileRoleResult:
    role: FileRole
    confidence: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {"file_role": self.role.value, "confidence": self.confidence, "reasons": list(self.reasons)}


def classify_file_role(document: DocumentModel) -> FileRoleResult:
    text = document.all_text()
    question_score = 0
    answer_score = 0
    reasons: list[str] = []
    if any(token in text for token in ("一、", "单选题", "单项选择", "多选题", "多项选择", "填空题", "解答题")):
        question_score += 3
        reasons.append("question section heading")
    if sum(text.count(marker) for marker in ("A.", "B.", "C.", "D.", "A、", "B、", "C、", "D、")) >= 2:
        question_score += 2
        reasons.append("option labels")
    if any(token in text for token in ("班级", "姓名", "评分", "考号")):
        question_score += 1
        reasons.append("student fields")
    if any(token in text for token in ("参考答案", "答案解析", "详解", "解析")):
        answer_score += 3
        reasons.append("answer heading")
    if any(pattern in text for pattern in ("【答案】", "故选", "故答案为")):
        answer_score += 3
        reasons.append("explicit answer phrases")
    for table in document.sorted_tables():
        detection = detect_student_answer_grid(table, document)
        if detection.is_student_answer_grid:
            question_score += 1
            reasons.append("student answer grid ignored")
            continue
        table_text = "\n".join(" ".join(row) for row in table.grid())
        if "题号" in table_text and "答案" in table_text:
            answer_score += 3
            reasons.append("answer-like table")
    if question_score >= 3 and answer_score >= 3:
        return FileRoleResult(FileRole.MIXED_QUESTION_ANSWER, 0.9, reasons)
    if answer_score >= 3 and question_score < 3:
        return FileRoleResult(FileRole.ANSWER_ONLY, 0.88, reasons)
    if question_score >= 3 and answer_score < 3:
        return FileRoleResult(FileRole.QUESTION_ONLY, 0.88, reasons)
    return FileRoleResult(FileRole.UNKNOWN, 0.3, reasons)
