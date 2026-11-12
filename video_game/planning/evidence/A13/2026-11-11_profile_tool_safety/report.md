# A13 profiling tool safety increment — 2026-11-11

A13 remains in progress. This increment isolates the profiling CLI; it is not release performance evidence.

Environment: macOS host, dedicated `/opt/anaconda3/envs/6equj5_game/bin/python`, dummy SDL video and audio. No graphical or audible inspection, live AI, model download, or 120-second certification run was performed.

Changed `video_game/tools/profile_game.py` and `video_game/tests/test_profile.py`. The CLI accepts `--headless` (default) or `--graphical`, validates duration and scale, uses temporary save/settings stores, and writes metrics only when `--output-dir` is supplied. Existing `metrics.json` is not overwritten. Metadata records the actual display driver, audio configuration and whether the mixer initialized, machine/OS information where available, AI status, and workload limitations. Actual audio driver, GPU and RAM are explicitly unknown where not obtained. The CPU profiler uses an in-memory stream. The full/leak CLI skips AI cancellation tests rather than starting an AI request, and peak RSS changes are not reported as leak verdicts. Callable benchmark methods remain available.

A follow-up corrected synthetic input delivery: key transitions now pass through the state machine and input manager each frame. A focused field test observed player displacement and projectile spawn. CPU profiler cleanup now runs on exceptions.

The workload is an uncapped synthetic scene loop with fixed simulated time steps and injected inputs. Actor and projectile counts are sampled after each update and reported as per-scene ranges; counts are not controlled, and the fresh-campaign catwalk has no activated defense waves; AI dialogue is not initiated by the CLI. Peak RSS is a high-water mark, not current memory. This does not establish normal-play, real-display or audio performance, nor the 120-second performance gate.

Checks:

- `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_profile.py video_game/tests/test_checkpoint_audit.py -q` — 19 passed in 4.53s. Includes short actual scene runs, output collision and player-data isolation, bounds and graphical-option forwarding, actual field displacement and projectile spawn, scene-switch input reset, and profiler cleanup on failure.
- An earlier combined command used the nonexistent `video_game/tests/test_checkpoint.py`; no tests ran. Corrected to `test_checkpoint_audit.py` above.

Recovery copies, created and hash-verified before edits:

| Original | Recovery copy | SHA-256 |
| --- | --- | --- |
| `video_game/tools/profile_game.py` | `video_game/_trash/2026-11-11_A13_profile_tool/video_game/tools/profile_game.py` | `db74f6ba4d2daa8a9f852c3d5e4832fd6f237853e4f3ca0eb882f4fbb0ea262b` |
| `video_game/tests/test_profile.py` | `video_game/_trash/2026-11-11_A13_profile_tool/video_game/tests/test_profile.py` | `7eaed62ddde442fffdbd89ba2355d8cceec55e1e258294e43070f202bb0e1f70` |

To restore, verify each copy's hash and copy it to its original path; this reverses this increment. No files retired or swept. Temporary test and benchmark directories are cleaned by their owners.
