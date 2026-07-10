from enum import Enum


class ReviewIssueType(str, Enum):
    IDENTITY_MISSING = "IDENTITY_MISSING"
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    IDENTITY_DUPLICATE = "IDENTITY_DUPLICATE"
    PAGE_QUALITY_FAILED = "PAGE_QUALITY_FAILED"
    PAGE_LOCATION_FAILED = "PAGE_LOCATION_FAILED"
    TEMPLATE_MISMATCH = "TEMPLATE_MISMATCH"
    ANSWER_UNREADABLE = "ANSWER_UNREADABLE"
    MULTI_MARK_CONFLICT = "MULTI_MARK_CONFLICT"
    WEAK_MARK = "WEAK_MARK"
    ERASURE_DETECTED = "ERASURE_DETECTED"
    BLANK_UNCERTAIN = "BLANK_UNCERTAIN"
    GRADING_BLOCKED = "GRADING_BLOCKED"


def teacher_message(issue_type: ReviewIssueType, question_number: int | None = None) -> str:
    if issue_type is ReviewIssueType.IDENTITY_MISSING:
        return "这张试卷识别不到学生，请输入姓名或学号。"
    if issue_type is ReviewIssueType.ANSWER_UNREADABLE:
        return f"第 {question_number} 题识别不清，请直接处理这题。"
    if issue_type is ReviewIssueType.MULTI_MARK_CONFLICT:
        return f"第 {question_number} 题疑似多涂，请确认。"
    if issue_type is ReviewIssueType.PAGE_QUALITY_FAILED:
        return "这张照片太模糊或光线不合格，请重新拍照或人工处理。"
    if issue_type is ReviewIssueType.PAGE_LOCATION_FAILED:
        return "未能定位答题页面，请重新拍照或人工排除。"
    return "这条识别结果需要老师确认。"
