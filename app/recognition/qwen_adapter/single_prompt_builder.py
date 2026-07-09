"""Single Qwen prompt builder — no API key, no base64, no local paths.

Builds the prompt text for a single-image Qwen request from the manifest
and ROI metadata.  The prompt forbids grading, forbids identity
confirmation, and requires question_id from ROI/template only.
"""

from pathlib import Path
from typing import Any, Dict, List


PROMPT_VERSION = "v2"

SINGLE_QWEN_PROMPT_TEMPLATE = """\
你是答题卡识别助手。你只负责识别作答内容，不判分，不确认身份。

指令：
1. 只返回 JSON，不要解释
2. 每个题目必须使用给定的 question_id，不得自造编号
3. 选择题答案只能是 A、B、C、D 的组合，或 blank、unclear
4. 填空题答案原样输出，不要解题
5. 身份信息（学号/姓名）只能作为 candidate 返回，不得确认
6. 低置信度必须标记 needs_review=true
7. 非法选项（非 A-D）标记 invalid_option=true
8. 不得返回 score、grade、correct/wrong 等判分信息

已有题目结构：
{question_metadata}

返回 JSON 格式：
{{
  "identity_candidate": {{
    "raw_text": "...",
    "student_number": "...",
    "student_name": "...",
    "confidence": 0.0
  }},
  "items": [
    {{
      "question_id": "Q1",
      "question_type": "single_choice|multiple_choice|blank",
      "answer": "A|B|C|D|AB|...|blank|unclear",
      "raw_text": "...",
      "confidence": 0.0,
      "needs_review": false,
      "invalid_option": false,
      "warnings": []
    }}
  ]
}}"""


def build_single_qwen_prompt(
    manifest: Any,
    roi_file: Any,
    prompt_version: str = PROMPT_VERSION,
) -> Dict[str, Any]:
    """Build a safe prompt from manifest + ROI metadata.

    Returns dict with prompt_text, expected_json_schema, and warnings.
    Never includes API keys, base64, or full local paths.
    """
    warnings: List[str] = []

    # Build question metadata from ROI
    question_metadata = _build_question_metadata(roi_file)

    prompt_text = SINGLE_QWEN_PROMPT_TEMPLATE.format(
        question_metadata=question_metadata,
    )

    # Safety checks
    raw = prompt_text
    if "sk-" in raw or "Bearer " in raw:
        warnings.append("PROMPT_CONTAINS_SECRET")
    if "data:image" in raw:
        warnings.append("PROMPT_CONTAINS_BASE64")
    if "score" in raw.lower() and "不要" not in raw and "禁止" not in raw:
        warnings.append("PROMPT_MAY_CONTAIN_SCORING_INSTRUCTION")

    image_name = ""
    if hasattr(manifest, 'image_path') and manifest.image_path:
        image_name = Path(manifest.image_path).name

    return {
        "prompt_text": prompt_text,
        "prompt_version": prompt_version,
        "expected_json_schema": _expected_schema(),
        "warnings": warnings,
        "summary": {
            "prompt_version": prompt_version,
            "image_name": image_name,
            "question_count": len(question_metadata.split("Q")) - 1 if "Q" in question_metadata else 0,
            "has_identity_instruction": True,
            "forbids_scoring": True,
            "forbids_identity_confirmation": True,
        },
    }


def _build_question_metadata(roi_file: Any) -> str:
    """Extract question structure from ROI file for the prompt."""
    lines = []
    # Collect questions from all ROI types
    all_rois = []
    for attr in ['question_rois', 'choice_cell_rois', 'blank_rois']:
        rois = getattr(roi_file, attr, [])
        if rois:
            all_rois.extend(rois)

    # Deduplicate by question_id
    seen = set()
    for roi in all_rois:
        qid = getattr(roi, 'question_id', '') or ''
        if qid and qid not in seen:
            seen.add(qid)
            roi_type = getattr(roi, 'roi_type', 'single_choice')
            label = getattr(roi, 'label', '') or qid
            lines.append(f"  {qid}: type={roi_type}, label={label}")

    if not lines:
        # Fallback from choice_cell_rois count
        choice_count = len(getattr(roi_file, 'choice_cell_rois', []))
        blank_count = len(getattr(roi_file, 'blank_rois', []))
        for i in range(1, choice_count + 1):
            lines.append(f"  Q{i}: type=single_choice")
        for i in range(choice_count + 1, choice_count + blank_count + 1):
            lines.append(f"  Q{i}: type=blank")

    return "\n".join(lines) if lines else "  (no question metadata available)"


def _expected_schema() -> Dict[str, Any]:
    """Return the expected JSON schema for the response."""
    return {
        "type": "object",
        "required": ["items"],
        "properties": {
            "identity_candidate": {
                "type": "object",
                "properties": {
                    "raw_text": {"type": "string"},
                    "student_number": {"type": "string"},
                    "student_name": {"type": "string"},
                    "confidence": {"type": "number"},
                },
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["question_id", "answer", "confidence"],
                    "properties": {
                        "question_id": {"type": "string"},
                        "question_type": {"type": "string"},
                        "answer": {"type": "string"},
                        "raw_text": {"type": "string"},
                        "confidence": {"type": "number"},
                        "needs_review": {"type": "boolean"},
                        "invalid_option": {"type": "boolean"},
                        "warnings": {"type": "array"},
                    },
                },
            },
        },
    }
