# Public preview images

The main README should show what an installed pet actually looks like. Public previews are therefore deterministic composites of three cells from the final published `spritesheet.webp`, not concept art, regenerated character art, or an aspirational mockup.

## Standard

- One `1800×720` PNG with three equal pose slots.
- Exactly three complete cells from the shipped Codex v2 atlas.
- One identity pose, one expressive or greeting pose, and one work, review, movement, or other characteristic pose.
- A common scale and baseline across all three slots; the complete `192×208` source cell is preserved.
- No labels, logos, interface controls, shadows, detached effects, or other additions.
- `lanczos` resampling for painted, plush, clay, and 3D pets; `nearest` for true pixel art.

The configuration lives beside the pet as `preview.json`. This makes the visible README asset reproducible and records exactly which shipped frames were selected.

## Generate and verify

Install Pillow in the active Python environment, then run:

```bash
python3 scripts/generate_public_preview.py pets/<pet-id>/preview.json
python3 scripts/generate_public_preview.py pets/<pet-id>/preview.json --check
```

The first command writes `preview.png`. The second renders the same configuration in memory and fails if the committed preview differs.

## Pose selection

Prefer three visibly different, flattering, semantically correct frames. Good starting points are:

1. `idle:0` for the primary silhouette and face.
2. `waving:1` or another clearly expressive greeting frame.
3. `running:2`, `review:2`, `jumping:2`, or a direction frame that best communicates the pet's distinctive motion language.

Review the final composite at the README's displayed width before publication. Change only the frame choices in `preview.json`; never retouch an individual pose in `preview.png`.
