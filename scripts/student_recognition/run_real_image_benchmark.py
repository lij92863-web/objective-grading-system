"""Protocol runner for local anonymous real-image material; never committed."""
import argparse, hashlib, json
from pathlib import Path

def run_protocol(root):
    root=Path(root); metadata=root/'ground_truth.json'
    if not root.exists() or not metadata.exists(): return {'status':'NOT_RUN','reason':'local anonymous dataset missing'}
    data=json.loads(metadata.read_text(encoding='utf-8')); failures=[]; processed=0
    for case in data.get('cases',[]):
        image=root/case.get('image',''); processed+=1
        if not image.is_file(): failures.append({'case':case.get('case_id'),'reason':'image_missing'}); continue
        digest=hashlib.sha256(image.read_bytes()).hexdigest()
        if case.get('sha256') and digest!=case['sha256']: failures.append({'case':case.get('case_id'),'reason':'gt_or_image_tampered'})
        if case.get('contains_real_student_data') is not False: failures.append({'case':case.get('case_id'),'reason':'privacy_declaration_missing'})
    return {'status':'FAIL' if failures else 'PROTOCOL_READY','processed':processed,'failures':failures,'page_detect_success_rate':None,'corner_error_ratio':None,'roi_alignment_error':None,'omr_wrong_auto_accept_count':None,'needs_review_rate':None,'processing_time_ms':None}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--root',default='local-test-materials/student_recognition_real_images');parser.add_argument('--allow-missing-local-data',action='store_true');args=parser.parse_args();report=run_protocol(args.root);print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['status'] in ('PROTOCOL_READY','NOT_RUN') and (report['status']!='NOT_RUN' or args.allow_missing_local_data) else 1
if __name__=='__main__': raise SystemExit(main())
