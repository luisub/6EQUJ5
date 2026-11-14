"""PURPOSE: Verify compact energy presentation against real projectile lifecycle.
CALLED BY: pytest.
HOW TO MODIFY: Keep live swept collision, routed firing and temporary saves under test.
"""
import math
from copy import deepcopy

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.energy_filament import EnergyFilament
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.weapons import CombatTarget, ProjectileManager
from .test_combat_assist import _room


@pytest.fixture(autouse=True)
def display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((960, 540))
    yield
    pygame.quit()


def sample_filament():
    source = pygame.Surface((96, 24), pygame.SRCALPHA)
    pygame.draw.line(source, (255, 240, 200, 255), (4, 12), (95, 12), 1)
    return source


class Camera:
    viewport_w, viewport_h = 480, 270
    def world_to_screen(self, x, y):
        return round(x), round(y)


class Recorder:
    def __init__(self):
        self.layers = []
    def composite_native_effects(self, layers):
        self.layers.extend(layers)


def shot(manager, x=20, y=50, dx=1, dy=0, *, primary=True):
    return manager.spawn(x, y, dx, dy, 420, 25, weapon_type='starter_maser',
                         is_primary_discharge=primary)


def test_segment_uses_actual_head_and_old_projectile_keeps_only_small_glow():
    view = EnergyFilament(sample_filament())
    manager = ProjectileManager()
    projectile = shot(manager)
    view.register([projectile], 7)
    manager.update(.05, _room())
    before = deepcopy(projectile.__dict__)
    recorder = Recorder()
    view.render(recorder, Camera(), manager.projectiles, 7)
    assert len(recorder.layers) == 3  # emitter, muzzle stem and projectile head
    image, (left, _top), _ = recorder.layers[1]
    assert left <= 2 * 20 <= left + image.get_width()
    assert left + image.get_width() <= 2 * projectile.x + 2
    assert projectile.__dict__ == before
    manager.update(.15, _room())
    recorder = Recorder()
    view.render(recorder, Camera(), manager.projectiles, 7)
    assert len(recorder.layers) == 1  # beyond stream age: a small live photon head
    glow, dest, _ = recorder.layers[0]
    assert glow.get_size() == (4, 7)
    assert dest == (2 * round(projectile.x) - 6, 2 * round(projectile.y) - 3)


@pytest.mark.parametrize('kind', ['wall', 'enemy'])
def test_absorbed_shot_leaves_no_stream_or_head(kind):
    view = EnergyFilament(sample_filament())
    manager = ProjectileManager()
    projectile = shot(manager)
    view.register([projectile], 4)
    room = _room(wall_column=4) if kind == 'wall' else _room()
    targets = [CombatTarget('target', pygame.Rect(44, 45, 6, 10), health=100, max_health=100)] if kind == 'enemy' else []
    manager.update(.05, room, targets)
    if manager.projectiles:
        manager.update(.1, room, targets)
    assert not manager.projectiles
    recorder = Recorder()
    view.render(recorder, Camera(), manager.projectiles, 4)
    assert recorder.layers == [] and not view.origins


def test_secondary_heads_follow_actual_paths_and_epoch_blocks_stale_fire():
    view = EnergyFilament(sample_filament())
    manager = ProjectileManager()
    prim = shot(manager)
    support = shot(manager, dy=.05, primary=False)
    view.register([prim, support], 1)
    manager.update(.2, _room())
    recorder = Recorder()
    view.render(recorder, Camera(), manager.projectiles, 1)
    assert [layer[0].get_size() for layer in recorder.layers] == [(4, 7), (3, 5)]
    assert recorder.layers[1][1][1] > recorder.layers[0][1][1]
    recorder = Recorder()
    view.render(recorder, Camera(), manager.projectiles, 1, blocked=True)
    view.render(recorder, Camera(), manager.projectiles, 2)
    assert recorder.layers == []  # pause/focus changes the input generation


