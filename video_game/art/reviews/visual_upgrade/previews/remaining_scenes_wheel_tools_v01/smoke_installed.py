"""PURPOSE: Smoke installed family loaders and room entry outside the checkout.
CALLED BY: remaining_scenes_wheel_tools_v01/check.py using isolated Python.
HOW TO MODIFY: Keep explicit installed path, temporary saves and fixture disclosures.
"""
import json
from pathlib import Path
import sys


target = Path(sys.argv[1]).resolve()
present = json.loads(sys.argv[2])
sys.path.insert(0, str(target))
import pygame
import video_game
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.native_room_assets import (
    _load_room_family_v2, load_approach_family, load_native_opaque_backdrop, load_native_room_family,
)
from video_game.engine.room_art_contracts import backdrop_manifest_template, manifest_template
from video_game.engine.state_machine import GameStateMachine
from video_game.main import run_game


if not Path(video_game.__file__).resolve().is_relative_to(target):
    raise RuntimeError(f'Imported game outside installed target: {video_game.__file__}')
if not Path(config.ASSETS_DIR).resolve().is_relative_to(target):
    raise RuntimeError('Asset root is outside installed target')
print('installed_game', video_game.__file__)
print('installed_assets', config.ASSETS_DIR)
if run_game(max_frames=2) != 2:
    raise RuntimeError('Installed game did not run two frames')
pygame.init()
pygame.display.set_mode((960, 540))
for family in present:
    if family == 'ohio_approach_v1':
        result = load_approach_family(config.ASSETS_DIR, 'act_01_approach', (960, 288))
    elif family.startswith('ohio_') and family != 'ohio_bunker_v1':
        template = manifest_template(family)
        result = _load_room_family_v2(config.ASSETS_DIR, family, template['room_id'], template['world'])
        if load_native_room_family(config.ASSETS_DIR, template['room_id'], template['world']) is None:
            raise RuntimeError(f'Public layered room loader failed: {family}')
    else:
        template = backdrop_manifest_template(family)
        result = load_native_opaque_backdrop(config.ASSETS_DIR, template['room_id'], template['world'])
    if result is None:
        raise RuntimeError(f'Installed family did not validate: {family}')
    print('validated_family', family)

machine = GameStateMachine(CRTRenderer(scale=1))
try:
    success, reason = machine.start_new_game()
    if not success:
        raise RuntimeError(f'Could not start temporary new game: {reason}')
    if 'ohio_bunker_v1' in present and machine.current_scene.native_backdrop is None:
        raise RuntimeError('Bunker did not load installed backdrop on entry')
    machine.render()
    print('rendered_scene', 'bunker_hub')
    field_rooms = [
        ('ohio_approach_v2', 'act_01/approach.json', 'bunker_exit', 'act_01_approach', 'native_approach'),
        ('ohio_salvage_v1', 'act_01/salvage_yard.json', 'yard_entrance', 'act_01_salvage_yard', 'native_approach'),
        ('ohio_dish_v1', 'act_01/dish_catwalk.json', 'catwalk_start', 'act_01_dish_catwalk', 'native_approach'),
        ('mandela_annex_v1', 'act_01/mandela_test.json', 'default', 'act_01_mandela_test', 'native_opaque'),
        ('dodleston_relay_v1', 'act_04/dodleston_relay.json', 'relay_entrance', 'act_04_dodleston_relay', 'native_opaque'),
        ('ehman_1977_v1', 'flashback/ehman_1977.json', 'default', 'flashback_ehman_1977', 'native_opaque'),
    ]
    for family, path, spawn, room_id, field in field_rooms:
        if family not in present:
            continue
        machine.change_state(config.STATE_FIELD_OPS, room=path, spawn=spawn)
        scene = machine.current_scene
        if scene.room.room_id != room_id or getattr(scene, field) is None:
            raise RuntimeError(f'Actual field entry did not load {family}')
        machine.render()
        print('rendered_scene', room_id, 'family', family)
    if 'ohio_arena_v1' in present:
        machine.change_state(config.STATE_BOSS_BOUNTY)
        if machine.current_scene.native_room is None:
            raise RuntimeError('Boss scene did not load arena family')
        machine.render()
        print('rendered_scene', 'act_01_greenkeeper_arena', 'family', 'ohio_arena_v1')
finally:
    machine.close()
    pygame.quit()
print('smoke_passed', json.dumps(present))
