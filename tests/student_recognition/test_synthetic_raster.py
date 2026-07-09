"""Tests for the pure-stdlib raster canvas and PNG/PPM codec."""

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from app.student_recognition.synthetic.raster import (
    Canvas,
    read_png_bytes,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestCanvasDrawing(unittest.TestCase):
    def test_draw_filled_circle_darkens_center(self):
        c = Canvas(40, 40)
        c.draw_filled_circle(20, 20, 8, 30)
        self.assertEqual(c.get_pixel(20, 20), 30)  # centre is dark
        self.assertEqual(c.get_pixel(0, 0), 255)    # corner is background

    def test_out_of_bounds_set_pixel_is_safe(self):
        c = Canvas(10, 10)
        # Should not raise.
        c.set_pixel(-5, -5, 0)
        c.set_pixel(100, 100, 0)
        self.assertEqual(c.get_pixel(0, 0), 255)

    def test_clone_is_independent(self):
        c = Canvas(10, 10)
        c.draw_filled_circle(5, 5, 3, 0)
        d = c.clone()
        d.draw_filled_circle(5, 5, 3, 200)
        self.assertEqual(c.get_pixel(5, 5), 0)   # original unchanged
        self.assertEqual(d.get_pixel(5, 5), 200)


class TestPngEncoding(unittest.TestCase):
    def _roundtrip(self, canvas: Canvas, tmp: Path):
        png_path = tmp / "sheet.png"
        canvas.write_png(str(png_path))
        data = png_path.read_bytes()
        # Signature
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        # IHDR dimensions
        # First chunk after signature: length(4) + 'IHDR'(4) + data(13)
        (ihdr_len,) = struct.unpack(">I", data[8:12])
        chunk_type = data[12:16]
        self.assertEqual(chunk_type, b"IHDR")
        self.assertEqual(ihdr_len, 13)
        w, h, bit_depth, colour_type = struct.unpack(">IIBB", data[16:26])
        self.assertEqual((w, h), (canvas.width, canvas.height))
        self.assertEqual(bit_depth, 8)
        self.assertEqual(colour_type, 2)  # truecolour RGB
        # Decode with stdlib zlib and verify total pixel byte count.
        width, height, pixels = read_png_bytes(data)
        self.assertEqual((width, height), (canvas.width, canvas.height))
        self.assertEqual(len(pixels), width * height * 3)
        return data

    def test_write_png_valid_and_readable(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            canvas = Canvas(64, 48)
            canvas.draw_filled_circle(32, 24, 10, 40)
            self._roundtrip(canvas, tmp)

    def test_drawn_pixel_is_reflected_in_decoded_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            canvas = Canvas(20, 20)
            canvas.draw_filled_circle(10, 10, 6, 20)
            png_path = tmp / "c.png"
            canvas.write_png(str(png_path))
            width, height, pixels = read_png_bytes(png_path.read_bytes())
            # centre pixel red channel should be the dark value we drew
            idx = (10 * width + 10) * 3
            self.assertEqual(pixels[idx], 20)
            # a far corner should be white
            idx2 = (0 * width + 0) * 3
            self.assertEqual(pixels[idx2], 255)


class TestPpmEncoding(unittest.TestCase):
    def test_write_ppm_header_and_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            canvas = Canvas(32, 24)
            canvas.draw_filled_circle(16, 12, 5, 10)
            ppm_path = tmp / "c.ppm"
            canvas.write_ppm(str(ppm_path))
            raw = ppm_path.read_bytes()
            header, _, rest = raw.partition(b"\n255\n")
            # header is "P6\n<w> <h>"
            lines = header.decode("ascii").split("\n")
            self.assertEqual(lines[0], "P6")
            w, h = map(int, lines[1].split())
            self.assertEqual((w, h), (32, 24))
            self.assertEqual(len(rest), w * h * 3)
            # centre pixel should be the dark value
            idx = (12 * w + 16) * 3
            self.assertEqual(rest[idx], 10)


if __name__ == "__main__":
    unittest.main()
