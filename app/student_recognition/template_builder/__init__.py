"""SRE945 Template Builder package -- calibration levels (L0/L1/L2).

* **Level 0**: pure JSON template IO / validation (``level0_json``).
* **Level 1**: headless calibration from synthetic templates or explicit
  anchors + grids (``calibrator``).
* **Level 2**: interactive visual calibrator *interface* only -- no UI
  implementation in this stage (``level2_interface``).

This package contains no OMR / image / grading / web_app logic (constitution
B10 / §13).
"""

from app.student_recognition.template_builder.calibrator import (
    Calibrator,
    FOUR_CORNER,
    GRID_ORIGIN,
)
from app.student_recognition.template_builder.level0_json import (
    build_profile_from_json,
    load_template_json,
    save_template_json,
    validate_template_json,
)
from app.student_recognition.template_builder.level2_interface import VisualCalibrator

__all__ = [
    "Calibrator",
    "GRID_ORIGIN",
    "FOUR_CORNER",
    "load_template_json",
    "validate_template_json",
    "build_profile_from_json",
    "save_template_json",
    "VisualCalibrator",
]
