# Code standards and file map

This document owns the target structure. Paths below are relative to `video_game/`. Create each file when its task begins. Existing builders migrate with their callers and source paths during F08. The original terminal package remains at `src/signal_6EQUJ5/` in the repository.

## Runtime and dependency direction

`main.py` owns lifecycle and resources. `GameStateMachine` selects scenes. Scenes receive shared services and call domain modules. Domain modules use validated content data. Asset tools depend on source masters and export manifests. Runtime code loads exported assets. The AI adapter calls the existing terminal backend's data and inference interfaces.

Pygame display, event and surface operations occur on the main thread. The AudioManager uses bounded background byte reads and handles mixer decode/playback on the main update thread; the I38 fade/load fix awaits final integration, and real-device audio acceptance remains open. The AI worker exchanges plain data with that thread. Campaign mutation has one owner. Avoid circular imports by passing required services through constructors.

## Target tree and responsibilities

| Path | Responsibility and creation task |
|---|---|
| `main.py` | Initialization, frame clock, event dispatch, shutdown, CLI flags. Existing, F04/F07 |
| `engine/config.py` | Display constants, shared paths and global defaults. Existing, F05 |
| `engine/state_machine.py` | Scene routing, enter/exit, deferred transitions. Existing, F04 |
| `engine/crt_renderer.py` | Canvas scaling and optional postprocessing. Existing |
| `engine/assets.py` | Manifest loading, path validation, cached surfaces and frames. F04 |
| `engine/asset_transactions.py` | F03 staged group promotion, hash-verified recovery archives and interrupted-build recovery before startup. |
| `engine/input.py` | Action mapping, pressed/held/released state, input focus. F07 |
| `engine/settings.py` | User controls, volume, effects, display and settings persistence. F07 |
| `engine/campaign.py` | Campaign data validation and idempotent progression. F05 |
| `engine/save_game.py` | Versioned atomic saves, migrations, backups and load errors. F06 |
| `engine/audio.py` | Music transitions, sound channels, volume, missing-device behavior. A12 |
| `engine/animation.py` | Frame timing, pivots, clip selection and attachment points. A04 |
| `engine/world.py` | Room data, tile collision, triggers, camera and spawn validation. A01 |
| `engine/player.py` | Movement, health, cover and locomotion state. A02/A03 |
| `engine/weapons.py` | Weapon data, fire rules, projectiles and collision. A05 |
| `engine/enemies.py` | Enemy state machines and attack telegraphs. A06 |
| `engine/objectives.py` | Mission objectives, rewards, 72-second defense and reset rules. A08 |
| `engine/effects.py` | Bounded particles, flashes and screen shake. A12 |
| `engine/ai_adapter.py` | Existing civilization data/history and configurable inference client. C03 |
| `engine/ai_worker.py` | Request queue, token events, cancellation and shutdown. C03 |
| `engine/contact_session.py` | Scan/contact state, dialogue exchanges and session IDs. C04 |
| `engine/protocols.py` | Deterministic evidence, fragment and validated-reward rules. C06 |
| `engine/mandela_world.py` | Timeline transactions and valid geometry swaps. S06 |
| `engine/temporal_relay.py` | Dodleston historical actions and consequences. S07 |
| `engine/abilities.py` | Civilization powers, costs, timers and counters. S05 |
| `engine/endings.py` | Ending evaluation and epilogue data. P08 |
| `engine/scenes/base.py` | Minimal lifecycle interface. F04 |
| `engine/scenes/title.py` | New game, continue and opening briefing. F04/F06 |
| `engine/scenes/bunker.py` | Bunker scene and proximity-based station interactions. F04/A07 |
| `engine/scenes/terminal.py` | Receiver controls, text input and transcript presentation. F04/C04 |
| `engine/scenes/lab.py` | Workbench selection and validation feedback. C07 |
| `engine/scenes/field.py` | Coordinates world, actors, projectiles and objectives. A01 |
| `engine/scenes/boss.py` | Bounty intro and boss arena lifecycle. A09 |
| `engine/scenes/ending.py` | Finale results and epilogue playback. P08 |
| `engine/ui/hud.py` | Player telemetry, objectives and campaign meter views. F04/A07 |
| `engine/ui/text.py` | Wrapping, scrolling, glyph fallback and readable transcript layout. C04 |
| `engine/ui/pause.py` | Pause/settings overlay and focus-safe resume. F07 |
| `engine/labs/formal.py` | Claim/evidence classification and counterexample puzzle. C07 |
| `engine/labs/quantum.py` | Double-slit/coherence simulation and observation tasks. S01 |
| `engine/labs/neuro.py` | Circuit reconstruction and intervention puzzle. S02 |
| `engine/labs/biosecurity.py` | Abstract trial/resource allocation and uncertainty puzzle. S03 |
| `engine/bosses/base.py` | Shared damage, phase and reset interface. A09 |
| `engine/bosses/greenkeeper.py` | Act I boss. A09 |
| `engine/bosses/synchronicity.py` | Act II boss. P01c |
| `engine/bosses/amalgam.py` | Act III boss. P02c |
| `engine/bosses/mandela_architect.py` | Act IV boss. P03c |
| `engine/bosses/core_prime.py` | Act V two-stage finale. P04c |
| `data/campaign.json` | Act ordering, room links, checkpoints and unlock prerequisites. F05/P05 |
| `data/balance.json` | Tunable movement, combat, timers, meter changes and difficulty. A02 |
| `data/civilization_missions.json` | Eleven readiness/evidence/reward definitions. C06/P06 |
| `data/dialogue_offline.json` | Curated per-civilization branches and fallback replies. C05 |
| `data/lab_scenarios.json` | Versioned puzzle inputs, targets, claims and references. C07/S04 |
| `data/endings.json` | Ending rules and epilogue text. P08 |
| `data/levels/act_01/*.json` through `act_05/*.json` | Room files named in CONTENT_PLAN.md. A01/P01–P04 |
| `data/levels/flashback/ehman_1977.json` | Playable historical sequence. S08 |
| `assets/manifest.json` | Runtime asset index and source provenance links. F08 |
| `assets/civilizations/manifest.json` | Existing civilization resource IDs and portrait metadata. F03/C01 |
| `assets/civilizations/fasr-*_face.png`, `*_env.png`, `*_constellation.png` | Runtime portrait layers and source charts. Existing |
| `assets/bunker/scene_manifest.json`, six named layers | Existing bunker resources, alpha migration C02 |
| `assets/sprites/mateo/manifest.json`, `<outfit>/<animation>.png` | Organized sprite sheets and frame metadata. F08/A04 |
| `assets/sprites/enemies/<enemy-id>/<animation>.png` | Faction animations. A06/S09 |
| `assets/sprites/bosses/<boss-id>/<animation>.png` | Boss animations. A09/P01–P04 |
| `assets/environments/<biome>/manifest.json`, `tiles.png`, `props.png`, `background_*.png` | Biome art and layers. A11/P01–P04 |
| `assets/audio/music/*.mp3`, `assets/audio/sfx/*.wav` | Runtime audio. A12 |
| `assets/ui/font.png`, `font.json`, `icons.png` | Approved font atlas, glyph metrics and HUD icons. C04/R01 |
| `art/source/civilizations/<civ-id>/`, `art/source/mateo/`, `art/source/bunker/` | Rebuild masters, layers and original concept references. F08 |
| `art/source/enemies/`, `art/source/bosses/`, `art/source/environments/` | Masters for later production tasks |
| `art/palettes/materials.json` | Material ramps and palette metadata. C01 |
| `tools/build_assets.py`, `civ_art_builder.py`, `bunker_scene_builder.py`, `mateo_sprite_builder.py` | Safe build coordinator and asset generators. F08 |
| `tools/preview_assets.py` | Intentional screenshot export command. F02/F08 |
| `tools/validate_content.py` | Validate manifests, IDs, references, rooms and objective routes. A01/P05 |
| `tools/profile_game.py` | Reproducible frame-time and memory benchmark. A13/R04 |
| `tests/test_engine_boot.py`, `test_checkpoint_audit.py` | Existing baseline and focused structural checks. F02 |
| `tests/test_assets.py`, `test_campaign.py`, `test_save_game.py` | Resource, reward and persistence regressions |
| `tests/test_ai_worker.py`, `test_contact_session.py` | Fake-client latency, cancellation, session and offline behavior |
| `tests/test_world.py`, `test_player.py`, `test_combat.py`, `test_objectives.py` | Physics and gameplay regressions |
| `tests/test_labs.py`, `test_timelines.py`, `test_content.py`, `test_endings.py` | Puzzle, time and full-content regressions |
| `tests/fixtures/` | Small authored edge cases and fake inference data |
| `packaging/game.spec` | PyInstaller entry/resource definition. R06 |
| `README.md`, `CREDITS.md` | Game installation, controls, model setup, source credits. R06 |
| `planning/` | Execution instructions and durable evidence |
| `_temp/<task-id>/` | Disposable task-local output |
| `_trash/<date>_<task-id>/` | Logged retired material excluded from runtime and packaging |

