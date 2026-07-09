# Stage AE001-AE120 Summary

Start commit: 07dd3d7 feat harden controlled single qwen trial gate

End commit: pending until final commit

Push: pending

Added modules:

- `app/answer_extraction` DocumentModel, DOCX parser, classifiers, student grid detector, table and itemized extractors, question index, aligner, validator, strategy router, extraction engine, report, review item, and LLM fallback stub.
- `scripts/extract_answer_key.py`
- `scripts/classify_paper_files.py`
- `scripts/run_local_answer_extraction_smoke.py`

Four strategy links:

- same file plus boxed answer table: available with synthetic fixture
- same file plus itemized answers: available with synthetic fixture
- split files plus boxed answer table: available with synthetic fixture
- split files plus itemized answers: available with synthetic fixture

Local real sample smoke: skipped when `local-test-materials/answer-extraction-samples/` is missing.

Safety boundaries: no real API call, no `.env` read, no grading/workflow/web integration, no dependency file changes, and no formal score report generation.

Test results: pending final run.

Current unavailable links: production UI integration, grading integration, real student answer-card photo recognition, and real Qwen fallback.

Next step: add controlled real teacher DOCX samples locally, run smoke, and use review output to refine heuristics without widening integration boundaries.
