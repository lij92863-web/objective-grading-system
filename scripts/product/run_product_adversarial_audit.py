"""Adversarial regression audit for product policy and publication bypasses."""

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
tests = (
    "tests.product.test_manual_score_policy",
    "tests.product.test_review_workflow",
    "tests.product.test_finalization_gate",
    "tests.product.test_product_workflow_benchmark",
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
    print("adversarial regression audit: FAIL")
    raise SystemExit(result.returncode)
print("adversarial regression audit: PASS")
