# SRE Algorithm Foundation Report

Delivered: Template hardening, image backend and quality reports, fail-closed page normalization, TemplateProfile-driven ROI artifacts, conservative OMR metrics/candidates, synthetic benchmark, negative guards and automated audit.

Safety invariant: quality failure or page failure blocks downstream work; ROI failure blocks metrics; blank/weak/multi/erased marks go to review; candidate is not final answer and never writes grading outputs.

The benchmark acceptance gate is clean accuracy >= 0.98, blank false-positive <= 0.01, multi-mark review = 1.0 and wrong auto-accepted = 0.

## Final verification (2026-07-10)

- `python run_tests.py`: 1503 passed, 5 skipped.
- `python -m unittest discover`: 1490 passed, 5 skipped; a separate pre-existing 19-test nested suite is emitted outside `tests/student_recognition`.
- `python -m unittest discover -s tests/student_recognition`: one canonical result, 244 passed.
- Benchmark: PASS; clean single-choice accuracy 1.0, blank false-positive 0.0, weak/multi/erased review rates 1.0, wrong auto-accepted 0, p95 2.3052 ms.
- Algorithm audit: PASS_WITH_CAVEATS, with no critical/high finding. Caveat: no production certification for real-photo contour/perspective processing.

The former ambiguous `114 + N` student-recognition output was caused by a compatibility test starting a nested unittest runner. That nested runner has been removed; normal discovery now owns regression execution exactly once.
