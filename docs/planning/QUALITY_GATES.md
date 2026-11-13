# Quality gates and verification

Each task card adds concrete checks to these shared gates. Record observed evidence before changing a task to done.

## Baseline commands

Run from `/Users/nzlab-la/Desktop/Github/6EQUJ5` using the dedicated environment.

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests -q
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest tests -q
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.main
```

The last command is an interactive run. Dummy SDL checks exercise rendering and assertions. Real-window input/audio checks require a graphical session and their own evidence. Respect the execution environment's actual permission controls when launching a GUI.

Tests write preview PNGs only under pytest's temporary directory. To export the current bunker and terminal deliberately, choose a separate output directory (existing files with the same names there are overwritten):

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.preview_assets --output-dir video_game/planning/evidence/F02/2026-11-10_checkpoint/previews
```

The dummy drivers permit headless capture; omit them for a real graphical display. The preview command is in the tools package. Future commands in task cards are implementation requirements until implemented and verified.

## Checkpoint maintenance

The audit parses active Python files, checks module purpose/caller/modification headers and rejects wildcard imports. It discovers modules rather than maintaining a second file registry. The asset audit validates the current manifest references, locks and dimensions; scene and preview tests exercise behavior. File length is a review signal, not a hard cap. Assess responsibilities and readability in review instead of compressing code. Investigate suspected unused files against imports, dynamic references, manifests, builders, packaging and runtime behavior before applying the retirement protocol.

The game tree has a tracked checkpoint at `a43c2b3`, but the working tree also contains modified and untracked files that the checkpoint cannot recover. Do not assume a checkout or local copies provide an independent backup. Before any replacement or retirement, make and verify a separate recovery copy of each affected file and record its original location and SHA-256; use the archive procedure for retirements. Preserve the working tree and avoid destructive cleanup. Establish and verify an independent recoverable backup; I11 remains open, including recovery of the missing historical portrait sources.

## Save and recovery checks

F06's focused tests use temporary directories and cover both supported save versions, invalid versions and data, partial writes, failed replacement, explicit backup recovery, title controls and continuing through the normal game entry point after a process restart:

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_save_game.py -q
```

For a manually launched development session, set `SIX_GAME_SAVE_DIR` to a chosen writable test directory before starting the game. The title offers New Game, Continue and Restore Backup; F5 saves at the bunker. Do not use a real player save for fault injection. The actual macOS user-data path and supported save formats are in DATA_CONTRACTS.md.

## Safe asset builds

Use the macOS game environment. The normal command preserves complete locked groups:

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets --replace FASR-001 --dry-run
```

Remove `--dry-run` only to explicitly replace that group. Repeat `--replace` for multiple IDs, or select `mateo`, `bunker`, or `review`. Each civilization group comprises its face, environment, composite, chart and shared manifest; `mateo` owns the sprites and character sheet; `bunker` owns its layers, tileset, previews and scene manifest; `review` owns the palette, comparison and roster sheets. Bunker builds consume the existing Mateo bunker sprite; review builds consume civilization exports and the preserved legacy portraits. Group output paths and source names are explicit in the builders. The individual `mateo_sprite_builder` and `bunker_scene_builder` module commands default to preserving their own groups and accept `--replace mateo` or `--replace bunker` respectively. `--assets-dir` and `--archive-dir` permit isolated experiments; keep the archive outside the active asset directory.

All selected inputs are checked before any promotion. Missing members of an existing locked group require explicit replacement. Each group is staged and validated, its previous outputs are copied and hash-verified in `_trash/<date>_F03/<transaction>/`, and its manifest records original paths, hashes and recovery steps. The asset directory is locked during a build. A pending journal is rolled back by the next build, normal game start or preview start before loading assets. Do not run a build while the game is already open: it can load assets again after startup. Groups are committed separately and their files are promoted sequentially, not as one atomic multi-group transaction; a hard interruption is recovered on the next entry point, not by the terminated process itself. Restoration of an archived intentional replacement is a manual operation: verify the archive hashes, copy originals to their recorded paths, remove outputs recorded as previously absent, and rerun the loader and checkpoint suites. Do not delete archives.

## Gate G0 — Reproducible foundation

F01–F08 pass. The game boots after scene extraction. Test runs leave runtime resources unchanged. Asset rebuilds preserve locked data and recover from failure. Saves survive reload, migration, partial writes and corrupted inputs. The project structure has an inventoried source-to-export map. All retirement records include recovery information.

## Gate G1 — Visual standard and contact loop

C01–C08 pass. Art rubric meets its threshold. The terminal supports target selection, tuning, decode, typing, streaming, cancellation, reconnect, transcript scrolling and offline progression. Exit/reentry and target switches discard stale events. Font wrapping handles long text and supported Unicode. A fragment can be acquired, tested, deployed and saved through normal input.

Use fake inference streams for deterministic cancellation, delayed response, malformed output, server failure and queue saturation tests. Perform at least one real Ollama session when the service/model is available. Record unavailable live-inference checks as pending. The current user explicitly permits skipping them: G1 retains its earlier acceptance, with live checks documented as skipped rather than passed.

