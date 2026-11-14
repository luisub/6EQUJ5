# Runtime and content contracts

## New-game opening — 2026-11-13

`data/opening_story.json` schema 1 contains three authored title/text pages. The title's START and confirmed NEW paths request an opening over the bunker, while Continue and subsequent bunker reentry do not. Pages auto-advance after 14 seconds; one fresh Enter, Space, arrow, controller A/D-pad or on-screen-arrow click skips all pages. The initiating event cannot also skip, and held inputs remain guarded until release/neutral. Pause/focus freezes timing; missing or malformed pages return to the playable bunker. The opening does not modify campaign flags, rewards, save envelope or game physics. [Evidence](../../_trash/2026-11-13_separation/historical-reviews/docs/planning/evidence/OPENING_STORY/2026-11-13_basement_intro/report.md).

## Hazard timing and 003 asset registration — 2026-11-13

An early INCOMING warning precedes the approaching obstacle; HOLD JUMP is displayed only in a feasible action window using actual relative motion and the grounded player's jump. The full authored sprite and visible-alpha bounds remain unchanged, while contact uses a centered lower core of at most 16×18 logical pixels inside the visible bounds. Damage, one-hit-per-pass behavior, warning duration, travel speed and player jump physics remain unchanged. The cue is suppressed for paused/modal, airborne/dead, nonclosing, unsafe/late and already-hit cases. Eighteen mapped carrier/wagon/stone scenarios with 0–0.2 s response passed, without proving every terrain or human reaction. [Evidence](../../_trash/2026-11-13_separation/historical-reviews/docs/planning/evidence/WORLD_ART/2026-11-13_sequential_continuation/hazard_cue_v01/report.md).

The add-only `realm_fasr_003_v1/background.png` family is opaque 1920×540; `guardian_fasr_003/body.png` is a transparent 256×192 static pose registered to the existing 128×96 logical boss rectangle and muzzle. Missing/invalid alpha art uses the verified fallback rather than crashing. [Promotion](../../_trash/2026-11-13_separation/historical-reviews/docs/planning/evidence/WORLD_ART/2026-11-13_sequential_continuation/technical_v01/live_pair_promotion_v01/report.md).

## Planet threats and local hazards — 2026-11-13

`data/planet_encounters.json` schema 1 maps each of the eleven alien world IDs to a unique minor-threat ID/art family, movement style and bounded encounter data. Each 3840-pixel field has 18 finite triggers, starting at x=240, spaced 180 pixels, with at most four active foes. Authored health is 110–160; the existing starter damage, cadence, player physics, saves and Assisted scaling are preserved. Each planet hazard uses the matching local art ID, an early warning of at least 1.25 s, bounded contact damage and cooldown; wait for the actionable HOLD JUMP cue, then press and hold jump. Modern wagons are limited to modern outdoor rooms; fictional stone effigies are used in the three Göbekli traversal fields. The 84 Act V/alien high platforms each retain their original top with one-way steps at y=208 and y=176. Static poses use runtime motion, not full animation cycles. [Schema, evidence and limits](../../_trash/2026-11-13_separation/historical-reviews/docs/planning/evidence/PLANET_ENCOUNTERS/2026-11-13_world_threats/report.md).

## Galaxy navigation and recovery — 2026-11-13

`data/galaxy_navigation.json` contains twelve fictionally placed, normalized schematic display markers, including an unknown SCAN-H and a terrestrial-memory echo. It is presentation data and makes no astronomical coordinate claim. `world_states["bunker_hub"]["alien_journey"]["pending_transit"]` holds only validated `source` and `destination` for the next ordered earned leg. Saves retain the existing version-2 envelope. Receipt and pending leg are saved before travel; Continue replays a pending leg, while old ledgers without one resume directly. Arrival clears the pending value only after successful durable save; failure keeps it retryable. New game clears session travel, and scene transitions clear held input. The loader requires the complete hash-validated map/vortex family or displays a plain fallback; no receipt is inferred from art or travel. [Evidence](../../_trash/2026-11-13_separation/historical-reviews/docs/planning/evidence/VISUAL_POLISH/2026-11-13_solid_activity_laser/report.md).

> Current audit corrections (2026-11-11) below override historical task-stage wording such as “not yet implemented.” See `CURRENT_STATE.md` and the roadmap for actual status.


Implement these contracts in the owning task. Validate schemas with straightforward Python checks first. Introduce a schema library only if a demonstrated maintenance need justifies it. IDs and file formats require a schema_version field when persisted.

