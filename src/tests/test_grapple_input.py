"""PURPOSE: Verify grapple and fire guards through real scene/key dispatch.
CALLED BY: pytest tests/test_grapple_input.py.
HOW TO MODIFY: Keep save/settings temporary and disclose fixture prerequisites.
"""
import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.player import PlayerInput


@pytest.fixture
def game(tmp_path):
    pygame.init()
    pygame.display.set_mode((480, 270))
    machine = GameStateMachine(CRTRenderer(), development=False,
                               save_store=SaveStore(tmp_path), settings_store=SettingsStore(tmp_path))
    assert machine.start_new_game()[0]
    # Public event is a prerequisite fixture, not an Act I playthrough.
    machine.campaign.apply_event({"event_id": "grapple-fixture", "type": "defeat_greenkeeper"})
    yield machine
    machine.close()
    pygame.quit()


def frame(game, *events, dt=1 / 60):
    game.input.begin_frame()
    for event_type, key in events:
        game.handle_event(pygame.event.Event(event_type, key=key))
    game.update(dt)


def tap(game, key):
    frame(game, (pygame.KEYDOWN, key))
    frame(game, (pygame.KEYUP, key))


def enter(game):
    tap(game, pygame.K_m)
    field = game.current_scene
    assert field.room.room_id == "act_01_mandela_test"
    return field


def test_g_press_hold_release_and_second_press(game):
    field = enter(game)
    frame(game, (pygame.KEYDOWN, pygame.K_g))
    assert field.player.is_grappling and field.player.grapple_anchor
    for _ in range(5):
        frame(game)
        assert field.player.is_grappling
    frame(game, (pygame.KEYUP, pygame.K_g))
    assert field.player.is_grappling
    frame(game, (pygame.KEYDOWN, pygame.K_g))
    assert not field.player.is_grappling
    assert field.player.grapple_anchor is None and field.player.grapple_anchor_pos is None
    frame(game, (pygame.KEYUP, pygame.K_g))


def test_short_frame_preserves_grapple_edge_until_fixed_step(game):
    field = enter(game)
    # A frame shorter than 1/120 second must not lose a short G press.
    field.player.accumulator = 0
    frame(game, (pygame.KEYDOWN, pygame.K_g), dt=1 / 240)
    assert not field.player.is_grappling
    frame(game, (pygame.KEYUP, pygame.K_g), dt=1 / 240)
    assert field.player.is_grappling


def test_no_anchor_and_jump_dash_release(game):
    field = enter(game)
    # Fixture moves only the player to a point outside the anchor's range.
    player = field.player
    player.x, player.y = 400, 208
    player.rect.topleft = (400, 208)
    tap(game, pygame.K_g)
    assert not player.is_grappling
    player.x, player.y = 32, 208
    player.rect.topleft = (32, 208)
    tap(game, pygame.K_g)
    assert player.is_grappling
    frame(game, (pygame.KEYDOWN, pygame.K_SPACE))
    assert not player.is_grappling
    frame(game, (pygame.KEYUP, pygame.K_SPACE))
    tap(game, pygame.K_g)
    assert player.is_grappling
    frame(game, (pygame.KEYDOWN, pygame.K_LSHIFT))
    assert player.is_dashing and not player.is_grappling
    assert player.grapple_anchor is None and player.grapple_anchor_pos is None


def test_pause_focus_death_and_room_reset(game):
    field = enter(game)
    tap(game, pygame.K_g)
    player = field.player
    assert player.is_grappling
    tap(game, pygame.K_F2)
    assert game.pause.active
    position = (player.x, player.y)
    frame(game, (pygame.KEYDOWN, pygame.K_g))
    frame(game, (pygame.KEYUP, pygame.K_g))
    assert player.is_grappling and (player.x, player.y) == position
    tap(game, pygame.K_F2)
    assert not game.pause.active and player.is_grappling
    game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    assert game.pause.active
    tap(game, pygame.K_F2)
    assert not game.pause.active and player.is_grappling
    player.health = 0; player.is_dead = True
    frame(game)
    assert not player.is_grappling and player.grapple_anchor is None
    # Return to the known annex start after the checkpoint respawn.
    tap(game, pygame.K_ESCAPE)
    tap(game, pygame.K_m)
    # Scene and room entry must not retain anchors from a previous room.
    tap(game, pygame.K_g)
    assert player.is_grappling
    tap(game, pygame.K_F6)
    assert not player.is_grappling and player.grapple_anchor is None
    tap(game, pygame.K_F8)
    assert not player.is_grappling and player.grapple_anchor is None
    tap(game, pygame.K_g)
    assert player.is_grappling
    tap(game, pygame.K_ESCAPE)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    tap(game, pygame.K_m)
    assert not player.is_grappling and player.grapple_anchor is None


