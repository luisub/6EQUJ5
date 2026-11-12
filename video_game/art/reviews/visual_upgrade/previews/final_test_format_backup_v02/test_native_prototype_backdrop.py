"""PURPOSE: Verify prototype background routing across existing timeline scenes.
CALLED BY: pytest.
HOW TO MODIFY: Use temporary families and real field/key routes; keep standalone fallback.
"""
import shutil
from copy import deepcopy
from pathlib import Path
import pygame
import pytest
from video_game.engine import config
from video_game.engine.assets import AssetCache
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.tools.build_room_family import build_backdrop_family

def key(game, code):
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))
    game.update(1 / 60)
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=code))

@pytest.fixture
def prototype_game(tmp_path):
    pygame.init()
    pygame.display.set_mode((960, 540))
    root = tmp_path / 'assets'
    shutil.copytree(config.ASSETS_DIR, root, ignore=shutil.ignore_patterns('mandela_annex_v1', 'dodleston_relay_v1', 'ehman_1977_v1'))
    for index, name in enumerate(('mandela_annex_v1', 'dodleston_relay_v1', 'ehman_1977_v1')):
        image = pygame.Surface((960, 576))
        image.fill((30 + index * 30, 40, 50))
        image.set_at((900, 80), (230, 5, 4))
        image.set_at((901, 80), (5, 4, 230))
        image.set_at((900, 116), (230, 5, 4))
        image.set_at((901, 116), (5, 4, 230))
        for x in range(200, 800, 20):
            for y in range(100, 400, 20):
                for offset in (0, 36):
                    image.set_at((x, y + offset), (230, 5, 4))
                    image.set_at((x + 1, y + offset), (5, 4, 230))
        path = tmp_path / f'{name}.png'
        pygame.image.save(image, str(path))
        build_backdrop_family(name, assets_dir=root, archive_dir=tmp_path / 'archive', backdrop=path, promote=True)
    game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path / 'save'), settings_store=SettingsStore(tmp_path / 'save'))
    try:
        game.assets = AssetCache(root)
        assert game.start_new_game()[0]
        yield (game, root)
    finally:
        game.close()
        pygame.quit()

def test_reality_background_routes_and_timeline_layers(prototype_game, monkeypatch):
    game, root = prototype_game
    game.campaign.apply_event({'event_id': 'fixture_boss', 'type': 'defeat_greenkeeper'})
    key(game, pygame.K_m)
    field = game.current_scene
    assert field.room.room_id == 'act_01_mandela_test' and field.native_opaque is not None
    assert field.reality.world is not None
    calls = []
    native_samples = []
    room = field.room
    original_composite = game.crt.composite_opaque_background

    def capture_native(surface, *a, **kw):
        native_samples.append((surface.get_at((900, 80))[:3], surface.get_at((901, 80))[:3]))
        return original_composite(surface, *a, **kw)
    monkeypatch.setattr(game.crt, 'composite_opaque_background', capture_native)
    bg = room.render_background
    tiles = room.render_tiles
    objects = room.get_objects_for_timeline

    def bg_call(*a, **kw):
        calls.append('background')
        return bg(*a, **kw)

    def tiles_call(*a, **kw):
        calls.append('tiles')
        return tiles(*a, **kw)

    def obj_call(*a, **kw):
        calls.append('objects')
        return objects(*a, **kw)
    monkeypatch.setattr(room, 'render_background', bg_call)
    monkeypatch.setattr(room, 'render_tiles', tiles_call)
    monkeypatch.setattr(room, 'get_objects_for_timeline', obj_call)
    monkeypatch.setattr(room, 'render_weather', lambda *a, **kw: None)
    collision_before = deepcopy(room.timeline_collision_layers)
    for timeline in ('2029_CORE', '1977_ANALOG'):
        if field.reality.world.active_timeline != timeline:
            key(game, pygame.K_t)
        assert field.reality.world.active_timeline == timeline
        field.reality.world.transition_timer = 0
        for y in (0, 18):
            calls.clear()
            field.camera.x = 0
            field.camera.y = y
            game.render()
            assert 'background' not in calls and calls.index('tiles') < calls.index('objects')
            assert native_samples[-1] == ((230, 5, 4), (5, 4, 230))
            frame = game.crt.render_surface
            assert any((frame.get_at((x, yp))[:3] == (230, 5, 4) and frame.get_at((x + 1, yp))[:3] == (5, 4, 230) for x in range(200, 800, 20) for yp in range(100, 400, 20)))
    assert room.timeline_collision_layers == collision_before
    field.camera.y = 0
    with monkeypatch.context() as patch:
        original_open = Path.open

        def no_family_read(path, *a, **kw):
            if path.is_relative_to(root / 'environments/mandela_annex_v1'):
                pytest.fail('family file read during frame')
            return original_open(path, *a, **kw)
        patch.setattr(Path, 'open', no_family_read)
        patch.setattr(pygame.image, 'load', lambda *a, **kw: pytest.fail('image loaded during frame'))
        game.render()
    calls.clear()
    field.camera.y = -0.25
    game.render()
    assert calls.count('background') == 1 and 'tiles' in calls
    calls.clear()
    field.camera.y = 0
    surface = pygame.Surface((480, 270))
    field.reality.world.render(surface, field.camera)
    assert calls.count('background') == 1 and calls.index('background') < calls.index('tiles')

def test_key_routes_reload_correct_family_and_corrupt_falls_back(prototype_game, monkeypatch):
    game, root = prototype_game
    game.campaign.apply_event({'event_id': 'fixture_boss', 'type': 'defeat_greenkeeper'})
    key(game, pygame.K_m)
    field = game.current_scene
    assert field.native_opaque.surface.get_at((100, 100))[:3] == (30, 40, 50)
    health = field.player.health
    hitbox = field.player.rect.size
    key(game, pygame.K_F6)
    assert field.room.room_id == 'act_04_dodleston_relay'
    assert field.native_opaque.surface.get_at((100, 100))[:3] == (60, 40, 50)
    field.player.x = 96
    key(game, pygame.K_e)
    assert field.reality.panel_open
    drawn = []
    original_draw = game.crt.draw_text

    def record(text, *args, **kwargs):
        drawn.append(str(text))
        return original_draw(text, *args, **kwargs)
    monkeypatch.setattr(game.crt, 'draw_text', record)
    game.render()
    assert any(('DODLESTON RELAY' in text for text in drawn))
    assert not any((text.startswith('[Q] ') for text in drawn))
    key(game, pygame.K_e)
    assert not field.reality.panel_open
    drawn.clear()
    game.render()
    assert any((text.startswith('[Q] ') for text in drawn))
    key(game, pygame.K_F7)
    assert field.room.room_id == 'flashback_ehman_1977' and field.flashback is not None
    assert field.native_opaque.surface.get_at((100, 100))[:3] == (90, 40, 50)
    assert field.player.health == health and field.player.rect.size == hitbox
    path = root / 'environments/ehman_1977_v1/backdrop_960x576.png'
    path.write_bytes(path.read_bytes() + b'corrupt')
    field.load_room('flashback/ehman_1977.json', spawn_name='ehman_entrance')
    assert field.native_opaque is None
    game.render()
