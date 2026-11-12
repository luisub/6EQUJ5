# S09 counter coverage — 2026-11-11

Status: bounded functional increment; S09 and G3 remain open. This is scripted dummy-SDL testing, not a human playthrough, a graphical-performance measurement, an audio review, or art acceptance. No live AI or asset rebuild was used. The prior S09 runtime/spawn reports remain applicable.

## What was tested and fixed

Using isolated temporary saves and settings, tests enter the annex with a public `defeat_greenkeeper` event fixture and cycle N through the actual field router. They deliberately isolate and reposition actors; synthetic contact event IDs unlock equipment. `FASR-004` supplies EMP, `FASR-002` supplies scattergun, and a synthetic `reality_anchor_1977` event ID with a valid FASR-001 contact payload supplies tape. These are not earned prerequisite progression. The earlier S11 ordered route separately exercises earned equipment and tape activation; this increment does not claim to use its earned save. Ordinary physical-key Pygame KEYDOWN/KEYUP events fire and select equipment, activate tape and jump. Tests observe real field-managed enemies and projectiles rather than calling ability/counter methods directly.

- Watcher naturally enters windup/channel and drains coherence. A Q/X EMP projectile applies stun; the next enemy update clears channel and telegraph, and coherence remains constant during the observed 30-frame stunned interval.
- A starter-maser hit against an unrevealed Phantom deals reduced damage. Q/X fires scattergun projectiles; reveal is applied to the actual Phantom and a non-mutating observer records a real individual pellet input and result: 12 configured damage becomes 18 while revealed. An actual earlier maser hit records the 25% unrevealed rule. Existing integration coverage tests Watcher teleport suppression under reveal.
- The Splicer telegraphs and emits an acid projectile with gravity 380; the test observes upward motion, positive vertical velocity and subsequent descent before collision or expiry. This does not validate every cover placement or trajectory.
- Guardian's natural telegraph creates two ground-only shockwaves. In controlled matched cases an unjumping grounded player loses health, while a SPACE keydown immediately after wave creation avoids damage. This one timing and placement is not a general fairness or timing review.
- The tape selected by R and activated by K interrupts an actual telegraphing Operative into recovery, applies `prediction_shattered`, and an actual X-fired starter-maser projectile deals the expected 3× configured damage (capped at remaining health). The target is controlled and the unlock is synthetic.
- Five boundary checks found Shield Hound, Watcher, Splicer, Guardian and Phantom entered attack despite losing line of sight on the same update that their windup expired. Before their respective fixes, all five failed: Hound and Watcher entered attack; Splicer, Guardian and Phantom fired and entered recovery. The fix makes attack expiry an `elif` of LOS loss in those five windups. The regression fixture begins from a naturally observed telegraph, sets its remaining timer to half a frame, and forces LOS false for that update; this isolates the boundary and does not claim an ordinary walk-to-cover route.

## Commands and outcomes

