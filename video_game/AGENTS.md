# Instructions for work on the game

Read `planning/CURRENT_STATE.md`, `planning/TODO_ROADMAP.md`, the selected task card and `planning/EXECUTION_PROTOCOL.md` before editing. The roadmap is the single task-status owner; the progress log is history. Current audit evidence overrides older contradictory completion claims. Check current files and repository status each session.

- Keep the original terminal package functional. Runtime code belongs in `engine/`, scene routing/input in `engine/scenes/`, authored content in `data/`, exported runtime assets in `assets/`, rebuild masters in `art/source/`, reproducible developer commands in `tools/`, and tests in `tests/`.
- `engine/field_reality.py` integrates MandelaWorld/TemporalRelay with the playable field scene. Do not create standalone mechanics with no normal-input caller. Prototype-room access is documented in `CONTROLS.md`; these connectors are not completed later campaign acts.
- `Campaign` owns persistent state. Use `apply_event` for contact/rewards/timeline and `store_world_state` for JSON room snapshots. Never mutate `_state` in runtime callers or mutate detached `Campaign.state` reads. A validation is unique by `(fragment ID, scenario ID)`, allowing beginner and advanced work from the same fragment.
- `world_states` is an additive campaign field; absent means `{}` for earlier saves. The save envelope remains version 2. Update migration/roundtrip tests whenever state contracts change. Continue starts at the safe bunker checkpoint, with room mechanics restored on reentry. Active projectiles, buffs, energy costs/cooldowns and incomplete lab attempts reset as documented.
- Bind real keys in `engine/input.py` and route field/boss controls through the same mapper. Check press/hold/release, pause/focus loss, death/retry and fresh-save isolation. Do not certify control behavior by directly passing synthetic PlayerInput into a component alone.
- New/Continue must reset transcripts, evidence actions, temporary unlocks and scene actors. Old scene on_exit must not write into the newly assigned campaign.
- Live AI can be skipped when unavailable. Use fake workers for deterministic failure tests and authored offline channels for progression. Never start/download models merely to satisfy a completion claim.
- Tests and capture tools use temporary save directories. Never overwrite player saves or durable evidence during pytest. Run captures with an explicit output directory. Fixture screenshots and component tests are not normal-playthrough evidence.
- Do not promote G2/G3 from a test count, static infographic or scripted reward injection. Record exact commands, actual outcomes, input shortcuts, drivers, fixture preconditions and remaining limits. Do not invent FPS, playtimes, scientific source verification, art review or audible checks. Historical reports may contain invalidated claims.
- Keep locked assets and unique masters. Before editing untracked files, verify recovery copies; before retirement, search all callers and record original/archive paths, reason, replacement and SHA-256 in `_trash/TRASH_LOG.md`. Do not delete recovery archives or mass-prune files based on static import searches.

On this host use `/opt/anaconda3/envs/6equj5_game/bin/python`. Baseline checks:

```
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests tests -q -k 'not live_ollama_stream_if_available and not gate_g1_live_local_model_and_offline_route_parity'
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.validate_content
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets --dry-run
```

Use an appropriate installed Python environment on other hosts. Tests currently require Python 3.12 and game dependencies; the CLI's older advertised Python range does not establish game support there. After packaging changes build a clean wheel, inspect that tests/art/planning/_trash/_temp are excluded, and smoke-launch the installed wheel from outside the repository. Do not commit build output. Update handoff, task status, issue disposition, contracts and controls together.
