import unittest
from app.student_recognition.image.image_types import ImageMatrix
from app.student_recognition.omr.mark_metrics import MarkMetrics,extract_mark_metrics
from app.student_recognition.omr.single_choice_recognizer import recognize_single_choice
from app.student_recognition.omr.multi_choice_recognizer import recognize_multi_choice
from app.student_recognition.omr.omr_evidence import OMREvidence
from app.student_recognition.errors.error_codes import ErrorCode

def img(fn,w=20,h=20): return ImageMatrix(w,h,tuple(fn(x,y) for y in range(h) for x in range(w)))
def metric(option,score,cls): return MarkMetrics(option,score,score,score,0,1,0,score,cls)
class TestOMRMetrics(unittest.TestCase):
    def test_mark_metrics_strong_mark(self): self.assertEqual(extract_mark_metrics(img(lambda x,y:0),"A").classification,"strong")
    def test_mark_metrics_blank_mark(self): self.assertEqual(extract_mark_metrics(img(lambda x,y:255),"A").classification,"blank")
    def test_mark_metrics_weak_mark(self): self.assertEqual(extract_mark_metrics(img(lambda x,y:0 if x in (9,10) else 255),"A").classification,"weak")
    def test_mark_metrics_erased_mark(self): self.assertEqual(extract_mark_metrics(img(lambda x,y:0 if x==9 else 255),"A").classification,"erased")
    def test_border_noise_does_not_count_as_fill(self): self.assertEqual(extract_mark_metrics(img(lambda x,y:0 if x in (0,19) or y in (0,19) else 255),"A").classification,"dirty")
class TestRecognizers(unittest.TestCase):
    def test_single_choice_clean_strong_auto_candidate(self): self.assertEqual(recognize_single_choice(1,[metric("A",.05,"blank"),metric("B",.8,"strong"),metric("C",.05,"blank")]).status,"auto_candidate")
    def test_single_choice_blank_not_guessed(self): self.assertEqual(recognize_single_choice(1,[metric("A",.05,"blank")]).status,"blank_candidate")
    def test_single_choice_weak_mark_needs_review(self): self.assertEqual(recognize_single_choice(1,[metric("A",.3,"weak")]).status,"needs_review")
    def test_single_choice_weak_mark_has_specific_reason(self): self.assertEqual(recognize_single_choice(1,[metric("A",.3,"weak")]).reason_codes,(ErrorCode.OMR_WEAK_MARK,))
    def test_single_choice_two_strong_marks_needs_review(self): self.assertEqual(recognize_single_choice(1,[metric("A",.8,"strong"),metric("B",.7,"strong")]).status,"needs_review")
    def test_single_choice_erased_needs_review(self): self.assertEqual(recognize_single_choice(1,[metric("A",.4,"erased")]).status,"needs_review")
    def test_multi_choice_two_selected(self): self.assertEqual(recognize_multi_choice(1,[metric("B",.8,"strong"),metric("D",.8,"strong")]).selected,("B","D"))
    def test_multi_choice_ambiguous_band_needs_review(self): self.assertEqual(recognize_multi_choice(1,[metric("A",.4,"weak")]).status,"needs_review")
    def test_multi_choice_blank_not_guessed(self): self.assertEqual(recognize_multi_choice(1,[metric("A",.05,"blank")]).status,"blank_candidate")
    def test_candidate_is_not_final_answer(self): self.assertFalse(recognize_single_choice(1,[metric("A",.8,"strong")]).is_final_answer)
    def test_candidate_preserves_typed_evidence(self):
        metrics=(metric("A",.8,"strong"),)
        evidence=OMREvidence("crop.pgm","a"*64,{"template_id":"t","template_version":1},1,("A",),metrics)
        candidate=recognize_single_choice(1,metrics,(evidence,))
        self.assertIs(candidate.evidence[0],evidence)
if __name__=="__main__": unittest.main()
