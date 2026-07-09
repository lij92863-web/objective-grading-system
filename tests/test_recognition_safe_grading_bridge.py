"""R12: Recognition → Grading Safe E2E bridge tests."""
import shutil, tempfile, unittest
from pathlib import Path
from app.recognition.contracts import (RecognizedSubmissionDraft, RecognitionDecision,
    TeacherConfirmedSubmission)
from app.application.use_cases.recognition.safe_grading_bridge import (
    validate_draft_safe_for_grading, convert_confirmed_to_submission_rows,
    write_submission_csv, safe_dry_run_grading)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_KEY = PROJECT_ROOT / "samples/demo_exam/answer_key_sample.csv"


class RecognitionSafeGradingBridgeTests(unittest.TestCase):
    def _make_clean_draft(self):
        return RecognizedSubmissionDraft(student_id="S001", student_name="Test",
            identity_status="confirmed",
            decisions=[RecognitionDecision(question_number=1, value="A", status="auto_accepted",
                                           needs_review=False)],
            ready_for_confirmation=True)

    def test_default_draft_not_ready_for_grading(self):
        d = RecognizedSubmissionDraft()
        self.assertFalse(d.ready_for_grading)

    def test_unconfirmed_draft_has_blockers(self):
        d = RecognizedSubmissionDraft()
        blockers = validate_draft_safe_for_grading(d)
        self.assertIn("DRAFT_NOT_READY_FOR_CONFIRMATION", blockers)

    def test_needs_review_blocks_confirmation(self):
        d = self._make_clean_draft()
        d.decisions = [RecognitionDecision(question_number=1, status="needs_review", needs_review=True)]
        blockers = validate_draft_safe_for_grading(d)
        self.assertTrue(any("UNREVIEWED" in b for b in blockers))

    def test_identity_conflict_blocks(self):
        d = self._make_clean_draft()
        d.identity_status = "conflict"
        blockers = validate_draft_safe_for_grading(d)
        self.assertIn("IDENTITY_CONFLICT", blockers)

    def test_missing_identity_blocks(self):
        d = self._make_clean_draft()
        d.identity_status = "missing"
        blockers = validate_draft_safe_for_grading(d)
        self.assertIn("IDENTITY_MISSING", blockers)

    def test_blocking_exception_blocks(self):
        d = self._make_clean_draft()
        d.exceptions = [{"code": "BLOCKING_BEFORE_GRADING", "level": "blocking"}]
        blockers = validate_draft_safe_for_grading(d)
        self.assertIn("BLOCKING_EXCEPTIONS_PRESENT", blockers)

    def test_clean_draft_passes_validation(self):
        d = self._make_clean_draft()
        blockers = validate_draft_safe_for_grading(d)
        self.assertEqual([], blockers)

    def test_confirmed_to_submission_rows(self):
        confirmed = TeacherConfirmedSubmission(student_id="S001", name="Test",
            answers={1: "A", 2: "B"}, confirmed_by="teacher")
        rows = convert_confirmed_to_submission_rows(confirmed)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["student_id"], "S001")

    def test_safe_dry_run_grading(self):
        confirmed = TeacherConfirmedSubmission(student_id="S001", name="Test",
            answers={1: "A", 2: "BD", 3: "C"}, confirmed_by="teacher")
        t = tempfile.mkdtemp(prefix="r12_", dir=PROJECT_ROOT/"data")
        try:
            result = safe_dry_run_grading(confirmed, str(DEMO_KEY), str(Path(t)/"sub.csv"))
            self.assertTrue(result["passed"])
            self.assertEqual(result["student_count"], 1)
        finally: shutil.rmtree(t, ignore_errors=True)

    def test_no_legacy_import(self):
        import ast
        src = (PROJECT_ROOT/"app/application/use_cases/recognition/safe_grading_bridge.py").read_text("utf-8")
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                for a in node.names: self.assertNotIn("legacy", a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module: self.assertNotIn("legacy", node.module)


if __name__ == "__main__": unittest.main()
