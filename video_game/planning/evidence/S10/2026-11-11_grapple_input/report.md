# S10 grapple input repair — 2026-11-11

Status: in progress. Ownership: `engine/player.py`, new `tests/test_grapple_input.py`, and this evidence directory; field runtime and shared planning are owned by the S11 worker. Plan: reproduce real M/G input using a public Act I completion-event fixture and temporary stores; fix the second press without double-toggle across the fixed substeps, preserve established jump/dash/distance exits, and verify hold/repeat/no-anchor, pause/focus, death and room transitions. Consolidate duplicate fire guard, preserving dead and background-cover restrictions. Run focused player, grapple and runtime tests, record exact results and fixture limits; inspect native/3x captures if visual output changes. No live AI. This is targeted fixture evidence, not a complete human route.

## Outcome and scope

The physical G edge is buffered until a fixed physics step and consumed only once even if a render frame runs multiple steps. A second press now releases an existing grapple; holding G does not repeat. Pause, focus loss and resize clear a buffered edge through the narrow state-machine control-release hook. Distance and Space release remain available; dash clears the anchor references. Duplicate `can_fire` definitions were consolidated so a dead player and background cover both prevent firing. Weapon dispatch was tested directly while dead, without triggering physics respawn.

The S11 worker owns the field-side calls to `Player.cancel_traversal()` on room/scene reset and clears pending field jump/fire edges on room load. The helper cancels grapple, dash, slide, wall-slide and transient movement, preserving health, equipment, cooldowns and permanent campaign state. Both sets of changes were jointly exercised. A first version of the room reset test tried to re-grapple immediately at the death checkpoint, outside the anchor range; it failed, and the fixture was corrected to return to the known annex start before re-grappling. This was a fixture correction, not a claimed gameplay fix.

Checks used actual GameStateMachine key dispatch with temporary SaveStore and SettingsStore. The Act I completion event is injected solely as a prerequisite. Tests cover G down/hold/up/repress, multi-step updates, a 1/240-second press, pause/focus/resize interruption before a physics step, no-anchor negative, jump, dash and reaching-anchor release, paused state, death, F6/F8 room changes, Esc/M reentry, pending-edge clearing and preserved dash cooldown. These do not constitute a human playthrough or the earned S11 route.

`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_grapple_input.py video_game/tests/test_player.py video_game/tests/test_runtime_integration.py video_game/tests/test_combat.py video_game/tests/test_input_settings.py video_game/tests/test_save_game.py video_game/tests/test_checkpoint_audit.py -q` — 133 passed in 3.89s.

## Captures

Native and nearest-neighbor 3x latch/release frames under `captures/` were captured with dummy display/audio, temporary saves and the same Act I fixture. I inspected native latch/release and 3x latch: the anchor ring is visible, but no obvious grapple tether indicates latch in these stills; human motion and visual-teaching review remains open. The capture asserts latched/released state, but the images alone cannot establish that state. Exact capture command:

```sh
mkdir -p video_game/planning/evidence/S10/2026-11-11_grapple_input/captures
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python - <<'PY'
import pygame, tempfile
from pathlib import Path
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
pygame.init(); pygame.display.set_mode((480,270))
out=Path('video_game/planning/evidence/S10/2026-11-11_grapple_input/captures')
with tempfile.TemporaryDirectory() as d:
 g=GameStateMachine(CRTRenderer(),development=False,save_store=SaveStore(d),settings_store=SettingsStore(d))
 try:
  g.start_new_game(); g.campaign.apply_event({'event_id':'capture-fixture','type':'defeat_greenkeeper'})
  def frame(t,k):
   g.input.begin_frame();g.handle_event(pygame.event.Event(t,key=k));g.update(1/60)
  frame(pygame.KEYDOWN,pygame.K_m);frame(pygame.KEYUP,pygame.K_m)
  frame(pygame.KEYDOWN,pygame.K_g); frame(pygame.KEYUP,pygame.K_g)
  assert g.current_scene.player.is_grappling
  def capture(label):
   g.render(); surf=g.crt.canvas.copy()
   for suffix,img in [('native',surf),('3x',pygame.transform.scale(surf,(1440,810)))]:
    name=out / f'{label}_{suffix}.png'
    with name.open('xb') as f:pygame.image.save(img,f,name.name)
  capture('latched')
  frame(pygame.KEYDOWN,pygame.K_g)
  assert not g.current_scene.player.is_grappling
  capture('released')
 finally:g.close();pygame.quit()
PY
```

## Recovery and limits

Verified pre-edit recovery copies and SHA-256:

- `video_game/engine/player.py` → `video_game/_trash/2026-11-11_S10_grapple_input/video_game/engine/player.py`: `36a789c332beb428969742d58fe8c24485a330e23b596ddaf68bbac03f38afcf`.
- `video_game/engine/state_machine.py` → `video_game/_trash/2026-11-11_S10_grapple_input/video_game/engine/state_machine.py`: `1ce4acdf2a0a084bd93207815fd0a9b4f6594ccc477461e84c171ddcc06f5f0d`.

Verify each hash before copying its recovery copy to the original path. No files were retired or swept; temporary saves were cleaned automatically. No live AI, audible or real-window checks were performed. S11 earned-state route, human traversal and teaching clarity remain separate acceptance work.

## Wall-jump and room-buffer follow-up

The normal input mapper treats Space as both jump and upward aim. Its former implicit airborne up+jump grapple latch therefore stole a wall jump near an anchor. Latching now uses the documented G action only; Space still releases an active grapple. After that change, the same route exposed a separate priority conflict: remaining coyote time launched an ordinary vertical jump before the active wall-slide jump could execute. An active wall slide now takes priority. With only the Act I completion prerequisite fixture, normal M/T entry, D and Space down at frame 5/up at frame 17, the authored 1977 wall-slide was observed at frame 37. A fresh Space produced vx -200, vy -254, lock 0.142 seconds and no grapple after one 1/60-second frame. The S11 owner separately exercises the earned route.

Room/scene cancellation now also clears jump buffer, coyote timer and fixed-step accumulator. A test stages those three values before normal F6 and checks they reset while health, weapon and dash cooldown remain unchanged. The initial normal-key wall-jump regression failed after removing implicit grapple because ordinary coyote jump gave vx 0 and no lock; it passed after the wall-slide priority fix. No world geometry changed.

Latest focused command (replaces the earlier count):

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_grapple_input.py video_game/tests/test_player.py video_game/tests/test_runtime_integration.py video_game/tests/test_combat.py video_game/tests/test_input_settings.py video_game/tests/test_save_game.py video_game/tests/test_checkpoint_audit.py -q
```

Result: 135 passed in 4.74s. Earlier latch/release screenshots precede the field owner's later tether-visibility change and do not represent its current rendering; inspect that owner's evidence for the updated visuals. Human motion, audio and complete route acceptance remain open.
