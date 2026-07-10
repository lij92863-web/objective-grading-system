from pathlib import Path

from .capture_queue import CaptureQueue, CaptureRegistration
from .capture_source import CaptureSourceType


class ManualUploadSource:
    def __init__(self, queue: CaptureQueue) -> None:
        self.queue = queue

    def upload(self, session_id: str, path: Path) -> CaptureRegistration:
        return self.queue.add_file(
            session_id,
            path,
            CaptureSourceType.MANUAL_UPLOAD,
        )
