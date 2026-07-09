"""Student Recognition Engine (SRE) package.

This package contains the student answer-sheet recognition engine. It is
governed by ``docs/student_recognition/SRE_GLOBAL_CONSTITUTION.md`` and must
never import ``app.workflow``, ``objective_grader`` or ``web_app`` (see the
constitution §1 B10 / §13).

Layers (strictly separated, see constitution §2):
    CaptureJob -> RecognitionDraft -> TeacherConfirmedSubmission -> OfficialGradingInput
"""

__version__ = "0.0.0"
__all__ = ["errors"]

from app.student_recognition import errors  # noqa: F401,E402  (re-export sub-package)
