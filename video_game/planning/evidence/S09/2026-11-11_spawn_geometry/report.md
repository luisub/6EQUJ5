# S09 encounter placement and checkpoint reset — 2026-11-11

The annex N encounter used y=128 for every class. Grounded enemies use their spawn height as their ground and remained above normal ground-level attacks. The field scene now searches the active collision grid for a fully supported solid/one-way surface for each grounded enemy, preferring the normal player-spawn floor. Aerial Watcher, Phantom and Drone retain an elevated position with clearance for hover. It rejects blocked, hazardous, out-of-bounds, player-overlapping or pair-overlapping footprints. Patrol bounds stay within contiguous valid positions. Both candidates are selected before replacing an existing pair; if no safe pair exists, the prior encounter and cycle index are retained and a warning is shown. A successful N clears previous enemies and enemy/player projectiles before adding the new pair.

A separate discovered checkpoint defect occurred when `Player.update` auto-respawned and cleared `is_dead` before the field scene's enemy-reset check. The field now detects the actual respawn-count transition and resets enemy states/statuses and both projectile managers. The actual catwalk defense retains its independent casualty detection. No health, damage or enemy tuning was changed.

Before edits, the current `field.py` and affected shared documents were copied and SHA-256 verified under `_trash/2026-11-11_S09_spawn/manifest.json`. This is a same-device local recovery copy, not an independent backup. No files retired.

Checks from repository root (dummy SDL video/audio; isolated test saves/settings):

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_runtime_integration.py video_game/tests/test_act_01_playthrough.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests tests -q -k 'not live_ollama_stream_if_available and not gate_g1_live_local_model_and_offline_route_parity'
```

19 focused tests passed in 2.17s; full offline suite passed 379, 2 excluded in 15.80s on the shared checkout. Another worker's focused checks cover M/N for all four pairs in both timelines, blocked-placement rejection, paused operation and fixture-seeded death followed by respawn/status/projectile reset; their full commands and fixture disclosures are in the companion runtime evidence. The separately tested complete A14 scripted route remains part of the full suite. Root independently verified the prior A14 baseline at 371 passed/2 excluded in 14.98s, seven levels and 14 locked asset groups.

The companion M/N fixture captures (`../2026-11-11_runtime/captures/`) were inspected: pairs 1 and 4 at 3×, pairs 2 and 3 at native resolution. Grounded models appear at floor level and the aerial pair is elevated. Enemies are small at native size; stills alone do not establish player readability, motion quality or counter teaching. Fixture prerequisite is a public Act I completion event, not a complete route. S09 and G3 remain in progress for mixed-play fairness, human art/motion and teaching review, native display and audio checks. No native graphical display was available; no FPS or human playtime is claimed.

Independent parent review of the field diff ran `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_faction_integration.py video_game/tests/test_runtime_integration.py video_game/tests/test_act_01_playthrough.py -q`: 28 passed in 3.01s. Parent reviewed full-tile support and transactional rejection. A separate worker continues examining moving-enemy geometry; this increment does not close S09.
