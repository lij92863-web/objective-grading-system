import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.capture import CaptureQueue, CaptureSourceType
from app.classes import ClassService
from app.exam_session import AssetService, AssetType, SessionService
from app.product.finalization import FinalScoreService, FinalizationGateState
from app.product.pipeline import MockRecognitionInput, ProductPipeline
from app.product.review.manual_resolution import TeacherAction
from app.product.review.review_workflow import ReviewWorkflow
from app.roster.roster_importer import RosterImporter
from app.storage import LocalDatabase
from app.product.scoring.final_score_policy import FinalScoreInvariantError


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

    def test_excluded_duplicate_does_not_create_final_score(self):
        self.process(
            b"original",
            MockRecognitionInput(
                student_no="001",
                answer_candidates={1: "A", 2: "B"},
            ),
        )
        duplicate = self.process(
            b"duplicate",
            MockRecognitionInput(
                student_no="001",
                answer_candidates={1: "A", 2: "B"},
            ),
        )
        issue = self.review.list_issues(self.session.session_id)[0]
        self.assertEqual(issue.issue_type, "IDENTITY_DUPLICATE")
        self.review.exclude_capture_from_identity_issue(
            issue.issue_id,
            reason="重复拍摄",
        )
        decision = self.final.confirm_teacher(self.session.session_id)
        self.assertEqual(decision.state, FinalizationGateState.READY)
        result = self.final.finalize(self.session.session_id)
        self.assertEqual(result.score_count, 1)
        with self.database.connection() as connection:
            excluded = connection.execute(
                "SELECT state FROM capture_jobs WHERE id = ?",
                (duplicate.capture_job_id,),
            ).fetchone()[0]
            score_count = connection.execute(
                "SELECT COUNT(*) FROM final_scores"
            ).fetchone()[0]
        self.assertEqual(excluded, "EXCLUDED")
        self.assertEqual(score_count, 1)
        with self.database.connection() as connection:
            connection.execute(
                "UPDATE review_issues SET state = 'OPEN' WHERE id = ?",
                (issue.issue_id,),
            )
            connection.commit()
        with self.assertRaises(ValueError):
            self.review.exclude_capture_from_identity_issue(
                issue.issue_id,
                reason="post-finalization attack",
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

    def prepare_ready_manual_score(self):
        self.process(
            b"manual-ready",
            MockRecognitionInput(answer_candidates={1: "A", 2: None}),
        )
        issues = self.review.list_issues(self.session.session_id)
        self.review.resolve_identity(issues[0].issue_id, student_no="001")
        self.review.resolve_answer(
            issues[1].issue_id,
            TeacherAction.MANUAL_SCORE,
            manual_score=1,
            reason="teacher reviewed source",
        )
        self.final.confirm_teacher(self.session.session_id)

    def test_finalization_rejects_corrupted_manual_override_atomically(self):
        self.prepare_ready_manual_score()
        with self.database.connection() as connection:
            connection.execute(
                "UPDATE review_resolutions SET manual_score = 20"
            )
            connection.commit()
        decision = self.final.gate.evaluate(self.session.session_id)
        self.assertTrue(any(
            blocker.startswith("manual_score_above_question_max")
            for blocker in decision.blockers
        ))
        with self.assertRaises(ValueError):
            self.final.finalize(self.session.session_id)
        self.assert_no_formal_publication()

    def test_publication_failure_rolls_back_database_and_files(self):
        self.prepare_ready_manual_score()
        with mock.patch.object(
            self.final,
            "_record_artifact",
            side_effect=RuntimeError("publish attack"),
        ):
            with self.assertRaises(RuntimeError):
                self.final.finalize(self.session.session_id)
        self.assert_no_formal_publication()

    def test_finalization_rejects_non_finite_database_override(self):
        self.prepare_ready_manual_score()
        with self.database.connection() as connection:
            connection.execute(
                "UPDATE review_resolutions SET manual_score = ?",
                (float("inf"),),
            )
            connection.commit()
        decision = self.final.gate.evaluate(self.session.session_id)
        self.assertTrue(any(
            blocker.startswith("manual_score_non_finite")
            for blocker in decision.blockers
        ))

    def test_finalization_rejects_override_action_and_question_mismatch(self):
        for sql, prefix in (
            (
                "UPDATE review_resolutions SET teacher_action = 'MARK_WRONG', manual_score = 1",
                "manual_score_action_mismatch",
            ),
            (
                "UPDATE review_issues SET question_number = 99 WHERE question_number IS NOT NULL",
                "manual_score_question_missing",
            ),
        ):
            with self.subTest(prefix=prefix):
                self.tearDown()
                self.setUp()
                self.prepare_ready_manual_score()
                with self.database.connection() as connection:
                    connection.execute(sql)
                    connection.commit()
                decision = self.final.gate.evaluate(self.session.session_id)
                self.assertTrue(any(
                    blocker.startswith(prefix)
                    for blocker in decision.blockers
                ))

    def test_publication_layer_rejects_invalid_final_score_row(self):
        self.prepare_ready_manual_score()
        with self.database.connection() as connection:
            student_id = connection.execute(
                "SELECT id FROM students WHERE student_no = '001'"
            ).fetchone()[0]
        invalid_rows = [{
            "student_no": "001",
            "student_name": "张三",
            "score": 20,
            "max_score": 2,
            "percent": 1000,
            "status": "FINAL",
            "unresolved_count": 0,
            "manual_review_count": 1,
        }]
        submissions = [{"student_id": student_id, "answers": {}}]
        with mock.patch.object(
            self.final,
            "_build_scores",
            return_value=(invalid_rows, submissions),
        ):
            with self.assertRaises(FinalScoreInvariantError):
                self.final.finalize(self.session.session_id)
        self.assert_no_formal_publication()

    def assert_no_formal_publication(self):
        with self.database.connection() as connection:
            session_state = connection.execute(
                "SELECT state FROM exam_sessions WHERE session_id = ?",
                (self.session.session_id,),
            ).fetchone()[0]
            counts = [
                connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("final_scores", "final_submissions", "artifact_index")
            ]
            evidence_count = connection.execute(
                "SELECT COUNT(*) FROM recognition_drafts"
            ).fetchone()[0]
            resolution_count = connection.execute(
                "SELECT COUNT(*) FROM review_resolutions"
            ).fetchone()[0]
        self.assertNotEqual(session_state, "FINALIZED")
        self.assertEqual(counts, [0, 0, 0])
        self.assertGreater(evidence_count, 0)
        self.assertGreater(resolution_count, 0)
        output = self.root / "exports" / self.session.session_id
        self.assertFalse((output / "final_scores.csv").exists())
        self.assertFalse((output / "final_scores.json").exists())


if __name__ == "__main__":
    unittest.main()
