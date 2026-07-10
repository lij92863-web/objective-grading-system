import dataclasses
from pathlib import Path

from .capture_queue import CaptureQueue, CaptureRegistration, IMAGE_SUFFIXES
from .capture_source import CaptureSourceType


@dataclasses.dataclass(frozen=True)
class WatchedFolderScan:
    created: tuple[CaptureRegistration, ...]
    duplicate_count: int


class WatchedFolderSource:
    def __init__(self, queue: CaptureQueue) -> None:
        self.queue = queue

    def scan(self, session_id: str, folder: Path) -> WatchedFolderScan:
        folder = Path(folder)
        if not folder.is_dir():
            raise ValueError("watched folder does not exist")
        created: list[CaptureRegistration] = []
        duplicates = 0
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() not in IMAGE_SUFFIXES or not path.is_file():
                continue
            result = self.queue.add_file(
                session_id,
                path,
                CaptureSourceType.WATCHED_FOLDER,
            )
            if result.duplicate:
                duplicates += 1
            else:
                created.append(result)
        return WatchedFolderScan(tuple(created), duplicates)
