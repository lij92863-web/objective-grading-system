"""Connection factory with safe defaults and foreign-key enforcement."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def default_database_path() -> Path:
    return PROJECT_ROOT / "data" / "local_app" / "product.sqlite3"


class LocalDatabase:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else default_database_path()

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.close()
