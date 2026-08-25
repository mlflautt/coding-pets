from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

from PIL import Image, PngImagePlugin


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from generate_public_preview import pixels_match  # noqa: E402


def encoded_png(*, color: tuple[int, int, int, int], compress_level: int, note: str) -> bytes:
    image = Image.new("RGBA", (4, 3), color)
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("note", note)
    payload = io.BytesIO()
    image.save(payload, format="PNG", compress_level=compress_level, pnginfo=metadata)
    return payload.getvalue()


class PixelEquivalenceTests(unittest.TestCase):
    def test_accepts_different_png_encodings_with_identical_pixels(self) -> None:
        first = encoded_png(color=(14, 31, 48, 255), compress_level=0, note="windows")
        second = encoded_png(color=(14, 31, 48, 255), compress_level=9, note="linux")

        self.assertNotEqual(first, second)
        self.assertTrue(pixels_match(first, second))

    def test_rejects_a_visual_pixel_change(self) -> None:
        first = encoded_png(color=(14, 31, 48, 255), compress_level=0, note="first")
        second = encoded_png(color=(15, 31, 48, 255), compress_level=0, note="second")

        self.assertFalse(pixels_match(first, second))

    def test_rejects_invalid_image_bytes(self) -> None:
        valid = encoded_png(color=(14, 31, 48, 255), compress_level=0, note="valid")

        self.assertFalse(pixels_match(valid, b"not an image"))


if __name__ == "__main__":
    unittest.main()
