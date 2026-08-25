# Agent instructions

This repository is a public catalogue, not a scratch workspace.

## Goal

Maintain portable pet packages that work in Codex and remain legible to Hermes Agent and medium-sized local agents. Preserve creative intent, provenance, validation evidence, and reversible edits.

## Before changing a pet

1. Read `README.md`, `HERMES.md`, `catalog.schema.json`, and the pet's `pet.json` plus `hermes.md`.
2. Treat existing images and metadata as user-owned source material.
3. Work in a temporary run directory; do not overwrite a published pet until the replacement passes validation and visual review.
4. Never invent validation results, provenance, authorship, or licensing.

## Publish contract

- Pet directory: `pets/<pet-id>/`
- Required: `pet.json`, `spritesheet.webp`, `preview.png`, `hermes.md`, `provenance.json`
- New deterministic public previews also include `preview.json`; legacy screenshot and showcase previews are exempt.
- New packages should set `catalog.autoPublish: true`, `catalog.readmeOrder`, and `catalog.tags` in `pet.json`; `scripts/update_finalized_pets.py` then owns their preview, provenance hashes, catalogue entry, and README card.
- Required QA: `qa/validation-extended.json`, `qa/chroma-despill-extended.json`, `qa/run-summary.json`
- Required concept record: `concept-development/README.md`
- Optional but encouraged: contact sheet, look-direction sheet, animation previews, and human review notes
- Codex v2 atlas: 1536×2288 WebP, 192×208 cells, 8 columns, 11 rows
- `spriteVersionNumber` must be `2`

Run `python3 scripts/validate_catalog.py` before handing off. Visual quality still requires human or qualified visual-agent review; structural validation alone is insufficient.

For a pet with `preview.json`, also run `python3 scripts/generate_public_preview.py pets/<pet-id>/preview.json --check`. The public preview must be reproduced from three shipped atlas cells; do not substitute concept art or regenerated character art.

For an auto-published pet, run `python3 scripts/update_finalized_pets.py` before validation and `python3 scripts/update_finalized_pets.py --check` before handing off. Do not edit content between the README auto-publish markers by hand; derive it from finalized manifests.

## Creative behavior

Keep distinct variants when the user wants comparison. Retain stable IDs and lineage. Record warnings honestly. Do not choose a creative winner without user guidance.

Concept images are development evidence, not proof of the shipped pet. Label each retained image with its role, origin, relationship to the final asset, and outcome. Never present a rejected or aspirational concept as an actual animation frame.