## Compact starter-maser firing — 2026-11-13

For normal starter-maser tap/repeat, field and boss use a cached optional 96×24 RGBA energy-filament family at the live muzzle, with bounded short trace clipped to collision and projectile heads still visible. An invalid/missing family falls back to the existing firing presentation. A light-only event preserves the brief actor illumination and eligible Ohio approach material bounce without drawing the legacy muzzle burst. Charged and non-starter paths remain unchanged. Assisted spacing is 1° across five rays (−2°, −1°, 0°, +1°, +2°); Classic uses one. Count, cadence, damage and per-shot shared-hit semantics are preserved. Scene transitions, pause/focus-loss and retry continue to clear held controls and transient effects. See [bounded runtime and test evidence](../../_trash/2026-11-13_separation/historical-reviews/docs/planning/evidence/SHOOTING/2026-11-13_compact_energy_stream/SHOOTING_REPORT.md).

## Alien journey contract — active development (2026-11-13)

`data/alien_journey.json` schema 1 defines an ordered list of eleven unique world IDs and canonical civilization IDs, field/arena paths, entry spawn, guardian ID/defeat event and flag, portrait reference, contact pages and next world. Its `rooms` map uses the field route metadata shape; `final_earth` identifies a separate Core Prime arena and `earth_ai_defeated` event/flag. All rooms retain the existing `act_05` campaign registry context. The Earth Göbekli encounter uses `portal_warden_defeated`; preserve old `core_prime_defeated` for legacy saves but never treat it as the new final-AI victory.

A journey receipt is distinct from `contacted_civs`, extracted fragments and validation records and may only be committed after its guardian is defeated and the contact pages are acknowledged. All eleven receipts must gate both Earth-return entry and final victory. Pending conversation and receipt state must survive interruption/reload without duplication; `world_states` is additive and the outer save envelope remains version 2. Earth route signal milestones contain no contact/fragment grant events; the original Ohio receiver and lab stay unchanged. The active runtime stores `world_states["bunker_hub"]["alien_journey"]` with version, world ID, stage, checkpoint and ordered receipt list. Final-page acknowledgement records the receipt and existing contact/fragment grants when absent, saves the pending world leg, then starts map/vortex transit; a failed save remains retryable and blocks transition. Intermediate pages may advance with time; the final page requires input. A [portal-seeded mapped-input probe](../../_trash/2026-11-13_separation/historical-reviews/docs/planning/evidence/WORLD_EXPANSION/2026-11-13_connected_worlds/content/alien_route_probe_report.md) exercised all eleven and loaded the actual final autosave in a fresh child. This does not establish a fresh full-campaign human playthrough.

## Connected-world route checkpoint — active implementation (2026-11-13)

`data/campaign_route.json` schema 1 maps act IDs to entry room/spawn, unlock and completion flags, boss ID/event, next act, art ID and authored pages. It maps room IDs to level paths, act IDs, previous/next IDs, background art/view, finite encounters and physical-location milestones. Earth milestones are scouting clues with no contact/fragment grants; they must not create lab validation records or imply unimplemented abilities. Room progression is unlocked by the prior boss flag; a reward is never needed to acquire itself.

Route recovery is additive in `world_states["bunker_hub"]["campaign_route"]` with `room_id` and `checkpoint`; it is written through `Campaign.store_world_state`, with the existing save envelope version 2 unchanged. Continue enters the bunker; departure resumes a valid checkpoint in the highest earned act, falling back to that act's entrance. Field checkpoint and room handoffs save through the campaign store; a failed transition save must not silently advance. The existing Dodleston relay snapshot and mechanisms remain intact, with an entrance-side route onward that does not require the locked bulkhead. Active projectiles and transient actors reset. See [route probe](../../_trash/2026-11-13_separation/historical-reviews/docs/planning/evidence/WORLD_EXPANSION/2026-11-13_connected_worlds/content/route_probe_report.md) for bounded evidence and remaining acceptance limits.

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

Each exit names a destination room and spawn. Validate destination existence, required flags, collision-free spawns and return paths. Contact/lab rewards that open an exit must be obtainable before that exit is required. A seeded RNG handles reproducible encounters and tests. The registered Act I field route is approach → perimeter road → Ohio campus → salvage outer → salvage yard → salvage runoff → dish service → dish catwalk → dish return. Return exits and the catwalk shortcut remain; five new room and checkpoint registrations do not change the save envelope. Forty-six finite forward-encounter opportunities use a living cap of four Assisted or three Classic; placements can be skipped or living enemies retreat, neither counted as kills.

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

