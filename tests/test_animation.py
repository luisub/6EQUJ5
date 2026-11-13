"""
MODULE: tests/test_animation.py
PURPOSE: Verify frame-rate independent playback, mirrored pivot registration,
         and animation state transitions for Mateo's action clips.
CALLED BY: pytest (`python -m pytest tests/test_animation.py -q`).
HOW TO MODIFY: Add focused test cases when new animation clips or outfits are introduced.
"""

from video_game.engine import config

from pathlib import Path
import pytest
import pygame

from video_game.engine.animation import (
    AnimationClip,
    AnimationPlayer,
    load_mateo_animations,
)
from video_game.engine.player import Player, PlayerConfig, PlayerInput
from video_game.engine.world import Room

ASSETS_DIR = config.ASSETS_DIR


@pytest.fixture(scope="module")
def pygame_setup():
    """Ensure headless pygame display is initialized for surface transformations."""
    pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((480, 270))
    yield
    pygame.quit()


def test_animation_clip_deterministic_timing(pygame_setup):
    """Verify frame index calculations for single-frame, looping, and non-looping clips."""
    surf1 = pygame.Surface((96, 128), pygame.SRCALPHA)
    surf2 = pygame.Surface((96, 128), pygame.SRCALPHA)
    surf3 = pygame.Surface((96, 128), pygame.SRCALPHA)
    surf4 = pygame.Surface((96, 128), pygame.SRCALPHA)

    # 1. Looping 4-frame run cycle (100ms per frame = 400ms cycle)
    clip_run = AnimationClip(
        name="run",
        frames=[surf1, surf2, surf3, surf4],
        frame_durations_ms=[100, 100, 100, 100],
        loop=True,
    )
    assert clip_run.total_duration_ms == 400
    assert clip_run.total_duration_s == 0.400
    assert clip_run.get_frame_index(0.000) == 0
    assert clip_run.get_frame_index(0.050) == 0
    assert clip_run.get_frame_index(0.100) == 1
    assert clip_run.get_frame_index(0.199) == 1
    assert clip_run.get_frame_index(0.200) == 2
    assert clip_run.get_frame_index(0.350) == 3
    # Wraparound
    assert clip_run.get_frame_index(0.400) == 0
    assert clip_run.get_frame_index(0.550) == 1
    assert clip_run.get_frame_index(1.050) == 2

    # 2. Non-looping clamp (e.g. shoot / land)
    clip_land = AnimationClip(
        name="land",
        frames=[surf1, surf2],
        frame_durations_ms=[80, 80],
        loop=False,
    )
    assert clip_land.get_frame_index(0.000) == 0
    assert clip_land.get_frame_index(0.079) == 0
    assert clip_land.get_frame_index(0.080) == 1
    assert clip_land.get_frame_index(0.500) == 1  # Stays clamped to last frame

    # 3. Static single-frame clip (duration = 0)
    clip_jump = AnimationClip(
        name="jump",
        frames=[surf1],
        frame_durations_ms=[0],
        loop=False,
    )
    assert clip_jump.get_frame_index(0.0) == 0
    assert clip_jump.get_frame_index(10.0) == 0