Add `__init__.py` only to Python package directories as they are created. Game saves, settings and logs live in the user's platform application-data directory. Development and packaging commands must accept explicit temporary directories for tests.

## Migration order

1. F02 removes the duplicated handwritten Python-file allowlist, hard line cap, and screenshot writes from tests. Keep meaningful header, syntax, import, manifest and behavior checks. Report suspected unused files for review.
2. F03 makes builder writes opt-in and transactional before moving any assets.
3. F04 extracts scenes from the current state_machine.py and introduces cached loading. Keep existing imports used by tests working through a small compatibility re-export during migration. Remove that re-export after all callers migrate and tests pass.
4. F08 moves builders from `engine/` to `tools/`, source concepts to `art/source/`, generated review sheets to evidence, and sprites into named outfit folders. Change all callers/manifests in the same checkpoint. Existing archived comparison art is still a build dependency until its reference is migrated.
5. Retire `engine/imports.py` only after inspecting actual callers and replacing broad exports with explicit imports. Game installation should make the original package importable without repeated sys.path edits.
6. Retain required `*_composite.png` files while callers use them. Once equivalent composition is verified and all references are migrated, retain one evidence composite and retire redundant runtime copies.

## Readability rules

Use clear names, direct imports, explicit units, and short responsibilities. Include purpose and modification guidance in public module headers. Split modules when responsibilities become independent. File length is a review signal. Formatting must remain readable.

