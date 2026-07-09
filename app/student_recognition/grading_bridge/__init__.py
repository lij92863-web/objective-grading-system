"""Grading bridge: the dual-gate boundary between draft and official grading.

Responsibilities (constitution §2 / §10 / B3): ``grading_gate`` implements the
two gates that a ``RecognitionDraft`` MUST pass before any ``OfficialGradingInput``
is produced. Even in this skeleton phase the refuse branches are written dead:
a raw draft can never become official input.
"""
