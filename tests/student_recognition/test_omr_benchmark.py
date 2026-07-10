import tempfile,unittest
from pathlib import Path
from app.student_recognition.benchmark import run_benchmark
ROOT=Path(__file__).parent/'fixtures'/'synthetic'
class TestOMRBenchmark(unittest.TestCase):
    def test_benchmark_reports_required_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            r,f=run_benchmark(ROOT,tmp)
            for key in ('single_choice_accuracy','blank_false_positive_rate','multi_mark_review_rate','wrong_auto_accepted_count','p95_processing_time_ms'): self.assertIn(key,r)
            self.assertTrue((Path(tmp)/'benchmark_report.json').exists())
    def test_benchmark_fails_when_wrong_auto_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            r,_=run_benchmark(ROOT,tmp); self.assertEqual(r['wrong_auto_accepted_count'],0)
    def test_benchmark_records_failure_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_benchmark(ROOT,tmp); self.assertTrue((Path(tmp)/'failure_samples.json').exists())
if __name__=='__main__': unittest.main()
