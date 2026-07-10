import unittest
from app.student_recognition.grading_bridge.grading_gate import GradingGate,TeacherConfirmedSubmission
from app.student_recognition.grading_bridge.class_report_gate import ClassReportGate
from app.student_recognition.omr.omr_candidate import RecognizedAnswerCandidate
from app.student_recognition.drafts.recognition_draft import RecognitionDraft
class TestStrictGradingBridge(unittest.TestCase):
    def submission(self,sid='1'):return TeacherConfirmedSubmission('j',{'review_items':[]},'teacher','now',{'student_id':sid})
    def test_recognition_draft_cannot_enter_bridge(self): self.assertFalse(GradingGate().try_build(object()).ok)
    def test_omr_candidate_cannot_enter_bridge(self): self.assertFalse(GradingGate().try_build(RecognizedAnswerCandidate(1,(),'blank_candidate',())).ok)
    def test_unresolved_review_rejected(self):
        s=self.submission();s.draft_snapshot={'review_items':[{'resolution':'pending'}]};self.assertFalse(GradingGate().try_build(s).ok)
    def test_identity_missing_rejected(self): self.assertFalse(GradingGate().try_build(self.submission('')).ok)
    def test_duplicate_student_rejected(self): self.assertFalse(ClassReportGate().try_build_input([self.submission(),self.submission()],'e',True,True).ok)
    def test_missing_student_requires_authorization(self): self.assertFalse(ClassReportGate().try_build_input([self.submission()],'e',True,True,False,2).ok)
    def test_bridge_only_builds_input_not_report(self):
        result=ClassReportGate().try_build_input([self.submission()],'e',True,True);self.assertTrue(result.ok);self.assertFalse(hasattr(result.payload,'official_report'))
if __name__=='__main__':unittest.main()