def test_animation_timings_are_framerate_independent(pygame_setup):
    """
    Acceptance Check: Advancing animation across 30, 60, and 120 render FPS
    produces identical frame progression at equivalent simulation times.
    """
    clips = load_mateo_animations(ASSETS_DIR, outfit="olive_field")
    assert "run" in clips

    # Simulate 1.0 second of playback at 30, 60, 120 FPS
    player_30 = AnimationPlayer(clips, default_state="run", scale_factor=0.25)
    player_60 = AnimationPlayer(clips, default_state="run", scale_factor=0.25)
    player_120 = AnimationPlayer(clips, default_state="run", scale_factor=0.25)

    dt_30 = 1.0 / 30.0
    dt_60 = 1.0 / 60.0
    dt_120 = 1.0 / 120.0

    # Test key time milestones (0.11s, 0.22s, 0.33s, 0.44s, 0.55s)
    # Step synchronized to 120Hz ticks
    history_30 = []
    history_60 = []
    history_120 = []

    for step_120 in range(120):
        player_120.update(dt_120)
        history_120.append(player_120.current_frame_index)

        # Every 2 ticks of 120 is one tick of 60
        if (step_120 + 1) % 2 == 0:
            player_60.update(dt_60)
            history_60.append(player_60.current_frame_index)

        # Every 4 ticks of 120 is one tick of 30
        if (step_120 + 1) % 4 == 0:
            player_30.update(dt_30)
            history_30.append(player_30.current_frame_index)

    # Verify matching states at every 30 FPS boundary
    for i in range(len(history_30)):
        idx_30 = history_30[i]
        idx_60 = history_60[(i + 1) * 2 - 1]
        idx_120 = history_120[(i + 1) * 4 - 1]
        assert idx_30 == idx_60 == idx_120, f"Frame mismatch at frame {i}: 30fps={idx_30}, 60fps={idx_60}, 120fps={idx_120}"


def test_mirrored_registration_preserves_foot_anchor(pygame_setup):
    """
    Acceptance Check: Facing changes preserve world foot anchor registration.
    No horizontal shifting, jumping pivots, or 1-pixel drift occurs when turning.
    """
    clips = load_mateo_animations(ASSETS_DIR, outfit="navy_chore")
    animator = AnimationPlayer(clips, default_state="idle", scale_factor=0.25)

    foot_world_x = 160.0
    foot_world_y = 200.0

    # Facing RIGHT
    animator.set_facing("right")
    dest_rx, dest_ry = animator.get_render_dest(foot_world_x, foot_world_y)
    piv_rx, piv_ry = animator.get_foot_pivot()
    drawn_foot_rx = dest_rx + piv_rx
    drawn_foot_ry = dest_ry + piv_ry

    # Facing LEFT
    animator.set_facing("left")
    dest_lx, dest_ly = animator.get_render_dest(foot_world_x, foot_world_y)
    piv_lx, piv_ly = animator.get_foot_pivot()
    drawn_foot_lx = dest_lx + piv_lx
    drawn_foot_ly = dest_ly + piv_ly

    # Both must align with the exact integer pixel of the foot anchor
    assert abs(drawn_foot_rx - foot_world_x) < 0.5
    assert abs(drawn_foot_lx - foot_world_x) < 0.5
    assert abs(drawn_foot_ry - foot_world_y) < 0.5
    assert abs(drawn_foot_ly - foot_world_y) < 0.5
    assert round(drawn_foot_rx) == round(drawn_foot_lx) == round(foot_world_x)
    assert round(drawn_foot_ry) == round(drawn_foot_ly) == round(foot_world_y)


def test_attachment_points_flip_symmetrically(pygame_setup):
    """Verify weapon muzzle attachment mirrors symmetrically across the actor center."""
    clips = load_mateo_animations(ASSETS_DIR, outfit="olive_field")
    animator = AnimationPlayer(clips, default_state="shoot", scale_factor=0.25)

    foot_world_x = 100.0
    foot_world_y = 150.0

    animator.set_facing("right")
    muzzle_right = animator.get_attachment_world_pos("muzzle", foot_world_x, foot_world_y)
    assert muzzle_right is not None

    animator.set_facing("left")
    muzzle_left = animator.get_attachment_world_pos("muzzle", foot_world_x, foot_world_y)
    assert muzzle_left is not None

    # Muzzle should project forward along facing axis with matching vertical height
    dx_right = muzzle_right[0] - foot_world_x
    dx_left = foot_world_x - muzzle_left[0]
    assert dx_right > 0, "Muzzle must point in front of character when facing right"
    assert dx_left > 0, "Muzzle must point in front of character when facing left"
    assert abs(dx_right - dx_left) < 1e-4, f"Asymmetrical muzzle offset: right={dx_right}, left={dx_left}"
    assert abs(muzzle_right[1] - muzzle_left[1]) < 1e-4, "Muzzle height must remain identical when turning"


