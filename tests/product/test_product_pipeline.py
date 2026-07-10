import json
import tempfile
import unittest
from pathlib import Path

from app.capture import CaptureQueue, CaptureSourceType
from app.classes import ClassService
from app.exam_session import AssetService, AssetType, SessionService
from app.product.pipeline import MockRecognitionInput, ProductPipeline
from app.roster.roster_importer import RosterImporter
from app.storage import LocalDatabase


ROOT = Path(__file__).resolve().parents[2]
PNG = b"\x89PNG\r\n\x1a\nproduct-pipeline"


class ProductPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.database = LocalDatabase(self.root / "product.sqlite3")
        classroom = ClassService(self.database).create_class("高一 3 班")
        roster = self.root / "roster.csv"
        roster.write_text("学号,姓名\n001,张三\n", encoding="utf-8-sig")
        RosterImporter(self.database).import_file(classroom.class_id, roster)
        sessions = SessionService(self.database)
        self.session = sessions.create_session("期中考试", classroom.class_id)
        assets = AssetService(self.database, self.root / "local_app")
        answer = self.root / "answer.csv"
        answer.write_text(
            "question,answer,type\n1,A,single_choice\n2,B,single_choice\n",
            encoding="utf-8-sig",
        )
        template = self.root / "template.json"
        template.write_text("{}", encoding="utf-8")
        assets.register(self.session.session_id, answer, AssetType.ANSWER_KEY)
        assets.register(self.session.session_id, template, AssetType.TEMPLATE)
        self.queue = CaptureQueue(self.database, self.root / "local_app")
        self.pipeline = ProductPipeline(self.database, self.root / "local_app")

    def tearDown(self):
        self.temp.cleanup()

    def job(self, suffix=b""):
        return self.queue.add_bytes(
            self.session.session_id,
            "image.png",
            PNG + suffix,
            CaptureSourceType.MANUAL_UPLOAD,
        ).job

    def test_capture_job_runs_to_provisional_score_with_mock_recognition(self):
        result = self.pipeline.process_mock(
            self.job().capture_job_id,
            MockRecognitionInput(
                student_no="001",
                answer_candidates={1: "A", 2: "B"},
                evidence_path="synthetic/evidence.json",
            ),
        )
        self.assertEqual(result.provisional_score, 2)
        self.assertEqual(result.issue_ids, ())

    def test_identity_missing_keeps_answer_candidates(self):
        result = self.pipeline.process_mock(
            self.job(b"identity").capture_job_id,
            MockRecognitionInput(answer_candidates={1: "A", 2: "B"}),
        )
        self.assertEqual(result.provisional_score, 2)
        self.assertEqual(len(result.issue_ids), 1)
        with self.database.connection() as connection:
            draft = connection.execute(
                "SELECT provisional_json FROM recognition_drafts WHERE id = ?",
                (result.draft_id,),
            ).fetchone()
        self.assertEqual(json.loads(draft[0])["answers"], {"1": "A", "2": "B"})

    def test_answer_unreadable_creates_issue_and_continues_other_questions(self):
        result = self.pipeline.process_mock(
            self.job(b"answer").capture_job_id,
            MockRecognitionInput(
                student_no="001",
                answer_candidates={1: "A", 2: None},
            ),
        )
        self.assertEqual(result.provisional_score, 1)
        self.assertEqual(len(result.issue_ids), 1)

    def test_quality_and_page_failure_block_recognition_for_image(self):
        for suffix, recognition in [
            (b"quality", MockRecognitionInput(quality_ok=False)),
            (b"page", MockRecognitionInput(page_ok=False)),
        ]:
            with self.subTest(suffix=suffix):
                result = self.pipeline.process_mock(
                    self.job(suffix).capture_job_id,
                    recognition,
                )
                self.assertIsNone(result.provisional_score)
                self.assertEqual(len(result.issue_ids), 1)

    def test_provisional_score_is_never_official(self):
        result = self.pipeline.process_mock(
            self.job(b"guard").capture_job_id,
            MockRecognitionInput(
                student_no="001",
                answer_candidates={1: "A", 2: "B"},
            ),
        )
        with self.database.connection() as connection:
            payload = json.loads(connection.execute(
                "SELECT provisional_json FROM recognition_drafts WHERE id = ?",
                (result.draft_id,),
            ).fetchone()[0])
        self.assertFalse(payload["official"])
        self.assertEqual(
            connection_count(self.database, "final_scores"),
            0,
        )


def connection_count(database, table):
    with database.connection() as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


if __name__ == "__main__":
    unittest.main()
