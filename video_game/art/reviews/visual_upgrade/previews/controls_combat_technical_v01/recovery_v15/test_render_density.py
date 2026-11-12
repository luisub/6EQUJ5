"""PURPOSE: Verify render density preserves geometry and compositing order.
CALLED BY: pytest.
HOW TO MODIFY: Extend observable frame and geometry invariants for new layers.
"""
import json
import pygame
import pytest
from video_game.engine import config
from video_game.engine.animation import load_mateo_animations, AnimationPlayer
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.settings import Settings, SettingsStore


@pytest.fixture
def display():
    pygame.init()
    pygame.display.set_mode((960, 540))
    yield
    pygame.quit()


def test_native_layers_occlusion_and_next_frame_clear(display):
    crt = CRTRenderer(scale=1)
    crt.clear((1, 2, 3))
    # Two distinct native pixels occupy the same logical pixel.
    sprite = pygame.Surface((4, 2), pygame.SRCALPHA)
    sprite.fill((255, 0, 0, 255))
    sprite.set_at((1, 0), (0, 255, 0, 255))
    crt.composite_native(sprite, (10, 20), (2, 1))
    pygame.draw.rect(crt.logical_canvas, (0, 0, 255), (11, 20, 1, 1))
    frame = crt.finalize_frame()
    assert frame.get_size() == (960, 540)
    assert frame.get_at((20, 40))[:3] == (255, 0, 0)
    assert frame.get_at((21, 40))[:3] == (0, 255, 0)
    assert frame.get_at((22, 40))[:3] == (0, 0, 255)
    assert frame.get_at((23, 40))[:3] == (0, 0, 255)
    crt.clear((4, 5, 6))  # next frame, e.g. blink or another scene
    assert crt.finalize_frame().get_at((20, 40))[:3] == (4, 5, 6)


def test_mateo_native_detail_without_world_geometry_change(display):
    clips = load_mateo_animations(config.ASSETS_DIR, 'olive_field')
    anim = AnimationPlayer(clips, scale_factor=.25)
    foot = (56, 240)
    before = (anim.get_foot_pivot(), anim.get_hurtbox(*foot), anim.get_attachment_world_pos('muzzle', *foot))
    assert anim.current_surface.get_size() == (24, 32)
    hi = anim.surface_for_density(2)
    assert hi.get_size() == (48, 64)
    # Detailed direct source sampling must not equal doubling the old sample.
    assert pygame.image.tobytes(hi, 'RGBA') != pygame.image.tobytes(pygame.transform.scale(anim.current_surface, (48,64)), 'RGBA')
    assert (anim.get_foot_pivot(), anim.get_hurtbox(*foot), anim.get_attachment_world_pos('muzzle', *foot)) == before
    for facing in ('right', 'left'):
        anim.set_facing(facing)
        px, py = anim.get_foot_pivot()
        world_hurtbox = anim.get_hurtbox(*foot)
        world_muzzle = anim.get_attachment_world_pos('muzzle', *foot)
        dx, dy = anim.get_render_dest_for_density(*foot, None, 2)
        assert (dx, dy) == (round((foot[0] - px) * 2), round((foot[1] - py) * 2))
        assert abs(dx + px * 2 - foot[0] * 2) <= 0.5
        assert abs(dy + py * 2 - foot[1] * 2) <= 0.5
        anim.surface_for_density(2)
        assert anim.get_hurtbox(*foot) == world_hurtbox
        assert anim.get_attachment_world_pos('muzzle', *foot) == world_muzzle
        if facing == 'left':
            anim.set_facing('right'); right = anim.surface_for_density(2)
            anim.set_facing('left'); left = anim.surface_for_density(2)
            assert pygame.image.tobytes(left, 'RGBA') == pygame.image.tobytes(pygame.transform.flip(right, True, False), 'RGBA')


def test_actual_field_and_boss_frames_clear_blink_and_keep_camera(display, tmp_path, monkeypatch):
    from video_game.engine.save_game import SaveStore
    from video_game.engine.state_machine import GameStateMachine
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path), settings_store=SettingsStore(tmp_path))
    try:
        machine.start_new_game()
        for state in (config.STATE_FIELD_OPS, config.STATE_BOSS_BOUNTY):
            machine.change_state(state)
            scene = machine.current_scene
            assert (scene.camera.viewport_w, scene.camera.viewport_h) == (480, 270)
            marker = pygame.Surface((48, 64), pygame.SRCALPHA); marker.fill((255, 0, 255, 255))
            monkeypatch.setattr(scene.player.animator, 'surface_for_density',
                                lambda density: pygame.transform.scale(marker, (24 * density, 32 * density)))
            monkeypatch.setattr(scene.room, 'render_weather', lambda *args: None)
            scene.player.invulnerable_timer = 0
            machine.render()
            dest = scene.player.animator.get_render_dest_for_density(scene.player.x + scene.player.width / 2, scene.player.y + 32, scene.camera, 2)
            pos = (dest[0] + 2, dest[1] + 2)
            assert machine.crt.render_surface.get_at(pos)[:3] == (255, 0, 255)
            scene.player.invulnerable_timer = .1  # flash_hidden: int(.1 * 20) is even
            machine.render()
            assert machine.crt.render_surface.get_at(pos)[:3] != (255, 0, 255)
            machine.pause.active = True
            machine.render()
            assert machine.crt.render_surface.get_size() == (960, 540)
            machine.pause.active = False
        machine.change_state(config.STATE_BUNKER_HUB)
        machine.render()
        assert machine.crt.render_surface.get_at(pos)[:3] != (255, 0, 255)
    finally:
        machine.close()


def test_legacy_settings_migrate_in_memory_without_rewrite(tmp_path):
    store = SettingsStore(tmp_path)
    for old, new in ((1,1), (2,1), (3,2), (4,2)):
        raw = json.dumps({'schema_version':1,'volume':37,'crt_effects':False,'scale':old})
        store.path.write_text(raw)
        assert store.load() == Settings(volume=37, crt_effects=False, scale=new)
        assert store.path.read_text() == raw and not store.warning
    for raw in ('null', '[]', '123'):
        store.path.write_text(raw)
        assert store.load() == Settings() and store.warning
    store.save(Settings(volume=37, crt_effects=False, scale=2))
    assert json.loads(store.path.read_text())['schema_version'] == 2
