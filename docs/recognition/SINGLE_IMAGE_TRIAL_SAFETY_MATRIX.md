# Single Image Trial Safety Matrix

| Risk | Guard | Test | Expected behavior | Status |
| --- | --- | --- | --- | --- |
| non-anonymous image | manifest validator | `tests/test_single_image_manifest.py` | blocked | pass |
| real student data | manifest validator | `tests/test_single_image_manifest.py` | blocked | pass |
| missing ROI | dry-run/context | `tests/test_single_image_dry_run.py` | blocked | pass |
| missing identity ROI | ROI validator/context | `tests/test_manual_roi_schema.py` | blocked | pass |
| invalid ROI bounds | ROI validator | `tests/test_validate_manual_roi_cli.py` | blocked | pass |
| accidental real API call | check-only wrapper | `tests/test_single_image_no_real_api_guard.py` | no API path | pass |
| raw response saved | trial report model | `tests/test_single_image_trial_report.py` | false | pass |
| base64 output | manifest/report guards | `tests/test_single_image_cli_output_safety.py` | absent | pass |
| data/tmp commit | artifact guard | `tests/test_single_image_artifact_guard.py` | no tracked files | pass |
| formal report generation | script scan | `tests/test_single_image_no_formal_report_guard.py` | forbidden | pass |
| direct grade_all | script scan | `tests/test_single_image_no_formal_report_guard.py` | forbidden | pass |
| workflow import | script scan | `tests/test_single_image_no_formal_report_guard.py` | forbidden | pass |
