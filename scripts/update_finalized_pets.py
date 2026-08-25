#!/usr/bin/env python3
"""Refresh derived catalogue assets for finalized, auto-published pet packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from generate_public_preview import PreviewError, pixels_match, render


ROOT = Path(__file__).resolve().parents[1]
PETS_ROOT = ROOT / "pets"
CATALOG_PATH = ROOT / "catalog.json"
README_PATH = ROOT / "README.md"
BEGIN_MARKER = "<!-- BEGIN AUTO-PUBLISHED PETS -->"
END_MARKER = "<!-- END AUTO-PUBLISHED PETS -->"


class UpdateError(ValueError):
    """Raised when an auto-published package is incomplete or inconsistent."""


@dataclass(frozen=True)
class ManagedPet:
    pet_id: str
    directory: Path
    manifest: dict
    catalog: dict
    provenance: dict
    preview_bytes: bytes
    preview_path: Path


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UpdateError(f"{path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise UpdateError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise UpdateError(f"unable to hash {path.relative_to(ROOT)}: {exc}") from exc
    return digest.hexdigest()


def discover() -> tuple[list[ManagedPet], set[str]]:
    managed: list[ManagedPet] = []
    withdrawn: set[str] = set()
    for manifest_path in sorted(PETS_ROOT.glob("*/pet.json")):
        manifest = load_json(manifest_path)
        catalog = manifest.get("catalog")
        if not isinstance(catalog, dict) or catalog.get("autoPublish") is not True:
            continue

        directory = manifest_path.parent
        pet_id = manifest.get("id")
        if pet_id != directory.name:
            raise UpdateError(f"{manifest_path.relative_to(ROOT)} id must match its directory")
        if catalog.get("status") != "published":
            withdrawn.add(pet_id)
            continue
        for field in ("displayName", "description", "license"):
            if not isinstance(manifest.get(field), str) or not manifest[field].strip():
                raise UpdateError(f"{pet_id}: pet.json requires non-empty {field}")
        if manifest.get("spriteVersionNumber") != 2:
            raise UpdateError(f"{pet_id}: spriteVersionNumber must be 2")
        tags = catalog.get("tags")
        if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) and tag for tag in tags):
            raise UpdateError(f"{pet_id}: catalog.tags must be a non-empty string array")
        order = catalog.get("readmeOrder")
        if not isinstance(order, int) or order < 0:
            raise UpdateError(f"{pet_id}: catalog.readmeOrder must be a non-negative integer")

        atlas_path = directory / "spritesheet.webp"
        preview_config = directory / "preview.json"
        provenance_path = directory / "provenance.json"
        for required in (atlas_path, preview_config, provenance_path):
            if not required.is_file():
                raise UpdateError(f"{pet_id}: missing {required.relative_to(directory)}")
        try:
            preview_path, preview_bytes, _poses = render(preview_config)
        except PreviewError as exc:
            raise UpdateError(f"{pet_id}: {exc}") from exc
        if preview_path != (directory / "preview.png").resolve():
            raise UpdateError(f"{pet_id}: preview.json output must resolve to preview.png")

        managed.append(ManagedPet(
            pet_id=pet_id,
            directory=directory,
            manifest=manifest,
            catalog=catalog,
            provenance=load_json(provenance_path),
            preview_bytes=preview_bytes,
            preview_path=preview_path,
        ))
    return (
        sorted(managed, key=lambda pet: (pet.catalog["readmeOrder"], pet.pet_id)),
        withdrawn,
    )


def desired_catalog_entry(pet: ManagedPet) -> dict:
    return {
        "id": pet.pet_id,
        "displayName": pet.manifest["displayName"],
        "description": pet.manifest["description"],
        "status": "published",
        "license": pet.manifest["license"],
        "manifest": f"pets/{pet.pet_id}/pet.json",
        "preview": f"pets/{pet.pet_id}/preview.png",
        "tags": pet.catalog["tags"],
        "derivedFrom": pet.provenance.get("derivedFrom"),
    }


def updated_catalog(catalog: dict, managed: list[ManagedPet], withdrawn: set[str]) -> dict:
    entries = catalog.get("pets")
    if not isinstance(entries, list):
        raise UpdateError("catalog.json pets must be an array")
    result = [
        entry
        for entry in entries
        if not (isinstance(entry, dict) and entry.get("id") in withdrawn)
    ]
    indexes = {
        entry.get("id"): index
        for index, entry in enumerate(result)
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    for pet in managed:
        desired = desired_catalog_entry(pet)
        index = indexes.get(pet.pet_id)
        if index is None:
            indexes[pet.pet_id] = len(result)
            result.append(desired)
        else:
            result[index] = desired
    return {**catalog, "pets": result}


def readme_card(pet: ManagedPet) -> str:
    name = pet.manifest["displayName"]
    pet_id = pet.pet_id
    alt = pet.catalog.get("previewAlt", f"{name} public preview")
    width = pet.catalog.get("readmeWidth", 720)
    if not isinstance(alt, str) or not alt.strip():
        raise UpdateError(f"{pet_id}: catalog.previewAlt must be a non-empty string")
    if not isinstance(width, int) or width < 240 or width > 1200:
        raise UpdateError(f"{pet_id}: catalog.readmeWidth must be between 240 and 1200")
    return (
        f"### {name}\n\n"
        f"[<img src=\"pets/{pet_id}/preview.png\" width=\"{width}\" alt=\"{alt}\">]"
        f"(pets/{pet_id}/preview.png)\n\n"
        f"{pet.manifest['description']}\n\n"
        f"[Character and motion guide](pets/{pet_id}/hermes.md) · "
        f"[Codex manifest](pets/{pet_id}/pet.json) · "
        f"[QA evidence](pets/{pet_id}/qa/)"
    )


def updated_readme(readme: str, managed: list[ManagedPet]) -> str:
    begin = readme.find(BEGIN_MARKER)
    end = readme.find(END_MARKER)
    if begin < 0 or end < 0 or end < begin:
        raise UpdateError("README.md is missing the auto-published pet markers")
    end += len(END_MARKER)
    cards = "\n\n".join(readme_card(pet) for pet in managed)
    block = f"{BEGIN_MARKER}\n\n{cards}\n\n{END_MARKER}"
    return readme[:begin] + block + readme[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if previews, provenance hashes, catalog.json, or README.md are stale.",
    )
    args = parser.parse_args()

    try:
        managed, withdrawn = discover()
        catalog = load_json(CATALOG_PATH)
        readme = README_PATH.read_text(encoding="utf-8")
        catalog_after = updated_catalog(catalog, managed, withdrawn)
        readme_after = updated_readme(readme, managed)
    except (OSError, UpdateError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    stale: list[str] = []
    pending_writes: list[tuple[Path, bytes]] = []
    for pet in managed:
        try:
            current_preview = pet.preview_path.read_bytes()
        except OSError:
            current_preview = b""
        preview_is_current = pixels_match(current_preview, pet.preview_bytes)
        if not preview_is_current:
            stale.append(str(pet.preview_path.relative_to(ROOT)))
            pending_writes.append((pet.preview_path, pet.preview_bytes))

        published_preview = current_preview if preview_is_current else pet.preview_bytes

        provenance_after = dict(pet.provenance)
        provenance_after["assetSha256"] = sha256_file(pet.directory / "spritesheet.webp")
        provenance_after["previewSha256"] = sha256_bytes(published_preview)
        if provenance_after != pet.provenance:
            path = pet.directory / "provenance.json"
            stale.append(str(path.relative_to(ROOT)))
            pending_writes.append((path, json_bytes(provenance_after)))

    if catalog_after != catalog:
        stale.append("catalog.json")
        pending_writes.append((CATALOG_PATH, json_bytes(catalog_after)))
    if readme_after != readme:
        stale.append("README.md")
        pending_writes.append((README_PATH, readme_after.encode("utf-8")))

    if args.check:
        if stale:
            for path in stale:
                print(f"STALE: {path}")
            print("Run: python3 scripts/update_finalized_pets.py", file=sys.stderr)
            return 1
        print(
            f"OK: {len(managed)} auto-published pet(s) are current; "
            f"{len(withdrawn)} draft pet(s) are withheld"
        )
        return 0

    for path, payload in pending_writes:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        print(f"UPDATED: {path.relative_to(ROOT)}")
    if not pending_writes:
        print(
            f"OK: {len(managed)} auto-published pet(s) already current; "
            f"{len(withdrawn)} draft pet(s) are withheld"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
