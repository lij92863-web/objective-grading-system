"""Recognition worker: a scheduler only (constitution §2 / §14).

``RecognitionWorker`` queues job descriptors and processes them one at a time by
delegating to :class:`RecognitionJob`. It performs NO recognition or grading
itself — it only schedules. This keeps the pipeline thin and prevents business
algorithms from leaking into the orchestration layer.
"""

from typing import Any, Dict, List, Optional

from app.student_recognition.capture.capture_job import CaptureJobStore
from app.student_recognition.pipeline.recognition_job import RecognitionJob


class RecognitionWorker:
    def __init__(self, store: Optional[CaptureJobStore] = None):
        self.job = RecognitionJob(store=store)
        self._queue: List[Dict[str, Any]] = []

    def enqueue(self, item: Dict[str, Any]) -> None:
        """Queue a job descriptor (kwargs for ``RecognitionJob.process``)."""
        self._queue.append(item)

    def process_next(self) -> Optional[tuple]:
        if not self._queue:
            return None
        item = self._queue.pop(0)
        return self.job.process(**item)

    def run(self, limit: Optional[int] = None) -> List[tuple]:
        out: List[tuple] = []
        n = 0
        while self._queue and (limit is None or n < limit):
            out.append(self.process_next())  # type: ignore[arg-type]
            n += 1
        return out

    def pending(self) -> int:
        return len(self._queue)
