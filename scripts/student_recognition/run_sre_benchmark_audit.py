import json,tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app.student_recognition.benchmark import run_benchmark
from scripts.student_recognition.run_real_image_benchmark import run_protocol
def run():
    with tempfile.TemporaryDirectory() as tmp: synthetic,_=run_benchmark(ROOT/'tests/student_recognition/fixtures/synthetic',tmp)
    real=run_protocol(ROOT/'local-test-materials/student_recognition_real_images')
    blocked=synthetic['wrong_auto_accepted_count']>0 or synthetic['blank_false_positive_rate']>.01 or synthetic['multi_mark_review_rate']!=1
    return {'status':'BLOCKED' if blocked else 'APPROVED_WITH_CAVEATS','synthetic':synthetic,'real':real}
if __name__=='__main__':result=run();print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(1 if result['status']=='BLOCKED' else 0)