All commands from repository root, Python 3.12 game environment; dummy SDL video/audio; game fixtures use temporary saves/settings.

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_faction_integration.py video_game/tests/test_runtime_integration.py video_game/tests/test_combat.py video_game/tests/test_checkpoint_audit.py -q
# 92 passed in 4.36s
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests tests -q -k 'not live_ollama_stream_if_available and not gate_g1_live_local_model_and_offline_route_parity'
# 412 passed, 2 deselected in 23.00s (shared checkout; before final Hound/Phantom fixes and fixture audio isolation)
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.validate_content
# seven levels validated
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets --dry-run
# 14 locked groups preserved
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.faction_counter_audit --output-dir video_game/planning/evidence/S09/2026-11-11_counter_coverage/captures_final
# completed; nine native frames and nearest-neighbor 3× copies
```

Faction combat tests suppress AudioManager mixer initialization because audio is outside their scope. Two focused-run attempts before this isolation crashed in the background music worker at audio.py:173 during pygame teardown (one segmentation fault and one abort); the root and audio owner were informed. The focused pass above was after isolation. This is not a runtime audio fix; full verification after the final two LOS edits is pending coordinated audio lifecycle work.

The first capture attempt stopped at a wrong assumed weapon-cycle count because the coilgun was locked by the disclosed fixture. Its partial files remain in `captures/`; the driver was corrected to stop on the observed scattergun selection and rerun to the distinct `captures_final/` directory. The first focused regression run reported 89 pass and one failure because the new capture tool lacked required module header tags; after adding them, the command above passed. No capture files were overwritten.

## Pair hints, cover, and HUD follow-up

The annex now contains a non-solid low-cover object at (48, 224, 16, 16), drawn as a simple outlined box in both timelines. It does not overlap the default player spawn or other active objects, does not intersect solid/hazard tiles, has floor support and is reachable by D in both timelines. In 2029, an isolated, naturally firing Splicer at x=205 hits a standing player at this cover, whereas holding C causes the actual projectile to be absorbed from the right with no damage. The enemy is deliberately placed, not encountered through an earned route. Tests asserting the same hit in 1977 timed out: intervening authored solids prevented that staged enemy from seeing the player. The final tests verify 1977 placement/reachability, not an actual 1977 Splicer hit; no such claim is made.

N cycles now display pair-specific mappings, including Splicer cover and Guardian jump, for eight seconds unless another notification replaces them. A test advances four seconds with enemy cooldowns controlled and verifies the same banner remains. The longest full hint measures 261 pixels in the actual small font. Shared HUD notifications moved to x=140..474, and the ability label is fitted to 106 pixels at the left; notification text is fitted to 322 pixels, keeping these zones disjoint. Long unrelated notifications can now be ellipsized based on actual font width. The fixture captures show the full hints, but they do not prove human teaching effectiveness.

After the HUD change the following focused command passed **46 in 3.87s**; a broader focused command including the earned mechanics route passed **98 in 7.16s** after cover changes and before the HUD change. Content validation passed seven levels and asset dry-run preserved 14 locked groups after the cover change. The root owns the final shared checkpoint.

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_faction_integration.py video_game/tests/test_objectives.py video_game/tests/test_checkpoint_audit.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_faction_integration.py video_game/tests/test_runtime_integration.py video_game/tests/test_combat.py video_game/tests/test_checkpoint_audit.py video_game/tests/test_mechanics_route.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.faction_counter_audit --output-dir video_game/planning/evidence/S09/2026-11-11_counter_coverage/captures_verified
```

The final capture fixture additionally uses synthetic FASR-001, -002, -004, anchor and Act I completion event IDs. It uses a direct boss-scene transition solely for a layout check. Inspected all four final hint frames at native and nearest-neighbor 3×, as well as active and cooldown ability with hint and boss HUD at both scales. The ability and notification no longer overlap; all four labels fit. Cover and its prompt were visible in 2029 and 1977, inspected native and 3×; small actor size remains. Boss layout inspection exposed a separate pre-existing issue: the lock-on warning obscures the center of the boss health bar. It was not changed in this increment. Earlier Watcher, Guardian, Splicer, Phantom and Operative staged captures were also inspected as recorded above. A capture attempt to `captures_hud_final/` stopped because the initial fixture lacked the separate FASR-001 event ID needed for time dilation; the corrected driver was rerun into `captures_verified/` without overwriting. Earlier partial and superseded captures remain.

Motion, mixed encounter fairness, human readability, actual art review, audible transitions, native window and graphical performance remain open. The native-display attempt was already known unavailable and was not retried.

## Recovery and ownership

Before editing, SHA-256-matched same-device local copies of `engine/enemies.py`, `tests/test_faction_integration.py`, and `tools/faction_runtime_audit.py` were placed under `video_game/_trash/2026-11-11_S09_counter_coverage/video_game/`; hashes and paths are in the adjacent `manifest.json`. They are recovery copies, not independent backup. `tools/faction_counter_audit.py` and this evidence are new. No existing files were retired. Field, shared HUD, and annex data were subsequently edited in the scoped hint/cover follow-up. Before their edits SHA-256-matched copies were saved under `_trash/2026-11-11_S09_counter_hints/manifest.json`. Player code and shared planning were not edited by this worker.
