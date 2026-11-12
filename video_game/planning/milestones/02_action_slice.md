# Complete playable Act I

Use EXECUTION_PROTOCOL.md for the session workflow and QUALITY_GATES.md for shared acceptance. Paths are relative to the repository root. The authoritative status table is TODO_ROADMAP.md. Create only files used by the selected task.

This milestone ends at gate G2.

<a id="a01"></a>

## A01 — Load a playable room and camera

Dependencies — F08. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/world.py`
- `video_game/engine/scenes/field.py`
- `video_game/data/levels/act_01/approach.json`
- `video_game/tools/validate_content.py`
- `video_game/tests/test_world.py`

Implementation sequence

1. Implement room schema validation and tile/prop/background loading.
2. Add solid, one-way, hazard and empty collision categories.
3. Implement camera bounds, stable pixel positioning, spawn validation and an exit back to bunker.
4. Author a short traversal blockout with obstacles, platforms, cover and a checkpoint.
5. Connect Field Ops to this room through the real scene router.

Acceptance checks

- [x] Room loads from data with actionable errors for invalid references.
- [x] Viewport handles partial tiles and room edges correctly.
- [x] Player spawn and exit locations are collision-free.
- [x] Normal bunker navigation reaches the room.

Save evidence under `video_game/planning/evidence/A01/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a02"></a>

## A02 — Implement stable player locomotion

Dependencies — A01. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/player.py`
- `video_game/data/balance.json`
- `video_game/main.py`
- `video_game/tests/test_player.py`

Implementation sequence

1. Implement fixed-step movement, gravity, jump, landing and horizontal/vertical collision.
2. Add configurable jump buffer, coyote time and acceleration/deceleration values.
3. Support one-way platforms, hazards, knockback, health and checkpoint respawn.
4. Clamp simulation backlog after stalls and keep world coordinates independent of camera.
5. Measure travel and jump results at multiple render rates.

Acceptance checks

- [x] Equivalent inputs at 30/60/120 render FPS produce matching movement within documented tolerance.
- [x] Corners, ceilings, one-way edges and fast falls cannot tunnel or trap the player.
- [x] Death returns to a valid checkpoint with coherent state.

Save evidence under `video_game/planning/evidence/A02/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a03"></a>

## A03 — Implement cover, crouch and slide-kick

Dependencies — A02. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/player.py`
- `video_game/engine/world.py`
- `video_game/data/balance.json`
- `video_game/tests/test_player.py`

Implementation sequence

1. Add crouch and legal standing-clearance checks.
2. Implement foreground cover and background doorway cover with explicit protection directions.
3. Add slide duration, cooldown, collision bounds and kick damage event.
4. Give cover entry/exit clear animation states and prevent firing through forbidden geometry.
5. Author a room section that teaches cover and slide through visible cues.

Acceptance checks

- [x] Protection matches attack direction and cover type.
- [x] Standing under low ceilings is rejected safely.
- [x] Sliding cannot cross solid walls or repeatedly damage one target per slide.
- [x] Pause/death/reset restore the right locomotion state.

Save evidence under `video_game/planning/evidence/A03/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a04"></a>

## A04 — Turn Mateo poses into reviewed animation clips

Dependencies — A03. Resource flag — GPU_IMAGE.

Files to create or modify

- `video_game/engine/animation.py`
- `video_game/assets/sprites/mateo/manifest.json`
- `video_game/art/source/mateo/`
- `video_game/tests/test_assets.py`

Implementation sequence

1. Use the existing three outfits as source material and review the current eleven poses in motion.
2. Author missing locomotion, transition, recoil, hurt and death frames using ART_PRODUCTION.md.
3. Record frame rectangles, timing, foot pivots, hurtboxes and weapon attachments.
4. Connect animation states to actual player state and preserve mirrored registration.
5. Create a movement/pose preview at combat and bunker scale.

Acceptance checks

- [x] No foot sliding, clipped limbs, jumping pivots or inconsistent outfit transitions remain at the review threshold.
- [x] Animation timings are frame-rate independent.
- [x] Manifest frame bounds and attachment points validate.

Save evidence under `video_game/planning/evidence/A04/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a05"></a>

## A05 — Implement the starter weapon and projectile loop

Dependencies — A04. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/weapons.py`
- `video_game/engine/player.py`
- `video_game/data/balance.json`
- `video_game/tests/test_combat.py`

Implementation sequence