def test_rotations_and_crop_cache_are_bounded_without_file_io(monkeypatch):
    view = EnergyFilament(sample_filament())
    from pathlib import Path
    monkeypatch.setattr(Path, 'read_bytes', lambda *_: pytest.fail('per-frame file read'))
    monkeypatch.setattr(Path, 'read_text', lambda *_args, **_kwargs: pytest.fail('per-frame manifest read'))
    monkeypatch.setattr(pygame.image, 'load', lambda *_args, **_kwargs: pytest.fail('per-frame image decode'))
    for angle in range(0, 360, 2):
        for length in (5.0, 20.0, 46.0):
            assert view._rotated_segment(length, angle) is not None
            assert view._rotated_emitter(length, angle) is not None
    assert len(view.cache) <= view.MAX_CACHE
    assert len(view.emitter_cache) <= view.MAX_CACHE
    image, pivot = view._rotated_segment(20, 0)
    assert image.get_width() - pivot[0] <= 40
    image, pivot = view._rotated_segment(20, 180)
    assert pivot[0] <= 40


@pytest.mark.parametrize('state', [config.STATE_FIELD_OPS, config.STATE_BOSS_BOUNTY])
def test_real_input_registers_actual_shot_and_pause_cancels_visual(state, tmp_path, monkeypatch):
    import video_game.engine.scenes.field as field_module
    import video_game.engine.scenes.boss as boss_module
    monkeypatch.setattr(field_module, 'load_energy_filament', lambda root: sample_filament())
    monkeypatch.setattr(boss_module, 'load_energy_filament', lambda root: sample_filament())
    game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path), settings_store=SettingsStore(tmp_path))
    try:
        assert game.start_new_game()[0]
        game.change_state(state)
        scene = game.current_scene
        if state == config.STATE_BOSS_BOUNTY:
            for _ in range(91):
                game.update(1/60)
                game.input.begin_frame()
        scene.player.x, scene.player.y = 100, 208 if state == config.STATE_BOSS_BOUNTY else 192
        scene.camera.snap_to(scene.player.x, scene.player.y)
        target = (round((scene.player.x + 150 - scene.camera.x) * 2),
                  round((scene.player.y + 15 - scene.camera.y) * 2))
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=target))
        game.update(1/60)
        manager = scene.projectile_manager if state == config.STATE_FIELD_OPS else scene.proj_mgr
        primary = next(p for p in manager.projectiles if p.is_primary_discharge and not p.is_charged)
        origin = scene.energy_filament.origins[primary.id]
        assert origin[0] == pytest.approx(primary.x - primary.vx / 60)
        assert origin[1] == pytest.approx(primary.y - primary.vy / 60)
        assert len(scene.effects.flashes) == 1
        assert scene.effects.flashes[0]['lighting_only']
        assert scene.effects.flashes[0]['maser_presentation']
        game.render()
        generation = game.input.charge_reset_generation
        game.open_pause()
        assert game.input.charge_reset_generation != generation
        recorder = Recorder()
        scene.energy_filament.render(recorder, scene.camera, manager.projectiles,
                                     game.input.charge_reset_generation)
        assert not recorder.layers
    finally:
        game.close()


def test_live_muzzle_anchor_is_clipped_to_head_wall_and_enemy():
    view = EnergyFilament(sample_filament())
    manager = ProjectileManager()
    projectile = shot(manager, x=20, y=50)
    view.register([projectile], 1)
    manager.update(.1, _room())  # Actual head is at x=62.
    muzzle = (30.0, 50.0)  # Mateo moved after the shot.
    clear_length = view._visible_stem(projectile, muzzle, _room())
    assert clear_length == pytest.approx(31.5)
    assert view._visible_stem(projectile, muzzle, _room(wall_column=3)) <= 17.5
    target = CombatTarget('near', pygame.Rect(40, 45, 6, 10), health=100, max_health=100)
    assert view._visible_stem(projectile, muzzle, _room(), [target]) <= 9.5
    recorder = Recorder()
    view.render(recorder, Camera(), manager.projectiles, 1, muzzle=muzzle, room=_room())
    _image, destination, _ = recorder.layers[1]
    _, pivot = view._rotated_segment(clear_length, 0)
    assert destination == (2 * round(muzzle[0]) - pivot[0], 2 * round(muzzle[1]) - pivot[1])
    # Strong perpendicular movement gets only a tiny, early muzzle flame, then just the head.
    projectile.lifetime = projectile.max_lifetime - .05
    assert view._visible_stem(projectile, (30.0, 60.0), _room()) <= view.MUZZLE_FLAME_LENGTH
    projectile.lifetime = projectile.max_lifetime - .1
    assert view._visible_stem(projectile, (30.0, 60.0), _room()) == 0


