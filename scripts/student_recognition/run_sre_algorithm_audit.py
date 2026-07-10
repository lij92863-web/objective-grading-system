import ast,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
APP=ROOT/'app'/'student_recognition'; findings=[]
def add(severity,check,detail): findings.append({'severity':severity,'check':check,'detail':detail})
def main():
    anchor=(APP/'template'/'anchor_layout.py').read_text(encoding='utf-8')
    if '_clamp_roi' in anchor: add('critical','silent_clamp','anchor expansion still clamps ROI')
    for p in APP.rglob('*.py'):
        tree=ast.parse(p.read_text(encoding='utf-8'))
        for n in ast.walk(tree):
            mods=[]
            if isinstance(n,ast.Import): mods=[a.name for a in n.names]
            elif isinstance(n,ast.ImportFrom): mods=[n.module or '']
            for mod in mods:
                if mod=='cv2' and p.name!='backend.py': add('high','cv2_isolation',str(p))
                if any(x in mod.lower() for x in ('objective_grader','app.workflow','web_app')): add('critical','boundary_import',f'{p}:{mod}')
    recognizer=''.join(p.read_text(encoding='utf-8') for p in (APP/'omr').glob('*recognizer.py'))
    if 'ground_truth' in recognizer: add('critical','gt_leak','recognizer reads ground truth')
    if not (APP/'roi'/'roi_cropper.py').exists(): add('high','evidence_crop','crop artifact layer missing')
    add('caveat','real_image_backend','real-photo contour/perspective backend is not production-certified')
    severe=[x for x in findings if x['severity'] in ('critical','high')]; status='FAIL' if severe else ('PASS_WITH_CAVEATS' if findings else 'PASS')
    result={'status':status,'findings':findings}; print(json.dumps(result,ensure_ascii=False,indent=2)); return 1 if status=='FAIL' else 0
if __name__=='__main__': raise SystemExit(main())
