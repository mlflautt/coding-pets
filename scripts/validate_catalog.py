#!/usr/bin/env python3
"""Validate catalogue paths and the core Codex v2 package contract."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_PET_FILES = (
    "pet.json",
    "spritesheet.webp",
    "preview.png",
    "hermes.md",
    "provenance.json",
    "concept-development/README.md",
    "qa/validation-extended.json",
    "qa/chroma-despill-extended.json",
    "qa/run-summary.json",
)
STATE_FRAME_COUNTS = {
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


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path.relative_to(ROOT)}: {exc}") from exc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_preview_config(pet_id: str, pet_dir: Path, errors: list[str]) -> None:
    config_path = pet_dir / "preview.json"
    if not config_path.is_file():
        return
    try:
        config = load_json(config_path)
    except ValueError as exc:
        errors.append(str(exc))
        return
    if config.get("previewVersion") != 1:
        errors.append(f"{pet_id}: previewVersion must be 1")
    if config.get("sourceAtlas") != "spritesheet.webp":
        errors.append(f"{pet_id}: preview sourceAtlas must be spritesheet.webp")
    if config.get("output") != "preview.png":
        errors.append(f"{pet_id}: preview output must be preview.png")
    poses = config.get("poses")
    if not isinstance(poses, list) or len(poses) != 3:
        errors.append(f"{pet_id}: preview poses must contain exactly three entries")
        return
    seen: set[tuple[str, int]] = set()
    for index, pose in enumerate(poses):
        if not isinstance(pose, dict):
            errors.append(f"{pet_id}: preview pose {index + 1} must be an object")
            continue
        state = pose.get("state")
        frame = pose.get("frame")
        if state not in STATE_FRAME_COUNTS:
            errors.append(f"{pet_id}: preview pose {index + 1} has invalid state {state!r}")
            continue
        if not isinstance(frame, int) or not 0 <= frame < STATE_FRAME_COUNTS[state]:
            errors.append(f"{pet_id}: preview pose {index + 1} has invalid frame {frame!r}")
            continue
        key = (state, frame)
        if key in seen:
            errors.append(f"{pet_id}: preview poses must be distinct")
        seen.add(key)


def main() -> int:
    errors: list[str] = []
    try:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: README.md: {exc}")
        return 1
    try:
        catalog = load_json(ROOT / "catalog.json")
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    if catalog.get("catalogVersion") != 1:
        errors.append("catalogVersion must be 1")
    pets = catalog.get("pets")
    if not isinstance(pets, list):
        errors.append("pets must be an array")
        pets = []

    seen: set[str] = set()
    for entry in pets:
        if not isinstance(entry, dict):
            errors.append("each catalogue entry must be an object")
            continue
        pet_id = entry.get("id", "")
        if not isinstance(pet_id, str) or not ID_RE.fullmatch(pet_id):
            errors.append(f"invalid pet id: {pet_id!r}")
            continue
        if pet_id in seen:
            errors.append(f"duplicate pet id: {pet_id}")
        seen.add(pet_id)

        pet_dir = ROOT / "pets" / pet_id
        expected_manifest = f"pets/{pet_id}/pet.json"
        expected_preview = f"pets/{pet_id}/preview.png"
        if entry.get("manifest") != expected_manifest:
            errors.append(f"{pet_id}: manifest must be {expected_manifest}")
        if entry.get("preview") != expected_preview:
            errors.append(f"{pet_id}: preview must be {expected_preview}")
        if expected_preview not in readme:
            errors.append(f"{pet_id}: README must display or link {expected_preview}")
        for relative in REQUIRED_PET_FILES:
            if not (pet_dir / relative).is_file():
                errors.append(f"{pet_id}: missing {relative}")

        for relative in (
            "qa/validation-extended.json",
            "qa/chroma-despill-extended.json",
            "qa/run-summary.json",
        ):
            report_path = pet_dir / relative
            if report_path.is_file():
                try:
                    report = load_json(report_path)
                    if report.get("ok") is not True:
                        errors.append(f"{pet_id}: {relative} must report ok: true")
                except ValueError as exc:
                    errors.append(str(exc))

        validation_path = pet_dir / "qa" / "validation-extended.json"
        if validation_path.is_file():
            try:
                validation = load_json(validation_path)
                if validation.get("width") != 1536 or validation.get("height") != 2288:
                    errors.append(f"{pet_id}: retained validation must report a 1536x2288 atlas")
                if validation.get("sprite_version_number") != 2:
                    errors.append(f"{pet_id}: retained validation must report sprite version 2")
                if validation.get("errors") != []:
                    errors.append(f"{pet_id}: retained validation errors must be empty")
            except ValueError as exc:
                errors.append(str(exc))

        validate_preview_config(pet_id, pet_dir, errors)

        provenance_path = pet_dir / "provenance.json"
        if provenance_path.is_file():
            try:
                provenance = load_json(provenance_path)
                asset_hash = provenance.get("assetSha256")
                if asset_hash and asset_hash.lower() != sha256(pet_dir / "spritesheet.webp"):
                    errors.append(f"{pet_id}: provenance assetSha256 does not match spritesheet.webp")
                preview_hash = provenance.get("previewSha256")
                if preview_hash and preview_hash.lower() != sha256(pet_dir / "preview.png"):
                    errors.append(f"{pet_id}: provenance previewSha256 does not match preview.png")
            except (OSError, ValueError) as exc:
                errors.append(str(exc))

        manifest_path = pet_dir / "pet.json"
        if manifest_path.is_file():
            try:
                manifest = load_json(manifest_path)
                if manifest.get("id") != pet_id:
                    errors.append(f"{pet_id}: pet.json id does not match")
                if manifest.get("spriteVersionNumber") != 2:
                    errors.append(f"{pet_id}: spriteVersionNumber must be 2")
                if manifest.get("spritesheetPath") != "spritesheet.webp":
                    errors.append(f"{pet_id}: spritesheetPath must be spritesheet.webp")
            except ValueError as exc:
                errors.append(str(exc))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"OK: {len(pets)} pet(s) validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
