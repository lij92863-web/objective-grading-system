# Controlled Real Qwen Sample Preparation (R19)

## Preconditions (NONE met this round)
- Single anonymous image (no student name, ID, school)
- `QWEN_API_ENABLED=true` explicitly set
- API key available but never logged
- `max_real_api_calls=1` enforced

## Output Rules
- Only `raw_response_sanitized.json` — no base64, no API key
- No grading, no CSV/Excel/HTML reports
- No data/reports, no legacy

## Failure Rules
- Any failure → returncode non-zero
- No fallback to fake success
- Request ID logged for audit

## NOT done this round
- No real Qwen calls made
- All tests use fake/dry-run only
