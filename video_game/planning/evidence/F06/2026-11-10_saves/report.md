# F06 saves and recovery evidence

Date 2026-11-10, America/Denver. Environment: macOS arm64; Python 3.12.16 from `/opt/anaconda3/envs/6equj5_game`, pygame-ce 2.5.8, pytest 9.2.0. Rendering and keyboard events used dummy SDL video/audio. Every save used for testing and visual capture lived in an isolated temporary directory; no real player save was used or modified.

## Outcome

Added `engine/save_game.py`: a configurable user-data location, versioned campaign/checkpoint envelope, validation, staged file write with flush and fsync, atomic replacement, previous-valid backup and explicit recovery. A valid primary and backup survive tested partial writes and replacement failures. Damaged or unsupported primary files are retained before explicit replacement or recovery, and damaged/unsupported backup files are retained before replacement. Unchanged saves preserve a valid prior backup; a missing or invalid backup can be repaired without discarding its previous bytes.

The title offers New Game, Continue, Retry and Restore Backup. Starting over requires confirmation if a primary or backup exists. Save attempts occur on starting a game, timeline changes in the bunker, safe transitions into or out of the bunker, F5 in the bunker and bunker shutdown. While the bunker is open, a failed save displays a retry message and prevents departure until the save succeeds. The title uses its own relevant footer controls. The game README now reflects the prototype's save support.

Version 2 is the current envelope. Version 1 is a deliberately defined campaign-only migration fixture, not a claim of a previously shipped save. Fixtures for both supported versions live in `tests/fixtures/`. The actual state stores campaign/checkpoint data only; future contact and objective systems must integrate their own completed-state/checkpoint boundaries. F07 owns pause-menu semantics. Physical power-loss durability and simultaneous processes sharing a save slot remain open as I13.

Changed `engine/state_machine.py`, `engine/scenes/title.py`, `engine/scenes/bunker.py`, `engine/ui/hud.py`, `tests/test_engine_boot.py`, and `video_game/README.md`; added `engine/save_game.py`, `tests/test_save_game.py`, and two version fixtures. Updated save contracts, quality gates, roadmap, handoff, issue, progress and archive records. Existing files were not retired. The [pre-F06 recovery manifest](../../../../_trash/2026-11-10_F06_before_changes_manifest.json) records hashes and original paths for 13 archived originals plus the HUD and README recovery copies. They share the working device and are not an independent backup.

## Checks and results

Working directory `/Users/nzlab-la/Desktop/Github/6EQUJ5`:

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests -q
# 70 passed in 3.90s
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest tests -q
# 20 passed in 0.01s
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_save_game.py -q
# 23 passed in 0.77s
```

The focused tests cover a seeded development campaign with earned fragment/validation data, checkpoint and timeline round trips, both supported version fixtures, migration without rewriting on load, missing/corrupt/too-old/too-new/migration-failure outcomes, malformed checkpoints, preservation of unsupported files, a simulated short staged write, failed primary replacement, failed recovery, damaged backup preservation and explicit recovery. They exercise title controls, confirmation/cancellation, F5 retry and blocked bunker departure after a save failure. One test starts a separate Python process and continues the saved checkpoint through `video_game.main.run_game`; its restored campaign matches the original. The in-memory seeded rewards are fixtures, not production gameplay progression.

A visual capture script used `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy` with a temporary `SaveStore`, generated an empty title, introduced a damaged primary and valid backup, pressed Continue and then Restore Backup, and captured each resulting scene with the real renderer. Inspected [native title](previews/title_native.png), [3× title](previews/title_3x.png), [damaged-save feedback](previews/damaged_save_3x.png), and [restored bunker](previews/restored_bunker_3x.png), plus their native/scaled counterparts. The save choices and recovery message fit the panel; the restored bunker displays the backup confirmation and F5 control. The original title footer incorrectly listed bunker actions; it was corrected during visual review. Native text remains small, with broader readability work tracked by R01.

After verification, SHA-256 hashes for all 122 active asset files matched the [F02 baseline inventory](../../F02/2026-11-10_checkpoint/assets_before.sha256). The pre-change archive and all 15 recovery copies were reverified. Test scratch and preview save data were temporary; only screenshots and this report remain as task evidence.

## Limits

No files or assets were retired and no user save was accessed. The game remains a prototype: actual contact rewards and objective completion do not yet exist, so their eventual save hooks must be integrated when those systems are built. No real-window keyboard/controller, audio, live Ollama, power-failure, concurrent-instance or native Windows/Linux save testing was performed. I11 (untracked workspace and no independent backup), I12 (builder-platform checks) and I13 (save power-loss/concurrent-instance checks) remain open. Use one game instance per save directory until I13 is resolved.
