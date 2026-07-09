"""Review queue model (constitution §9).

Holds the set of ``ReviewItem`` for a job/exam and supports enqueue, dequeue of
pending items, and resolution. ``has_unresolved`` is what the grading gate
consults before allowing official grading.
"""

from typing import Dict, List, Optional

from app.student_recognition.review.review_item import ReviewItem, ReviewStatus


class ReviewQueue:
    def __init__(self) -> None:
        self._items: List[ReviewItem] = []

    def enqueue(self, item: ReviewItem) -> None:
        # Enqueuing an already-resolved item resets it to pending.
        if item.resolution == ReviewStatus.RESOLVED:
            item.resolution = ReviewStatus.PENDING
        self._items.append(item)

    def all(self) -> List[ReviewItem]:
        return list(self._items)

    def pending(self) -> List[ReviewItem]:
        return [
            i
            for i in self._items
            if i.resolution in (ReviewStatus.PENDING, ReviewStatus.IN_PROGRESS)
        ]

    def pending_count(self) -> int:
        return len(self.pending())

    def has_unresolved(self) -> bool:
        return self.pending_count() > 0

    def get(self, item_id: str) -> Optional[ReviewItem]:
        for item in self._items:
            if item.item_id == item_id:
                return item
        return None

    def resolve(
        self,
        item_id: str,
        resolution: ReviewStatus,
        note: str = "",
        by: str = "",
    ) -> Optional[ReviewItem]:
        item = self.get(item_id)
        if item is None:
            return None
        item.resolve(resolution, note=note, by=by)
        return item

    def to_dict(self) -> Dict[str, object]:
        return {"items": [i.to_dict() for i in self._items]}

    @classmethod
    def from_dict(cls, d: Dict[str, object]) -> "ReviewQueue":
        q = cls()
        for raw in d.get("items", []):  # type: ignore[arg-type]
            q.enqueue(ReviewItem.from_dict(raw))  # type: ignore[arg-type]
        return q
