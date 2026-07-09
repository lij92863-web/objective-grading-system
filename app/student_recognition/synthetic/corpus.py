"""Corpus orchestration: build many synthetic sheets from one template.

This module defines the *spec* vocabulary for a batch of sheets and helpers to
turn a spec into a concrete :class:`GroundTruth`. The actual rendering is delegated
to :class:`~app.student_recognition.synthetic.generator.SyntheticSheetGenerator`.

:func:`default_corpus_spec` returns a small but representative set (clean + every
perturbation + every mark type) used by the generator script and exercised by the
truthfulness guard.
"""

import random
from typing import Any, Dict, List, Tuple

from app.student_recognition.synthetic.ground_truth import AnswerRecord, GroundTruth
from app.student_recognition.synthetic.template_profile import TemplateProfile

__all__ = [
    "default_corpus_spec",
    "build_ground_truth",
]

# (perturbation_name, mark_pattern_kind) tuples. Cycled to reach ``count`` sheets.
_BASE_SPECS: List[Tuple[str, str]] = [
    ("clean", "all_strong"),
    ("clean", "all_weak"),
    ("clean", "all_multi"),
    ("clean", "all_erased"),
    ("clean", "mixed"),
    ("skew_x", "all_strong"),
    ("rotate_small", "all_strong"),
    ("box_blur", "all_strong"),
    ("add_gaussian_noise", "all_strong"),
    ("contrast", "all_strong"),
    ("shift", "all_strong"),
    ("skew_x", "mixed"),
    ("rotate_small", "mixed"),
    ("box_blur", "all_multi"),
    ("contrast", "all_erased"),
    ("shift", "all_multi"),
]


def _pattern_for(kind: str, n: int) -> List[str]:
    """Return a list of ``n`` mark types for the given pattern kind."""
    if kind == "all_strong":
        return ["strong"] * n
    if kind == "all_weak":
        return ["weak"] * n
    if kind == "all_multi":
        return ["multi"] * n
    if kind == "all_erased":
        return ["erased"] * n
    if kind == "mixed":
        base = ["strong", "weak", "multi", "erased", "none"]
    elif kind == "multi_weak_mix":
        base = ["multi", "weak", "strong", "erased", "none"]
    else:
        base = ["strong"]
    repeats = (n // len(base)) + 1
    return (base * repeats)[:n]


def default_corpus_spec(template: TemplateProfile, count: int = 16, seed: int = 12345) -> List[Dict[str, Any]]:
    """Return ``count`` sheet specifications covering clean + all perturbations.

    Each spec is a plain dict consumed by :func:`build_ground_truth` and the
    generator script:

    ``{"sheet_id", "seed", "perturbation", "student", "pattern", "expected"}``

    Args:
        template: The template whose geometry / option labels define the grid.
        count: Number of sheets to produce (default 16).
        seed: Base seed; each sheet gets ``seed + index * 7919`` for variety.
    """
    labels = list(template.bubble_grid["option_labels"])
    n = int(template.bubble_grid["rows"])
    base_n = len(_BASE_SPECS)
    specs: List[Dict[str, Any]] = []
    for i in range(count):
        perturbation, kind = _BASE_SPECS[i % base_n]
        pattern = _pattern_for(kind, n)
        # Deterministic "expected" answer key (unrelated to the student's marks).
        expected = [labels[(q * 7 + i) % len(labels)] for q in range(n)]
        sheet_id = f"sheet-{i:03d}"
        if i % 2 == 0:
            student: Dict[str, str] = {
                "student_id": f"2024{i:04d}",
                "name": f"学生{i:02d}",
            }
        else:
            student = {"name": f"无名{i:02d}"}
        specs.append(
            {
                "sheet_id": sheet_id,
                "seed": seed + i * 7919,
                "perturbation": perturbation,
                "student": student,
                "pattern": pattern,
                "expected": expected,
            }
        )
    return specs


def build_ground_truth(spec: Dict[str, Any], template: TemplateProfile) -> GroundTruth:
    """Build a :class:`GroundTruth` from a spec produced by :func:`default_corpus_spec`."""
    labels = list(template.bubble_grid["option_labels"])
    answers: List[AnswerRecord] = []
    for q, mark_type in enumerate(spec["pattern"]):
        selected = None if mark_type == "none" else labels[q % len(labels)]
        answers.append(
            AnswerRecord(
                question=q,
                selected=selected,
                mark_type=mark_type,
                expected_option=spec["expected"][q],
            )
        )
    return GroundTruth(
        sheet_id=spec["sheet_id"],
        template_id=template.template_id,
        student=dict(spec["student"]),
        answers=answers,
        perturbation=spec["perturbation"],
        seed=spec["seed"],
    )
