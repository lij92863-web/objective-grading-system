# Real DOCX Smoke Guide

Local real teacher samples are optional and must stay outside git:

`local-test-materials/answer-extraction-samples/`

Run:

```powershell
python scripts/run_local_answer_extraction_smoke.py --json
```

The script prints JSON to stdout only. It does not write reports or artifacts.

If the directory is missing, the result is `status: skipped`. If files exist, each case reports strategy, status, counts, missing answers, unexpected answers, blocking errors, review items, warnings, and a small evidence sample.

Synthetic DOCX smoke is always available:

```powershell
python scripts/run_answer_extraction_synthetic_docx_smoke.py --json
```
