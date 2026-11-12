# Act I remediation — 2026-11-11

## Outcome

The dish-defense model now runs in `FieldOpsScene` when the player enters the repaired catwalk. The three scheduled waves instantiate actual drone/hound enemies. The HUD shows time, signal bin, integrity and a warning that surviving hostiles damage the array. Each wave has an eight-second grace period; after that, each living enemy causes 0.65 integrity points per second. Jams cause the existing additional decay and can be cleared with E near the feedhorn. Pause freezes the simulation. Player death or dish collapse fails the encounter; R restarts it, clearing enemies and projectiles and restoring the player. Completion awards the campaign event once and attempts a checkpoint save; a completed campaign can dispatch to the boss from the bunker. Exiting and returning starts a new unfinished attempt.

The approach room now has an exit into the salvage yard, where the coupler pickup is restricted. An integration test exercises this exit and pickup. A live-mode contact can use the same explicit numbered evidence channels as offline mode while free-form conversation remains model-driven; untrusted model output does not itself grant fragments.

The old A14 automated harness still injects state and is not a player playthrough. Its output and test now say gate G2 is not verified, and accurately describe its reload as a second state machine in the same process. HUD labels now fit their assigned columns. Corrected retired builder/preview commands in the quality-gate document.

## Verification

macOS arm64, dedicated `/opt/anaconda3/envs/6equj5_game/bin/python`, dummy SDL video and audio:

```
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests tests -q
# 254 passed, 2 skipped in 12.17s
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets --dry-run
# 14 locked groups preserved
```

Scene tests exercise bunker dispatch, wave creation, pause, dish pressure, player casualty, failure and retry, the unjam interaction, 72 seconds of scene updates, one-shot reward, saved state, and dispatch to the boss. Enemies are programmatically neutralized in the completion test, and the salvage link test places the player at the exit and pickup; these are integration tests, not proof of human traversal or combat fairness. Online channel testing simulates online mode, not a real model response. The two skipped tests require real Ollama.

`defense_native.png` and `defense_3x.png` are dummy-driver captures inspected at 480×270 and 3× nearest-neighbor scale. The capture uses a precondition fixture, so the displayed initial objective does not represent a fresh player's route. HUD text did not overlap in this static capture; motion, jam state and real display remain to be reviewed.

The local Ollama endpoint was unavailable; `ollama serve` failed with `listen tcp 127.0.0.1:11434: bind: operation not permitted` under the sandbox. No model was downloaded. Real-model parity, audible review, representative real-window performance, a full fresh-save player route, separate-process persistence at the relevant boundaries and the remaining visual acceptance are outstanding. G1 and G2 remain pending.

## Recovery

Pre-change copies and SHA-256 records for modified existing files are in `video_game/_trash/2026-11-11_defense_fix/`. Verify using `shasum -a 256 -c MANIFEST.sha256` from that directory before restoring individual original-relative paths. No source assets, files or previous evidence were removed. These local copies do not replace the independent backup requested by I11.
