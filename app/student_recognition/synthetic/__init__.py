"""Synthetic answer-sheet generator package (SRE121-220).

This package is a pure *upstream data factory*: it renders synthetic answer
sheets (and their ground truth) for downstream testing/benchmarking. It does NOT
perform OMR, image correction, recognition, or grading, and it does not import
any forbidden module (constitution §1 B4/B10, boundary lock for this stage).

Public API:
    from app.student_recognition.synthetic import (
        Canvas, TemplateProfile, GroundTruth, SyntheticSheetGenerator,
        default_corpus_spec, build_ground_truth,
    )
"""

from app.student_recognition.synthetic.generator import SyntheticSheetGenerator
from app.student_recognition.synthetic.ground_truth import (
    AnswerRecord,
    GroundTruth,
    MARK_TYPES,
)
from app.student_recognition.synthetic.perturbations import (
    PERTURBATION_NAMES,
    add_gaussian_noise,
    box_blur,
    contrast,
    inject_erased_mark,
    inject_multi_mark,
    inject_weak_mark,
    rotate_small,
    shift,
    skew_x,
)
from app.student_recognition.synthetic.raster import Canvas, read_png, read_png_bytes
from app.student_recognition.synthetic.template_profile import (
    SCHEMA_VERSION,
    SyntheticProfileError,
    TemplateProfile,
    build_default_template,
)
from app.student_recognition.synthetic.corpus import (
    build_ground_truth,
    default_corpus_spec,
)

__all__ = [
    "Canvas",
    "TemplateProfile",
    "SyntheticProfileError",
    "build_default_template",
    "SCHEMA_VERSION",
    "GroundTruth",
    "AnswerRecord",
    "MARK_TYPES",
    "SyntheticSheetGenerator",
    "skew_x",
    "rotate_small",
    "box_blur",
    "add_gaussian_noise",
    "contrast",
    "shift",
    "inject_weak_mark",
    "inject_multi_mark",
    "inject_erased_mark",
    "PERTURBATION_NAMES",
    "read_png",
    "read_png_bytes",
    "default_corpus_spec",
    "build_ground_truth",
]
