"""Local SQLite persistence for the browser product."""

from .local_db import LocalDatabase, default_database_path
from .migrations import initialize_database
from .repositories import ProductRepository

__all__ = [
    "LocalDatabase",
    "ProductRepository",
    "default_database_path",
    "initialize_database",
]
