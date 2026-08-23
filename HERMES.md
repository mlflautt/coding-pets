# Hermes Agent handoff

## Entry points

- `catalog.json`: discover published pets and paths
- `catalog.schema.json`: catalogue data contract
- `pets/<pet-id>/pet.json`: Codex installation manifest plus catalogue metadata
- `pets/<pet-id>/hermes.md`: character identity, motion language, creative constraints, and usage notes
- `pets/<pet-id>/provenance.json`: lineage and source declarations
- `pets/<pet-id>/qa/`: retained validation evidence

## Safe workflow

1. Select by stable `id`; never infer identity from filenames alone.
2. Confirm `status` is `published`, the asset paths exist, and retained QA reports success.
3. For Codex installation, copy only `pet.json` and `spritesheet.webp` to `~/.codex/pets/<id>/`.
4. For a derivative, create a new stable ID and set `derivedFrom`; do not mutate the original lineage.
5. Ask the user to judge creative variants. Automated checks may reject structural defects but must not declare aesthetic superiority.

## Compatibility boundary

Codex consumes the packaged atlas and `pet.json`. Hermes consumes the catalogue and markdown context; it should not assume native animated-pet UI support. Other renderers may use the atlas only after explicitly mapping the row contract.
