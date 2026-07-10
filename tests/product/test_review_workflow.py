import json
import tempfile
import unittest
from pathlib import Path

from app.capture import CaptureQueue, CaptureSourceType
from app.classes import ClassService
from app.exam_session import AssetService, AssetType, SessionService
from app.product.pipeline import MockRecognitionInput, ProductPipeline
from app.product.review.manual_resolution import TeacherAction
from app.product.review.review_workflow import ReviewWorkflow
from app.roster.roster_importer import RosterImporter
from app.storage import LocalDatabase


ROOT = Path(__file__).resolve().parents[2]
PNG = b"\x89PNG\r\n\x1a\nreview"


class ReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "data")
        self.root = Path(self.temp.name)
        self.database = LocalDatabase(self.root / "product.sqlite3")
        classroom = ClassService(self.database).create_class("高一 3 班")
        roster = self.root / "roster.csv"
        roster.write_text(
            "学号,姓名\n001,张三\n002,同名\n003,同名\n",
            encoding="utf-8-sig",
        )
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
        queue = CaptureQueue(self.database, self.root / "local_app")
        job = queue.add_bytes(
            self.session.session_id,
            "image.png",
            PNG,
            CaptureSourceType.MANUAL_UPLOAD,
        ).job
        self.result = ProductPipeline(
            self.database,
            self.root / "local_app",
        ).process_mock(
            job.capture_job_id,
            MockRecognitionInput(
                answer_candidates={1: "A", 2: None},
                evidence_path="immutable/evidence.png",
            ),
        )
        self.review = ReviewWorkflow(self.database)

    def tearDown(self):
        self.temp.cleanup()

    def test_identity_issue_presented_first_and_message_not_raw_code(self):
        issues = self.review.list_issues(self.session.session_id)
        self.assertEqual(issues[0].issue_type, "IDENTITY_MISSING")
        self.assertNotEqual(issues[0].teacher_message, issues[0].issue_type)
        self.assertEqual(issues[1].issue_type, "ANSWER_UNREADABLE")

    def test_manual_identity_resolution_by_student_no(self):
        issue = self.review.list_issues(self.session.session_id)[0]
        self.review.resolve_identity(issue.issue_id, student_no="001")
        self.assertEqual(len(self.review.list_issues(self.session.session_id)), 1)

    def test_manual_identity_name_duplicate_blocks(self):
        issue = self.review.list_issues(self.session.session_id)[0]
        with self.assertRaises(ValueError):
            self.review.resolve_identity(
                issue.issue_id,
                name="同名",
                confirm_name=True,
            )

    def test_manual_answer_score_and_zero_require_reason(self):
        issue = self.review.list_issues(self.session.session_id)[1]
        with self.assertRaises(ValueError):
            self.review.resolve_answer(
                issue.issue_id,
                TeacherAction.MANUAL_SCORE,
                manual_score=0,
                reason="",
            )
        self.review.resolve_answer(
            issue.issue_id,
            TeacherAction.MANUAL_SCORE,
            manual_score=0,
            reason="教师确认错误",
        )

    def test_review_rejects_score_above_canonical_question_max(self):
        issue = self.review.list_issues(self.session.session_id)[1]
        with self.assertRaises(ValueError):
            self.review.resolve_answer(
                issue.issue_id,
                TeacherAction.MANUAL_SCORE,
                manual_score=20,
                reason="attack",
            )
        with self.database.connection() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM review_resolutions WHERE issue_id = ?",
                (issue.issue_id,),
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_review_resolution_preserves_original_evidence_and_audits(self):
        issue = self.review.list_issues(self.session.session_id)[1]
        with self.database.connection() as connection:
            before = connection.execute(
                "SELECT evidence_json FROM recognition_drafts WHERE id = ?",
                (self.result.draft_id,),
            ).fetchone()[0]
        self.review.resolve_answer(
            issue.issue_id,
            TeacherAction.MARK_BLANK,
            reason="教师确认空白",
        )
        with self.database.connection() as connection:
            after = connection.execute(
                "SELECT evidence_json FROM recognition_drafts WHERE id = ?",
                (self.result.draft_id,),
            ).fetchone()[0]
            resolution = connection.execute(
                "SELECT * FROM review_resolutions WHERE issue_id = ?",
                (issue.issue_id,),
            ).fetchone()
            audit_count = connection.execute(
                "SELECT COUNT(*) FROM audit_events WHERE entity_id = ?",
                (issue.issue_id,),
            ).fetchone()[0]
        self.assertEqual(json.loads(before), json.loads(after))
        self.assertEqual(resolution["original_evidence_path"], "immutable/evidence.png")
        self.assertEqual(audit_count, 1)


if __name__ == "__main__":
    unittest.main()
