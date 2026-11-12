# A14 bounded failure and recovery supplement — 2026-11-11

Environment: macOS, Python 3.12 / pygame-ce 2.5.8, dummy SDL video and audio. All route saves/settings used temporary directories. Live AI was deliberately skipped. This is a state-observed, accelerated 60 Hz keyboard/text script, not a human playthrough or performance measurement. The tested route has no direct placement, damage, health, or progression grants. See `traversal.json` for the full event trace and captures in this directory.

Reproduce from repository root:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.act_01_traversal --recovery --output-dir video_game/planning/evidence/A14/2026-11-11_recovery
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_act_01_playthrough.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_act_01_playthrough.py video_game/tests/test_objectives.py video_game/tests/test_combat.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests tests -q -k 'not live_ollama_stream_if_available and not gate_g1_live_local_model_and_offline_route_parity'
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.mechanics_route --output-dir /tmp/6equj5_a14_recovery_s11
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.validate_content
/opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.build_assets --dry-run
```

The fresh route earned FASR-001 validation and the coupler, repaired the feedhorn, and entered defense. F2 paused the defense: its timer remained at 0.0333 seconds across 120 paused frames. Escape and normal airlock reentry restarted it; an actual SaveStore load retained repair and no defense completion. With the player idle, enemy pressure collapsed dish integrity after 51.2167 simulated seconds, with player health 70. R reset health to 100 and started a fresh defense; normal combat completed all three waves at 72 seconds. The completion flag was read from the actual save before leaving the field.

The player then entered Greenkeeper's arena, walked into attack range and waited without firing. Enemy attacks caused death after 542 frames, with boss health 300. R restored player health 100 and boss health 300. Normal movement/fire won at frame 297, with health 70. SaveStore loaded the Act I completion flag while still in the boss scene. R replayed the real fight; the second win left the complete campaign dictionary and save file bytes unchanged. Escape returned to the bunker with victory saved. FASR-007 was acquired offline, F5 saved, and a separate Python process used title Continue to recover the completed campaign. Final run: 162.183 simulated seconds, 1.32 wall seconds. Neither is human playtime.

Before the fix the failed-defense R left `cycle_ability` queued in InputManager; the route had only one unlocked ability so its selected ID did not visibly change. The same R changed boss selection from decoy to time dilation on the next update. Both retry paths now release mapped/held controls, so R owns the retry. A separate focused fixture explicitly supplies two unlocked abilities and failure/death state; through GameStateMachine key events it verifies retry leaves selection unchanged and a subsequent R in normal combat cycles correctly in each scene. This fixture is not route evidence. Retry clears held controls, so controls must be pressed again after retry.

A pre-fix SaveStore check found that boss victory existed only in memory until leaving for the bunker. The unique boss reward now calls the existing checkpoint saver immediately; replay does not regrant or rewrite it. A separate fixture makes the save store fail, verifies one attempt, and checks the existing `SAVE FAILED - F5 RETRY` notice. That notice is displayed in the bunker; F5 retry is a bunker control. A failed immediate save still requires a successful later save; no failure recovery or power-loss guarantee is implied.

An initial attempt waited idle at the boss entrance for 75 simulated seconds and did not die; the changed hypothesis was to enter attack range, which produced the actual death above. The first save-boundary assertion exposed the missing boss checkpoint and was corrected by the runtime change. The prior unmodified boss/defense probes confirmed the R-edge issue. No repeated unbounded attempts were made.

Results: focused playthrough tests **10 passed in 2.88s**; playthrough/objectives/combat **70 passed in 3.07s**. The full offline checkpoint returned **413 passed, 2 deselected in 23.10s**; it ran before the final driver-only change bounding the approach loop, which was subsequently covered by the fresh recovery route and focused tests. The combined S11 route passed using the unchanged `_traverse_in_directory` caller, with 49.417 additional simulated seconds and 2.597 wall seconds. Seven levels validated; asset dry-run preserved 14 locked groups. Checks were run while separate project workers were active, so suite count reflects that shared checkout at run time.

Inspected the 3× actual boss victory capture; its victory banner and defeated label were present. The change added no visual assets or user-facing HUD content. Still captures and headless input do not verify motion, subjective art/readability, human pacing, audible audio, native input or native graphical performance. Live AI was excluded; G2/G3 remain pending. Failure after actual defense exit, boss-death exit/reentry, native display and further save-interruption cases were not separately exercised here.

Changed `engine/scenes/field.py`, `engine/scenes/boss.py`, `tools/act_01_traversal.py`, and `tests/test_act_01_playthrough.py`. SHA-256-verified pre-edit local copies and restore instructions are in `_trash/2026-11-11_A14_recovery_before/manifest.json`; these are not an independent backup. No existing files were retired or deleted.
