import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app.student_recognition.grading_bridge.grading_gate import GradingGate
from app.student_recognition.identity import parse_identity_text, validate_candidate
from app.student_recognition.ocr import FakeOCRClient
from app.student_recognition.omr.mark_metrics import MarkMetrics
from app.student_recognition.omr.single_choice_recognizer import recognize_single_choice
from app.student_recognition.qwen import FakeQwenClient

def run():
    failures=[]
    metric=lambda label,score,kind:MarkMetrics(label,score,score,score,0,1,0,score,kind)
    unsafe=[recognize_single_choice(1,[metric('A',0,'blank')]),recognize_single_choice(1,[metric('A',.1,'weak')]),recognize_single_choice(1,[metric('A',.8,'strong'),metric('B',.8,'strong')])]
    if any(item.status=='auto_candidate' for item in unsafe):failures.append('unsafe_omr_acceptance')
    if validate_candidate(parse_identity_text('1张三'),{'1':'李明'}).status!='blocked':failures.append('identity_conflict_passed')
    for candidate in (FakeOCRClient('A',1).recognize('x'),FakeQwenClient('A',1).propose('x')):
        if candidate.direct_accepted or GradingGate().try_build(candidate).ok:failures.append('fake_candidate_bypass')
    return {'status':'BLOCKED' if failures else 'APPROVED_WITH_CAVEATS','failures':failures,'caveats':['real_image_not_run']}
if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2));raise SystemExit(1 if run()['status']=='BLOCKED' else 0)
