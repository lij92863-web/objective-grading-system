"""R92: Batch recognition summary."""
from dataclasses import dataclass, field


@dataclass
class BatchRecognitionSummary:
    job_id: str = ""
    total_images: int = 0
    processed_images: int = 0
    failed_images: int = 0
    auto_accepted_items: int = 0
    needs_review_items: int = 0
    blocking_items: int = 0
    identity_blocking_count: int = 0
    qwen_call_count: int = 0
    omr_only_count: int = 0
    qwen_needed_count: int = 0
    estimated_cost: float = 0.0


def count_from_decisions(decisions_per_image: list) -> BatchRecognitionSummary:
    s = BatchRecognitionSummary(total_images=len(decisions_per_image))
    for decs in decisions_per_image:
        if decs:
            s.processed_images += 1
            for d in decs:
                if d.status == "auto_accepted": s.auto_accepted_items += 1
                if d.needs_review: s.needs_review_items += 1
                if d.blocking: s.blocking_items += 1
    s.qwen_call_count = max(0, s.needs_review_items - s.blocking_items)
    s.qwen_needed_count = s.needs_review_items
    s.estimated_cost = s.qwen_call_count * 0.002
    return s
