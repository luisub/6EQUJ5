"""PURPOSE: Compare actual field recoil with a single visual-only native pose candidate.
CALLED BY: Run from repository root with dummy SDL and --output-dir NEW_DIR.
HOW TO MODIFY: Keep temporary saves, fixture-only override and real gameplay anchors unchanged.
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine

CELL=Path('video_game/art/reviews/visual_upgrade/previews/mateo_armed_registration_director_v02/cell_v01/mateo_olive_recoil_60x80.png')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',required=True,type=Path)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=False)
    pygame.init();pygame.display.set_mode((960,540))
    try:
        with tempfile.TemporaryDirectory(prefix='6equj5-armed-room-') as tmp:
            game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
            try:
                game.start_new_game();game.change_state(config.STATE_FIELD_OPS)
                scene=game.current_scene
                for _ in range(30):
                    game.input.begin_frame();game.update(1/60)
                animator=scene.player.animator
                assert animator is not None
                original_surface=animator.surface_for_density
                original_dest=animator.get_render_dest_for_density
                candidate=pygame.image.load(str(CELL)).convert_alpha()
                samples=[]
                for facing in ('right','left'):
                    animator.set_state('recoil');animator.set_facing(facing)
                    scene.player.facing=facing
                    foot=(scene.player.x+scene.player.width/2,scene.player.y+32)
                    hand=animator.get_attachment_world_pos('hand',*foot)
                    muzzle=animator.get_attachment_world_pos('muzzle',*foot)
                    def native_point(world):
                        return [round((world[0]-scene.camera.x)*2),round((world[1]-scene.camera.y)*2)]
                    points={'foot':native_point(foot),'hand':native_point(hand),'muzzle':native_point(muzzle)}
                    for mode in ('original','candidate'):
                        if mode=='original':
                            animator.surface_for_density=original_surface
                            animator.get_render_dest_for_density=original_dest
                        else:
                            pose=candidate if facing=='right' else pygame.transform.flip(candidate,True,False)
                            animator.surface_for_density=lambda density,pose=pose: pygame.transform.scale(pose,(30*density,40*density))
                            def visual_dest(foot_x,foot_y,camera,density,facing=facing):
                                sx,sy=camera.world_to_screen(foot_x,foot_y)
                                return (round(sx*density-(30 if facing=='right' else 29)*density/2),round(sy*density-78*density/2))
                            animator.get_render_dest_for_density=visual_dest
                        game.render()
                        raw=a.output_dir/f'{mode}_{facing}_native_960.png'
                        large=a.output_dir/f'{mode}_{facing}_review_1920.png'
                        marked=a.output_dir/f'{mode}_{facing}_targets_native_960.png'
                        surface=game.crt.render_surface.copy()
                        pygame.image.save(surface,str(raw))
                        pygame.image.save(pygame.transform.scale(surface,(1920,1080)),str(large))
                        for name,pt in points.items():
                            color={'foot':(255,240,0),'hand':(0,255,255),'muzzle':(255,60,60)}[name]
                            pygame.draw.line(surface,color,(pt[0]-4,pt[1]),(pt[0]+4,pt[1]),1)
                            pygame.draw.line(surface,color,(pt[0],pt[1]-4),(pt[0],pt[1]+4),1)
                        pygame.image.save(surface,str(marked))
                        samples.append({'facing':facing,'mode':mode,'native':raw.name,'native_sha256':sha(raw),'review':large.name,'review_sha256':sha(large),'targets':marked.name,'targets_sha256':sha(marked),'points_native_direct':points,'foot_world':foot,'hand_world':hand,'muzzle_world':muzzle})
                info={'cell':str(CELL),'cell_sha256':sha(CELL),'asset_root':str(game.assets.root),'camera':[scene.camera.x,scene.camera.y],
                      'player_rect':list(scene.player.rect),'fixture':'dummy SDL, temporary save, new game, direct field, 30 fixed updates, recoil state and facing directly set; visual override only for candidate after actual installed background and before usual effects/HUD',
                      'target_note':'points use round((world-camera)*2); projectile logical rendering may round at a different boundary; no projectile spawned in this still.',
                      'limits':'not a real firing trace, animation playback, normal input, native window, human play, performance or art-gate acceptance; runtime gameplay anchors/collider unchanged.', 'samples':samples}
                (a.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n')
                print(json.dumps(samples,indent=2))
            finally:game.close()
    finally:pygame.quit()

if __name__=='__main__':main()
