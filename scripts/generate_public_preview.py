#!/usr/bin/env python3
"""Generate a reproducible three-pose public preview from a shipped Codex v2 atlas."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw


ATLAS_SIZE = (1536, 2288)
CELL_SIZE = (192, 208)
STATE_ROWS = {
    "idle": 0,
    "running-right": 1,
    "running-left": 2,
    "waving": 3,
    "jumping": 4,
    "failed": 5,
    "waiting": 6,
    "running": 7,
    "review": 8,
    "look-row-9": 9,
    "look-row-10": 10,
}
FRAME_COUNTS = {
    "idle": 7,
    "running-right": 8,
    "running-left": 8,
    "waving": 4,
    "jumping": 5,
    "failed": 8,
    "waiting": 6,
    "running": 6,
    "review": 6,
    "look-row-9": 8,
    "look-row-10": 8,
}


class PreviewError(ValueError):
    """Raised when a preview configuration or source atlas is invalid."""


def pixels_match(first: bytes, second: bytes) -> bool:
    """Return whether two encoded images contain the same rendered RGBA pixels."""
    try:
        with Image.open(io.BytesIO(first)) as first_image:
            first_rgba = first_image.convert("RGBA")
            first_rgba.load()
        with Image.open(io.BytesIO(second)) as second_image:
            second_rgba = second_image.convert("RGBA")
            second_rgba.load()
    except OSError:
        return False
    return first_rgba.size == second_rgba.size and first_rgba.tobytes() == second_rgba.tobytes()


def resolve_inside(base: Path, relative: str, field: str) -> Path:
    candidate = (base / relative).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError as exc:
        raise PreviewError(f"{field} must stay inside {base}") from exc
    return candidate


def load_config(path: Path) -> dict:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreviewError(f"unable to read {path}: {exc}") from exc
    if config.get("previewVersion") != 1:
        raise PreviewError("previewVersion must be 1")
    poses = config.get("poses")
    if not isinstance(poses, list) or len(poses) != 3:
        raise PreviewError("poses must contain exactly three entries")
    return config


def validate_pose(pose: object, index: int) -> tuple[str, int]:
    if not isinstance(pose, dict):
        raise PreviewError(f"pose {index + 1} must be an object")
    state = pose.get("state")
    frame = pose.get("frame")
    if state not in STATE_ROWS:
        raise PreviewError(f"pose {index + 1} has unsupported state {state!r}")
    if not isinstance(frame, int) or not 0 <= frame < FRAME_COUNTS[state]:
        raise PreviewError(
            f"pose {index + 1} frame must be between 0 and {FRAME_COUNTS[state] - 1}"
        )
    return state, frame


def gradient_background(width: int, height: int, top: str, bottom: str) -> Image.Image:
    top_rgb = ImageColor.getrgb(top)
    bottom_rgb = ImageColor.getrgb(bottom)
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    denominator = max(height - 1, 1)
    for y in range(height):
        ratio = y / denominator
        color = tuple(round(a + (b - a) * ratio) for a, b in zip(top_rgb, bottom_rgb))
        draw.line((0, y, width, y), fill=color)
    return image


def render(config_path: Path) -> tuple[Path, bytes, list[str]]:
    config = load_config(config_path)
    base = config_path.resolve().parent
    atlas_path = resolve_inside(base, config.get("sourceAtlas", "spritesheet.webp"), "sourceAtlas")
    output_path = resolve_inside(base, config.get("output", "preview.png"), "output")

    canvas = config.get("canvas", {})
    if not isinstance(canvas, dict):
        raise PreviewError("canvas must be an object")
    width = canvas.get("width", 1800)
    height = canvas.get("height", 720)
    if not isinstance(width, int) or not isinstance(height, int) or width < 900 or height < 360:
        raise PreviewError("canvas width and height must be integers of at least 900x360")
    if width % 3:
        raise PreviewError("canvas width must be divisible by three")

    top = canvas.get("backgroundTop", "#031411")
    bottom = canvas.get("backgroundBottom", "#071F1B")
    resampling_name = config.get("resampling", "lanczos")
    resampling = {
        "lanczos": Image.Resampling.LANCZOS,
        "nearest": Image.Resampling.NEAREST,
    }.get(resampling_name)
    if resampling is None:
        raise PreviewError("resampling must be 'lanczos' or 'nearest'")

    try:
        atlas = Image.open(atlas_path).convert("RGBA")
    except OSError as exc:
        raise PreviewError(f"unable to open atlas {atlas_path}: {exc}") from exc
    if atlas.size != ATLAS_SIZE:
        raise PreviewError(f"atlas must be {ATLAS_SIZE[0]}x{ATLAS_SIZE[1]}, got {atlas.size}")

    result = gradient_background(width, height, top, bottom)
    slot_width = width // 3
    horizontal_padding = max(12, slot_width // 40)
    vertical_padding = max(24, height // 16)
    scale = min(
        (slot_width - 2 * horizontal_padding) / CELL_SIZE[0],
        (height - 2 * vertical_padding) / CELL_SIZE[1],
    )
    scaled_size = (round(CELL_SIZE[0] * scale), round(CELL_SIZE[1] * scale))
    pose_labels: list[str] = []

    for index, raw_pose in enumerate(config["poses"]):
        state, frame = validate_pose(raw_pose, index)
        row = STATE_ROWS[state]
        left = frame * CELL_SIZE[0]
        top_px = row * CELL_SIZE[1]
        cell = atlas.crop((left, top_px, left + CELL_SIZE[0], top_px + CELL_SIZE[1]))
        if cell.getbbox() is None:
            raise PreviewError(f"pose {index + 1} ({state}:{frame}) is empty")
        cell = cell.resize(scaled_size, resample=resampling)
        x = index * slot_width + (slot_width - scaled_size[0]) // 2
        y = (height - scaled_size[1]) // 2
        result.paste(cell, (x, y), cell)
        pose_labels.append(f"{state}:{frame}")

    payload = io.BytesIO()
    result.save(payload, format="PNG", optimize=True)
    return output_path, payload.getvalue(), pose_labels


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Path to a pet preview.json configuration")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that the committed preview matches a fresh render without writing it",
    )
    args = parser.parse_args()

    try:
        output_path, payload, poses = render(args.config)
    except PreviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.check:
        try:
            existing = output_path.read_bytes()
        except OSError as exc:
            print(f"ERROR: unable to read {output_path}: {exc}", file=sys.stderr)
            return 1
        if not pixels_match(existing, payload):
            print(f"ERROR: {output_path} is not reproducible from {args.config}", file=sys.stderr)
            return 1
        digest = hashlib.sha256(existing).hexdigest()
        encoding_note = "exact encoding" if existing == payload else "pixel-equivalent encoding"
        print(
            f"OK: {output_path} matches {args.config} "
            f"({', '.join(poses)}; {encoding_note}; sha256={digest})"
        )
        return 0

    digest = hashlib.sha256(payload).hexdigest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)
    print(f"OK: wrote {output_path} ({', '.join(poses)}; sha256={digest})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
