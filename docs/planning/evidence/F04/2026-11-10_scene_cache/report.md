# F04 scene extraction and cache evidence

Date 2026-11-10, America/Denver. Environment: macOS arm64, Python 3.12.16 in `/opt/anaconda3/envs/6equj5_game`, pygame-ce 2.5.8, SDL 2.32.10 and pytest 9.2.0. Automated input and captures used dummy SDL video and audio; these were not a real-window or controller playthrough.

## Outcome

Extracted the base, title, bunker and terminal scenes and shared HUD into their documented modules. The three placeholder scenes remain. The state machine re-exports the existing scene class names and constants. A manifest-aware `AssetCache` validates paths and image dimensions, reads the bunker and civilization manifests, caches surfaces and preserves existing layer alpha handling. Missing or malformed required resources raise an actionable `AssetLoadError`; the normal CLI reports the error and the game loop cleans up Pygame.

Scene callbacks request transitions that apply after the event or update returns, with `on_exit`/`on_enter` lifecycle calls and an idempotent shutdown. Direct external `change_state` calls still take effect immediately. Active terminal requests do not yet exist and will need cancellation when C03/C04 introduce them. The loop converts Pygame's elapsed milliseconds to seconds once; scenes use seconds and the CRT update adapts seconds to its existing millisecond glitch interface. The preview command also closes its state machine.

Changed `engine/state_machine.py`, `engine/crt_renderer.py`, `engine/preview_assets.py`, `main.py`, `tests/test_engine_boot.py`; created `engine/assets.py`, `engine/scenes/{__init__,base,title,bunker,terminal}.py` and `engine/ui/{__init__,hud}.py`. Updated the timing contract, roadmap, handoff, progress, issue and archive records. No asset or source master was retired or replaced.

A verified pre-F04 local snapshot contains 12 original files. The [snapshot manifest](../../../../_trash/2026-11-10_F04_before_changes_manifest.json) records the archive and individual SHA-256 hashes, original paths, references and restoration procedure. It shares the same device as the working tree and is not an independent backup.

## Verification

Working directory `/Users/nzlab-la/Desktop/Github/6EQUJ5`:

```sh
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests -q
# 22 passed in 3.12s
/opt/anaconda3/envs/6equj5_game/bin/python -m pytest tests -q
# 20 passed in 0.01s
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.engine.preview_assets --output-dir video_game/planning/evidence/F04/2026-11-10_scene_cache/previews
# Exit 0; three PNGs written.
```

Tests render all six scene identifiers, send keyboard events for title, terminal, all placeholder scenes and bunker controls, and check ten bunker/terminal enter-exit cycles and retained state. A callback verifies transitions remain deferred until both an event and an update complete. Instrumented image loading and path resolution show no further reads/resolution during ten warmed terminal/inspector cycles; three FASR-001 image files are each loaded once. Missing files, invalid image dimensions and manifest path traversal produce controlled errors; the missing-file test also confirms Pygame shutdown.

[Baseline timing](baseline_timing.json) was recorded before edits. The additional [baseline trajectories](baseline_trajectories.json) were generated from the archived pre-F04 state-machine code and record every frame of one second moving and one second idle at each of 30, 60 and 120 FPS, using the integer-millisecond intervals produced by a Pygame-style clock. Tests match every pose and position against these trajectories, plus title elapsed time, timeline shift, and CRT timer checks. This is a deterministic behavior comparison, not a performance benchmark. A preliminary experiment using ideal fractional milliseconds rather than the actual integer-millisecond clock showed isolated one-frame animation-boundary differences due to floating-point rounding; the chosen seconds implementation matches the archived integer-clock trajectories exactly.

After the suites and preview, SHA-256 hashes of all 122 files under `video_game/assets/` matched the [F02 baseline inventory](../../F02/2026-11-10_checkpoint/assets_before.sha256). No archive or builder wrote active assets.

## Visible inspection and limitations

Inspected [native bunker](previews/pygame_live_480x270_crt_off.png), [3× CRT bunker](previews/pygame_live_1440x810_crt_on.png), and [3× terminal](previews/pygame_live_crt_terminal.png). Mateo, equipment, lighting, HUD, portrait and chart appear in the expected locations. Comparing RGB pixels with the F03 captures found all three images identical. The existing `30s` terminal label remains tracked as I10; these captures do not establish final art quality or motion.

No failures remain in F04. The workspace is still untracked and needs an independent backup or version-control strategy (I11). No real-window keyboard/controller, audio, live Ollama, sustained performance, power-loss or non-macOS platform checks were performed. Controller and pause work remain scheduled for F07/R02; live inference begins at C03. Temporary test directories were owned by pytest; only the documented snapshot, timing records and captures were retained.
