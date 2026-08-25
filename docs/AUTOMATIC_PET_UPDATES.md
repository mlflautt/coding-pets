# Automatic finalized-pet updates

Finalized pet packages can opt into repository-managed publication. The updater treats each opted-in `pets/<pet-id>/` directory as the source of truth and derives the public catalogue surfaces from it.

## What is automatic

For every published `pet.json` with `catalog.autoPublish: true`, the updater:

1. Regenerates `preview.png` from the three shipped atlas cells in `preview.json`.
2. Refreshes the spritesheet and preview SHA-256 values in `provenance.json`.
3. Adds or synchronizes the pet's entry in `catalog.json`.
4. Rebuilds the pet's card inside the auto-published section of the main README.

It never generates character art, changes atlas cells, edits creative notes, or replaces QA evidence.

## Finalize a pet

1. Copy `templates/pet/` to `pets/<pet-id>/` and complete the package contract in `AGENTS.md`.
2. Add the validated v2 `spritesheet.webp`, retained QA evidence, concept record, `hermes.md`, and provenance.
3. Set these fields in `pet.json`:

   ```json
   {
     "catalog": {
       "status": "published",
       "autoPublish": true,
       "readmeOrder": 100,
       "tags": ["codex-v2", "hermes"]
     }
   }
   ```

4. Select three characteristic shipped frames in `preview.json`.
5. Run:

   ```bash
   python3 scripts/update_finalized_pets.py
   python3 scripts/validate_catalog.py
   ```

Commit the source package and the derived updates together.

## GitHub automation

The **Update finalized pets** workflow runs automatically after source package changes land on `main`. It can also be launched manually from GitHub Actions. If derived files change, the workflow commits them as `github-actions[bot]`.

Pull-request validation runs the updater in `--check` mode, so stale previews, hashes, catalogue entries, or README cards are reported before merge.

## Local verification

```bash
python3 scripts/update_finalized_pets.py --check
python3 scripts/validate_catalog.py
```

Both commands must pass before publication.
