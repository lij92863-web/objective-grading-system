"""Prompt constants for Qwen recognition and judgment.

These are the prompts that will be sent to Qwen-OCR / Qwen-VL when the
real API integration is ready.  During the mock stage (R2-R7) they are
stored here for reference and tests; no API calls are made.
"""

# ---------------------------------------------------------------------------
# Name-field recognition
# ---------------------------------------------------------------------------

NAME_FIELD_RECOGNITION_PROMPT = """\
请识别这张图片中姓名栏的手写内容。
姓名栏中可能包含数字（学号/序号）和中文姓名。
请原样输出，不要修改或补充。
如果看不清，输出 unclear。
请只输出 JSON：
{
  "raw_text": "...",
  "confidence": 0.0,
  "status": "recognized|unclear"
}"""

# ---------------------------------------------------------------------------
# Choice-cell recognition
# ---------------------------------------------------------------------------

CHOICE_CELL_RECOGNITION_PROMPT = """\
你只识别这个答案格中的手写选择题答案。
答案只能是 A、B、C、D 的组合，或者 blank、unclear。
不要解释，不要补充。
如果看不清，输出 unclear。
如果没有作答，输出 blank。
请只输出 JSON：
{
  "answer": "A|B|C|D|AB|AC|AD|BC|BD|CD|ABC|ABD|ACD|BCD|ABCD|blank|unclear|invalid",
  "confidence": 0.0
}"""

# ---------------------------------------------------------------------------
# Blank-answer recognition
# ---------------------------------------------------------------------------

BLANK_ANSWER_RECOGNITION_PROMPT = """\
请只识别该填空题横线上的手写答案。
不要解题，不要判断对错。
尽量输出数学表达式。
如果能转成 LaTeX，请同时给出 LaTeX。
看不清输出 unclear，空白输出 blank。
请只输出 JSON：
{
  "raw_text": "...",
  "latex": "...",
  "confidence": 0.0,
  "status": "recognized|blank|unclear"
}"""

# ---------------------------------------------------------------------------
# Complex blank judgment
# ---------------------------------------------------------------------------

COMPLEX_BLANK_JUDGMENT_PROMPT = """\
你是高中数学填空题判分助手。
请根据题目、标准答案、学生答案判断是否数学等价。
不要重新解题，只判断学生答案是否可接受。
如果无法确定，请返回 needs_review。

题目原文：{stem}
题型：填空题
分值：{points} 分
标准答案：{correct_answer}
学生答案：{student_answer}
识别置信度：{ocr_confidence}
是否来自 OCR：是
评分要求：只判断数学等价性
是否允许不同形式答案：是
是否需要考虑答案形式要求：{format_required}

只输出 JSON：
{
  "verdict": "correct|wrong|partial|needs_review|invalid",
  "confidence": 0.0,
  "reason": "...",
  "normalized_standard": "...",
  "normalized_student": "...",
  "equivalence_type": "same_value|same_solution_set|same_expression|format_mismatch|unknown",
  "requires_review": true
}"""