@pytest.mark.parametrize('direction', [(1, 0), (-1, 0), (0, -1), (2**-.5, -2**-.5)])
def test_stream_never_extends_ahead_of_projectile(direction):
    manager = ProjectileManager()
    p = shot(manager, x=200, y=100, dx=direction[0], dy=direction[1])
    manager.update(.04, _room())
    muzzle = (200 + 2 * direction[0], 100 + 2 * direction[1])
    length = EnergyFilament._visible_stem(p, muzzle)
    distance_to_head = math.hypot(p.x - muzzle[0], p.y - muzzle[1])
    assert 0 < length < distance_to_head


def test_missing_new_asset_preserves_existing_maser_fallback(tmp_path, monkeypatch):
    import video_game.engine.scenes.field as field_module
    monkeypatch.setattr(field_module, 'load_energy_filament', lambda root: None)
    game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path), settings_store=SettingsStore(tmp_path))
    try:
        assert game.start_new_game()[0]
        game.change_state(config.STATE_FIELD_OPS)
        scene = game.current_scene
        assert scene.energy_filament is None and scene.maser_presentation is not None
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x))
        game.update(1/60)
        assert any(f.get('maser_presentation') for f in scene.effects.flashes)
    finally:
        game.close()


def test_single_bridged_stem_and_reversed_aim_has_none():
    view = EnergyFilament(sample_filament())
    manager = ProjectileManager()
    first = shot(manager)
    view.register([first], 1)
    manager.update(.05, _room())
    second = shot(manager)
    view.register([second], 1)
    manager.update(.02, _room())
    recorder = Recorder()
    view.render(recorder, Camera(), manager.projectiles, 1, muzzle=(20, 50), aim_vector=(1, 0))
    assert len(recorder.layers) == 4  # one emitter and stem, plus two photon packets
    recorder = Recorder()
    view.render(recorder, Camera(), manager.projectiles, 1, muzzle=(20, 50), aim_vector=(-1, 0))
    assert len(recorder.layers) == 2  # reversing aim never bends an old stem


@pytest.mark.parametrize('state', [config.STATE_FIELD_OPS, config.STATE_BOSS_BOUNTY])
def test_walking_fire_uses_current_rendered_muzzle_and_aim(state, tmp_path, monkeypatch):
    import video_game.engine.scenes.field as field_module
    import video_game.engine.scenes.boss as boss_module
    monkeypatch.setattr(field_module, 'load_energy_filament', lambda root: sample_filament())
    monkeypatch.setattr(boss_module, 'load_energy_filament', lambda root: sample_filament())
    game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path), settings_store=SettingsStore(tmp_path))
    try:
        assert game.start_new_game()[0]
        game.change_state(state)
        scene = game.current_scene
        if state == config.STATE_BOSS_BOUNTY:
            for _ in range(91):
                game.update(1/60)
                game.input.begin_frame()
        scene.player.x, scene.player.y = 100, 208
        scene.camera.snap_to(scene.player.x, scene.player.y)
        if hasattr(scene, 'enemy_manager'):
            scene.enemy_manager.clear()
        target = (900, 420)
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
        game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=target))
        for _ in range(5):
            game.update(1/60)
            game.input.begin_frame()
        manager = scene.projectile_manager if state == config.STATE_FIELD_OPS else scene.proj_mgr
        primary = next(p for p in manager.projectiles if p.is_primary_discharge)
        old_origin = scene.energy_filament.origins[primary.id][:2]
        seen = []
        original = scene.energy_filament.render
        def record(*args, **kwargs):
            seen.append(kwargs)
            return original(*args, **kwargs)
        monkeypatch.setattr(scene.energy_filament, 'render', record)
        game.render()
        assert seen and seen[-1]['muzzle'] == pytest.approx(scene.player.get_muzzle_world_pos())
        assert math.dist(seen[-1]['muzzle'], old_origin) > 1
        aim = seen[-1]['aim_vector']
        assert math.hypot(*aim) == pytest.approx(1)
        assert primary.dir_x * aim[0] + primary.dir_y * aim[1] >= .98
    finally:
        game.close()


