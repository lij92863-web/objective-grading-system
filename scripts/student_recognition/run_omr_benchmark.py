"""Run the synthetic OMR benchmark from the repository root or any cwd."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.student_recognition.benchmark import run_benchmark


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus", default="tests/student_recognition/fixtures/synthetic"
    )
    parser.add_argument(
        "--out", default="data/student_recognition/benchmark"
    )
    arguments = parser.parse_args()
    report, _failures = run_benchmark(arguments.corpus, arguments.out)
    print(report)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
