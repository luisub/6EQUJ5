"""PURPOSE: Register relay background against actual timeline and puzzle-state rendering.
CALLED BY: Run from repository root with dummy SDL and --output-dir NEW_DIR.
HOW TO MODIFY: Keep temporary saves, direct action disclosure, source trace and unchanged runtime.
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import pygame
from PIL import Image
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine

SOURCE = Path('video_game/art/source/visual_upgrade/candidates/relay_shared_background_v01/source/relay_shared_background_generated_master.png')
EXPECTED = 'f26f8f6c4c0441cdfb4e52d886515160c2c8d77d6e826660d31235575654397f'
CASES = [
    ('initial', '2029_CORE', [], False),
    ('ruptured', '2029_CORE', ['action_open_cistern_flood'], False),
    ('drained', '2029_CORE', ['action_seal_valve_drain'], False),
    ('bulkhead_open', '2029_CORE', ['action_seal_valve_drain', 'action_install_jumper_j1'], False),
    ('cassette_spawned', '2029_CORE', ['action_seal_valve_drain', 'action_install_jumper_j1', 'action_cache_tape_chimney'], False),
    ('cassette_collected', '2029_CORE', ['action_seal_valve_drain', 'action_install_jumper_j1', 'action_cache_tape_chimney'], True),
    ('analog_initial', '1977_ANALOG', [], False),
]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', required=True, type=Path)
    args = p.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    if sha(SOURCE) != EXPECTED:
        raise ValueError('Unexpected source hash')
    export = args.output_dir / 'relay_shared_background_960x576.png'
    with Image.open(SOURCE) as src:
        if src.mode != 'RGB' or src.size != (1619, 971):
            raise ValueError(f'Unexpected source {src.mode} {src.size}')
        src.resize((960, 576), Image.Resampling.LANCZOS).save(export)
    pygame.init()
    pygame.display.set_mode((960, 540))
    samples = []
    try:
        with tempfile.TemporaryDirectory(prefix='6equj5-relay-registration-') as tmp:
            for name, timeline, actions, collect in CASES:
                path = Path(tmp) / name
                path.mkdir()
                game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(path), settings_store=SettingsStore(path))
                try:
                    game.start_new_game()
                    game.change_state(config.STATE_FIELD_OPS)
                    scene = game.current_scene
                    scene.load_room('act_04/dodleston_relay.json', spawn_name='relay_entrance')
                    if not scene.room.set_active_timeline(timeline):
                        raise ValueError(timeline)
                    scene.reality.world.active_timeline = timeline
                    for _ in range(30):
                        game.input.begin_frame()
                        game.update(1 / 60)
                    results = []
                    for action in actions:
                        ok, message = scene.reality.relay.apply_action(action, scene.reality.world, scene.player)
                        results.append({'action': action, 'ok': ok, 'message': message})
                        if not ok:
                            raise RuntimeError(f'{action}: {message}')
                    if collect and scene.reality.world.collect_pickup('cache_relay_tape', scene.player) is None:
                        raise RuntimeError('Expected cassette collection')
                    plate = pygame.image.load(str(export)).convert()
                    def background(_surface, camera):
                        game.crt.composite_native(plate.subsurface(pygame.Rect(0, round(2 * camera.y), 960, 540)), (0, 0), (480, 270))
                    scene.room.render_background = background
                    world = scene.reality.world
                    cassette = next(o for o in scene.room.objects if o.id == 'cache_relay_tape')
                    for cy in (0, 18):
                        scene.camera.x, scene.camera.y = 0, cy
                        game.render()
                        stem = f'{name}_y{cy}'
                        native = args.output_dir / f'{stem}_native_960.png'
                        review = args.output_dir / f'{stem}_review_1920.png'
                        pygame.image.save(game.crt.render_surface, str(native))
                        pygame.image.save(pygame.transform.scale(game.crt.render_surface, (1920, 1080)), str(review))
                        samples.append({'case': name, 'timeline': timeline, 'camera': [0, cy], 'player_rect': list(scene.player.rect),
                                        'grounded': scene.player.is_grounded, 'actions': results,
                                        'relay_flags': dict(scene.reality.relay.puzzle_flags),
                                        'coolant_row14_cols10_14': scene.room.collision_grid[14][10:15],
                                        'door': world.state.get_door_state('door_bulkhead_relay'),
                                        'cassette_spawned': cassette.properties.get('spawned'),
                                        'cassette_collected': world.state.is_collected('cache_relay_tape'),
                                        'native': native.name, 'native_sha256': sha(native),
                                        'review': review.name, 'review_sha256': sha(review)})
                finally:
                    game.close()
        info = {'source': str(SOURCE), 'source_size': [1619, 971], 'source_sha256': sha(SOURCE),
                'export': export.name, 'export_sha256': sha(export),
                'transform': 'Full 1619x971 image Lanczos-resized to 960x576; full canvas retained; near-matching aspect, no masks, painting or cleanup.',
                'composition': 'Fixture-local background callback draws source crop at y=2*camera.y before actual MandelaWorld terrain, active objects and field actor/HUD.',
                'fixture': 'Dummy SDL, temporary save per case, direct relay entry and timeline selection, 30 updates at 1/60; actual relay.apply_action called directly to set puzzle state, direct collect_pickup where listed, then forced camera y=0/18 without further updates.',
                'limits': 'Static direct-action fixtures; no normal input progression, actual swaps, open panel, full playthrough, native window, CRT, performance or art-gate acceptance.', 'samples': samples}
        (args.output_dir / 'context.json').write_text(json.dumps(info, indent=2) + '\n')
        print(json.dumps([{'case': x['case'], 'camera': x['camera'], 'native': x['native'], 'door': x['door'], 'spawned': x['cassette_spawned'], 'collected': x['cassette_collected'], 'coolant': x['coolant_row14_cols10_14']} for x in samples], indent=2))
    finally:
        pygame.quit()

if __name__ == '__main__':
    main()
