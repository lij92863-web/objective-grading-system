"""Controlled fake recognition runner — no RealQwenClient."""
import json
from pathlib import Path
from .contracts import (RecognitionRunConfig, RecognitionRunResult,
                         RecognizedSubmissionDraft, RecognitionDecision,
                         EngineCandidate, ImageAsset)
from .quality import build_image_asset, validate_image_asset
from .layout import load_answer_sheet_layout, validate_answer_sheet_layout
from .roi_plan import build_recognition_request_batch
from .decision import fuse_candidates


def run_controlled_recognition(
    image_path, layout_path, payload_dir, out_dir, dry_run=True,
) -> RecognitionRunResult:
    config = RecognitionRunConfig(run_id="controlled_001", dry_run=dry_run,
                                   allow_real_api=False, qwen_enabled=False)
    asset = build_image_asset(image_path, source_kind="fixture")
    qr = validate_image_asset(asset)
    if not qr.is_valid:
        return RecognitionRunResult(run_id=config.run_id, asset_id=asset.asset_id,
                                     status="blocking", summary={"quality_rejected": qr.reasons})

    layout = load_answer_sheet_layout(layout_path)
    layout_errors = validate_answer_sheet_layout(layout)
    exceptions = [{"code": e} for e in layout_errors] if layout_errors else []
    if layout_errors:
        return RecognitionRunResult(run_id=config.run_id, asset_id=asset.asset_id,
                                     status="blocking", exception_queue=exceptions,
                                     summary={"layout_errors": layout_errors})

    batch = build_recognition_request_batch(asset, layout, config)
    payload_dir = Path(payload_dir)
    choices = json.loads((payload_dir/"demo_choices.json").read_text("utf-8")) if (payload_dir/"demo_choices.json").exists() else {}
    blanks = json.loads((payload_dir/"demo_blanks.json").read_text("utf-8")) if (payload_dir/"demo_blanks.json").exists() else {}
    identity = json.loads((payload_dir/"demo_identity.json").read_text("utf-8")) if (payload_dir/"demo_identity.json").exists() else {}

    decisions = []
    for item in batch.items:
        qn = str(item.question_number)
        candidates = []
        if item.question_type == "choice" and qn in choices:
            c = choices[qn]
            candidates.append(EngineCandidate(question_number=item.question_number,
                engine=c.get("engine","mock"), value=c["value"], confidence=c["confidence"]))
        elif item.question_type == "blank" and qn in blanks:
            c = blanks[qn]
            candidates.append(EngineCandidate(question_number=item.question_number,
                engine=c.get("engine","mock"), value=c["value"], latex=c.get("latex",""),
                confidence=c["confidence"]))
        decisions.append(fuse_candidates(item.question_number, item.question_type, candidates, config))

    draft = RecognizedSubmissionDraft(
        student_id=identity.get("student_id",""), student_number=identity.get("student_number",""),
        student_name=identity.get("student_name",""),
        identity_status=identity.get("status","missing"), decisions=decisions,
        exceptions=exceptions, ready_for_confirmation=True)

    auto = sum(1 for d in decisions if d.status == "auto_accepted")
    review = sum(1 for d in decisions if d.needs_review)
    blocking = sum(1 for d in decisions if d.blocking)
    result = RecognitionRunResult(run_id=config.run_id, asset_id=asset.asset_id,
                                   status="completed", drafts=[draft],
                                   exception_queue=exceptions,
                                   summary={"auto_accepted": auto, "needs_review": review, "blocking": blocking},
                                   config=config)

    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir/"recognition_run.json").write_text(json.dumps({"run_id": result.run_id, "status": result.status}, ensure_ascii=False, indent=2), "utf-8")
    (out_dir/"recognition_draft.json").write_text(json.dumps(
        {"student_id": draft.student_id, "identity_status": draft.identity_status,
         "decisions_count": len(draft.decisions),
         "ready_for_grading": draft.ready_for_grading},
        ensure_ascii=False, indent=2), "utf-8")
    (out_dir/"exception_queue.json").write_text(json.dumps(exceptions, ensure_ascii=False, indent=2), "utf-8")
    (out_dir/"recognition_summary.json").write_text(json.dumps(result.summary, ensure_ascii=False, indent=2), "utf-8")
    return result
