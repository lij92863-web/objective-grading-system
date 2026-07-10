# SRE481 Identity Architecture

Responsibility: parse manual/fake identity text, exact-match roster records and issue typed decisions. Inputs are sanitized text candidates and an in-memory roster; outputs are confirmed, needs_review or blocked decisions with ErrorCode reasons. It depends only on errors and the legacy identity contract. OCR/Qwen, grading and web are forbidden.

Missing, conflict, unknown id and duplicate are blocking; name-only and fake-source candidates require review. Exact manual id+name may confirm. Evidence and future teacher corrections are append-only extension points. Fuzzy matching is intentionally unsupported to prevent identity drift.
