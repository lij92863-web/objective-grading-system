"""Synthetic-safe PNG/PPM image loading; no third-party dependency."""
from pathlib import Path
from .image_types import ImageMatrix

def load_image(path)->ImageMatrix:
    path=Path(path); raw=path.read_bytes()
    if raw.startswith(b"\x89PNG"):
        from app.student_recognition.synthetic.raster import read_png_bytes
        w,h,rgb=read_png_bytes(raw); gray=tuple((rgb[i]+rgb[i+1]+rgb[i+2])//3 for i in range(0,len(rgb),3)); return ImageMatrix(w,h,gray)
    if raw.startswith(b"P6"):
        header,pixels=raw.split(b"\n255\n",1); lines=header.splitlines(); w,h=map(int,lines[-1].split()); gray=tuple((pixels[i]+pixels[i+1]+pixels[i+2])//3 for i in range(0,len(pixels),3)); return ImageMatrix(w,h,gray)
    raise ValueError("unsupported image format")
