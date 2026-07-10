"""Small parameterized repository surface shared by product services."""

import sqlite3
from typing import Iterable, Mapping, Sequence


class ProductRepository:
    def insert(
        self,
        connection: sqlite3.Connection,
        table: str,
        values: Mapping[str, object],
    ) -> None:
        allowed = {
            "classes", "students", "exam_sessions", "exam_assets",
            "capture_jobs", "recognition_drafts", "review_issues",
            "review_resolutions", "final_submissions", "final_scores",
            "artifact_index", "audit_events",
        }
        if table not in allowed:
            raise ValueError(f"unsupported repository table: {table}")
        columns = tuple(values)
        placeholders = ", ".join("?" for _ in columns)
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        connection.execute(sql, tuple(values[column] for column in columns))

    def one(
        self,
        connection: sqlite3.Connection,
        sql: str,
        parameters: Sequence[object] = (),
    ) -> sqlite3.Row | None:
        return connection.execute(sql, parameters).fetchone()

    def all(
        self,
        connection: sqlite3.Connection,
        sql: str,
        parameters: Sequence[object] = (),
    ) -> list[sqlite3.Row]:
        return list(connection.execute(sql, parameters).fetchall())

    def execute_many(
        self,
        connection: sqlite3.Connection,
        sql: str,
        parameters: Iterable[Sequence[object]],
    ) -> None:
        connection.executemany(sql, parameters)
