"""Explicit transaction boundary used by product services."""

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .local_db import LocalDatabase


@contextmanager
def transaction(database: LocalDatabase) -> Iterator[sqlite3.Connection]:
    with database.connection() as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
        except Exception:
            connection.rollback()
            raise
        else:
            connection.commit()
