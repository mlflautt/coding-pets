# Codex + Hermes Pet Catalogue

A public, machine-readable catalogue of custom animated pets built for Codex and designed to be easy for Hermes Agent and other local agents to inspect, install, and extend.

## Catalogue

| Pet | Preview | Codex package | Hermes notes |
| --- | --- | --- | --- |
| [Vesper](pets/vesper/hermes.md) | [Contact sheet](pets/vesper/preview.png) | [Manifest](pets/vesper/pet.json) | [Creative guide](pets/vesper/hermes.md) |

The canonical index is [`catalog.json`](catalog.json). Each pet lives under `pets/<pet-id>/` and carries its own manifest, packaged sprite atlas, preview, provenance, and retained QA evidence.

## Add a pet

1. Copy `templates/pet/` to `pets/<pet-id>/`.
2. Replace the placeholders and add the validated `spritesheet.webp` and preview image.
3. Add the entry to `catalog.json`.
4. Run `python3 scripts/validate_catalog.py`.

New Codex pets use the v2 atlas contract: `1536×2288`, `192×208` cells, 8 columns, 11 rows, and `spriteVersionNumber: 2`. The first nine rows contain app states; the final two contain 16 clockwise look directions.

## Install in Codex

Copy a pet directory containing `pet.json` and `spritesheet.webp` into:

```text
~/.codex/pets/<pet-id>/
```

## Use from Hermes

Hermes should read `catalog.json`, then the selected pet's `pet.json` and `hermes.md`. Agent-facing workflow guidance is in [`AGENTS.md`](AGENTS.md) and [`HERMES.md`](HERMES.md).

## Publishing policy

- Publish final packages, compact previews, provenance, and meaningful QA evidence.
- Keep prompts, decoded row strips, extracted frames, and temporary generation assets out of Git.
- Never claim a pet is validated unless its retained validation files pass.
- Preserve human authorship notes and creative intent; agents should not silently rank or replace variants.

## Licensing

No reuse license has been selected yet. Public visibility does not grant permission to reuse the artwork or code. Add an explicit license before inviting third-party contributions or reuse.
