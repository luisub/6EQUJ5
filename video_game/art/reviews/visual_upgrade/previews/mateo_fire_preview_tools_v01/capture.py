"""PURPOSE: Inspect one candidate recoil pose at an actual physical-input projectile event.
CALLED BY: python capture.py --output-dir NEW_DIR under dummy SDL.
HOW TO MODIFY: Preserve runtime animation state/anchors and disclose render-only override.
"""
import argparse,hashlib,json,tempfile
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine

CELL=Path('video_game/art/reviews/visual_upgrade/previews/mateo_armed_registration_director_v02/cell_v01/mateo_olive_recoil_60x80.png')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def tick(game,count=1):
    for _ in range(count):game.input.begin_frame();game.update(1/60)
def key(game,kind,code):game.handle_event(pygame.event.Event(kind,key=code))
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=False)
    pygame.init();pygame.display.set_mode((960,540));samples=[]
    try:
        with tempfile.TemporaryDirectory(prefix='6equj5-recoil-check-') as tmp:
            for facing in ('right','left'):
                save=Path(tmp)/facing;game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
                try:
                    assert game.start_new_game()[0];game.change_state(config.STATE_FIELD_OPS,room='act_01/approach.json',spawn='approach_checkpoint')
                    scene=game.current_scene;scene.enemy_manager.clear();tick(game,30)
                    direction=pygame.K_d if facing=='right' else pygame.K_a
                    key(game,pygame.KEYDOWN,direction);tick(game);key(game,pygame.KEYUP,direction);tick(game,20)
                    player=scene.player;animator=player.animator;assert animator is not None and player.facing==facing
                    assert player.is_grounded and not player.in_cover
                    prior={'state':animator.current_state,'facing':animator.facing,'foot_world':[player.x+player.width/2,player.y+32],
                           'muzzle_world':list(player.get_muzzle_world_pos()),'player_rect':list(player.rect),'camera':[scene.camera.x,scene.camera.y]}
                    spawned=[];original_spawn=scene.projectile_manager.spawn
                    def record_spawn(*a,**kw):
                        spawned.append({'state_at_spawn':animator.current_state,'facing_at_spawn':animator.facing,
                                        'muzzle_world':list(player.get_muzzle_world_pos()),'spawn_world':[kw['x'],kw['y']]})
                        return original_spawn(*a,**kw)
                    scene.projectile_manager.spawn=record_spawn
                    key(game,pygame.KEYDOWN,pygame.K_j);tick(game);key(game,pygame.KEYUP,pygame.K_j)
                    assert len(spawned)==1 and animator.current_state=='recoil'
                    candidate=pygame.image.load(str(CELL)).convert_alpha()
                    surface_original=animator.surface_for_density;dest_original=animator.get_render_dest_for_density
                    def candidate_surface(density):
                        if animator.current_state!='recoil':return surface_original(density)
                        pose=candidate if animator.facing=='right' else pygame.transform.flip(candidate,True,False)
                        return pygame.transform.scale(pose,(30*density,40*density))
                    def candidate_dest(foot_x,foot_y,camera,density):
                        if animator.current_state!='recoil':return dest_original(foot_x,foot_y,camera,density)
                        sx,sy=camera.world_to_screen(foot_x,foot_y)
                        return (round(sx*density-(30 if animator.facing=='right' else 29)*density/2),round(sy*density-78*density/2))
                    for frame in (0,1):
                        if frame:tick(game)
                        for mode in ('original','candidate'):
                            animator.surface_for_density=surface_original if mode=='original' else candidate_surface
                            animator.get_render_dest_for_density=dest_original if mode=='original' else candidate_dest
                            game.render();native=args.output_dir/f'{facing}_{mode}_frame{frame}_native_960.png';review=args.output_dir/f'{facing}_{mode}_frame{frame}_review_1920.png'
                            pygame.image.save(game.crt.render_surface,str(native));pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                            samples.append({'facing':facing,'mode':mode,'frame_after_fire':frame,'state':animator.current_state,'camera':[scene.camera.x,scene.camera.y],
                              'projectiles':[[p.x,p.y,p.active] for p in scene.projectile_manager.projectiles],
                              'native':native.name,'sha256':sha(native),'review':review.name})
                    animator.surface_for_density=surface_original;animator.get_render_dest_for_density=dest_original
                    samples.append({'facing':facing,'pre_fire':prior,'spawn':spawned})
                finally:game.close()
    finally:pygame.quit()
    info={'cell':str(CELL),'cell_sha256':sha(CELL),'samples':samples,
          'fixture':'dummy SDL, installed approach, temporary saves, direct checkpoint entry, enemy list cleared; physical left/right turn and J fire through actual input mapper, fixed 1/60 updates. Candidate replaces only render surface and placement when runtime animator reports recoil; original animator state, attachment, projectile and collider unchanged.',
          'limits':'two sampled updates per facing, not continuous playback, full animation family, native window, human gameplay or production-art acceptance.'}
    (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info,indent=2))
if __name__=='__main__':main()
