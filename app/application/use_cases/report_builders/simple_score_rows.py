"""Task-named entry for simple score rows.

The implementation lives in ``score_rows`` from the earlier report-builder
migration; this module gives the L3 migration an explicit stable import path.
"""

from .score_rows import build_simple_score_rows


__all__ = ["build_simple_score_rows"]
