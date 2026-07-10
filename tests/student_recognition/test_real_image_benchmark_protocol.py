import hashlib,json,tempfile,unittest
from pathlib import Path
from scripts.student_recognition.run_real_image_benchmark import run_protocol
class TestRealImageBenchmarkProtocol(unittest.TestCase):
    def test_missing_local_material_is_not_run(self):
        with tempfile.TemporaryDirectory() as tmp: self.assertEqual(run_protocol(Path(tmp)/'missing')['status'],'NOT_RUN')
    def test_tampered_image_or_gt_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'card.ppm').write_bytes(b'anonymous-card')
            (root/'ground_truth.json').write_text(json.dumps({'cases':[{'case_id':'x','image':'card.ppm','sha256':'0'*64,'contains_real_student_data':False}]}),encoding='utf-8')
            report=run_protocol(root);self.assertEqual(report['status'],'FAIL');self.assertEqual(report['failures'][0]['reason'],'gt_or_image_tampered')
    def test_anonymous_protocol_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=b'anonymous-card';(root/'card.ppm').write_bytes(raw)
            (root/'ground_truth.json').write_text(json.dumps({'cases':[{'case_id':'x','image':'card.ppm','sha256':hashlib.sha256(raw).hexdigest(),'contains_real_student_data':False}]}),encoding='utf-8')
            self.assertEqual(run_protocol(root)['status'],'PROTOCOL_READY')
if __name__=='__main__':unittest.main()
