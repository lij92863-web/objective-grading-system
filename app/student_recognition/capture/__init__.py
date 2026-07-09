"""Capture layer: ingest, validate and persist raw answer-sheet images.

Responsibilities (constitution §2 / §13): receive image bytes, compute sha256,
persist to the fixed tree, record events. This layer does NOT recognize answers
and does NOT grade. It must not import ``omr`` or ``grading_bridge``.
"""
