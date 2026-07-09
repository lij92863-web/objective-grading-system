# Stage C13 — COMPAT_EXPORTS Shrink Report

## Decision: No shrink this round

After safety scan, all 125 COMPAT_EXPORTS symbols are retained.

### Reasons
- Category E symbols (internal helpers) are not zero-reference — they're still used by tests and compat exports
- Category A symbols are kept for compatibility with external scripts
- Category F public API symbols must be kept
- Premature removal risks breaking old import paths

### Recommendation
Shrink in a dedicated round after baseline tests are replaced with fixture-based equivalents.
