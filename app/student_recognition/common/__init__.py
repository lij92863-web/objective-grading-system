"""Common low-level utilities for the Student Recognition Engine.

These helpers are dependency-free (they never import business modules) and are
shared across capture / drafts / review / pipeline layers. They enforce the
constitution's hard boundaries around persistence (§4), atomic writes (§4),
idempotency (§6) and privacy (no base64 in manifests, §12).
"""
