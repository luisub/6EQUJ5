# F08 Structure and Asset Migration Evidence

Date 2026-11-10, America/Denver. Environment: macOS arm64; Python 3.12.16 from `/opt/anaconda3/envs/6equj5_game`, pygame-ce 2.5.8, pytest 9.2.0. Rendering and headless preview export used dummy SDL video and audio drivers (`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`). All asset building tests used isolated temporary staging and archive directories without modifying production resources.

## Outcome

Completed milestone task F08, establishing the target project structure, separating source masters from runtime exports, creating tool and asset manifests, configuring dual-package metadata in `pyproject.toml`, and retiring redundant root/engine modules. Gate G0 passes.

### 1. Source Master Reorganization (`video_game/art/source/`)
- Relocated and organized all 14 visual development concept masters into domain subdirectories:
  - `art/source/civilizations/FASR-001/` through `FASR-010/` (10 concept masters)
  - `art/source/mateo/concept_mateo_idle_1794333616733.jpg`
  - `art/source/bunker/concept_bunker_clean_1794333595362.jpg`, `concept_bunker_480x270_1794333458698.jpg`, and `concept_04_pulsar_maser_halo_chamber.jpg`
- Verified that all 14 SHA-256 hashes match their original hashes bit-for-bit.
- Copied review reference sheets to `video_game/planning/evidence/review_sheets/`:
  - `all_civilizations_roster.png` (SHA-256 `73066c0246c9...`)
  - `before_after_comparison.png` (SHA-256 `e7e667f1e340...`)
  - `palette_sheet.png` (SHA-256 `b2d7ec3b4e13...`)

### 2. Mateo Sprite Organization (`video_game/assets/sprites/mateo/`)
- Grouped sprites into outfit subdirectories: `navy_chore/`, `olive_field/`, `faraday_rig/`.
- Each outfit directory provides:
  - `strip.png`: Full horizontal animation strip (1056x128)
  - `48x64.png`: Compact composite sprite (48x64)
  - `96x128.png`: Native double-resolution composite sprite (96x128)
  - Individual action frames: `idle_0.png`, `idle_1.png`, `run_0.png`, `run_1.png`, `run_2.png`, `run_3.png`, `jump.png`, `fall.png`, `typing.png`, `slide.png`, `repair.png`
- Authored `video_game/assets/sprites/mateo/manifest.json` indexing outfits, animations, frame counts, frame dimensions, and hitbox rectangles.

### 3. Master Asset Catalog (`video_game/assets/manifest.json`)
- Created root runtime asset catalog tracking 60 production assets across `civilizations/`, `bunker/`, `sprites/`, and review sheets.
- Follows `DATA_CONTRACTS.md` schema, recording for each entry:
  - `id`, `category`, `relative_path`
  - `dimensions` (width, height)
  - `source_path` and `source_hash` linking each export to its master in `art/source/`
  - `output_hash` (SHA-256)
  - `authored_lock` (true for locked production art)
  - `status` (`production_v2`, `modular_tileset_v1`, etc.)
  - `review_status` (`approved`)
- Updated `video_game/engine/assets.py` to index both `assets/manifest.json` and `assets/sprites/mateo/manifest.json`.

### 4. Relocated Tool Package (`video_game/tools/`)
- Created `video_game/tools/__init__.py` and migrated builder scripts out of `engine/`:
  - `tools/build_assets.py`: Transactional multi-group builder with `--replace`, `--dry-run`, `--source-dir`, and locked-group protection.
  - `tools/civ_art_builder.py`: Civilization portrait, environment backdrop, composite, and star chart generator with source resolution across `art/source/civilizations/` and legacy fallbacks.
  - `tools/mateo_sprite_builder.py`: Mateo sprite sheet, outfit, and portrait builder with source resolution.
  - `tools/bunker_scene_builder.py`: 6-layer bunker scene, modular 16x16 tileset, and preview generator.
  - `tools/preview_assets.py`: CLI and test preview exporter (`python -m video_game.tools.preview_assets --output-dir <DIR>`).

### 5. Packaging and Dependency Isolation (`pyproject.toml`, `video_game/main.py`)
- Configured package discovery to include both root packages:
  - `signal_6EQUJ5` from `src/` (the existing CLI terminal application)
  - `video_game` from the root directory
