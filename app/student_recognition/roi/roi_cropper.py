"""Crop option cells exclusively through TemplateProfile query methods."""

import hashlib
from pathlib import Path

from app.student_recognition.image.backend import get_backend
from app.student_recognition.image.page_normalizer import NormalizedPageImage

from .roi_artifact import ROICropArtifact
from .roi_mapper import map_normalized_roi


def _write_pgm(path, image):
    header = f"P5\n{image.width} {image.height}\n255\n".encode("ascii")
    path.write_bytes(header + bytes(image.pixels))


def crop_option_cells(page: NormalizedPageImage, profile, output_dir):
    if page.location.status != "page_located":
        raise ValueError("page_location_failed")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    backend = get_backend()
    artifacts = []
    image_hash = hashlib.sha256(bytes(page.image.pixels)).hexdigest()
    template_ref = profile.get_template_ref().to_dict()
    for question_no in profile.list_questions():
        for cell in profile.get_option_cells(question_no):
            box = map_normalized_roi(
                cell.roi, page.image.width, page.image.height
            )
            crop = backend.crop(
                page.image, (box.x0, box.y0, box.x1, box.y1)
            )
            path = output_path / f"q{question_no}_{cell.option_label}.pgm"
            _write_pgm(path, crop)
            artifacts.append(
                ROICropArtifact(
                    question_no, cell.option_label, str(path),
                    box.x0, box.y0, box.x1, box.y1, crop.width, crop.height,
                    image_hash, dict(template_ref),
                )
            )
    return artifacts
