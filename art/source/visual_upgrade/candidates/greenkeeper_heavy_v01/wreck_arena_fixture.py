"""Static dummy-driver arena comparison with monkeypatched native candidate; not runtime integration."""
from pathlib import Path
import tempfile
import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
root=Path(__file__).resolve().parent
out=root.parents[3]/'reviews/visual_upgrade/previews/greenkeeper_heavy_wreck_v01'
with tempfile.TemporaryDirectory(prefix='gk-wreck-review-') as tmp:
    pygame.init(); pygame.display.set_mode((960,540))
    game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
    try:
        game.start_new_game(); game.change_state(config.STATE_BOSS_BOUNTY)
        scene=game.current_scene; original=scene.boss.render
        image=pygame.image.load(str(root/'exports/wreck_nearest_256x192.png')).convert_alpha()
        def candidate(surface,camera):
            x,y=camera.world_to_screen(428,144)
            game.crt.composite_native(image,(x,y),(128,96))
        def save(name):
            game.render(); pygame.image.save(game.crt.render_surface,str(out/(name+'.png')))
        scene.boss.render=original; save('checkpoint_original_960')
        scene.boss.render=candidate; save('checkpoint_candidate_960')
        scene.player.x=300; scene.player.y=208; scene.player.rect.x=300;scene.player.rect.y=208
        scene.camera.snap_to(400,208)
        scene.boss.render=original;save('encounter_original_960')
        scene.boss.render=candidate;save('encounter_candidate_960')
        (out/'context.txt').write_text('Dummy SDL; temporary save; direct boss scene entry. Candidate render is monkeypatched, using CRT composite_native at world (428,144) size (128,96). Encounter: player artificially moved to (300,208), camera snapped to (400,208), i.e. x=160, y=18. Baseline original. Checkpoint: default on_enter position/camera. Images capture render_surface prior to CRT presentation; no attacks or normal play. This does not install the candidate or prove gameplay/native-window acceptance.\n')
    finally:
        game.close();pygame.quit()