Bunker Enter, keypad Enter and Up invoke the same guarded surface departure from any position; controller A maps to Enter. Space/NEXT invokes the guided objective, while E or a nearby prompt click invokes the available station. The existing first-mission and failed-save guards remain; completed Act I departure returns to the Ohio approach without resetting campaign progress. This changes input/routing behavior, not the save schema or a playable Act II.

Field and boss share InputManager. In field, Up is consumed by a currently available exit or feedhorn interaction and otherwise jumps; Space remains jump. The visible contextual button invokes the same guarded interaction before pointer fire is routed. C is crouch; K/Alt activates abilities; Shift dashes; G grapples; Q cycles weapons; R cycles abilities except explicit death/defense retry. The I36 retry isolation fix has independent acceptance pending final integration; death/defense retry clears held and mapped input; fresh Space or click and legacy R retry failed defense or boss death. Assisted forward field-to-field transitions may hand off held forward movement, repeat fire and aim only, with no carried action edge or charge; gates and explicit boss entry remain. Focus loss clears the scene's legacy held-key cache as well as the action mapper. The post-Act-I annex is a prototype normal-input connector for mechanics rooms, not the completed Act IV campaign. Its controls and checkpoint reset rules are in `video_game/CONTROLS.md`. `/restart` resets only the receiver's 12-exchange session counter, preserving campaign evidence and one-shot grants.

### Prototype science prerequisite and future campaign identity

The current eight authored scenarios all require the earned `FASR-001` fragment, including those whose target protocol IDs are `FASR-002`, `FASR-003`, or `FASR-004`. This is a prototype access mapping, not proof that those later civilizations were contacted or their full arcs completed. Validation identity remains `(id, scenario_id)` and existing saves must retain their distinct records. P06 must connect each civilization arc to its assigned act; P07 retains responsibility for every listed civilization reward and its actual mission ID. Any later prerequisite migration must preserve earned saves and avoid rewarding an unrelated civilization merely because a prototype scenario was completed.

### S09 prototype encounter placement and checkpoint reset

In a reality connector, N selects the next pair only after finding safe positions in the active collision grid: grounded actors require full solid/one-way support and aerial actors require clear hover space. Both footprints must avoid hazards, solids, the player and each other; a rejected placement retains the previous pair and cycle index. Successful replacement clears old enemies and both sides' active projectiles. A field checkpoint respawn resets enemy actors/statuses and clears projectiles; the defense independently treats casualty as failure. These connectors are prototypes, not later-act completion.

On field room relocation or exit, active grapple and anchor, dash/slide/wall-slide state, associated hit sets and transient velocity are cleared; health, equipment, cooldown timers and persistent campaign state remain. Room loads discard queued jump/fire edges. G toggles grapple with one action per physical press; jump remains an alternate release.


## 2026-11-13 intro and temporary combat presentation

- Opening schema 1 accepts 3–4 validated pages; optional `visual: "galaxy_map"` renders an inset in the same basement dialog. The shipped fourth page uses the validated navigation locations and existing map asset. Next/N/controller X advances one page; legacy skip inputs remain guarded through release. Continue never replays the opening. No transit ledger is modified by the briefing.
- `ArsenalManager.temporary_id`, `temporary_remaining` and `temporary_weapon` are transient. Arc Lance lasts 18 gameplay seconds (90 damage, two-target piercing); Nova Scatter lasts 16 (70 damage, three rays, one damage application per target per volley). Pickups replace rather than stack. Timers pause with play, expiry returns to starter maser, and checkpoint/scene/New/Continue resets discard them. They are excluded from arsenal serialization and campaign data; save envelope stays version 2.
- Supply cells are finite, on collision-checked supported sites, with one collection per room visit. Catwalk supplies begin beyond the original timed-defense area. Field targets: Ohio 206 (formerly 156), later Earth 96 (72), alien worlds 264 (198). Alien worlds have 24 arrivals each, spacing 132, ending at x=3276; caps are five active alien enemies, five Assisted/four Classic forward enemies. Existing warning/clearance logic remains.
- `CombatFeedback` caps events at 24, cached native burst frames at 256 and light stamps at 64. Beam rotation caches remain capped at 192. Cool white/cyan beams, warm destruction and gold rewards use consistent matching light. No full-screen flash or camera shake is added. Effects do not modify collision/damage or source assets.
