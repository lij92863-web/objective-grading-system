"""Cropper consumes TemplateProfile query methods; it never parses template JSON."""
from pathlib import Path
from app.student_recognition.image.backend import get_backend
from app.student_recognition.image.page_normalizer import NormalizedPageImage
from .roi_mapper import map_normalized_roi
from .roi_artifact import ROICropArtifact

def _write_pgm(path,image): path.write_bytes(f"P5\n{image.width} {image.height}\n255\n".encode("ascii")+bytes(image.pixels))
def crop_option_cells(page:NormalizedPageImage,profile,output_dir):
    if page.location.status!="page_located": raise ValueError("page_location_failed")
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); backend=get_backend(); artifacts=[]
    for q in profile.list_questions():
        for cell in profile.get_option_cells(q):
            b=map_normalized_roi(cell.roi,page.image.width,page.image.height); crop=backend.crop(page.image,(b.x0,b.y0,b.x1,b.y1))
            path=out/f"q{q}_{cell.option_label}.pgm"; _write_pgm(path,crop)
            artifacts.append(ROICropArtifact(q,cell.option_label,str(path),b.x0,b.y0,b.x1,b.y1,crop.width,crop.height))
    return artifacts
