"""Answer sheet layout — JSON-based, no CV."""
import json
from pathlib import Path
from .contracts import AnswerSheetLayout, QuestionROI


def load_answer_sheet_layout(path) -> AnswerSheetLayout:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rois = [QuestionROI(**r) for r in data.get("question_rois", [])]
    return AnswerSheetLayout(
        layout_id=data.get("layout_id", ""), version=data.get("version", "1.0"),
        page_count=data.get("page_count", 1),
        coordinate_space=data.get("coordinate_space", "pixel"),
        identity_roi=data.get("identity_roi", {}),
        question_rois=rois)


def validate_answer_sheet_layout(layout: AnswerSheetLayout) -> list:
    errors = []
    if not layout.identity_roi: errors.append("LAYOUT_MISSING_IDENTITY_ROI")
    seen = set()
    for roi in layout.question_rois:
        if roi.question_number in seen: errors.append(f"LAYOUT_DUPLICATE_QUESTION:{roi.question_number}")
        seen.add(roi.question_number)
        if not roi.roi_box: errors.append(f"LAYOUT_MISSING_QUESTION_ROI:{roi.question_number}")
    return errors
