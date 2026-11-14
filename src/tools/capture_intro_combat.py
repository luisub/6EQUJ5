"""PURPOSE: Capture intro/field VFX with temporary saves and input fixtures.
CALLED BY: Developer command below; never normal play or automated tests.
HOW TO MODIFY: Keep output explicit, temporary saves and fixture disclosures.

Run with --output <new-directory>; uses dummy SDL, not a native play certification.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
from PIL import Image

from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.opening_story import OpeningStory
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def capture(output):
    output.mkdir(parents=True, exist_ok=False)
    pygame.init()
    pygame.display.set_mode((960, 540))
    with tempfile.TemporaryDirectory(prefix='6equj5-intro-combat-') as temp:
        game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(Path(temp) / 'save'),
                                settings_store=SettingsStore(Path(temp) / 'settings'))
        game.change_settings(scale=1, crt_effects=False)

        def key(code, down=True):
            game.handle_event(pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP, key=code))

        def tap(code):
            key(code)
            key(code, False)

        def step(frames=1):
            for _ in range(frames):
                game.update(1 / 60)
                game.input.begin_frame()

        def snap(name):
            game.render()
            frame = game.crt.render_surface.copy()
            pygame.image.save(frame, output / f'{name}_960.png')
            pygame.image.save(pygame.transform.scale(frame, (1920, 1080)), output / f'{name}_1920.png')
            return frame

        try:
            tap(pygame.K_RETURN)
            for index in range(4):
                snap(f'intro_{index + 1}')
                x, y = OpeningStory.NEXT_BUTTON.center
                for event_type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                    game.handle_event(pygame.event.Event(event_type, button=1, pos=(x * 2, y * 2)))
            tap(pygame.K_RETURN)
            scene = game.current_scene
            game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(900, 424)))
            step(4)
            snap('starter_electricity')
            key(pygame.K_d)
            for _ in range(100):
                step()
                if scene.player.arsenal.temporary_id:
                    break
            key(pygame.K_d, False)
            assert scene.player.arsenal.temporary_id == 'arc_lance', 'Walk did not reach supply'
            snap('arc_pickup')
            frames = []
            for index in range(180):
                step()
                if index % 3 == 0:
                    game.render()
                    frame = game.crt.render_surface
                    frames.append(Image.frombytes('RGB', frame.get_size(), pygame.image.tobytes(frame, 'RGB')))
                if index == 24:
                    snap('arc_combat')
            frames[0].save(output / 'arc_combat.gif', save_all=True, append_images=frames[1:],
                           duration=50, loop=0, optimize=False)
            # Nova is a declared position fixture; the pickup/collision/fire paths
            # are still the runtime scene paths, with no campaign rewards injected.
            item = next(item for item in scene.weapon_pickups.items if item['weapon_id'] == 'nova_scatter')
            scene.player.x = item['rect'].x
            scene.player.y = item['rect'].bottom - scene.player.height
            scene.player.rect.topleft = (scene.player.x, scene.player.y)
            scene.camera.snap_to(scene.player.x, scene.player.y)
            step(15)
            snap('nova_combat')
            (output / 'capture.json').write_text(json.dumps({
                'display_driver': pygame.display.get_driver(), 'audio': 'dummy',
                'intro': 'title, four mouse Next clicks, bunker Enter; no travel scene',
                'arc': 'earned by mapped D movement; mapped mouse fire',
                'nova': 'player position fixture at second supply; scene collection and mapped mouse fire',
                'native_resolution': [960, 540], 'scaled_resolution': [1920, 1080],
                'no_player_saves_touched': True,
            }, indent=2) + '\n')
        finally:
            game.close()
            pygame.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    capture(parser.parse_args().output)
