# Controlled Recognition Pipeline Design (R15)

## Core Boundary
- **RecognitionDraft is NOT Submission** — AI output is a candidate, never final
- **Qwen judgment is NOT a final score** — it's an engine suggestion
- **Teacher confirmation is the hard boundary** between recognition and grading
- **Unconfirmed drafts NEVER enter grading**

## Pipeline Flow
```
ImageAsset → ImageQualityReport → AnswerSheetLayout → RecognitionRequestBatch
→ Fake/Qwen Engine → EngineCandidate → RecognitionDecision → RecognizedSubmissionDraft
→ TeacherConfirmation → TeacherConfirmedSubmission → CSV → grade_all
```

## Fake Runner vs Real Qwen
- **Fake runner**: uses fixture payloads, no network, deterministic output
- **Real Qwen**: requires explicit `--allow-real-api`, `QWEN_API_ENABLED=true`, max 1 call
- **Default**: dry-run, no real API

## Blocking Rules
- identity missing/conflict → blocking
- invalid option → blocking
- engine error → blocking
- layout missing required ROI → blocking
- image unsupported → blocking

## No-Real-API Policy
- `RealQwenClient` default disabled
- `QWEN_API_ENABLED` must be explicitly set
- No `.env` reading in tests
- No API key in logs or output

## Next: Controlled Single Real Qwen Sample
Prerequisites:
1. Anonymous single image
2. Explicit `--allow-real-api` flag
3. Sanitized output JSON only
4. No grading, no report generation
