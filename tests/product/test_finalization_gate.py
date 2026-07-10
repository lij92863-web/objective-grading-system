import json
import tempfile
import unittest
from pathlib import Path

from app.capture import CaptureQueue, CaptureSourceType
from app.classes import ClassService
from app.exam_session import AssetService, AssetType, SessionService
from app.product.finalization import FinalScoreService, FinalizationGateState
from app.product.pipeline import MockRecognitionInput, ProductPipeline
from app.product.review.manual_resolution import TeacherAction
from app.product.review.review_workflow import ReviewWorkflow
from app.roster.roster_importer import RosterImporter
from app.storage import LocalDatabase


ROOT = Path(__file__).resolve().parents[2]
PNG = b"\x89PNG\r\n\x1a\nfinal"


class FinalizationGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.database = LocalDatabase(self.root / "product.sqlite3")
        classroom = ClassService(self.database).create_class("高一 3 班")
        roster = self.root / "roster.csv"
        roster.write_text("学号,姓名\n001,张三\n002,李四\n", encoding="utf-8-sig")
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
        self.review = ReviewWorkflow(self.database)
        self.final = FinalScoreService(self.database, self.root / "exports")

    def tearDown(self):
        self.temp.cleanup()

    def process(self, suffix: bytes, recognition: MockRecognitionInput):
        job = self.queue.add_bytes(
            self.session.session_id,
            "image.png",
            PNG + suffix,
            CaptureSourceType.MANUAL_UPLOAD,
        ).job
        return self.pipeline.process_mock(job.capture_job_id, recognition)

    def test_finalize_blocks_open_identity_and_answer_issue(self):
        self.process(b"open", MockRecognitionInput(answer_candidates={1: "A", 2: None}))
        decision = self.final.confirm_teacher(self.session.session_id)
        self.assertEqual(decision.state, FinalizationGateState.BLOCKED)
        self.assertTrue(any("open_review:IDENTITY_MISSING" in item for item in decision.blockers))
        self.assertTrue(any("open_review:ANSWER_UNREADABLE" in item for item in decision.blockers))
        with self.assertRaises(ValueError):
            self.final.finalize(self.session.session_id)

    def test_finalize_blocks_provisional_score_without_teacher_confirmation(self):
        self.process(
            b"provisional",
            MockRecognitionInput(student_no="001", answer_candidates={1: "A", 2: "B"}),
        )
        with self.assertRaises(ValueError):
            self.final.finalize(self.session.session_id)

    def test_finalize_blocks_duplicate_student(self):
        for suffix in (b"one", b"two"):
            self.process(
                suffix,
                MockRecognitionInput(student_no="001", answer_candidates={1: "A", 2: "B"}),
            )
        decision = self.final.confirm_teacher(self.session.session_id)
        self.assertTrue(
            any(
                "duplicate_student" in item or "IDENTITY_DUPLICATE" in item
                for item in decision.blockers
            )
        )

    def test_finalize_allows_after_all_issues_resolved_and_writes_exports(self):
        self.process(b"resolved", MockRecognitionInput(answer_candidates={1: "A", 2: None}))
        issues = self.review.list_issues(self.session.session_id)
        self.review.resolve_identity(issues[0].issue_id, student_no="001")
        self.review.resolve_answer(
            issues[1].issue_id,
            TeacherAction.MANUAL_SCORE,
            manual_score=1,
            reason="教师依据原卷给分",
        )
        decision = self.final.confirm_teacher(self.session.session_id)
        self.assertEqual(decision.state, FinalizationGateState.READY)
        result = self.final.finalize(self.session.session_id)
        self.assertEqual(result.score_count, 1)
        self.assertTrue((result.output_dir / "final_scores.csv").exists())
        self.assertTrue((result.output_dir / "final_scores.json").exists())
        audit = json.loads(
            (result.output_dir / "finalization_audit.json").read_text(encoding="utf-8")
        )
        self.assertEqual(audit["gate"], "READY")
        with self.database.connection() as connection:
            state = connection.execute(
                "SELECT state FROM exam_sessions WHERE session_id = ?",
                (self.session.session_id,),
            ).fetchone()[0]
        self.assertEqual(state, "FINALIZED")

    def test_final_score_requires_teacher_confirmation(self):
        self.process(
            b"teacher",
            MockRecognitionInput(student_no="001", answer_candidates={1: "A", 2: "B"}),
        )
        self.assertIn(
            "teacher_confirmation_missing",
            self.final.gate.evaluate(self.session.session_id).blockers,
        )


if __name__ == "__main__":
    unittest.main()
