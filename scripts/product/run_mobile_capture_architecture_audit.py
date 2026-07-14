"""Fail-closed static audit for the mobile USB capture architecture."""

import ast
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
FAILURES: list[str] = []


def text(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        FAILURES.append(f"required file is missing: {relative}")
        return ""
    return path.read_text(encoding="utf-8")


def imported_modules(source: str) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    return modules


controller = text("app/web_product/product_app.py")
facade = text("app/web_product/facade.py")
service = text("app/product/capture/mobile_capture_service.py")
source = text("app/capture/mobile_web_camera_source.py")
queue = text("app/capture/capture_queue.py")
mobile_js = text("web/static/mobile_capture.js")
mobile_html = text("web/templates/product/mobile_capture.html")
web_app = text("web_app.py")
ignore = text(".gitignore")

for module in imported_modules(controller):
    if module.startswith(("sqlite3", "app.domain.grading", "app.student_recognition", "legacy")):
        FAILURES.append(f"mobile web controller crosses a forbidden boundary: {module}")

required_edges = [
    (controller, "facade.capture_mobile_web", "web controller -> facade"),
    (facade, "MobileCaptureService", "facade -> application service"),
    (service, "MobileWebCameraSource", "application service -> capture source"),
    (service, "ProductPipeline", "application service -> conservative pipeline"),
    (source, "self.queue.add_bytes", "capture source -> shared CaptureQueue"),
    (queue, "hashlib.sha256", "CaptureQueue SHA-256 deduplication"),
]
for body, marker, label in required_edges:
    if marker not in body:
        FAILURES.append(f"missing architecture edge: {label}")

for marker in (
    "indexedDB.open", "LOCAL_PENDING", "ACKNOWLEDGED", "uploadWorkerActive",
    "ImageCapture", "enumerateDevices", 'ideal: "environment"',
):
    if marker not in mobile_js:
        FAILURES.append(f"mobile page capability missing: {marker}")

if "a4-guide" not in mobile_html or "mobile_capture.js" not in mobile_html:
    FAILURES.append("mobile capture template is not wired to the dedicated camera UI")
if 'def run(host: str = "127.0.0.1"' not in web_app:
    FAILURES.append("web service no longer defaults to 127.0.0.1")
if 'def run(host: str = "0.0.0.0"' in web_app:
    FAILURES.append("web service was opened to 0.0.0.0")
if 'if product_controller().handles(parsed.path):' not in web_app:
    FAILURES.append("mobile requests do not enter the product controller")

combined_new_code = "\n".join((controller, facade, service, source, mobile_js)).lower()
for forbidden in (
    "domain.grading", "grade_submission", "legacy.", "dotenv", "os.getenv",
    "qwen", "student_recognition", "api_key", "requests.post",
):
    if forbidden in combined_new_code:
        FAILURES.append(f"forbidden integration in mobile capture path: {forbidden}")

for false_claim in ("识别成功", "批改完成", "成绩已生成"):
    if false_claim in mobile_html:
        FAILURES.append(f"mobile page contains unsupported result claim: {false_claim}")

if "local-tools/" not in ignore or "data/mobile-capture/" not in ignore:
    FAILURES.append("ADB tools or local mobile images are not gitignored")
tracked = subprocess.run(
    ["git", "ls-files"],
    cwd=ROOT,
    check=True,
    capture_output=True,
    text=True,
).stdout.splitlines()
for path in tracked:
    normalized = path.lower().replace("\\", "/")
    if normalized.endswith(("/adb", "/adb.exe")):
        FAILURES.append(f"ADB binary is tracked: {path}")

if FAILURES:
    print("FAIL")
    for failure in FAILURES:
        print(f"- {failure}")
    sys.exit(1)
print("PASS")
