# Runtime and content contracts

> Current audit corrections (2026-11-11) below override historical task-stage wording such as “not yet implemented.” See `CURRENT_STATE.md` and the roadmap for actual status.


Implement these contracts in the owning task. Validate schemas with straightforward Python checks first. Introduce a schema library only if a demonstrated maintenance need justifies it. IDs and file formats require a schema_version field when persisted.

## Timing, scenes and input — F04/F07/A02

Scene updates use `dt_seconds`, converted once from Pygame's millisecond clock in the main loop. The CRT adapter accepts seconds and retains its existing millisecond glitch duration interface. Animation durations stored in manifests use milliseconds and convert at the animation boundary.

A scene supports `on_enter(payload)`, `on_exit()`, `handle_event(event)`, `update(dt_seconds)`, and `render(renderer)`. State changes are applied after the current update or event dispatch completes. Exiting a terminal cancels its active request. Shutdown must release worker, audio and display resources even after an exception. The initial I38 fix invalidates stale requests and moves mixer decode/playback to the main update thread; a later measured fade/load stall was fixed by stopping the owned fade before loading, pending final integration. Final integration and audible acceptance remain open.

Combat uses a 1/120-second fixed simulation step and a rendering target of 60 FPS. Bound the accumulator after stalls to prevent an update spiral. Pause freezes game-time objectives and physics. AI timeout accounting uses monotonic wall time. Clamp camera/actor drawing to integer pixel positions while retaining fractional world positions.

Input actions include move, jump, crouch, cover, slide, fire, aim, interact, weapon cycle, ability, timeline shift, pause, confirm and cancel. Terminal text focus consumes typing before gameplay actions. Development shortcuts require an explicit development mode. Controller mappings join the same actions in R02.

## Settings — F07

Settings schema version 1 stores `schema_version` (int = 1), `volume` (int 0–100, default 70), `crt_effects` (bool, default true), and integer window `scale` (int 1–4, default 3). Persisted to `settings.json` in the user data directory. Invalid schema versions, missing files or out-of-range values fall back safely to defaults on read without rewriting the file. Writes stage to a unique sibling temporary file (`.settings.*.tmp`), flush and fsync, re-read and verify the staged payload, and atomically replace the target via `os.replace()`. A failed atomic replacement leaves the prior settings file intact.

## Campaign — F05

CampaignState stores `schema_version`, `save_id`, `current_act`, `current_room`, `checkpoint_id`, `timeline_mode`, `room_flags`, `inventory`, `contacted_civs`, `extracted_fragments`, `validation_records`, `unlocked_weapons`, `unlocked_abilities`, `meters`, `choices`, and `applied_event_ids`.

Use stable string IDs for content and JSON-compatible values at save boundaries. The initial campaign grants the starter maser and first mission access. Story fragment and validation grants require gameplay. Test fixtures can seed later states explicitly.

The six meters are Alignment Confidence, Scientific Certainty, Coordination Capacity, Public Trust, Human Agency, and Biosecurity Readiness. Store integer values clamped to 0–100. Each named campaign event defines bounded deltas in content data and can apply once per event ID. Timed modifiers are tracked separately from permanent meter changes.

`Campaign.apply_event(event)` validates prerequisites and handles grants atomically. Scenes submit typed events. The AI's free text never directly mutates the campaign. Repeated completion, return-to-room, replayed save events, and double-clicks cannot duplicate rewards.

F05 implements schema version 1 with `act_01`, `bunker_hub`, `bunker_start`, snake-case meter IDs and the existing `maser_1420` identifier. The initial mission-access flag is a foundation value; the mission itself is not yet playable. `Campaign.to_dict()` returns the canonical JSON-compatible state, `Campaign.state` returns a detached snapshot, and the temporary mapping interface preserves legacy integer act, display-meter and `validated_protocols` reads. Mutation of snapshots or mapping reads does not alter the owner. Event dictionaries carry `event_id`, `type` and optional `payload`; recognized events are content-defined. `applied_event_ids` prevents replay, and `completed_event_types` prevents a one-shot grant from paying twice under different event IDs. Each grant validates prerequisites, registered IDs and the complete staged state before committing; meter deltas are integers from -100 to 100 and resulting meters are clamped to 0–100.