1. Implement starter maser fire cadence, charge/pierce rules and eight-direction aim.
2. Use attachment points from animation metadata and resolve camera-independent muzzle positions.
3. Implement swept projectile collision against world and targets with hit IDs.
4. Add damage, invulnerability, knockback, death and cleanup rules.
5. Exercise moving/jumping/crouched firing and simultaneous hits.

Acceptance checks

- [x] Fast projectiles hit thin walls and targets reliably.
- [x] A piercing shot has explicit per-target hit behavior.
- [x] Held fire respects timing and pause.
- [x] Damage/retry cannot duplicate rewards or leave orphan projectiles.

Save evidence under `video_game/planning/evidence/A05/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a06"></a>

## A06 — Build first enemies and predictive attacks

Dependencies — A05. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/enemies.py`
- `video_game/assets/sprites/enemies/`
- `video_game/data/balance.json`
- `video_game/tests/test_combat.py`

Implementation sequence

1. Implement a Core recon drone and a Static Hound with patrol, detect, windup, attack, recovery, hurt and death states.
2. Add predictive laser targeting with a visible aim lock and a dodge window.
3. Integrate enemy spawns, line-of-sight checks, collision and bounded projectile counts.
4. Author readable initial sprites and telegraph effects.
5. Tune one encounter around cover and movement.

Acceptance checks

- [x] Every damaging attack has a visible warning and a tested escape/counter.
- [x] Offscreen enemies and wall occlusion follow explicit rules.
- [x] Enemy death, room exit and checkpoint reset clean their state.
- [x] Encounter is playable with the starter weapon.

Save evidence under `video_game/planning/evidence/A06/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a07"></a>

## A07 — Connect bunker stations, inventory and HUD

Dependencies — A06. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/scenes/bunker.py`
- `video_game/engine/ui/hud.py`
- `video_game/engine/objectives.py`
- `video_game/tests/test_campaign.py`

Implementation sequence

1. Use player proximity and Interact for receiver, lab and field door.
2. Display health, active weapon, objective and prediction-lock feedback.
3. Add collectible analog parts and one repair interaction tied to mission data.
4. Expose campaign meters through a readable dossier view.
5. Replace development-only shortcuts with discoverable prompts in normal play.

Acceptance checks

- [x] Station activation works only when the relevant interaction is available.
- [x] Collected parts and repaired objects persist exactly once.
- [x] HUD communicates damage, objective changes and failure reasons without overlap.

Save evidence under `video_game/planning/evidence/A07/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a08"></a>

## A08 — Implement the 72-second dish defense

Dependencies — A07. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/objectives.py`
- `video_game/data/levels/act_01/dish_catwalk.json`
- `video_game/tests/test_objectives.py`

Implementation sequence

1. Create idle/active/failed/completed holdout states and six 12-second signal bins.
2. Schedule enemy waves and jammed feed-horn repair interactions from data.
3. Define dish integrity, player death, retry and checkpoint reset behavior.
4. Freeze objective time during pause and use gameplay time after resume.
5. Connect reward and mission completion through campaign events.

Acceptance checks

- [x] Completion occurs at exactly 72 seconds of accumulated active game time within one simulation step.
- [x] Signal display follows the rising and falling six-bin sequence.
- [x] Failure/retry clears wave state and restores valid geometry.
- [x] Completion reward applies once.

Save evidence under `video_game/planning/evidence/A08/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a09"></a>

## A09 — Implement Greenkeeper and the boss framework

Dependencies — A08. Resource flag — THINKING.

Files to create or modify

- `video_game/engine/bosses/base.py`
- `video_game/engine/bosses/greenkeeper.py`
- `video_game/engine/scenes/boss.py`
- `video_game/data/levels/act_01/greenkeeper_arena.json`
- `video_game/tests/test_combat.py`

Implementation sequence

1. Implement boss intro, health, phase transition, death and arena reset interface.
2. Author Greenkeeper mortar, sweep and exposed-weak-point phases with recoveries.
3. Create boss art and telegraphs with safe player routes.
4. Connect the pre-boss checkpoint, defeat reward and Act II unlock.
5. Test retries from each phase and simultaneous player/boss death.

Acceptance checks

- [x] Each phase can be completed with available Act I equipment.
- [x] No attack pattern requires an unavoidable hit.
- [x] Boss reset clears prior attacks and restores arena state.
- [x] Win/death edge cases resolve consistently.

Save evidence under `video_game/planning/evidence/A09/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a10"></a>

## A10 — Assemble the Act I mission chain

Dependencies — A09. Resource flag — STANDARD.

Files to create or modify

- `video_game/data/campaign.json`
- `video_game/data/levels/act_01/salvage_yard.json`
- `video_game/data/civilization_missions.json`
- `video_game/tests/test_content.py`

