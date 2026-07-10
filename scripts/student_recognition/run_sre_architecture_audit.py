import ast,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];APP=ROOT/'app'/'student_recognition'
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
def run():
    failures=[];forbidden=('objective_grader','app.workflow','web_app')
    for path in APP.rglob('*.py'):
        tree=ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            module=(node.module or '') if isinstance(node,ast.ImportFrom) else ''
            names=[a.name for a in node.names] if isinstance(node,ast.Import) else [module]
            if any(any(bad in name for bad in forbidden) for name in names):failures.append(str(path.relative_to(ROOT)))
    return {'status':'BLOCKED' if failures else 'APPROVED_WITH_CAVEATS','failures':failures,'caveats':['real_image_not_validated','ocr_qwen_mock_only']}
if __name__=='__main__':result=run();print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(1 if result['status']=='BLOCKED' else 0)
