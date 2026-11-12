"""PURPOSE: Inspect Greenkeeper scene art against real boss states in disposable fixtures.
CALLED BY: PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python capture.py --output-dir NEW_DIR.
HOW TO MODIFY: Preserve all injected state, direct entry, source transform and temporary-save disclosures.
"""
import argparse, hashlib, json, tempfile
from pathlib import Path
import pygame
from PIL import Image
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.bosses.base import PHASE_1, PHASE_2, STATE_VULNERABLE
SOURCE=Path('video_game/art/source/visual_upgrade/candidates/greenkeeper_world_scene_v02/source/greenkeeper_world_scene_generated_master.png')
FAR=Path('video_game/art/reviews/visual_upgrade/previews/approach_far_registration_v01/far_native_1152x544.png')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=False)
with Image.open(SOURCE) as src:
    if src.mode!='RGBA':raise ValueError(f'Expected RGBA: {src.mode}')
    size=src.size;src.resize((1280,576),Image.Resampling.LANCZOS).save(a.output_dir/'arena_world_layer_1280x576.png')
pygame.init();pygame.display.set_mode((960,540))
try:
  with tempfile.TemporaryDirectory(prefix='6equj5-arena-registration-') as tmp:
    game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
    try:
      game.start_new_game();game.change_state(config.STATE_BOSS_BOUNTY)
      scene=game.current_scene;scene.player.x=240;scene.player.y=208;scene.player.vx=scene.player.vy=0
      for _ in range(30):game.input.begin_frame();game.update(1/60)
      far=pygame.image.load(str(FAR)).convert_alpha();layer=pygame.image.load(str(a.output_dir/'arena_world_layer_1280x576.png')).convert_alpha()
      def background(_surface,camera):
        f=(round(.2*camera.x),round(.1*camera.y));w=(round(2*camera.x),round(2*camera.y))
        game.crt.composite_native(far.subsurface(pygame.Rect(*f,960,540)),(0,0),(480,270))
        game.crt.composite_native(layer.subsurface(pygame.Rect(*w,960,540)),(0,0),(480,270))
      scene.room.render_background=background
      samples=[]
      def capture(name,cx):
        scene.camera.x,scene.camera.y=cx,18;game.render()
        native=a.output_dir/f'{name}_x{cx}_native_960.png';review=a.output_dir/f'{name}_x{cx}_review_1920.png'
        pygame.image.save(game.crt.render_surface,str(native));pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
        samples.append({'name':name,'camera':[cx,18],'player_rect':list(scene.player.rect),'grounded':scene.player.is_grounded,
          'boss_rect':list(scene.boss.rect),'phase':scene.boss.current_phase,'phase_state':scene.boss.phase_state,
          'attack':scene.boss.current_attack_type,'weak_exposed':scene.boss.weak_point_exposed,
          'telegraphs':len(scene.boss.telegraphs),'native':native.name,'native_sha256':sha(native),'review':review.name,'review_sha256':sha(review)})
      for cx in (0,80,160):capture('active',cx)
      boss=scene.boss;boss.current_phase=PHASE_1;boss._schedule_next_attack(scene.player.rect.center)
      capture('mortar_telegraph',80)
      boss.telegraphs.clear();boss.phase_state=STATE_VULNERABLE;boss.weak_point_exposed=True;boss.vulnerability_timer=2.5
      capture('weakpoint_exposed',80)
      boss.current_phase=PHASE_2;boss.health=150;boss.weak_point_exposed=False;boss.volley_count=0;boss._schedule_next_attack(scene.player.rect.center)
      capture('sweep_telegraph',80)
      boss.telegraphs.clear();boss._execute_telegraphed_attack();capture('sweep_active',80)
      info={'source':str(SOURCE),'source_size':list(size),'source_sha256':sha(SOURCE),
        'export':'arena_world_layer_1280x576.png','export_sha256':sha(a.output_dir/'arena_world_layer_1280x576.png'),
        'transform':'full-image Lanczos resize to 1280x576; no masks, alpha edits, painting or cleanup',
        'far_fixture':str(FAR),'far_sha256':sha(FAR),'far_use':'interim fixture, not an approved arena sky',
        'composition':'fixture-local callback: far then world layer before real boss scene tiles, objects, boss/telegraphs, player projectiles, Mateo, effects and HUD',
        'fixture':'dummy SDL, temporary saves, new game and direct boss entry; teleport player x240/y208 and simulate 30 updates at 1/60, then force camera x0/80/160 y18. After active stills, directly invoke boss private scheduling for phase-1 mortar, inject vulnerability, set phase=2 and health=150 and invoke scheduling/execution for sweep; no updates between injected-state stills.',
        'samples':samples,'limits':'explicitly injected state fixtures; not earned entry, natural timing, actual phase transitions, normal-input play, complete motion, native display, performance, human fairness or art acceptance'}
      (a.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(samples,indent=2))
    finally:game.close()
finally:pygame.quit()
