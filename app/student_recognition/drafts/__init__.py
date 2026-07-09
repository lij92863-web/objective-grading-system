"""Draft layer: recognition candidates, fusion and validation.

Responsibilities (constitution §2 / §13): consume capture artifacts, hold OMR /
identity *candidates*, fuse multiple candidates, and validate them into
``blocking_errors`` (ErrorCode) + ``review_items`` (ErrorCode reason_code).
Drafts are candidates only and MUST NOT write ``submissions.csv`` or generate an
official report.
"""
