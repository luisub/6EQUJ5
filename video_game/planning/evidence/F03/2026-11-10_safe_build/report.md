# F03 safe asset build evidence

Date: 2026-11-10, America/Denver. Host: macOS arm64; Python 3.12.16 from `/opt/anaconda3/envs/6equj5_game`, pygame-ce 2.5.8, SDL 2.32.10, Pillow 13.0.0, pytest 9.2.0. Test rendering used dummy SDL video/audio. No real-window input, audio, GPU or Ollama was tested.

## Outcome and inventory

Normal builder commands preserve locked groups and their metadata. Select a group with `--replace` and preview the intended build with `--dry-run`. The coordinator preflights all selected sources, stages complete groups, validates outputs, verifies archived originals, journals, and promotes each group with the manifest last. An exception rolls back; after a hard process interruption the next builder, game startup or preview startup rolls the entire affected group back before loading. The builders use explicit source filenames rather than selecting the first glob match. Output paths stay unchanged.

- Each civilization group: four named 128×128 PNGs (face, environment, composite, chart) plus its entry in the shared civilization manifest. The ten authored face sources are individually named concepts; FASR-005 also uses its concept for its environment; SCAN-H is procedural. New entries also require the corresponding `src/signal_6EQUJ5/data/civilizations/<folder>/info.txt`.
- Mateo group: 33 pose PNGs, three outfit strips, six outfit size aliases, the idle and bunker aliases, portrait, and 1180×520 character sheet. Inputs are `concept_mateo_idle_1794333616733.jpg` and `concept_bunker_clean_1794333595362.jpg`.
- Bunker group: six layers, tileset, two previews and scene manifest. Inputs are the explicitly named clean bunker concept and the existing 96×128 bunker sprite. It does not silently rebuild Mateo.
- Review group: palette, comparison and roster sheets; inputs include the civilization exports and preserved legacy portraits in `_trash/legacy_ascii_portraits/`.

Changed `engine/build_assets.py`, `civ_art_builder.py`, `bunker_scene_builder.py`, `mateo_sprite_builder.py`; added `engine/asset_transactions.py` and `tests/test_assets.py`. `main.py` and `engine/preview_assets.py` now recover before loading. Updated quality gates, contracts, file map, roadmap, current state, issues, progress and trash log. The previous unsafe `force_overwrite=True` argument now raises an actionable error: individual explicit selections are required. Existing lower-level render helpers return their outputs without replacing live files.

Before changes, created `_trash/2026-11-10_F03_before_changes.tar.gz`, containing 182 non-cache files with original paths. Every member was verified against its original SHA-256. Archive SHA-256: `5378fe657bb906960fb003cdb0542a03b9cabda81cc69c89028edc8eb1756fb5`. The local archive is not an independent-device backup. See the [trash log](../../../../_trash/TRASH_LOG.md) for restoration instructions.

## Commands and observed results

From `/Users/nzlab-la/Desktop/Github/6EQUJ5`:

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests -q
# 18 passed in 2.90s
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest tests -q
# 20 passed in 0.01s
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.engine.build_assets
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.engine.mateo_sprite_builder
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.engine.bunker_scene_builder
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.engine.build_assets --replace FASR-001 --dry-run
```

All four commands exited 0. The first preserved all eleven civilization groups, Mateo, bunker and review; individual commands preserved their groups; dry-run reported `Would stage and promote: FASR-001`. SHA-256 inventory of all 122 active asset files exactly matches the [F02 pre-test inventory](../../F02/2026-11-10_checkpoint/assets_before.sha256), including after the suites and commands.

The automated tests use isolated copies. They cover unchanged defaults and dry-run, missing input before any promotion, missing related outputs and explicit repair, selected replacement and verified recovery records, unaffected groups, stable repeated civilization/Mateo/bunker/review outputs, injected promotion failure and rollback, forced process exit after the first changed file, and recovery through a one-frame normal game launch before loading. Concurrent builder/startup attempts are rejected. The non-`fcntl` fallback lets the game load when no recovery is pending and requests a supported host otherwise; it was simulated, not run on Windows.

For visible evidence, copied the full asset tree into a temporary directory, ran the normal CLI three times with `--assets-dir <copy> --archive-dir <temporary archive> --replace FASR-001`, then `--replace mateo`, then `--replace bunker`; pointed game configuration to that copy and invoked `export_previews` under dummy SDL. All three selected builds exited 0 and the temporary data was removed after capture. Inspected the [native bunker](previews/pygame_live_480x270_crt_off.png), [3× bunker](previews/pygame_live_1440x810_crt_on.png), [terminal](previews/pygame_live_crt_terminal.png) and [rebuilt portrait](fasr-001_face.png). They show the expected character, equipment, HUD, CRT and constellation composition; the known `30s` label remains I10. These captures do not certify motion or artistic acceptance.

## Limits and cleanup

No production asset was replaced or retired. Tests and the visual experiment used temporary copies and temporary recovery archives; the pre-change snapshot and this evidence remain. Groups commit separately and individual files are promoted sequentially: do not rebuild while a game is already running, and an abrupt interruption is recovered on the next supported entry point. Power-loss durability and native Windows/Linux behavior were not tested. macOS `fcntl` directory locking is required for building; on hosts without it normal loading works only without a pending recovery. Follow the restoration instructions in each transaction manifest; do not remove retained archives. The game directory is still untracked and the local snapshot shares the same storage device, so I11 remains open.
