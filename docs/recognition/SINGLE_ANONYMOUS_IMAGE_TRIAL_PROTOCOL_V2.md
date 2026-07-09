# Single Anonymous Image Trial Protocol V2

Steps:

1. Prepare one anonymous image.
2. Confirm it has no real name, student number, school, class, exam number, or real score.
3. Create a manifest.
4. Manually mark ROI JSON.
5. Run `validate_single_image_manifest.py`.
6. Run `validate_manual_roi.py`.
7. Run `run_single_image_dry_run.py`.
8. Run `check_single_image_qwen_readiness.py --check-only`.
9. Only after every check passes may the next stage consider one explicit `--allow-real-api` trial.
10. That future real API trial is still single-image only.
11. Audit sanitized output.
12. Audit parser candidates.
13. Audit review queue.
14. Do not enter formal grading.
15. Do not generate formal reports.

Single-image success is not small-batch readiness.
