"""PURPOSE: Inspect the actual boss loader with a staged reviewed room family.
CALLED BY: PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python capture.py --output-dir NEW_DIR.
HOW TO MODIFY: Preserve all injected state, direct entry, source transform and temporary-save disclosures.
"""
import argparse, hashlib, json, tempfile, shutil
from pathlib import Path
import pygame
from video_game.tools.build_room_family import build_family
from video_game.engine.assets import AssetCache
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
WORLD=Path('video_game/art/reviews/visual_upgrade/previews/arena_registration_director_v02/capture_v01/arena_world_layer_1280x576.png')
pygame.init();pygame.display.set_mode((960,540))
try:
  with tempfile.TemporaryDirectory(prefix='6equj5-arena-registration-') as tmp:
    root=Path(tmp)/'assets';shutil.copytree(config.ASSETS_DIR,root)
    result=build_family('ohio_arena_v1',assets_dir=root,archive_dir=Path(tmp)/'archive',far=FAR,world=WORLD,props=[],promote=True)
    game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(Path(tmp)/'save'),settings_store=SettingsStore(Path(tmp)/'save'))
    try:
      game.assets=AssetCache(root);game.start_new_game();game.change_state(config.STATE_BOSS_BOUNTY)
      scene=game.current_scene;scene.player.x=240;scene.player.y=208;scene.player.vx=scene.player.vy=0
      for _ in range(30):game.input.begin_frame();game.update(1/60)
      if scene.native_room is None:raise RuntimeError('arena family did not load')
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
      info={'source':str(SOURCE),'source_sha256':sha(SOURCE),'export':str(WORLD),'export_sha256':sha(WORLD),
        'far_fixture':str(FAR),'far_sha256':sha(FAR),'promotion_status':result['status'],
        'composition':'temporary staged family via actual BossScene native loader before room tiles, objects, boss/telegraphs, player projectiles, Mateo, effects and HUD',
        'fixture':'dummy SDL, temporary assets and saves, direct boss entry; teleport player x240/y208 and simulate 30 ticks, fixed camera x0/80/160 y18, injected mortar, vulnerability and sweep states.',
        'samples':samples,'limits':'injected static fixtures only; not earned entry, natural timing, normal-input play, native display, performance, human fairness or art acceptance'}
      (a.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(samples,indent=2))
    finally:game.close()
finally:pygame.quit()
