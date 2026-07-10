import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.student_recognition.benchmark import run_benchmark
def main():
    p=argparse.ArgumentParser();p.add_argument('--corpus',default='tests/student_recognition/fixtures/synthetic');p.add_argument('--out',default='data/student_recognition/benchmark');a=p.parse_args();r,_=run_benchmark(a.corpus,a.out);print(r);return 0 if r['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