Only the existing `timeline_shift` is wired to production interaction in F05. Test-only grant definitions and `seeded_development_campaign()` exercise the framework without granting story rewards to a new game. The development validation scenario is a marked fixture, not a scientific finding. C06/C07 must define real evidence, scenarios and reward events before exposing them. F05 validates a fragment's associated contact and a validation's associated fragment; later tasks may add stricter evidence prerequisites. Additional rooms, checkpoints and real scenarios are registered when their owning content tasks implement them. F06 owns actual save files, migration and recovery; F05's dictionary round trip is an in-memory contract check only.

## Save file — F06

Save to a temporary sibling file, flush and sync it, validate the payload, then replace the destination atomically. Keep the previous valid save as a backup. Create missing directories with clear errors on failure.

A load result distinguishes success, missing file, corruption, unsupported future version, and migration failure. Failed writes keep the prior save usable. Loading invalid data preserves the file for recovery. Include a fixture for every supported schema version and migrate it explicitly.

Persist campaign state and checkpoint entry state. Reconstruct transient bullets, particles and in-flight AI requests from a clean checkpoint. Persist completed contact evidence and dialogue summaries as needed. Save at safe transitions, objective completion, and explicit save points. Confirm those semantics in the pause menu.

F06 uses a version-2 JSON envelope containing `schema_version`, canonical `campaign`, and `checkpoint` (`room_id`, `checkpoint_id`). Both checkpoint identifiers must match the validated campaign state. Version 1, defined for migration testing as the campaign-only envelope, is read and migrated in memory; there was no earlier shipped game-save format. A migration is persisted only on a later successful save. Unsupported old versions, future versions, malformed data, migration failure, missing files and I/O failure have distinct outcomes. Each supported version has a development-only fixture.

The default macOS directory is `~/Library/Application Support/6EQUJ5/`; `SIX_GAME_SAVE_DIR` or an injected `SaveStore` directory overrides it. A verified temporary sibling is flushed and synced before replacement. The previous valid primary becomes `campaign.backup.json`; unchanged saves keep a valid existing backup, and a missing or damaged backup is repaired while any damaged/unsupported copy is retained. Explicit recovery preserves the previous primary verbatim before restoring the verified backup. Explicitly starting a new game asks for confirmation when either file exists, and unsupported or corrupt primary files are preserved before replacement. Transient requests and other non-campaign data are not accepted in the save envelope.

F06 saves a new game, bunker timeline changes, safe transitions into or out of the bunker, F5 in the bunker, and bunker shutdown. While the bunker is open, failed saves are shown and departure is held until the save can be retried. There are no playable objective-completion events yet: C07/A01 and later tasks must call the checkpoint-save boundary after their committed objectives. The pause-menu save behavior belongs to F07. Tested interruption covers partial staged writes and replacement failures, not a physical power failure or multiple simultaneous game processes.

## AI messages — C03/C04/C05

Main-thread requests contain `request_id`, `session_id`, `civilization_id`, `user_text`, a frozen campaign context, and history owned by that session. The worker emits plain `token`, `completed`, `failed`, `cancelled`, and `availability` events with matching IDs and a monotonic sequence number.

Use a bounded request queue and bounded output buffering. Allow one active request. Coalesce tokens or backpressure with cancellation checks when the UI is paused. Keep terminal events deliverable under queue saturation.

Configure finite connection/read timeouts on the inference client. Use the existing prompts, initial messages, history model and response cleanup. If the existing streaming function needs optional client/cancellation parameters, preserve existing callers with defaults and tests. Worker cancellation cannot assume it can interrupt a blocking network read immediately. Bound that read, discard stale results, and close or join within a documented shutdown budget.

Check IDs before accepting any event. Switching targets, reopening the terminal, retrying, or cancelling invalidates the previous request. Never append a cancelled or partial reply as a complete exchange. Commit each successful user/assistant pair once. After an interrupted reply, present a clear retry/offline route.