Implementation sequence

1. Link approach, salvage yard, dish catwalk and boss arena with explicit objectives and return paths.
2. Integrate FASR-001 and FASR-007 evidence/validation into the unlock chain.
3. Add contextual onboarding for movement, cover, contact, lab and defense.
4. Define checkpoint state and recovery for every failed objective.
5. Remove bypasses from the normal route and retain explicit development fixtures.

Acceptance checks

- [x] A fresh save can reach every required objective in order.
- [x] Missing prerequisites explain the next action.
- [x] Backtracking and reload cannot strand required items or missions.
- [x] Act II unlocks only after valid Act I completion.

Save evidence under `video_game/planning/evidence/A10/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a11"></a>

## A11 — Finish Ohio environment art

Dependencies — A10. Resource flag — GPU_IMAGE.

Files to create or modify

- `video_game/art/source/environments/ohio/`
- `video_game/assets/environments/ohio/`
- `video_game/data/levels/act_01/`

Implementation sequence

1. Apply the approved visual standard to all four Act I blockouts.
2. Author sky/structure/parallax, tile materials, props, dish lattice and weather layers.
3. Match cover and platforms to their collision silhouettes.
4. Inspect every camera region with player, enemies, projectiles and HUD present.
5. Optimize repeated tiles/props and preserve source provenance.

Acceptance checks

- [x] All four rooms meet the visual rubric.
- [x] No visible seams or misleading collision surfaces remain.
- [x] Foreground and weather preserve combat readability.
- [x] Both CRT states remain readable.

Save evidence under `video_game/planning/evidence/A11/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a12"></a>

## A12 — Add audio and bounded combat effects

Dependencies — A11. Resource flag — STANDARD.

Files to create or modify

- `video_game/engine/audio.py`
- `video_game/engine/effects.py`
- `video_game/assets/audio/`
- `video_game/tests/test_combat.py`

Implementation sequence

1. Wire existing music to bunker, combat and boss transitions with controlled fades.
2. Create or source maser, impact, interaction, printer and warning sounds with provenance.
3. Add capped muzzle flashes, casing/rain particles, hit feedback and adjustable shake.
4. Apply pause/settings volume behavior and handle missing audio devices gracefully.
5. Cap event-driven sound repetition and particle allocations.

Acceptance checks

- [ ] Actual audio transitions and volume settings are audibly checked.
- [ ] Muted/missing-device launch remains playable.
- [ ] Repeated combat cannot create unbounded particles or sound channels.
- [ ] Reduced effects preserve necessary attack cues.

Save evidence under `video_game/planning/evidence/A12/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a13"></a>

## A13 — Measure and fix Act I performance

Dependencies — A12. Resource flag — CPU_PROFILE.

Files to create or modify

- `video_game/tools/profile_game.py`
- `video_game/planning/evidence/A13/`

Implementation sequence

1. Implement a repeatable traversal/combat benchmark with frame work and memory capture.
2. Run the 120-second protocol with AI idle and streaming.
3. Identify the highest measured cost and apply one bounded fix at a time.
4. Repeat after fixes and record remaining resource requirements.
5. Run scene-change and terminal-cancellation cycles for memory growth.

Acceptance checks

- [ ] Performance claims include machine, settings, scene load and measurements.
- [ ] No disk/model work blocks the render loop.
- [ ] Proposed budgets pass or the gate remains open with a concrete issue.

Save evidence under `video_game/planning/evidence/A13/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.

<a id="a14"></a>

## A14 — Accept the complete Act I gameplay loop

Dependencies — A13, C08. Resource flag — THINKING.

Files to create or modify

- `video_game/planning/evidence/A14/`
- `video_game/planning/ISSUES_AND_DECISIONS.md`

Implementation sequence

1. Play from a fresh save through the full Act I route with normal controls.
2. Repeat death, defense failure, boss retry and save/reload at each major boundary.
3. Record the complete route and user-facing explanations.
4. Fix progression, input, readability and fairness defects.
5. Use measured production cost and playtime to revisit D02 before later acts.

Acceptance checks

- [ ] Gate G2 passes.
- [ ] At least one complete offline route and the required live-contact checks are evidenced.
- [ ] No blocker or high-severity Act I defect remains.

Save evidence under `video_game/planning/evidence/A14/`. Record failures and resource needs in ISSUES_AND_DECISIONS.md, update PROGRESS_LOG.md, then update the roadmap and current handoff. Use EXECUTION_PROTOCOL.md for restoration if a migration or replacement fails.