def test_emitter_bridges_barrel_and_halo_remains_thin_without_changing_source():
    source = sample_filament()
    before = pygame.image.tobytes(source, 'RGBA')
    view = EnergyFilament(source)
    emitter, pivot = view._rotated_emitter(20, 0)
    bounds = emitter.get_bounding_rect(min_alpha=1)
    assert emitter.get_width() <= 13 and emitter.get_height() <= 13
    assert bounds.left - pivot[0] <= -7  # Covers the small barrel-to-muzzle gap.
    assert bounds.right >= pivot[0]  # Connects the light to the actual beam origin.
    segment, _ = view._rotated_segment(20, 0)
    assert 1 < segment.get_bounding_rect(min_alpha=1).height <= 9
    assert pygame.image.tobytes(source, 'RGBA') == before


@pytest.mark.parametrize('angle', [0, 90, 180, 270, 45, 135, 225, 315])
def test_emitter_does_not_extend_past_near_obstacle(angle):
    view = EnergyFilament(sample_filament())
    safe_length = 1.5
    emitter, pivot = view._rotated_emitter(safe_length, angle)
    unit = (math.cos(math.radians(angle)), math.sin(math.radians(angle)))
    forward = []
    for y in range(emitter.get_height()):
        for x in range(emitter.get_width()):
            if emitter.get_at((x, y)).a:
                forward.append((x - pivot[0]) * unit[0] + (y - pivot[1]) * unit[1])
    assert forward and max(forward) <= safe_length * 2


def test_installed_filament_halo_is_no_wider_than_nine_native_pixels():
    from video_game.engine.energy_stream_assets import load_energy_filament
    image = load_energy_filament(config.ASSETS_DIR)
    assert image is not None
    segment, _ = EnergyFilament(image)._rotated_segment(46, 0)
    assert segment.get_bounding_rect(min_alpha=1).height <= 9


