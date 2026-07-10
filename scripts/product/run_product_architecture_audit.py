"""Static dependency and bypass audit for the local web product."""

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FAILURES = []


def imports(path: Path) -> list[str]:
    modules = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    return modules


web_controller = ROOT / "app/web_product/product_app.py"
for module in imports(web_controller):
    if module.startswith((
        "sqlite3", "app.domain.grading", "app.student_recognition",
        "app.recognition",
    )):
        FAILURES.append(f"web controller imports forbidden low-level module: {module}")

web_app = (ROOT / "web_app.py").read_text(encoding="utf-8")
if "def handle_grade" in web_app or "run_grading(" in web_app:
    FAILURES.append("legacy web grading bypass remains callable")
if 'if parsed.path == "/api/exams/grade"' not in web_app or "410" not in web_app:
    FAILURES.append("legacy grade endpoint is not explicitly retired")

for path in (ROOT / "app/capture").glob("*.py"):
    text = path.read_text(encoding="utf-8")
    if "domain.grading" in text or "finalization" in text:
        FAILURES.append(f"capture crosses into grading/finalization: {path.name}")

review_text = (ROOT / "app/product/review/review_workflow.py").read_text(encoding="utf-8")
if "SET evidence_json" in review_text:
    FAILURES.append("review overwrites original evidence")

final_text = (ROOT / "app/product/finalization/finalization_gate.py").read_text(encoding="utf-8")
for guard in ("capture_not_confirmed", "open_review", "identity_unconfirmed"):
    if guard not in final_text:
        FAILURES.append(f"finalization guard missing: {guard}")
if 'draft_snapshot={"blocking_errors": [], "review_items": []}' in final_text:
    FAILURES.append("finalization still fabricates an empty confirmed snapshot")
if "for row, submission in zip" in final_text:
    FAILURES.append("finalization still couples drafts and submissions by order")

builder_text = (
    ROOT / "app/product/finalization/confirmed_submission_builder.py"
).read_text(encoding="utf-8")
for persisted_fact in (
    "recognition_drafts", "capture_jobs", "review_issues", "review_resolutions"
):
    if persisted_fact not in builder_text:
        FAILURES.append(f"confirmed snapshot omits persisted fact: {persisted_fact}")

benchmark_text = (
    ROOT / "scripts/product/run_product_workflow_benchmark.py"
).read_text(encoding="utf-8")
if "0 if len(scores)" in benchmark_text or "len(scores) ==" in benchmark_text:
    FAILURES.append("benchmark still treats result count as its truth oracle")
for benchmark_guard in (
    "compare_final_scores", "excluded_duplicate_capture_count", "wrong_finalized_count"
):
    if benchmark_guard not in benchmark_text:
        FAILURES.append(f"benchmark truth guard missing: {benchmark_guard}")

review_text = (ROOT / "app/product/review/review_workflow.py").read_text(encoding="utf-8")
if "ManualScorePolicy.validate" not in review_text:
    FAILURES.append("review bypasses the canonical manual-score policy")
if "exclude_capture_from_identity_issue" not in review_text:
    FAILURES.append("review has no explicit duplicate-capture exclusion")

for path in (ROOT / "app/product").rglob("*.py"):
    text = path.read_text(encoding="utf-8")
    if "real_ocr" in text or "real_qwen" in text or ".env" in text:
        FAILURES.append(f"forbidden external integration in {path}")

ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
if "data/local_app/" not in ignore:
    FAILURES.append("data/local_app is not gitignored")

if FAILURES:
    print("FAIL")
    for failure in FAILURES:
        print(f"- {failure}")
    sys.exit(1)
print("PASS")
