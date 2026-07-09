"""R40A: OMR/Qwen fusion tests."""
import unittest
from app.recognition.omr_qwen_fusion import fuse_omr_qwen, FusionResult
from app.recognition.contracts import EngineCandidate


class OMRQwenFusionTests(unittest.TestCase):
    def test_omr_only(self):
        omr = EngineCandidate(question_number=1, engine="omr", value="A", confidence=0.9, status="ok")
        r = fuse_omr_qwen(1, "choice", omr_candidate=omr)
        self.assertEqual(len(r.candidates), 1)

    def test_qwen_only(self):
        qwen = EngineCandidate(question_number=2, engine="qwen", value="B", confidence=0.85, status="ok")
        r = fuse_omr_qwen(2, "choice", qwen_candidate=qwen)
        self.assertEqual(len(r.candidates), 1)

    def test_agree_boosts(self):
        omr = EngineCandidate(engine="omr", value="A", confidence=0.9, status="ok")
        qwen = EngineCandidate(engine="qwen", value="A", confidence=0.8, status="ok")
        r = fuse_omr_qwen(1, "choice", omr, qwen)
        self.assertTrue(r.omr_qwen_agree)
        self.assertFalse(r.omr_qwen_conflict)

    def test_conflict(self):
        omr = EngineCandidate(engine="omr", value="A", confidence=0.9, status="ok")
        qwen = EngineCandidate(engine="qwen", value="B", confidence=0.8, status="ok")
        r = fuse_omr_qwen(1, "choice", omr, qwen)
        self.assertTrue(r.omr_qwen_conflict)
        self.assertEqual(len(r.candidates), 2)

    def test_omr_blocking_dominates(self):
        omr = EngineCandidate(engine="omr", status="blocking", reason="invalid_option")
        qwen = EngineCandidate(engine="qwen", value="A", confidence=0.9)
        r = fuse_omr_qwen(1, "choice", omr, qwen)
        self.assertEqual(r.candidates[0].status, "blocking")

    def test_qwen_malformed_fallback_to_omr(self):
        omr = EngineCandidate(engine="omr", value="A", confidence=0.9, status="ok")
        qwen = EngineCandidate(engine="qwen", status="engine_error")
        r = fuse_omr_qwen(1, "choice", omr, qwen)
        self.assertEqual(r.candidates[0].engine, "omr")
        self.assertIn("QWEN_ENGINE_ERROR", r.engine_errors)

    def test_qwen_malformed_no_omr(self):
        qwen = EngineCandidate(engine="qwen", status="malformed")
        r = fuse_omr_qwen(1, "choice", qwen_candidate=qwen)
        self.assertEqual(len(r.candidates), 0)
        self.assertIn("QWEN_MALFORMED", r.engine_errors)

    def test_output_serializable(self):
        import json
        r = fuse_omr_qwen(1, "choice",
                           EngineCandidate(engine="omr", value="A", confidence=0.9, status="ok"))
        s = json.dumps({"conflict": r.omr_qwen_conflict, "agree": r.omr_qwen_agree})
        self.assertIn("conflict", s)


if __name__ == "__main__": unittest.main()
