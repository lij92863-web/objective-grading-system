"""Build recognition request batch from asset + layout."""
from .contracts import (RecognitionRequestBatch, RecognitionRequestItem,
                         RecognitionRunConfig, ImageAsset, AnswerSheetLayout)


def build_recognition_request_batch(
    asset: ImageAsset, layout: AnswerSheetLayout, config: RecognitionRunConfig,
) -> RecognitionRequestBatch:
    items = []
    for roi in sorted(layout.question_rois, key=lambda r: r.question_number):
        items.append(RecognitionRequestItem(
            question_number=roi.question_number,
            question_type=roi.question_type,
            roi_box=roi.roi_box, expected_answer=roi.expected_answer,
            points=roi.points, tags=roi.tags, engine_hint=roi.engine_hint))
    return RecognitionRequestBatch(run_id=config.run_id, asset_id=asset.asset_id,
                                    layout_id=layout.layout_id, items=items, config=config)
