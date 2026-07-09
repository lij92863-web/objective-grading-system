"""Minimal pure-standard-library raster canvas for synthetic answer sheets.

This module renders small RGB images using *only* the Python standard library
(no ``PIL`` / ``numpy`` -- constitution §1 B4 "zero new dependencies"). Pixels are
stored in a flat :class:`bytearray` (R,G,B interleaved, 0 = black, 255 = white).

It provides:

* :class:`Canvas` -- an in-memory RGB drawing surface with circle primitives and
  PNG / PPM encoders.
* :func:`read_png_bytes` -- a tiny PNG decoder (signature + IHDR + zlib IDAT)
  used by tests and the truthfulness guard to read pixels back without third
  party libraries.

The PNG encoder is intentionally minimal: 8-bit true-colour (colour type 2),
no filters, single IDAT chunk. This keeps the implementation auditable and the
produced files small (constitution: keep canvas <= 320x440 to control repo size).
"""

import struct
import zlib

__all__ = [
    "Canvas",
    "read_png_bytes",
    "read_png",
]

# PNG colour type 2 == truecolour (RGB), 8 bits per channel.
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_PNG_COLOUR_TYPE_RGB = 2
_PNG_BIT_DEPTH = 8


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Build a single PNG chunk: length + type + data + CRC32(type+data)."""
    body = chunk_type + data
    return (
        struct.pack(">I", len(data))
        + body
        + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    )


class Canvas:
    """An in-memory RGB canvas backed by a flat ``bytearray``.

    Pixels are stored as consecutive (R, G, B) bytes. Intensity helpers use a
    single 0..255 grey value applied equally to R/G/B, which is sufficient for
    synthetic pencil-mark sheets (white paper, dark graphite).
    """

    def __init__(self, width: int, height: int, background: int = 255) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Canvas width and height must be positive")
        self._width = int(width)
        self._height = int(height)
        self._buf = bytearray([max(0, min(255, int(background)))] * (self._width * self._height * 3))

    # ------------------------------------------------------------------ #
    # Basic accessors
    # ------------------------------------------------------------------ #
    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def _index(self, x: int, y: int) -> int:
        return (y * self._width + x) * 3

    def set_pixel(self, x: int, y: int, intensity: int) -> None:
        """Set the grey ``intensity`` (0 black .. 255 white) at (x, y).

        Out-of-bounds coordinates are silently ignored so callers can draw
        without clipping math.
        """
        xi = int(x)
        yi = int(y)
        if 0 <= xi < self._width and 0 <= yi < self._height:
            v = max(0, min(255, int(intensity)))
            idx = self._index(xi, yi)
            self._buf[idx] = v
            self._buf[idx + 1] = v
            self._buf[idx + 2] = v

    def get_pixel(self, x: int, y: int) -> int:
        """Return the red-channel intensity at (x, y); 255 if out of bounds."""
        xi = int(x)
        yi = int(y)
        if 0 <= xi < self._width and 0 <= yi < self._height:
            return self._buf[self._index(xi, yi)]
        return 255

    # ------------------------------------------------------------------ #
    # Drawing primitives
    # ------------------------------------------------------------------ #
    def draw_filled_circle(self, x: int, y: int, r: int, intensity: int) -> None:
        """Fill a solid disc centred at (x, y) with radius ``r``.

        Args:
            x, y: Centre coordinates.
            r: Radius in pixels.
            intensity: Grey value (0 = black graphite, 255 = white).
        """
        cx = int(x)
        cy = int(y)
        radius = int(r)
        if radius <= 0:
            return
        r2 = radius * radius
        for dy in range(-radius, radius + 1):
            yy = cy + dy
            if yy < 0 or yy >= self._height:
                continue
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= r2:
                    self.set_pixel(cx + dx, yy, intensity)

    def draw_circle_outline(self, x: int, y: int, r: int, intensity: int, thickness: int = 1) -> None:
        """Draw a hollow ring (bubble outline) centred at (x, y).

        Used to render empty option bubbles so they remain visible in the
        synthetic image without being classified as "filled".
        """
        cx = int(x)
        cy = int(y)
        radius = int(r)
        if radius <= 0:
            return
        t = max(1, int(thickness))
        inner2 = max(0, (radius - t) * (radius - t))
        outer2 = radius * radius
        for dy in range(-radius, radius + 1):
            yy = cy + dy
            if yy < 0 or yy >= self._height:
                continue
            for dx in range(-radius, radius + 1):
                d2 = dx * dx + dy * dy
                if inner2 <= d2 <= outer2:
                    self.set_pixel(cx + dx, yy, intensity)

    def clone(self) -> "Canvas":
        """Return a deep copy of this canvas."""
        other = Canvas(self._width, self._height, 255)
        other._buf = bytearray(self._buf)
        return other

    # ------------------------------------------------------------------ #
    # Encoding
    # ------------------------------------------------------------------ #
    def _raw_scanlines(self) -> bytes:
        """Return filter-byte-prefixed scanlines (filter 0 = none) for PNG IDAT."""
        stride = self._width * 3
        raw = bytearray()
        for y in range(self._height):
            raw.append(0)  # PNG filter type 0 (None)
            start = y * stride
            raw.extend(self._buf[start : start + stride])
        return bytes(raw)

    def to_png_bytes(self) -> bytes:
        """Encode the canvas as PNG bytes (no file I/O)."""
        ihdr = struct.pack(
            ">IIBBBBB",
            self._width,
            self._height,
            _PNG_BIT_DEPTH,
            _PNG_COLOUR_TYPE_RGB,
            0,  # compression
            0,  # filter
            0,  # interlace
        )
        idat = zlib.compress(self._raw_scanlines(), 9)
        return (
            _PNG_SIGNATURE
            + _png_chunk(b"IHDR", ihdr)
            + _png_chunk(b"IDAT", idat)
            + _png_chunk(b"IEND", b"")
        )

    def write_png(self, path: str) -> str:
        """Write the canvas to ``path`` as a PNG file. Returns ``path``."""
        data = self.to_png_bytes()
        with open(path, "wb") as fh:
            fh.write(data)
        return str(path)

    def to_ppm_bytes(self) -> bytes:
        """Encode the canvas as raw PPM (P6) bytes."""
        header = f"P6\n{self._width} {self._height}\n255\n".encode("ascii")
        return header + bytes(self._buf)

    def write_ppm(self, path: str) -> str:
        """Write the canvas to ``path`` as a PPM (P6) file. Returns ``path``."""
        data = self.to_ppm_bytes()
        with open(path, "wb") as fh:
            fh.write(data)
        return str(path)


# ---------------------------------------------------------------------- #
# Decoding (stdlib only) -- used by tests and the truthfulness guard.
# ---------------------------------------------------------------------- #
def read_png_bytes(data: bytes):
    """Decode minimal PNG ``data`` into ``(width, height, pixels)``.

    Args:
        data: Raw PNG file bytes.

    Returns:
        A tuple ``(width, height, pixels)`` where ``pixels`` is a flat
        ``bytearray`` of interleaved RGB bytes (same layout as :class:`Canvas`).

    Raises:
        ValueError: If the data is not a supported true-colour PNG.
    """
    if data[:8] != _PNG_SIGNATURE:
        raise ValueError("not a PNG file (bad signature)")
    pos = 8
    width = height = None
    bit_depth = colour_type = None
    idat = bytearray()
    while pos < len(data):
        if pos + 8 > len(data):
            break
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        pos += 4
        chunk_type = data[pos : pos + 4]
        pos += 4
        chunk_data = data[pos : pos + length]
        pos += length
        pos += 4  # skip CRC
        if chunk_type == b"IHDR":
            width, height, bit_depth, colour_type = struct.unpack(">IIBB", chunk_data[:10])
        elif chunk_type == b"IDAT":
            idat.extend(chunk_data)
        elif chunk_type == b"IEND":
            break
    if width is None or height is None:
        raise ValueError("PNG missing IHDR chunk")
    if colour_type != _PNG_COLOUR_TYPE_RGB or bit_depth != _PNG_BIT_DEPTH:
        raise ValueError("only 8-bit true-colour PNG is supported")
    raw = zlib.decompress(bytes(idat))
    stride = width * 3
    expected = (stride + 1) * height
    if len(raw) != expected:
        raise ValueError(f"PNG scanline byte count mismatch: {len(raw)} != {expected}")
    pixels = bytearray(width * height * 3)
    for y in range(height):
        src_start = y * (stride + 1) + 1  # skip per-row filter byte (0)
        dst_start = y * stride
        pixels[dst_start : dst_start + stride] = raw[src_start : src_start + stride]
    return width, height, pixels


def read_png(path: str):
    """Read a PNG file from ``path`` and return ``(width, height, pixels)``."""
    with open(path, "rb") as fh:
        return read_png_bytes(fh.read())
