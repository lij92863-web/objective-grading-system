"""Run mobile capture counterfactual tests and client failure-control checks."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
FAILURES: list[str] = []

suite = unittest.defaultTestLoader.discover(
    str(ROOT / "tests" / "product"),
    pattern="test_mobile_capture_*.py",
)
result = unittest.TextTestRunner(verbosity=1).run(suite)
if not result.wasSuccessful():
    FAILURES.append("mobile capture counterfactual test suite failed")

javascript = (ROOT / "web/static/mobile_capture.js").read_text(encoding="utf-8")
for marker, description in (
    ("captureLocked", "double-click capture guard"),
    ("MAX_ATTEMPTS", "bounded retry policy"),
    ("RETRY_WAIT", "service-disconnect recovery state"),
    ("FAILED_MANUAL", "manual failure state"),
    ("item.blob = null", "blob removal only after acknowledgement"),
    ("response.status >= 400 && response.status < 500", "fail-closed client errors"),
):
    if marker not in javascript:
        FAILURES.append(f"missing client adversarial control: {description}")

controller = (ROOT / "app/web_product/product_app.py").read_text(encoding="utf-8")
for status in ("400", "404", "409", "413", "415", "500"):
    if status not in controller and status not in (
        ROOT / "app/capture/mobile_web_camera_source.py"
    ).read_text(encoding="utf-8"):
        FAILURES.append(f"mobile upload contract lacks HTTP {status}")

web_app = (ROOT / "web_app.py").read_text(encoding="utf-8")
if 'parsed.path == "/api/exams/grade"' not in web_app or "410" not in web_app:
    FAILURES.append("legacy grading bypass is not still retired with HTTP 410")

if FAILURES:
    print("mobile capture adversarial audit: FAIL")
    for failure in FAILURES:
        print(f"- {failure}")
    sys.exit(1)
print(f"mobile capture adversarial audit: PASS ({result.testsRun} tests)")
