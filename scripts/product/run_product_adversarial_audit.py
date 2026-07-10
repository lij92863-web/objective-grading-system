"""Executable attack suite for capture, review and finalization bypasses."""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
tests = (
    "tests.product.test_capture_sources",
    "tests.product.test_product_pipeline",
    "tests.product.test_review_workflow",
    "tests.product.test_finalization_gate",
    "tests.product.test_web_product_workflow",
)
result = subprocess.run(
    [sys.executable, "-m", "unittest", *tests],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=False,
)
if result.returncode:
    print(result.stdout)
    print(result.stderr)
    print("FAIL")
    raise SystemExit(result.returncode)
print("PASS")
