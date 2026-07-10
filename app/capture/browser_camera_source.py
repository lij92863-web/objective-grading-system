from .capture_queue import CaptureQueue, CaptureRegistration
from .capture_source import CaptureSourceType


class BrowserCameraSource:
    def __init__(self, queue: CaptureQueue) -> None:
        self.queue = queue

    def upload_blob(
        self,
        session_id: str,
        filename: str,
        content: bytes,
    ) -> CaptureRegistration:
        return self.queue.add_bytes(
            session_id,
            filename,
            content,
            CaptureSourceType.BROWSER_CAMERA,
        )
