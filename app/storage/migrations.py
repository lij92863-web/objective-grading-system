"""Idempotent schema initialization."""

from datetime import datetime, timezone

from .local_db import LocalDatabase
from .schema import SCHEMA_SQL, SCHEMA_VERSION
from .transaction import transaction


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def initialize_database(database: LocalDatabase) -> None:
    with transaction(database) as connection:
        connection.executescript(SCHEMA_SQL)
        now = utc_now()
        connection.execute(
            """
            INSERT OR IGNORE INTO schema_migrations
                (version, created_at, updated_at)
            VALUES (?, ?, ?)
            """,
            (SCHEMA_VERSION, now, now),
        )
