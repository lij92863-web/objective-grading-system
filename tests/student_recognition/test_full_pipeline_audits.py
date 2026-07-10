import unittest
from scripts.student_recognition.run_sre_full_adversarial_audit import run as adversarial
from scripts.student_recognition.run_sre_architecture_audit import run as architecture
from scripts.student_recognition.run_sre_benchmark_audit import run as benchmark
class TestFullPipelineAudits(unittest.TestCase):
    def test_full_adversarial_not_blocked(self):self.assertNotEqual(adversarial()['status'],'BLOCKED')
    def test_architecture_not_blocked(self):self.assertNotEqual(architecture()['status'],'BLOCKED')
    def test_benchmark_not_blocked(self):self.assertNotEqual(benchmark()['status'],'BLOCKED')
if __name__=='__main__':unittest.main()
