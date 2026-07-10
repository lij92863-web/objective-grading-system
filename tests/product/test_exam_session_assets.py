import hashlib
import tempfile
import unittest
from pathlib import Path

from app.classes import ClassService
from app.exam_session import AssetService, AssetType, ExamSessionState, SessionService
from app.storage import LocalDatabase


ROOT = Path(__file__).resolve().parents[2]


class ExamSessionAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.database = LocalDatabase(self.root / "product.sqlite3")
        self.classes = ClassService(self.database)
        self.sessions = SessionService(self.database)
        self.assets = AssetService(self.database, self.root / "local_app")
        self.classroom = self.classes.create_class("高一 3 班")
        self.session = self.sessions.create_session("期中考试", self.classroom.class_id)

    def tearDown(self):
        self.temp.cleanup()

    def file(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8-sig")
        return path

    def test_create_exam_session_requires_class(self):
        with self.assertRaises(ValueError):
            self.sessions.create_session("考试", "missing")
        self.assertEqual(self.session.state, ExamSessionState.CLASS_SELECTED)

    def test_upload_answer_asset_and_hash(self):
        path = self.file(
            "answer.csv",
            "question,answer,question_type\n1,A,single_choice\n",
        )
        result = self.assets.register(self.session.session_id, path, AssetType.ANSWER_KEY)
        self.assertEqual(result.asset.status, "VALID")
        self.assertEqual(result.asset.sha256, hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(
            self.sessions.get_session(self.session.session_id).state,
            ExamSessionState.ASSET_READY,
        )

    def test_session_without_answer_or_template_is_not_capture_ready(self):
        template = self.file("template.json", "{}")
        self.assets.register(self.session.session_id, template, AssetType.TEMPLATE)
        with self.assertRaises(ValueError):
            self.sessions.start_capture(self.session.session_id)

    def test_answer_and_template_make_capture_ready(self):
        answer = self.file(
            "answer.csv",
            "question,answer,type\n1,A,single_choice\n",
        )
        template = self.file("template.json", "{}")
        self.assets.register(self.session.session_id, answer, AssetType.ANSWER_KEY)
        self.assets.register(self.session.session_id, template, AssetType.TEMPLATE)
        self.assertEqual(
            self.sessions.get_session(self.session.session_id).state,
            ExamSessionState.CAPTURE_READY,
        )

    def test_duplicate_asset_warns(self):
        paper = self.file("paper.txt", "paper")
        first = self.assets.register(self.session.session_id, paper, AssetType.PAPER)
        second = self.assets.register(self.session.session_id, paper, AssetType.PAPER)
        self.assertFalse(first.duplicate)
        self.assertTrue(second.duplicate)
        self.assertEqual(len(self.assets.list_assets(self.session.session_id)), 1)

    def test_invalid_answer_does_not_become_capture_ready(self):
        answer = self.file("bad.csv", "answer\nA\n")
        result = self.assets.register(self.session.session_id, answer, AssetType.ANSWER_KEY)
        self.assertEqual(result.asset.status, "ASSET_INVALID")
        self.assertEqual(
            self.sessions.get_session(self.session.session_id).state,
            ExamSessionState.CLASS_SELECTED,
        )

    def test_finalized_session_rejects_new_asset(self):
        with self.database.connection() as connection:
            connection.execute(
                "UPDATE exam_sessions SET state = 'FINALIZED' WHERE session_id = ?",
                (self.session.session_id,),
            )
            connection.commit()
        with self.assertRaises(ValueError):
            self.assets.register(
                self.session.session_id,
                self.file("paper.txt", "paper"),
                AssetType.PAPER,
            )


if __name__ == "__main__":
    unittest.main()