@pytest.mark.parametrize('location', ['approach', 'campus', 'boss'])
def test_compact_shot_lights_real_actor_without_old_burst(location, tmp_path, monkeypatch):
    """Mapped shots supply real muzzle light in each presentation scene."""
    game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path), settings_store=SettingsStore(tmp_path))
    try:
        assert game.start_new_game()[0]
        if location == 'boss':
            game.change_state(config.STATE_BOSS_BOUNTY)
            for _ in range(91):
                game.update(1/60)
                game.input.begin_frame()
        else:
            room = 'act_01/approach.json' if location == 'approach' else 'act_01/ohio_campus.json'
            spawn = 'bunker_exit' if location == 'approach' else 'campus_west'
            game.change_state(config.STATE_FIELD_OPS, room=room, spawn=spawn)
        scene = game.current_scene
        assert scene.energy_filament is not None and scene.maser_presentation is not None
        if hasattr(scene, 'enemy_manager'):
            scene.enemy_manager.clear()
        scene.player.x, scene.player.y = 160, 208
        scene.camera.snap_to(scene.player.x, scene.player.y)
        actor_results = []
        original_light = scene.maser_presentation.light_actor
        def record_actor(sprite, dest, camera, flashes):
            result = original_light(sprite, dest, camera, flashes)
            actor_results.append((pygame.image.tobytes(sprite, 'RGBA'),
                                  pygame.image.tobytes(result, 'RGBA'),
                                  [f.copy() for f in flashes]))
            return result
        monkeypatch.setattr(scene.maser_presentation, 'light_actor', record_actor)
        monkeypatch.setattr(scene.maser_presentation, 'render_bursts', lambda *_: pytest.fail('old maser burst rendered'))
        if location == 'approach':
            assert scene.firing_lighting is not None
            monkeypatch.setattr(scene.firing_lighting, 'render_bursts', lambda *_: pytest.fail('old approach burst rendered'))
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x))
        game.update(1/60)
        flash = scene.effects.flashes[-1]
        assert flash['lighting_only'] and flash['maser_presentation']
        assert flash['input_generation'] == game.input.charge_reset_generation
        game.render()
        assert actor_results and actor_results[-1][2] and actor_results[-1][2][0]['lighting_only']
        before, after, _ = actor_results[-1]
        assert before != after
        assert before[3::4] == after[3::4]  # Actor alpha remains byte-identical.
        game.open_pause()
        assert not scene.effects.current_lighting_flashes(game.input.charge_reset_generation)
    finally:
        game.close()


def test_lighting_only_metadata_never_draws_legacy_polygon_or_bitmap(monkeypatch):
    from video_game.engine.effects import EffectManager, MaserPresentation
    effects = EffectManager()
    effects.add_muzzle_flash(50, 50, maser_presentation=True, lighting_only=True, input_generation=3)
    flash = effects.flashes[-1]
    flash['aim_vector'] = (1, 0)
    surface = pygame.Surface((100, 100), pygame.SRCALPHA)
    before = pygame.image.tobytes(surface, 'RGBA')
    effects.render(surface, Camera(), suppress_maser=False)
    assert pygame.image.tobytes(surface, 'RGBA') == before
    presentation = MaserPresentation(pygame.Surface((64, 32), pygame.SRCALPHA))
    recorder = Recorder()
    assert presentation.active_flashes(effects.flashes) == [flash]
    presentation.render_bursts(recorder, Camera(), [flash])
    assert recorder.layers == []
    effects.discard_maser_flashes()
    assert effects.flashes == []


def test_missing_old_maser_does_not_draw_fallback_polygon(tmp_path, monkeypatch):
    import video_game.engine.scenes.field as field_module
    monkeypatch.setattr(field_module, 'load_maser_presentation', lambda _root: None)
    game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path), settings_store=SettingsStore(tmp_path))
    try:
        assert game.start_new_game()[0]
        game.change_state(config.STATE_FIELD_OPS, room='act_01/ohio_campus.json', spawn='campus_west')
        scene = game.current_scene
        assert scene.energy_filament is not None and scene.maser_presentation is None
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x))
        game.update(1/60)
        assert scene.effects.flashes[-1]['lighting_only']
        surface = pygame.Surface((480, 270), pygame.SRCALPHA)
        scene.effects.sparks.clear(); scene.effects.dust.clear(); scene.effects.smoke.clear()
        scene.effects.render(surface, scene.camera, suppress_maser=False)
        assert not pygame.mask.from_surface(surface).count()
        game.render()
    finally:
        game.close()


