import tempfile
import unittest
from pathlib import Path

from app.storage import LocalDatabase, initialize_database
from app.storage.schema import SCHEMA_VERSION
from app.storage.transaction import transaction


ROOT = Path(__file__).resolve().parents[2]


class LocalStorageFoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.database = LocalDatabase(Path(self.temp.name) / "product.sqlite3")
        initialize_database(self.database)

    def tearDown(self):
        self.temp.cleanup()

    def test_schema_initializes_empty_database(self):
        with self.database.connection() as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        self.assertTrue({"classes", "students", "exam_sessions"} <= tables)
        self.assertTrue({"review_issues", "final_scores", "audit_events"} <= tables)

    def test_schema_version_recorded(self):
        with self.database.connection() as connection:
            version = connection.execute(
                "SELECT version FROM schema_migrations"
            ).fetchone()[0]
        self.assertEqual(version, SCHEMA_VERSION)

    def test_transaction_rolls_back_on_failure(self):
        with self.assertRaises(RuntimeError):
            with transaction(self.database) as connection:
                connection.execute(
                    """
                    INSERT INTO classes
                        (id, class_name, state, created_at, updated_at)
                    VALUES ('c1', 'Class', 'ACTIVE', 'now', 'now')
                    """
                )
                raise RuntimeError("attack")
        with self.database.connection() as connection:
            count = connection.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
        self.assertEqual(count, 0)

    def test_data_dir_is_gitignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("data/local_app/", ignore)
        self.assertIn("local-test-materials/", ignore)

    def test_repository_does_not_write_to_project_root(self):
        self.assertNotEqual(self.database.path.parent, ROOT)
        self.assertTrue(str(self.database.path).startswith(str(ROOT / "data")))


if __name__ == "__main__":
    unittest.main()
