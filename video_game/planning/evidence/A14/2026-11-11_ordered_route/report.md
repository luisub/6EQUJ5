# A14 ordered route increment — 2026-11-11

Fresh temporary save and settings, dummy SDL video/audio, Python 3.12 / pygame-ce 2.5.8 on macOS. Reproduce from the repository root:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.act_01_traversal --probe-yard --output-dir video_game/planning/evidence/A14/2026-11-11_ordered_route
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_act_01_playthrough.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests tests -q -k 'not live_ollama_stream_if_available and not gate_g1_live_local_model_and_offline_route_parity'
```

The route uses actual GameStateMachine keyboard/text events. From New, E opens the receiver, `/offline` and channel 2 obtain FASR-001; A/E enter the formal lab and the keys answer the first scenario, deploying its validation. D/E enters the airlock. Coordinate-timed Space jumps cross the sump and wall, followed by E at the exit. It reaches salvage with 70 health. A 245-frame yard probe uses observed positions to aim W+D+X diagonally: one shot hits the drone (50 to 25 health). It ends with 20 health and no coupler. The trace records 13.85 simulated seconds and 0.08 wall seconds; this is accelerated scripted execution, not player duration. No teleport, direct grant, damage or health setting was used. Targeted suite: 5 passed; combined offline suite: 368 passed, two live-AI checks deselected, 13.86 seconds. Counts reflect the current shared checkout.

Found and corrected a concrete room setup defect: the reused trench hound spawned at x=660 in the 640-pixel yard. The yard now uses x=560 and patrol 480–600. A regression checks that both yard enemy rectangles start inside the room, away from solids and hazards, and their patrol bounds stay inside. Balance, enemy health and projectile mechanics were not changed. No new art or audio was authored, and no screenshots, audible checks or native graphical performance review were performed.

Not completed: coupler collection/repair, actual 72-second defense, boss fight, FASR-007, save/reload at boundaries, death/defense/boss failure recovery and full player playthrough. Earlier individual fixture/component checks do not fill these gaps. G2 remains pending. Live AI remains deliberately excluded. Before edits, 138 current code/data/test/tool/planning/control files were copied and SHA-256 verified in `_trash/2026-11-11_A14_owner/before.tar.gz` and its manifest; this local copy is not independent backup. No source or recovery files were retired.


## Complete scripted route — later result

This result supersedes the earlier incomplete outcomes below. Reproduce with:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.act_01_traversal --complete --output-dir video_game/planning/evidence/A14/2026-11-11_ordered_route/complete_route
```

A fresh save and temporary settings were used. The driver sends only GameStateMachine keyboard/text events, with state-observed timing, no direct reward, health, damage or placement mutations. It performs FASR-001 offline contact and formal validation, crosses approach, jumps/dashes the salvage hazard, collects the depot coupler, returns via Escape, repairs at the bunker, and enters the actual defense. The defense runs 72.0 simulated seconds, clears three actual waves, finishes at 99.9667 integrity and 30 player health. The driver uses coordinate-observed diagonal aim, normal horizontal fire, time dilation and E to clear jams; its trace contains per-target health changes. Greenkeeper is defeated through ordinary movement/fire in 298 frames across all three phases, with 70 health remaining. After returning to the bunker, six receiver Tabs and channel 2 obtain FASR-007. F5 saves; a new Python process constructs a new machine, presses C at title and reaches the bunker with both fragments, formal validation, repair, defense and boss flags, Act I completion, and the Act II unlock flag. The latter is a flag only; playable Act II is not established. The complete run measured 93.35 simulated seconds and 0.903 seconds wall time, including headless screenshots and child startup; neither is human playtime. Full trace and native/3× scene captures are in `complete_route/`.

Inspected native and 3× pickup, defense, boss, and FASR-007 captures. Fixed two visible boss HUD defects observed during the run: Shift is labeled DASH, matching the real mapper, and defeated boss text no longer says phase 4/3. Static captures do not verify animation, subjective art, human readability, audible audio or native performance. Focused action/objective checks: 17 passed in 1.75s. Combined offline suite: 371 passed, 2 live-AI tests deselected in 14.45s. Content validation passed seven levels, and asset dry-run preserved 14 locked groups. G2 remains pending human play, failure/retry boundaries and other gate requirements; no real-window playthrough was performed.

## Subsequent route through repair

With `--through-repair` in place of `--probe-yard`, the same fresh-save route uses the unlocked time-dilation ability (R, K), jumps the yard's x=288–368 hazard, dashes and reverses after the upper platform to reach the authored depot. The actual pickup occurs at yard frame 228, x=535.58, health 70. Escape returns to bunker; normal E at the repair station repairs the feedhorn, and E at the airlock starts the actual catwalk defense. Trace and 480×270/3× captures are in `repair_route/`; the observed run took 14.717 simulated seconds and 0.176 seconds wall time. It does not complete the defense.

The depot JSON specifies x=520, y=208, but runtime previously displayed and collected a separate coupler at x=560, y=208. Runtime now derives its pickup center and rectangle size from the authored depot. The salvage room does not instantiate FieldReality, so the authored object was not a second active pickup. A focused test checks the authored coordinates and size, repeated room entry cannot grant a second item, and actual SaveStore load retains one coupler. Sixteen focused action/objective tests passed. Native/3× screenshots of actual pickup and defense entry and the native repair screenshot were inspected; at native resolution some HUD text is small and the pickup notice is truncated. These stills do not establish human readability or art acceptance.

An exploratory actual-defense input attempt held right until approximately x=305 and tapped fire, then remained at x=136 after knockback. It failed at 63.3 simulated seconds when dish integrity reached zero, with a jam left uncleared; player health was 10. A separate movement/jump attempt reached the feedhorn and cleared the jam but ended in player casualty at 28.2 seconds. A third lock-reactive attempt ended in casualty at 10.9 seconds. None demonstrates unwinnability. No failure was corrected by reducing enemy health, pressure, or damage. Retry and successful defense remain to be demonstrated in the full ordered route.

## Independent review reproduction

The parent reviewer independently ran `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m video_game.tools.act_01_traversal --complete --output-dir /tmp/6equj5_parent_complete_review`. It reproduced the complete route, all three defense waves, 72.0 seconds and 99.9667 integrity, boss victory, and child-process title Continue into the bunker with both fragments, formal validation and earned flags. The reviewer recorded 93.35 simulated seconds and 0.959 seconds wall time, inspected the native pickup and 3× boss victory captures, and reviewed the runtime changes. This is another scripted headless run, not human or real-window acceptance.