Curated offline dialogue covers every required readiness and evidence route. AI availability is optional for progression. Retry the service after an explicit reconnect without restarting the game. The session limit is 12 completed exchanges. Counters, triangulation consequences and session-end behavior are defined in mission data and tested at 11, 12 and beyond.

## Protocols and scientific evidence — C06/C07/S04

A mission specifies civilization ID, unlock prerequisites, allowed fragment IDs, readiness activities, accepted evidence, hazards, reward, repeat behavior and offline route. Model output may propose a structured candidate. The engine validates its shape, ID, prerequisites and completed player evidence before granting anything. Ignore fabricated IDs, malformed tags and attempts to grant unrelated items.

A validation record stores scenario ID/version, claim ID, observations, result, confidence, claim tier, source references, and deployment decision. Claims have `established`, `plausible`, or `speculative` tier. Trustworthiness of a transmission is a separate field. A speculative claim is not automatically a hostile trap.

The science pipeline is decode → experiment → replication check → risk/deployment choice → observed consequence. Workbench gameplay uses bounded, authored abstractions. Any educational claim needs an inspected primary source recorded in the scenario. Fictional gravity/time/reality abilities carry speculative labeling. Formal puzzles evaluate small finite claims and evidence.

## Asset manifest — F03/F08/C01

Top-level fields include schema_version and assets. Each entry contains stable ID, type, relative runtime path, dimensions, alpha_mode, source_path, source_hash, output_hash, generator_version, authored_lock, review_status and provenance. Animation entries add cell_size, frame_rects, frame_duration_ms, loop, foot_pivot, hurtbox, and weapon attachment point.

Allowed review states are `concept`, `candidate`, `reviewed`, and `retired`. Preserve the legacy `production_v2` marker through a compatibility loader while recording visual review status separately. A technical dimension check cannot set `reviewed`.

Paths resolve from an explicitly declared manifest directory or asset root. Reject absolute paths and traversal outside the asset root for runtime assets. Validate referenced files and dimensions before caching surfaces. Missing required resources produce an actionable load error. Optional effects may use a documented fallback.

Locked assets remain untouched by normal builds, including related environment, chart, composite and metadata outputs. Replacements require an explicit selection and archive record. Stage exports in a temporary location, validate the complete group, and promote only after success. Interrupted builds preserve the previous manifest and its usable assets.

F03 retains the existing civilization and bunker manifest formats until F08. The civilization ID, `mateo`, `bunker`, and `review` are the selectable group boundaries documented in QUALITY_GATES.md. The journal backs up each file before promotion and restores the full preceding group at the next build, game start or preview start after an interruption. Promotion is sequential, with the manifest last; do not rebuild while a game is already running. The F08 schema and richer provenance fields above are not yet implemented.

Source masters have stable names and explicit mappings. Replace wildcard selection of the first matching timestamped concept. Preserve original source names in provenance records when migrating.

## Room data — A01/S06

Room JSON contains schema_version, room_id, act_id, tile_size=16, width_tiles, height_tiles, tileset_id, background_layers, collision_layers, objects, spawns, checkpoints, exits, objectives, required_flags and rewards.

Tile-grid dimensions are independent of the 480×270 viewport. Handle the viewport's partial bottom tile without stretching artwork. Collision tiles distinguish solid, one-way, hazard and empty. Objects have stable IDs, type, world position, properties and optional timeline visibility.

Each exit names a destination room and spawn. Validate destination existence, required flags, collision-free spawns and return paths. Contact/lab rewards that open an exit must be obtainable before that exit is required. A seeded RNG handles reproducible encounters and tests.

Timelines `2029_CORE` and `1977_ANALOG` have aligned collision geometry and object IDs. A swap checks the player footprint and required objects before commit. Use a documented nearest-safe location or reject with feedback when blocked. Repeated swaps preserve unique pickups, dead enemies, doors and objectives according to explicit persistence rules.

## Combat, bosses and objectives — A05/A08/A09

Use world coordinates for hitboxes and camera coordinates for rendering. Projectiles resolve swept travel against walls and targets to prevent tunneling. Damage events include source ID, target ID, amount, damage type and unique hit ID. Handle simultaneous hits and invulnerability consistently.

