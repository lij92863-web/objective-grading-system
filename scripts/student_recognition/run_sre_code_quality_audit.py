import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];APP=ROOT/'app'/'student_recognition'
def run():
    findings=[]
    for path in APP.rglob('*.py'):
        text=path.read_text(encoding='utf-8');tree=ast.parse(text)
        if any(len(line)>140 for line in text.splitlines()):findings.append({'severity':'medium','check':'long_line','file':str(path.relative_to(ROOT))})
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and (getattr(node,'end_lineno',node.lineno)-node.lineno)>180:findings.append({'severity':'high','check':'giant_function','file':str(path.relative_to(ROOT))})
    status='BLOCKED' if any(x['severity']=='high' for x in findings) else ('APPROVED_WITH_CAVEATS' if findings else 'APPROVED')
    return {'status':status,'findings':findings}
if __name__=='__main__':result=run();print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(1 if result['status']=='BLOCKED' else 0)
