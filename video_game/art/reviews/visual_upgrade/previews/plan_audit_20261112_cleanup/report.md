# Repository cleanup and integrity audit

Date: 2026-11-12. Scope: read-only audit of `6EQUJ5` and the untracked game/evidence tree. No files outside this report were changed, moved, renamed, or removed. No builds, tests, or captures were run.

## Repository state and integrity context

`git status --short` at inspection showed pre-existing modified `pyproject.toml` and `src/signal_6EQUJ5/ai_engine.py`, plus untracked `_trash/`, `generated_images/`, and `video_game/`. Preserve all of these. The project instructions identify unique masters, locked assets, recovery copies, evidence, saves, and terminal package as retention obligations; they prohibit retiring based on static search alone.

`video_game/planning/CURRENT_STATE.md` records the current accepted checkpoint: 510 tests / 2 named live tests deselected, nine native families, 25 manifest/component files hash-matched, eight scenes, and a copied-source wheel with 487 members (SHA-256 `bf7cc9eb1e617a8d5e5d055b8220061a68b791385228861195f49e8d6d16c736` as recorded in the state document). It explicitly leaves native-window/human/audible/performance/final-art acceptance open. This wheel record is strong prior packaging integrity evidence; I did not rebuild it.

The `pyproject.toml` working copy has `include-package-data = false`, package discovery excludes game tests, `_trash`, `_temp`, planning and art, and `video_game` package data is limited to `assets/**/*` and `data/**/*`. This makes preview/evidence and recovery trees non-wheel content by design. The tracked working-tree change in `pyproject.toml` should be retained and reviewed by its owner; do not revert it during cleanup.

The active runtime references and checks make several likely false positives clear: `engine/native_room_assets.py` and scenes use installed families; `engine/firing_lighting.py` is explicitly connected in `field.py` as preview opt-in; `engine/save_game.py` owns persistent save data; builder tools reference `_trash` for transactional archival. Firing-light WIP must remain with its technical owner. Historical generator retirements already have before/retired copies and retirement manifests; do not prune these archives.

## Size and duplicate observations

The untracked `video_game/` tree is about 1.4 GB; `generated_images/` is about 35 MB. There are 198 direct child directories under `video_game/art/reviews/visual_upgrade/previews/`, and 158 files beneath `video_game/_trash/`. Many previews encode separate review stages, camera positions, versions, or provenance; the high directory count alone is not a cleanup signal.

Python bytecode caches account for roughly 6.5 MB across the observed game tree, including `video_game/engine/__pycache__` (~812 KB), `video_game/tools/__pycache__` (~556 KB), `video_game/engine/scenes/__pycache__` (~208 KB), and `video_game/tests/__pycache__` (~4.7 MB). These are reproducible, ignored by `.gitignore` (`__pycache__/`, `*.py[codz]`), and safe *housekeeping candidates* if the owner wants to reclaim a small amount of space. They were not removed. Note `video_game/tests/test_checkpoint_audit.py` explicitly excludes cache directories from checkpoint scans.

A SHA-256 scan found exact repeated files in staged/installed or iterated preview evidence. Examples:

- `previews/annex_staged_v01/` and `previews/annex_installed_v01/` contain byte-identical PNG captures; e.g. `1977_ANALOG_y0_native_960.png` is 603,545 bytes, SHA-256 `3787ba8df6bfb62f98c0c3f53c59f7a91213f53cbc8b180e266af02bd8be90fb`.
- The `ui_readability_after_v03` through `v08` folders repeat several captures byte-for-byte; `dossier_long_top_1920.png` is 159,757 bytes, SHA-256 `6757e30178e88ca09ac5ac74becf7576fd25b4505039b1c37bad021493e77d71`.
- `final_checks_20261112_v01/earned_route/` and `earned_route_v02/` contain some identical captures (e.g. `flashback_printer_native.png`, 257,968 bytes, SHA-256 `a8ef05aa99a161360345cdabfda89e008aa67ec9b43fabf9b147c12ac192063b`). Other route artifacts differ, so the folders are not duplicates as wholes.

These are evidence copies and may document separate review checkpoints. Treat them as candidates for a manifest-only deduplication proposal, not deletion: first inspect each directory's README/context, timestamps, references, and retention intent; any retirement requires preserving at least one byte-identical copy and recording original/archive path, reason, replacement, and SHA-256 in `_trash/TRASH_LOG.md`.

## Keep intact

- `video_game/art/source/` masters, generated source provenance, and accepted/rejected candidates.
- `video_game/art/reviews/visual_upgrade/` state, briefs, review decisions, captures, context JSON, and recovery backups. Current state has direct links into this evidence.
- `video_game/assets/environments/*` installed family files and manifests; current checkpoint explicitly verifies all 25 referenced files.
- `video_game/_trash/` and top-level `_trash/`, including retirement/recovery backups, manifests, and restoration instructions.
- `video_game/tests/fixtures/`, player-save behavior/data, package/CLI assets, and build/transaction tooling.
- `generated_images/` pending provenance/owner mapping; the filenames are opaque UUID-style identifiers and no safe ownership inference is available from names alone.

## Practical next steps

1. Optional low-risk housekeeping: remove only ignored `__pycache__` directories, then let normal Python execution recreate them as needed. This saves only a few MB and should be done separately from the pre-existing edits.
2. If reclaiming meaningful space matters, ask the evidence owner to review repeated preview captures using hashes plus per-folder provenance. Prepare a proposed manifest mapping duplicate bytes to retained canonical paths; do not bulk-delete versioned previews.
3. Keep `_trash` archives intact. Any future retirement must follow `video_game/AGENTS.md`: caller/recovery verification, reason and replacement, original/archive paths and SHA-256 in the trash log.
4. Leave `pyproject.toml` and `ai_engine.py` edits untouched; their owner should review them independently.