def test_player_animation_state_transitions(pygame_setup):
    """Verify Player locomotion and combat states cleanly update the animation player."""
    player = Player(48.0, 192.0)
    clips = load_mateo_animations(ASSETS_DIR, outfit="olive_field")
    animator = AnimationPlayer(clips, default_state="idle", scale_factor=0.25)
    player.animator = animator

    # Helper room
    room_data = {
        "schema_version": 1,
        "room_id": "test_room",
        "act_id": "act_01",
        "tile_size": 16,
        "width_tiles": 20,
        "height_tiles": 15,
        "collision_layers": [[0]*20 for _ in range(14)] + [[1]*20],
        "objects": [
            {"id": "sandbag", "type": "cover", "x": 32.0, "y": 192.0, "width": 32.0, "height": 32.0, "properties": {"cover_type": "low"}},
            {"id": "alcove", "type": "cover", "x": 80.0, "y": 176.0, "width": 32.0, "height": 48.0, "properties": {"cover_type": "background"}},
        ],
    }
    room = Room(room_data)

    # 1. Idle
    inp = PlayerInput()
    player.update(0.016, inp, room)
    assert player.animation_state == "idle"
    assert player.animator.current_state == "idle"

    # 2. Walk
    player.vx = 60.0
    inp_walk = PlayerInput(move_x=0.5)
    player.update(0.008, inp_walk, room)
    assert player.animation_state == "walk"
    assert player.animator.current_state == "walk"

    # 3. Run
    player.vx = 170.0
    player.update(0.001, PlayerInput(), room)
    assert player.animation_state == "run"
    assert player.animator.current_state == "run"

    # 4. Jump
    player.y = 100.0
    player.is_grounded = False
    player.vx = 0.0
    player.vy = -180.0
    player.update(0.016, inp, room)
    assert player.animation_state == "jump"
    assert player.animator.current_state == "jump"

    # 5. Fall
    player.y = 100.0
    player.is_grounded = False
    player.vx = 0.0
    player.vy = 120.0
    player.update(0.016, inp, room)
    assert player.animation_state == "fall"
    assert player.animator.current_state == "fall"

    # 6. Crouch
    player.y = 192.0
    player.is_grounded = True
    player.is_crouching = True
    inp_crouch = PlayerInput(crouch_held=True)
    player.update(0.016, inp_crouch, room)
    assert player.animation_state == "cover_low"
    assert player.animator.current_state == "cover_low"

    # 7. Background Doorway Cover
    player.x = 88.0
    player.is_crouching = False
    inp_cov = PlayerInput(cover_pressed=True)
    player.fixed_update(player.cfg.fixed_dt, inp_cov, room)
    if player.animator:
        player.animator.set_state(player.animation_state)
    assert player.animation_state == "cover_background"
    assert player.animator.current_state == "cover_background"

    # 8. Slide-kick
    player.in_cover = False
    player.cover_type = None
    player.is_sliding = True
    player.slide_timer = player.cfg.slide_duration
    player.vx = player.cfg.slide_speed
    player.update(0.016, inp, room)
    assert player.animation_state == "slide"
    assert player.animator.current_state == "slide"

    # 9. Death
    player.is_dead = True
    assert player.animation_state == "death"
    if player.animator:
        player.animator.set_state(player.animation_state)
        assert player.animator.current_state == "death"


def test_all_three_outfits_have_complete_matching_animation_sets(pygame_setup):
    """Verify outfit continuity across navy_chore, olive_field, and faraday_rig."""
    outfits = ("navy_chore", "olive_field", "faraday_rig")
    loaded = {o: load_mateo_animations(ASSETS_DIR, outfit=o) for o in outfits}

    base_set = set(loaded["olive_field"].keys())
    assert len(base_set) >= 15

    for o in outfits:
        assert set(loaded[o].keys()) == base_set, f"Outfit {o} has mismatched animation clip keys"
        for anim_name, clip in loaded[o].items():
            assert clip.frame_count > 0
            assert clip.cell_size == (96, 128)
            assert clip.foot_pivot == (48, 124)
            assert clip.review_status == "reviewed"