def test_compact_shot_lights_approach_material_without_legacy_burst(tmp_path, monkeypatch):
    game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path), settings_store=SettingsStore(tmp_path))
    try:
        assert game.start_new_game()[0]
        game.change_state(config.STATE_FIELD_OPS, room='act_01/approach.json', spawn='bunker_exit')
        scene = game.current_scene
        assert scene.energy_filament is not None and scene.firing_lighting is not None
        scene.enemy_manager.clear()
        scene.player.x, scene.player.y = 160, 208
        scene.camera.snap_to(scene.player.x, scene.player.y)
        seen = []
        original = scene.firing_lighting.render_world_bounce
        def record_bounce(crt, camera, flashes):
            before = pygame.image.tobytes(crt.render_surface, 'RGB')
            original(crt, camera, flashes)
            after = pygame.image.tobytes(crt.render_surface, 'RGB')
            seen.append((before, after, [f.copy() for f in flashes]))
        monkeypatch.setattr(scene.firing_lighting, 'render_world_bounce', record_bounce)
        monkeypatch.setattr(scene.firing_lighting, 'render_bursts', lambda *_: pytest.fail('old burst rendered'))
        monkeypatch.setattr(scene.maser_presentation, 'render_bursts', lambda *_: pytest.fail('old burst rendered'))
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x))
        game.update(1/60)
        flash = scene.effects.flashes[-1]
        assert flash['lighting_only'] and flash['lighting_token'] == scene._firing_light_token
        game.render()
        assert seen and seen[-1][2][0]['lighting_only']
        assert seen[-1][0] != seen[-1][1]  # The actual material RGB responds to the shot.
    finally:
        game.close()


def test_dead_boss_player_does_not_keep_compact_actor_light(tmp_path, monkeypatch):
    game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path), settings_store=SettingsStore(tmp_path))
    try:
        assert game.start_new_game()[0]
        game.change_state(config.STATE_BOSS_BOUNTY)
        scene = game.current_scene
        for _ in range(91):
            game.update(1/60)
            game.input.begin_frame()
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x))
        game.update(1/60)
        assert any(f.get('lighting_only') for f in scene._visible_lighting_events())
        scene.player.is_dead = True  # Exercise the death render before its next update.
        assert not any(f.get('lighting_only') for f in scene._visible_lighting_events())
        game.render()
    finally:
        game.close()


def test_repeat_shots_bridge_stem_only_while_newer_shot_is_fresh():
    view = EnergyFilament(sample_filament())
    manager = ProjectileManager()
    first = shot(manager)
    view.register([first], 1)
    manager.update(.15, _room())
    second = shot(manager)
    view.register([second], 1)
    manager.update(1/60, _room())
    assert first.max_lifetime - first.lifetime > view.STEM_TIME
    assert second.max_lifetime - second.lifetime < view.STEM_TIME
    recorder = Recorder()
    view.render(recorder, Camera(), manager.projectiles, 1, muzzle=(20, 50), aim_vector=(1, 0), room=_room())
    assert len(recorder.layers) == 4  # One connected stem and two actual photon heads.
    stem = next(surface for surface, _dest, _flags in recorder.layers if surface.get_width() > 20)
    assert stem.get_width() >= 90  # Prior live ray maintains the bounded full stem.
    manager.update(.16, _room())
    recorder = Recorder()
    view.render(recorder, Camera(), manager.projectiles, 1, muzzle=(20, 50), aim_vector=(1, 0), room=_room())
    assert len(recorder.layers) == 2  # No residual stem when the final tap ages out.


def test_prior_projectile_never_bridges_after_collision_or_aim_reversal():
    view = EnergyFilament(sample_filament())
    manager = ProjectileManager()
    first = shot(manager)
    view.register([first], 1)
    manager.update(.1, _room())
    second = shot(manager, dx=-1)
    view.register([second], 1)
    manager.update(.02, _room())
    recorder = Recorder()
    view.render(recorder, Camera(), manager.projectiles, 1, muzzle=(20, 50), aim_vector=(-1, 0), room=_room())
    assert len(recorder.layers) == 4  # Only the reversed newer ray can carry a stem.
    manager.projectiles.remove(first)  # Fixture: the old ray has already collided.
    recorder = Recorder()
    view.render(recorder, Camera(), manager.projectiles, 1, muzzle=(20, 50), aim_vector=(-1, 0), room=_room())
    assert len(recorder.layers) == 3 and first.id not in view.origins