Enemies and bosses expose update, damage, render and reset behavior. Attack states have windup, active and recovery intervals. Telegraphs visibly precede damage. Boss reset reconstructs phase state, projectiles, arena and checkpoint consistently.

Dish defense tracks `idle`, `active`, `failed`, `completed`. The active duration is 72 seconds of gameplay time. Six intensity bins last 12 seconds each and are `[6, 14, 26, 30, 19, 5]`. The last two bins decrease from the peak. Pause and retries have explicit behavior. Completion grants its reward once.

## Endings — P08

Evaluate ending rules in descending priority against saved campaign decisions. Resolve exactly one ending. Default proposed rules are control-delegation choice → Controlled Peace, otherwise a verified dossier and Human Agency at least 60 → Fermi Override, otherwise Severed Signal. Exact thresholds live in endings.json and are recorded as tunable design choices.

All routes finish the campaign. Preview final consequences before commitment and support returning to a pre-finale save. Ending text reflects actual decisions and meters.

## Current Milestone 3 persistence and input

Campaign state version 1 adds `world_states`, a room-ID-to-JSON-object map. Campaign construction adds `{}` when absent in older envelope versions 1/2; the outer save version remains 2. `Campaign.store_world_state` deep-copies and validates the staged campaign including JSON finite-number checks. Room snapshots hold world persistent objects, moving platforms, timeline selection, modified collision layers, object properties and relay state. Bunker snapshots hold scenario-keyed consequence notices with delivery flags. Continue starts in the bunker and restores room mechanics on reentry. Incomplete lab experiments reset when leaving or selecting another scenario; no reward is committed for them. Active bullets, request streams, temporary buffs, energy/cooldowns and scene actors reconstruct cleanly on New/Continue.

A validation record is unique by `(id, scenario_id)`; id remains the source fragment/protocol and scenario_id distinguishes beginner/advanced validation. Each scenario's deployment events remain one-shot. Contact is a validated `record_contact` event with civilization_id payload, not a private-state edit. All science scenarios have keyboard progression; H exposes complete prompts and explanations without clipped critical text. Deployment queues one persistent consequence message, delivered on a later bunker entry, independently from immediate bounded meter updates.

Field and boss share InputManager. C is crouch; K/Alt activates abilities; Shift dashes; G grapples; Q cycles weapons; R cycles abilities except explicit death/defense retry. The I36 retry isolation fix has independent acceptance pending final integration; death/defense retry clears held and mapped input. Focus loss clears the scene's legacy held-key cache as well as the action mapper. The post-Act-I annex is a prototype normal-input connector for mechanics rooms, not the completed Act IV campaign. Its controls and checkpoint reset rules are in `video_game/CONTROLS.md`. `/restart` resets only the receiver's 12-exchange session counter, preserving campaign evidence and one-shot grants.

### Prototype science prerequisite and future campaign identity

The current eight authored scenarios all require the earned `FASR-001` fragment, including those whose target protocol IDs are `FASR-002`, `FASR-003`, or `FASR-004`. This is a prototype access mapping, not proof that those later civilizations were contacted or their full arcs completed. Validation identity remains `(id, scenario_id)` and existing saves must retain their distinct records. P06 must connect each civilization arc to its assigned act; P07 retains responsibility for every listed civilization reward and its actual mission ID. Any later prerequisite migration must preserve earned saves and avoid rewarding an unrelated civilization merely because a prototype scenario was completed.

### S09 prototype encounter placement and checkpoint reset

In a reality connector, N selects the next pair only after finding safe positions in the active collision grid: grounded actors require full solid/one-way support and aerial actors require clear hover space. Both footprints must avoid hazards, solids, the player and each other; a rejected placement retains the previous pair and cycle index. Successful replacement clears old enemies and both sides' active projectiles. A field checkpoint respawn resets enemy actors/statuses and clears projectiles; the defense independently treats casualty as failure. These connectors are prototypes, not later-act completion.

On field room relocation or exit, active grapple and anchor, dash/slide/wall-slide state, associated hit sets and transient velocity are cleared; health, equipment, cooldown timers and persistent campaign state remain. Room loads discard queued jump/fire edges. G toggles grapple with one action per physical press; jump remains an alternate release.
