"""Benchmark orchestration reads GT; recognizers receive metrics only."""
import json,time
from pathlib import Path
from app.student_recognition.image.image_io import load_image
from app.student_recognition.image.backend import get_backend
from app.student_recognition.synthetic.template_profile import TemplateProfile as SyntheticProfile
from app.student_recognition.template.compatibility import adapt_synthetic_to_v2
from app.student_recognition.roi.roi_mapper import map_normalized_roi
from app.student_recognition.omr.mark_metrics import extract_mark_metrics
from app.student_recognition.omr.single_choice_recognizer import recognize_single_choice
from .metrics import percentile
from .report import write_reports
def run_benchmark(corpus_dir,output_dir):
    root=Path(corpus_dir); manifest=json.loads((root/'corpus_manifest.json').read_text(encoding='utf-8')); synth=SyntheticProfile.from_dict(json.loads((root/'template_profile.json').read_text(encoding='utf-8'))); profile=adapt_synthetic_to_v2(synth); backend=get_backend()
    clean_total=clean_ok=blank=blank_fp=weak=weak_review=multi=multi_review=erased=erased_review=wrong=0; times=[];failures=[]
    for entry in manifest['sheets']:
        im=load_image(root/entry['png']); gt=json.loads((root/entry['gt']).read_text(encoding='utf-8'))
        for answer in gt['answers']:
            start=time.perf_counter(); metrics=[]
            for cell in profile.get_option_cells(answer['question']+1):
                b=map_normalized_roi(cell.roi,im.width,im.height); crop=backend.crop(im,(b.x0,b.y0,b.x1,b.y1));metrics.append(extract_mark_metrics(crop,cell.option_label))
            candidate=recognize_single_choice(answer['question']+1,metrics,tuple(entry['png'] for _ in [0])); times.append((time.perf_counter()-start)*1000)
            mark=answer['mark_type']; expected=answer.get('selected')
            if entry['perturbation']=='clean' and mark=='strong': clean_total+=1; clean_ok+=candidate.selected==(expected,)
            if mark=='none': blank+=1; blank_fp+=candidate.status=='auto_candidate'
            if mark=='weak': weak+=1; weak_review+=candidate.status=='needs_review'
            if mark=='multi': multi+=1; multi_review+=candidate.status=='needs_review'
            if mark=='erased': erased+=1; erased_review+=candidate.status=='needs_review'
            if candidate.status=='auto_candidate' and candidate.selected!=(expected,): wrong+=1; failures.append({'sheet_id':entry['sheet_id'],'question':answer['question'],'expected':expected,'actual':candidate.selected})
    report={'single_choice_accuracy':clean_ok/clean_total if clean_total else 0,'multi_choice_exact_match_accuracy':0.0,'blank_false_positive_rate':blank_fp/blank if blank else 0,'weak_mark_review_rate':weak_review/weak if weak else 1,'multi_mark_review_rate':multi_review/multi if multi else 1,'erased_mark_review_rate':erased_review/erased if erased else 1,'wrong_auto_accepted_count':wrong,'ambiguous_review_recall':(weak_review+multi_review+erased_review)/max(1,weak+multi+erased),'average_processing_time_ms':sum(times)/len(times),'p95_processing_time_ms':percentile(times,.95)}
    report['status']='PASS' if report['single_choice_accuracy']>=.98 and report['blank_false_positive_rate']<=.01 and report['multi_mark_review_rate']==1 and wrong==0 else 'FAIL'
    write_reports(report,failures,output_dir); return report,failures
