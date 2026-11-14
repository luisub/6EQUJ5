"""PURPOSE: Capture actual milestone runtime scenes with explicit test preconditions.
CALLED BY: python -m video_game.tools.capture_runtime_audit --output-dir PATH.
HOW TO MODIFY: Capture rendered surfaces and disclose fixtures; never generate gate verdicts.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile
import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.state_machine import GameStateMachine


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    previous_save_dir = os.environ.get('SIX_GAME_SAVE_DIR')
    with tempfile.TemporaryDirectory() as saves:
        os.environ['SIX_GAME_SAVE_DIR'] = saves
        pygame.init()
        pygame.display.set_mode((480, 270))
        game = GameStateMachine(CRTRenderer(), development=False)
        try:
            game.start_new_game()
            game.contact_session.is_offline = True
            game.contact_session.send_message('2')
            def capture(label):
                game.update(1/60)
                game.render()
                surface = game.crt.render_surface
                pygame.image.save(surface, args.output_dir / f'{label}_native.png')
                pygame.image.save(pygame.transform.scale(surface, (1920, 1080)), args.output_dir / f'{label}_2x.png')
            game.change_state(config.STATE_SCIENCE_LAB)
            for index in range(4):
                game.current_scene._select_active(index)
                capture(f'lab_{index+1}')
                if index == 0:
                    game.current_scene.details_open = True
                    capture('lab_full_text')
                    game.current_scene.details_open = False
            game.change_state(config.STATE_BUNKER_HUB)
            game.campaign.apply_event({'event_id':'capture_fixture', 'type':'defeat_greenkeeper'})
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m))
            capture('annex')
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F6))
            game.current_scene.player.x = 96  # Placement fixture for panel layout inspection.
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
            capture('relay')
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F7))
            capture('flashback')
            (args.output_dir/'capture_context.json').write_text(json.dumps({
                'driver':pygame.display.get_driver(), 'fixtures':True,
                'purpose':'Static runtime layout inspection; no gameplay gate verdict',
                'preconditions':['offline evidence channel','Act I completion grant','relay panel placement']},indent=2))
        finally:
            game.close()
            pygame.quit()
            if previous_save_dir is None:
                os.environ.pop('SIX_GAME_SAVE_DIR', None)
            else:
                os.environ['SIX_GAME_SAVE_DIR'] = previous_save_dir


if __name__ == '__main__':
    main()