Shared global defaults belong in config.py. Combat tuning belongs in balance.json. Per-room values belong in room data. Asset metadata belongs in manifests. Each value has one owner.

Tests establish runtime contracts and specific failure cases. Static AST checks cannot establish that every function or dynamic asset is unused. Cleanup requires reference and runtime evidence.

Default game environment is Python 3.12 in `/opt/anaconda3/envs/6equj5_game`. Keep the CLI's supported Python range intact when shared files change. Declare game-specific dependencies and entry points during F08/R06 without imposing graphical dependencies on a CLI-only install.

## Current integration boundaries (2026-11-11 audit)

- `engine/field_reality.py`: active MandelaWorld, relay panel and durable room snapshots; called by field lifecycle/events/update/render.
- `engine/scenes/field.py`: traversal/combat/flashback integration; use the shared InputManager. On room relocation or exit it calls `Player.cancel_traversal()` to clear active motion/anchors without resetting health, equipment or cooldowns; room load also drops pending field jump/fire edges.
- `engine/player.py` / `state_machine.py`: `discard_pending_edges()` drops buffered fixed-step input on pause/focus/resize; `cancel_traversal()` clears transient movement on field relocation or exit.
- `engine/scenes/boss.py`: same action mapper and validated arsenal/abilities as the field scene; death waits for explicit retry.
- `engine/campaign.py`: only owner for persistent contact/reward/timeline and room snapshot mutations. Scenario-specific validation identity supports advanced scenarios.
- `tests/test_runtime_integration.py`: eight keyboard-driven lab scenarios, timeline/relay/flashback entry and controls, persistence through SaveStore and a separate process, new-game isolation, grapple/dash/tape, boss input/retry and atomic relay rejection. Prerequisite fixtures are disclosed in the tests.
- `tools/capture_runtime_audit.py`: real fixture-scene captures, never a gate-certification chart. See `tools/README.md` for current commands and retired generators.

`enemies.py`, `weapons.py`, `player.py` and the lab modules remain large; split them by responsibility only with their runtime callers and behavior tests preserved. Length alone is not grounds for rewriting working logic. Do not create parallel implementations.

- `tools/act_01_traversal.py` and `tools/mechanics_route.py`: earned fresh-save scripted normal-input Act I and combined mechanics routes, respectively, with disposable saves and explicit output directories; not human play. `tools/faction_runtime_audit.py` uses a disclosed Act I completion fixture for M/N captures. See `tools/README.md`.
