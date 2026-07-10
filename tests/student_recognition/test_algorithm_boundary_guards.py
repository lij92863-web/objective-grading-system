import ast,subprocess,unittest
from pathlib import Path
from app.student_recognition.image.image_types import ImageMatrix
from app.student_recognition.image.image_quality import assess_image_quality
from app.student_recognition.image.page_locator import locate_page
from app.student_recognition.omr.mark_metrics import MarkMetrics
from app.student_recognition.omr.single_choice_recognizer import recognize_single_choice
ROOT=Path(__file__).resolve().parents[2]; APP=ROOT/'app'/'student_recognition'
def imports(path):
    tree=ast.parse(path.read_text(encoding='utf-8')); result=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Import): result += [a.name for a in n.names]
        elif isinstance(n,ast.ImportFrom): result.append(n.module or '')
    return result
class TestAlgorithmBoundaryGuards(unittest.TestCase):
    def test_cv2_import_is_isolated_to_image_backend(self):
        hits=[]
        for p in APP.rglob('*.py'):
            if any(x=='cv2' or x.startswith('cv2.') for x in imports(p)) and p.name!='backend.py': hits.append(str(p))
        self.assertEqual(hits,[])
    def test_omr_does_not_import_grading_web_qwen_or_ocr(self):
        bad=('grading','web_app','app.workflow','objective_grader','qwen','openai','requests','httpx','ocr');hits=[]
        for p in (APP/'omr').rglob('*.py'):
            for name in imports(p):
                if any(x in name.lower() for x in bad): hits.append((str(p),name))
        self.assertEqual(hits,[])
    def test_omr_does_not_write_formal_outputs(self):
        hits=[]
        for p in (APP/'omr').rglob('*.py'):
            tree=ast.parse(p.read_text(encoding='utf-8'))
            for n in ast.walk(tree):
                if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value in ('submissions.csv','data/reports'): hits.append(str(p))
        self.assertEqual(hits,[])
    def test_omr_candidate_not_final_answer(self):
        m=MarkMetrics('A',1,1,1,0,1,0,1,'strong'); c=recognize_single_choice(1,[m]); self.assertFalse(c.is_final_answer); self.assertFalse(hasattr(c,'score'))
    def test_quality_and_page_fail_closed(self):
        small=ImageMatrix(10,10,(255,)*100); self.assertEqual(assess_image_quality(small).status,'quality_failed')
        blank=ImageMatrix(240,360,(255,)*86400); self.assertEqual(locate_page(blank,240,360).status,'page_location_failed')
    def test_no_real_images_committed(self):
        files=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines(); bad=[x for x in files if x.startswith('data/captures/')]
        self.assertEqual(bad,[])
if __name__=='__main__': unittest.main()
