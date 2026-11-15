"""Capture one world's real renderer with temporary progression/position fixtures.

These are art integration captures, not an earned playthrough. Run from the
repository with python -m video_game.tools.capture_alien_world
--world alien_008 --output <new dir>. Existing output directories are refused.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import tempfile

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
from PIL import Image, ImageDraw

from video_game.engine import config
from video_game.engine.campaign_scenery import background_directory
from video_game.engine.alien_journey import journey_data, save_ledger
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def capture(world_id: str, output: Path) -> None:
    random.seed(1977)
    worlds = journey_data()['worlds']
    index = next(i for i, item in enumerate(worlds) if item['id'] == world_id)
    world = worlds[index]
    output.mkdir(parents=True, exist_ok=False)
    records = []
    pygame.init()
    pygame.display.set_mode((960, 540))
    with tempfile.TemporaryDirectory(prefix='6equj5-world-review-') as temporary:
        previous = os.environ.get('SIX_GAME_SAVE_DIR')
        os.environ['SIX_GAME_SAVE_DIR'] = temporary
        game = GameStateMachine(CRTRenderer(scale=1),
                                save_store=SaveStore(Path(temporary) / 'save'),
                                settings_store=SettingsStore(Path(temporary) / 'settings'))

        def stage(stage):
            assert game.start_new_game(replace_existing=True)[0]
            assert game.campaign.apply_event({'event_id': 'art_portal_fixture', 'type': 'defeat_portal_warden'})
            for i, prior in enumerate(worlds[:index]):
                assert game.campaign.apply_event({'event_id': f'art_guardian_fixture_{i}',
                                                  'type': prior['defeat_event']})
            save_ledger(game.campaign, {'version': 1, 'world_id': world_id, 'stage': stage,
                                       'checkpoint': None, 'receipts': [w['civ_id'] for w in worlds[:index]]})
            if stage == 'field':
                game.change_state(config.STATE_FIELD_OPS, room=world['field_room'], spawn='default',
                                  journey_world=world_id, campaign_route=True)
            else:
                game.change_state(config.STATE_BOSS_BOUNTY, room=world['arena_room'], spawn='default',
                                  journey_world=world_id, boss_id=world['boss_id'])
            assert game.current_scene.campaign_scenery.background_source['kind'] == 'native'
            return game.current_scene

        def still(name, *, crt=False, scale=1, setup=''):
            game.crt.glitch_timer_ms = 0
            game.crt.glitch_intensity = 0
            game.crt.set_scale(scale)
            game.crt.is_crt_enabled = crt
            game.render()
            if scale == 1 and not crt:
                surface = game.crt.render_surface.copy()
            else:
                surface = pygame.Surface((960 * scale, 540 * scale)).convert()
                game.crt.present(surface)
            destination = output / (name + '.png')
            pygame.image.save(surface, destination)
            scene = game.current_scene
            records.append({'file': destination.name, 'world': world_id,
                            'scene': game.current_state_name, 'setup': setup,
                            'camera': [scene.camera.x, scene.camera.y],
                            'dimensions': list(surface.get_size()), 'crt': crt,
                            'source': scene.campaign_scenery.background_source,
                            'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()})

        def motion(name):
            game.crt.set_scale(1)
            game.crt.is_crt_enabled = False
            frames = []
            for index in range(120):
                game.update(1 / 60)
                game.input.begin_frame()
                if index % 4 == 0:
                    game.crt.glitch_timer_ms = 0
                    game.crt.glitch_intensity = 0
                    game.render()
                    frame = game.crt.render_surface
                    frames.append(Image.frombytes('RGB', frame.get_size(), pygame.image.tobytes(frame, 'RGB')))
            palette = frames[0].quantize(colors=128, dither=Image.Dither.NONE)
            indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
            destination = output / (name + '.gif')
            indexed[0].save(destination, save_all=True, append_images=indexed[1:],
                            duration=67, loop=0, optimize=True, disposal=1)
            records.append({'file': destination.name, 'world': world_id,
                            'setup': 'Two seconds of ordinary scene updates after explicit static field fixture; enemies remain active.',
                            'dimensions': [960, 540], 'frames': len(frames), 'crt': False,
                            'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()})

        try:
            scene = stage('field')
            for name, fraction in (('field-start', 0), ('field-middle', .5), ('field-end', 1)):
                # Explicit stationary position fixture: no enemies/rewards are removed.
                scene.camera.x = (scene.room.width_px - 480) * fraction
                scene.camera.y = 0
                scene.player.x = scene.camera.x + 180
                scene.player.y = 208
                scene.player.is_grounded = True
                scene.player.animator.set_state('idle')
                setup = 'Prior guardian victories/receipts and static field position are explicit art-review fixtures.'
                still(name, setup=setup)
                if fraction == .5:
                    still(name + '-2x-crt', crt=True, scale=2, setup=setup)
                    motion('field-motion')
                    still('field-motion-final', setup='Final frame after two seconds of ordinary field updates.')

            scene = stage('guardian')
            scene.player.x, scene.player.y = 120, 208
            scene.player.is_grounded = True
            scene.camera.snap_to(248, 224)
            scene.camera.y = 0
            still('arena', setup='Guardian scene entered through explicit prior-victory/receipt fixture; no current-world victory.')
            still('arena-2x-crt', crt=True, scale=2,
                  setup='Same arena frame at integer 2x with CRT scanlines enabled.')
            # Render the real telegraph state, avoiding synthetic drawn warning markers.
            for _ in range(240):
                game.update(1 / 60)
                game.input.begin_frame()
                if scene.boss.telegraphs:
                    break
            still('arena-telegraph', setup='Actual boss update until the first attack warning; same fixture entry.')
            scene.boss.take_damage(50, hit_pos=scene.boss.rect.midleft)
            still('arena-hit', setup='Single disclosed 50-damage fixture to inspect hit response; no defeat.')
            for _ in range(240):
                game.update(1 / 60)
                game.input.begin_frame()
                if scene.boss.phase_state == 'RECOVERY':
                    break
            assert scene.boss.phase_state == 'RECOVERY'
            still('arena-recovery', setup='Actual boss update through its first attack into the recovery weak-point window.')
            (output / 'capture.json').write_text(json.dumps({
                'purpose': 'Actual-renderer art review, not a playthrough or hardware acceptance',
                'world': world_id, 'isolated_saves_and_settings': True,
                'video_driver': pygame.display.get_driver(), 'audio_driver': 'dummy',
                'runtime_art': {
                    name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for name, path in {
                        'background': game.assets.root / background_directory(
                            journey_data()['rooms'][world_id + '_field']['art_id']) / 'background.png',
                        'guardian': game.assets.root / 'sprites/bosses/campaign' / world['boss_id'] / 'body.png',
                    }.items()
                },
                'runtime_code': {
                    name: hashlib.sha256((Path(config.__file__).parent / name).read_bytes()).hexdigest()
                    for name in ('campaign_scenery.py', 'combat_feedback.py',
                                 'bosses/campaign_bosses.py', 'scenes/field.py', 'scenes/boss.py')
                },
                'captures': records,
            }, indent=2) + '\n')
        finally:
            game.close()
            pygame.quit()
            if previous is None:
                os.environ.pop('SIX_GAME_SAVE_DIR', None)
            else:
                os.environ['SIX_GAME_SAVE_DIR'] = previous
    sheet = Image.new('RGB', (960, 588), '#101722')
    draw = ImageDraw.Draw(sheet)
    for row, name in enumerate(('field-start', 'field-middle', 'field-end', 'arena')):
        with Image.open(output / (name + '.png')) as image:
            thumb = image.resize((480, 270), Image.Resampling.NEAREST)
        x, y = (row % 2) * 480, (row // 2) * 294
        sheet.paste(thumb, (x, y + 24))
        draw.text((x + 8, y + 6), f'{world_id} / {name}', fill='#dfe8ed')
    sheet.save(output / 'contact-sheet.png')
    print(json.dumps({'world': world_id, 'output': str(output), 'captures': len(records)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--world', choices=[world['id'] for world in journey_data()['worlds']],
                        required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    capture(args.world, args.output)
