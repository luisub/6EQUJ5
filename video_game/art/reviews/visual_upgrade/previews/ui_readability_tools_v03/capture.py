"""PURPOSE: Capture reproducible UI text inspection fixtures at native and display size.
CALLED BY: PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python capture.py --output-dir NEW_DIR.
HOW TO MODIFY: Retain explicit fixture, temporary save, and output overwrite protection.
"""
import argparse
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from video_game.engine.flashback import FlashbackStage
import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='6equj5-ui-review-') as tmp:
        pygame.init();pygame.display.set_mode((960,540))
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
        try:
            def capture(name):
                game.render(); surface=game.crt.render_surface
                pygame.image.save(surface,str(args.output_dir/f'{name}_960.png'))
                pygame.image.save(pygame.transform.scale(surface,(1920,1080)),str(args.output_dir/f'{name}_1920.png'))
            capture('title')
            game.start_new_game(); game.change_state(config.STATE_CRT_TERMINAL)
            game.contact_session.is_offline=True
            game.contact_session.send_message('2');game.contact_session.send_message('1')
            game.current_scene._sync_transcript();capture('terminal_transcript')
            game.current_scene.input_buffer.set_text('A long message with variable-width text, σ and scientific measurement 1420.4056 MHz')
            capture('terminal_input_long')
            game.change_state(config.STATE_SCIENCE_LAB);capture('lab')
            game.current_scene.details_open=True;capture('lab_details')
            game.current_scene.details_offset=999;capture('lab_details_bottom')
            game.current_scene.details_open=False;game.pause.open();capture('settings')
            game.pause.close();game.change_state(config.STATE_FIELD_OPS)
            for _ in range(30):game.update(1/60)
            capture('field_hud')
            game.change_state(config.STATE_BUNKER_HUB)
            bunker=game.current_scene
            long_obj=SimpleNamespace(title='GREENKEEPER',description='Eliminate the Core Overseer and expose the reactor weak point while avoiding the mortar barrages and laser sweeps. '*5,hint='Use the arena cover, dodge telegraphed attacks, and fire on the exposed core. '*4)
            bunker.objective_tracker.get_active_objective=lambda campaign: long_obj
            bunker.dossier_open=True; capture('dossier_long_top')
            bunker.dossier_offset=100; capture('dossier_long_bottom')
            bunker.dossier_open=False
            game.change_state(config.STATE_FIELD_OPS,room='act_04/dodleston_relay.json')
            game.current_scene.reality.panel_open=True; capture('relay')
            game.change_state(config.STATE_BUNKER_HUB)
            game.change_state(config.STATE_FIELD_OPS,room='flashback/ehman_1977.json')
            flash=game.current_scene.flashback; flash.stage=FlashbackStage.ANNOTATION_APPLIED; flash.is_printout_open=True
            capture('flashback_annotated')
            game.change_state(config.STATE_BOSS_BOUNTY); capture('boss_hud')
            game.current_scene.boss.is_defeated=True;capture('boss_hud_no_alert')
            game.crt.is_crt_enabled=True; window=pygame.Surface((1920,1080)); game.crt.present(window)
            pygame.image.save(window,str(args.output_dir/'boss_hud_crt_on_1920.png'))
            (args.output_dir/'context.json').write_text(json.dumps({'driver':pygame.display.get_driver(),'save':'temporary',
                'preconditions':'direct scene changes; offline authored channels 2 and 1; laboratory details forced open; pause opened directly; field settled 30 ticks; dossier long objective injected; relay panel and annotated flashback opened by fixture; boss directly entered',
                'outputs':'960 native and nearest 2x 1920; CRT postprocessing off',
                'limits':'static fixture inspection, no live AI, human playthrough, native window or graphical-performance claim'},indent=2)+'\n')
        finally:game.close();pygame.quit()


if __name__=='__main__':main()