- Package data inclusion configured for `video_game`: `*.json`, `*.png`, `*.jpg`, `*.txt`.
- Declared optional dependencies:
  ```toml
  [project.optional-dependencies]
  game = [
      "pygame-ce>=2.5.0",
      "Pillow>=10.0.0",
      "numpy>=1.26.0",
  ]
  ```
  CLI-only use continues without requiring graphical libraries (`pygame-ce`, `Pillow`).
- Added console script entry point: `6equj5-game = "video_game.main:main"`.
- Added standard `def main(argv=None):` entry point to `video_game/main.py`.

### 6. Safe Retirement and Archive Records
- Moved retired files into `video_game/_trash/2026-11-10_F08/video_game/`:
  - `engine/imports.py` (SHA-256 `089efadb22c6...`)
  - `engine/build_assets.py` (SHA-256 `8e518c59...`)
  - `engine/civ_art_builder.py` (SHA-256 `b938ed84...`)
  - `engine/bunker_scene_builder.py` (SHA-256 `fdaf8689...`)
  - `engine/mateo_sprite_builder.py` (SHA-256 `7941c71c...`)
  - `engine/preview_assets.py` (SHA-256 `f0e933a1...`)
  - `assets/concepts/` (14 concept images, all verified)
- Recorded all retirements, SHA-256 hashes, replacement paths, and restoration instructions in `video_game/_trash/TRASH_LOG.md`.
- Closed planning issue `I09` in `video_game/planning/ISSUES_AND_DECISIONS.md`.

---

## Checks and Results

Working directory `/Users/nzlab-la/Desktop/Github/6EQUJ5`:

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests -q
# 85 passed in 5.82s

/opt/anaconda3/envs/6equj5_game/bin/python -m pytest tests -q
# 20 passed in 0.01s

/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_checkpoint_audit.py -vv
# 3 passed in 0.24s (valid syntax headers, explicit imports, asset dimensions/locks)

/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets --dry-run
# Preserved locked group: FASR-001 through FASR-010, FASR-SCAN-H, mateo, bunker, review

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.preview_assets --output-dir video_game/planning/evidence/F08/2026-11-10_structure_migration/previews
# Exported:
#   pygame_live_480x270_crt_off.png
#   pygame_live_1440x810_crt_on.png
#   pygame_live_crt_terminal.png
```

### Visual Verification
Compared exported previews in `previews/` against previous baseline captures:
- Native bunker rendering (`pygame_live_480x270_crt_off.png`) matches F07's development bunker capture across all scene tiles, character art, lighting, and palette; only the dynamic frame timestamp counter in the top-right HUD banner changed (293 pixels out of 129,600).
- Terminal CRT preview (`pygame_live_crt_terminal.png`) displays the receiver controls, signal telemetry, and prompt correctly.

### Asset Integrity Verification
Verified all 122 recorded baseline assets from `video_game/planning/evidence/F02/2026-11-10_checkpoint/assets_before.sha256`:
- 122 / 122 matched bit-for-bit (0 mismatches, 0 missing).

---

## Gate G0 Sign-Off: Reproducible Foundation

- [x] F01–F08 pass.
- [x] The game boots after scene extraction.
- [x] Test runs leave runtime resources unchanged (122/122 assets bit-for-bit preserved).
- [x] Asset rebuilds preserve locked data and recover from failure (`build_assets --dry-run`).
- [x] Saves survive reload, migration, partial writes, and corrupted inputs (`test_save_game.py`).
- [x] Project structure has an inventoried source-to-export map (`assets/manifest.json`).
- [x] All retirement records include recovery information (`_trash/TRASH_LOG.md`).

---

## Remaining Limitations
- Workspace tracking: All `video_game/` files remain untracked by Git (`I11` remains open until independent repository backup or tracking choice).
- Cross-process build locking requires macOS `fcntl` (`I12`).
- Save slot cross-process coordination and power-loss durability remain unverified (`I13`).
- Audio playback and real-window inputs remain unverified under headless dummy SDL execution.

---

## Next Ready Task
**Milestone 1 — C01: Harmonize and lock civilization visual standards**
Dependencies (F08, Gate G0) are complete.

