# Moon Regent for Hermes Agent

This directory is the native Hermes/Petdex compatibility package. It contains the first nine semantic animation rows in an 8×9 atlas of 192×208 cells (`1536×1872` RGBA WebP). The Codex v2 package one directory above retains two additional look-direction rows and must not replace this native Hermes atlas.

## Install into a Hermes profile

1. Resolve the profile home with `hermes pets doctor`.
2. Copy `pet.json` and `spritesheet.webp` from this directory into `<HERMES_HOME>/pets/moon-regent/`.
3. Run `hermes pets select moon-regent`.
4. Run `hermes pets doctor` and require the active pet to report `ready`.

Hermes maps its activity states to Moon Regent’s native rows: failures dim and recover, completed turns salute, tool execution ignites contained lunar insight, thinking performs measured review, approvals use the attentive waiting pose, and idle returns to lunar composure.

`validation.json`, `chroma-despill.json`, and `contact-sheet.png` are retained compatibility evidence. Installation should copy only `pet.json` and `spritesheet.webp`.
