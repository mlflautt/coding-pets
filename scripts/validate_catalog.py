#!/usr/bin/env python3
"""Validate catalogue paths and the core Codex v2 package contract."""

from __future__ import annotations

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
    "qa/validation-extended.json",
    "qa/chroma-despill-extended.json",
    "qa/run-summary.json",
)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path.relative_to(ROOT)}: {exc}") from exc


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
