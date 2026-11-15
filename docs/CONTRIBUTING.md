# Contributing

6EQUJ5 is an offline Pygame game. The legacy AI terminal lives in a separate repository. Read the [architecture](ARCHITECTURE.md) and [current state](planning/CURRENT_STATE.md) before changing behavior.

## Setup

Use Python 3.12 and a repository-local environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/6equj5-game
```

The flat `src/` directory installs as `video_game`. Use explicit imports from that package; do not add `sys.path` workarounds or import the sibling AI application. Runtime dependencies are pygame-ce, Pillow and NumPy.

## Code style

- Make the smallest change that fixes the stated problem. Reuse existing components; add an abstraction when there is an actual second use or a clear responsibility boundary.
- Use descriptive `snake_case` functions and variables, `PascalCase` classes and `UPPER_SNAKE_CASE` constants. Include units where they matter, such as `dt_seconds` and `speed_px_per_second`.
- Keep imports explicit, grouped as standard library, third-party and local. Match nearby formatting; avoid unrelated reformatting.
- Prefer direct control flow and small functions with one responsibility. Split a module when its responsibilities separate, not to meet an arbitrary line count.
- Add type hints to new interfaces when they clarify the contract. Document non-obvious behavior, inputs, units and failure cases; skip comments that restate the code and decorative module banners.
- Catch expected errors at the boundary that can handle them. Keep useful context; do not silently swallow failures or add speculative fallbacks.
- Keep tuning in `src/data/balance.json`, room values in level data, shared display defaults in `config.py`, and asset metadata in manifests.

## Runtime contracts

- `Campaign` owns persistent state. Use `apply_event()` and `store_world_state()`; `.state` is a detached snapshot. Do not modify `_state` directly.
- Preserve save-envelope version 2, older-save migration and recovery. Continue starts in the bunker. Scene exits must not write old state into a newly assigned campaign.
- Use the shared input mapper and deferred scene transitions. Check pause/focus, retry, scene exits and New/Continue isolation when changing interactive behavior.
- Keep Pygame display, event and surface work on the main thread. Avoid disk reads, asset decoding and unbounded work in frame loops.
- World coordinates are 480 × 270; the render surface is 960 × 540. Art resolution changes must preserve collision geometry, pivots and weapon attachments.
- Preserve authored dialogue, science prerequisites, rewards and route recovery. No model service or network access is required to play.

## Verification

Tests and fixtures are versioned under `src/tests/`; pytest discovers that directory. Deterministic input and timing baselines belong in `src/tests/fixtures/`, while builder tests use the maintained masters in `src/art/source/`. Use relative imports between test modules.

Run checks that exercise the changed behavior. A bug fix should have a regression test when the existing suite does not cover it. Documentation-only edits need link, formatting and content checks, not new tests that repeat the prose.

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy SIX_GAME_SAVE_DIR="$(mktemp -d)" .venv/bin/python -m pytest -q
.venv/bin/python -m video_game.tools.validate_content
.venv/bin/python -m video_game.tools.build_assets --dry-run
```

Use temporary saves and settings in tests and capture tools. Never write into a player's save directory. Give captures an explicit, unused output directory under `_temp/`. Useful commands are listed in [developer tools](../src/tools/README.md). Temporary output, historical reviews and `_trash/` must not become inputs for the game or maintained tests.

After packaging changes, build a clean wheel and a wheel from the source distribution. Check their contents and boot the installed game outside the checkout in an environment without AI packages. Wheels must contain runtime assets/data and exclude tests, tools, docs, art masters and local assistant files.

Inspect rendered output after visual changes. Dummy SDL checks and staged captures do not establish human playability, physical-controller support, audible quality or native display performance. Record actual results and limitations. Current results and known render-budget variability are documented in the [verification summary](maintenance/verification.json); retain the assertions and investigate any changed failure.

## Artwork and cleanup

`src/art/source/` owns rebuild masters and provenance; `src/assets/` contains runtime exports. Asset paths can be constructed from IDs and manifests, so a missing text-search match does not prove an asset is unused.

Before retiring unique material, preserve it in `_trash/` and record original path, archive path, SHA-256, reason and restoration steps in `_trash/TRASH_LOG.md` and `docs/maintenance/archive-manifest.json`. Keep recovery snapshots and player data intact.

Keep public documentation concrete: what works, how to run it, and what remains unfinished. Do not publish generated success claims or present promotional artwork as gameplay. Local assistant instructions and session files are ignored; public contributor guidance belongs here.
