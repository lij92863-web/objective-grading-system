import json
from pathlib import Path
def write_reports(report,failures,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'benchmark_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'failure_samples.json').write_text(json.dumps(failures,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'benchmark_report.md').write_text('# Synthetic OMR Benchmark\n\n'+''.join(f'- {k}: {v}\n' for k,v in report.items()),encoding='utf-8')
