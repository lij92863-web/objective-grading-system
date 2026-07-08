"""Application layer — use cases and workflow orchestration.

This layer coordinates domain services (grading, recognition) with
infrastructure (import/export/storage) to fulfil teacher workflows.

Do NOT put raw HTTP, file I/O, or UI logic here — those belong in
infrastructure or presentation layers.
"""