def test_fire_guard_blocks_dead_and_background_cover(game):
    field = enter(game)
    player = field.player
    assert player.can_fire(field.room)
    player.in_cover = True; player.cover_type = "background"
    assert not player.can_fire(field.room)
    player.in_cover = False; player.cover_type = None; player.is_dead = True
    assert not player.can_fire(field.room)
    before = len(field.projectile_manager.projectiles)
    player.update(0, PlayerInput(fire_pressed=True, fire_held=True), field.room,
                  projectile_manager=field.projectile_manager)
    assert len(field.projectile_manager.projectiles) == before
    # Exercise weapon dispatch without Player.update's automatic respawn.
    player.weapon.update(1 / 60, PlayerInput(fire_pressed=True, fire_held=True), player,
                         field.room, field.projectile_manager)
    assert len(field.projectile_manager.projectiles) == before


def test_reaching_anchor_releases(game):
    player = enter(game).player
    tap(game, pygame.K_g)
    assert player.is_grappling
    ax, ay = player.grapple_anchor_pos
    # A close position is a fixture for the existing distance release.
    player.x = ax - player.width / 2 - 1
    player.y = ay - player.height / 2
    player.rect.topleft = (int(player.x), int(player.y))
    frame(game)
    assert not player.is_grappling and player.grapple_anchor is None


def test_room_reset_discards_buffered_key_and_preserves_cooldown(game):
    field = enter(game)
    player = field.player
    player.accumulator = 0
    player.dash_cooldown_timer = 0.5
    frame(game, (pygame.KEYDOWN, pygame.K_g), dt=1 / 240)
    assert not player.is_grappling
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F6))
    assert player.dash_cooldown_timer == pytest.approx(0.5)
    frame(game)
    assert not player.is_grappling


@pytest.mark.parametrize("interruption", ["pause", "focus", "resize"])
def test_pending_short_frame_press_is_discarded_on_control_release(game, interruption):
    field = enter(game)
    field.player.accumulator = 0
    frame(game, (pygame.KEYDOWN, pygame.K_g), dt=1 / 240)
    assert not field.player.is_grappling
    if interruption == "pause":
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F2))
    elif interruption == "focus":
        game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
    else:
        game.handle_event(pygame.event.Event(pygame.VIDEORESIZE, size=(480, 270), w=480, h=270))
    if game.pause.active:
        tap(game, pygame.K_F2)
    frame(game)
    assert not field.player.is_grappling


def test_room_transition_discards_old_jump_buffers(game):
    field = enter(game)
    player = field.player
    # Staged preconditions represent a buffered jump and recent ledge contact.
    player.jump_buffer_timer = 0.15
    player.coyote_timer = 0.1
    player.accumulator = 0.004
    player.dash_cooldown_timer = 0.5
    health, weapon = player.health, player.arsenal.active_weapon_id
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F6))
    assert player.jump_buffer_timer == player.coyote_timer == player.accumulator == 0
    assert player.health == health and player.arsenal.active_weapon_id == weapon
    assert player.dash_cooldown_timer == pytest.approx(0.5)
    frame(game)
    assert player.vy >= 0  # no stale jump impulse in the new room


def test_space_wall_jump_uses_mapper_without_implicit_grapple(game):
    field = enter(game)
    tap(game, pygame.K_t)
    assert field.room.active_timeline == "1977_ANALOG"
    player = field.player
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
    for index in range(80):
        events = []
        if index == 5:
            events.append((pygame.KEYDOWN, pygame.K_SPACE))
        if index == 17:
            events.append((pygame.KEYUP, pygame.K_SPACE))
        frame(game, *events)
        if player.is_wall_sliding:
            break
    assert player.is_wall_sliding
    assert not player.is_grappling
    frame(game, (pygame.KEYDOWN, pygame.K_SPACE))
    assert player.vx < -100 and player.vy < -150
    assert player.wall_jump_lock_timer > 0
    assert not player.is_grappling and player.grapple_anchor is None