## Gate G2 — Playable Act I

A01–A14 pass. A new player can enter the bunker, get a mission, scavenge, contact FASR-001 and FASR-007, validate the first protocol, defend the dish, defeat Greenkeeper, and reach Act II. Death, pause, failed defense, replay and save/reload work. The path requires no development shortcuts.

Provide a full route recording or checkpointed captures plus a written playthrough. Include failures and recovery. At least one playthrough starts from a completely fresh save. Record duration without forcing an arbitrary target playtime.

The user authorized connected Earth-sector implementation in parallel ahead of the prior S11 acceptance sequence. Reaching Neo-Denver is now possible, but the scripted input route does not by itself satisfy the fresh human/native-window G2 criterion or close S11.

## Gate G3 — Full mechanics

S01–S11 pass. Four workbenches are playable, explain evidence, and feed progression. Every timeline swap either commits safely or gives clear rejection feedback. Dodleston changes persist correctly. The 1977 flashback and its artifact return work. Faction attacks, advanced mobility and unlocked weapons have explicit counters, costs and reset semantics.

## Gate G4 — Campaign complete

P01a–P09 and J01–J04 pass. A fresh campaign traverses all Earth sectors, then all eleven guardian → acknowledged information → teleport visits, then the final Earth Core Prime/Archon encounter. All eleven new receipts must be earned and saved before final entry and victory; legacy fragments alone cannot satisfy them. Every required room, lab arc, reward, boss and recovery path is reachable, and unique rewards apply once. Preserve the existing three-ending, consequence, offline and applicable live-dialogue acceptance requirements.

Every Earth sector and alien world requires a gameplay blockout, reviewed art, boss encounter, checkpoints and local playthrough. Record at least one complete fresh-campaign human playthrough and targeted alternative-choice/recovery routes. The portal-seeded scripted journey and single FASR-001 art benchmark are bounded evidence, not G4 acceptance.

## Gate G5 — Release candidate

R01–R08 pass. Package installation, full playthrough, settings, save recovery, model-offline behavior and resource loading succeed on each advertised platform. Credits identify shipped art/audio/fonts and source provenance. Assets marked concept or candidate cannot silently ship as reviewed final assets.

No open blocker or high-severity progression, data-loss, input, crash or unreadable-critical-UI defects remain. Lower-severity issues have a documented disposition and user-visible limitations where relevant.

## Performance protocol

Use a named machine and actual graphical session for release measurements. Record CPU/GPU/RAM, OS, display scale, scene, enemy/projectile counts, effects settings and model status. Warm assets, then measure 120 seconds with repeated traversal and combat. Report update/render work separately from frame limiter sleep.

Proposed target on the documented release machine is 60 FPS with p95 CPU frame work at or below 16.7 ms, p99 below 33.3 ms, and no avoidable main-thread blocking above 100 ms during streamed dialogue. Record results and revise budgets openly if hardware evidence demands it.

Measure memory before and after ten terminal visits, repeated room changes and AI cancellations. After cache warmup, investigate sustained growth greater than 10% or 50 MB. Treat these as investigation thresholds. Explain retained caches separately from leaked resources.

## Task-level acceptance checklist

- Intended behavior works through its normal entry point.
- Existing callers and older supported data continue to work.
- Valid, invalid, repeated, interrupted and boundary operations are exercised as relevant.
- New gameplay state can be saved/reloaded where required.
- Screenshots and motion were inspected for visible changes.
- Required targeted tests and checkpoint suites pass.
- No unexplained asset or source changes occurred during checks.
- Documentation and retirement records reflect the actual resulting files.

## Defect severity

Blocker means the task or campaign cannot proceed. High means crash, lost/corrupted progression, broken essential input or unfair unavoidable failure. Medium means impaired behavior with a workable route. Low means polish or minor inconsistency.

A failed gate creates a concrete issue and keeps dependent work planned. Independently useful tasks can continue when their dependencies are satisfied.

## Current audit override (2026-11-11)

See [CONTRIBUTING.md](../../CONTRIBUTING.md), [controls](../CONTROLS.md) and [current state](CURRENT_STATE.md) before using historical task-stage claims. The separated game is offline; its active suite no longer includes the retired live-model tests. Run the current suite without carrying forward historical deselections. Keep manual/visual/audio/native-performance gates distinct from component and keyboard integration tests. The annex connectors demonstrate mechanics access; the connected Earth/alien route and its remaining acceptance limits are recorded in CURRENT_STATE.md. Retired static A14/S11 card generators were historically reported archived under `_trash/2026-11-11_G3_audit/retired/`, and the later A13/S09 static generators at `_trash/2026-11-11_tool_retirement/retirement.json`. Both paths were absent during the 2026-11-12 cleanup audit, so their recovery records could not be verified. Their short dummy profiling and fixture captures do not establish native performance or visual/fairness acceptance. New runtime captures use `python -m tools.capture_runtime_audit --output-dir PATH` and disclose fixtures.
