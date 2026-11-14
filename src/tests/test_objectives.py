"""
MODULE: tests/test_objectives.py
PURPOSE: Test the 72-second dish defense holdout, wave schedules, bin progression, and rewards.
CALLED BY: pytest (`python -m pytest tests -q`).
HOW TO MODIFY: Add wave or timing regressions; maintain strict unit test standards.
"""

from pathlib import Path
import pygame
import pytest

from video_game.engine import config
from video_game.engine.campaign import Campaign, load_campaign_data
from video_game.engine.objectives import (
    DEFENSE_WAVES,
    DishDefenseHoldout,
    HOLDOUT_ACTIVE,
    HOLDOUT_COMPLETED,
    HOLDOUT_FAILED,
    HOLDOUT_IDLE,
    SIGNAL_BINS,
    TOTAL_DEFENSE_DURATION,
)
from video_game.engine.world import Room


def test_dish_defense_completion_at_exactly_72_seconds_within_one_step():
    """Verify defense completes at exactly 72.0s of active time within one step (A08 Check 1)."""
    holdout = DishDefenseHoldout(total_duration=72.0)
    assert holdout.state == HOLDOUT_IDLE
    assert not holdout.is_active

    holdout.start()
    assert holdout.is_active
    assert holdout.elapsed_time == 0.0

    # Advance in discrete ticks up to 71.8s
    dt = 0.2
    steps = round(71.8 / dt)
    for _ in range(steps):
        events = holdout.update(dt)
        assert holdout.state == HOLDOUT_ACTIVE
        assert not any(e["type"] == "COMPLETED" for e in events)

    assert pytest.approx(holdout.elapsed_time, abs=1e-4) == 71.8

    # Final tick crossing 72.0s threshold
    events = holdout.update(0.3)
    assert holdout.state == HOLDOUT_COMPLETED
    assert holdout.is_completed is True
    # Exactly clamped to 72.0s within that tick
    assert holdout.elapsed_time == 72.0
    completed_events = [e for e in events if e["type"] == "COMPLETED"]
    assert len(completed_events) == 1
    assert completed_events[0]["elapsed_time"] == 72.0

    # Subsequent ticks after completion do not advance time or emit completed events
    after_events = holdout.update(1.0)
    assert after_events == []
    assert holdout.elapsed_time == 72.0


def test_signal_display_follows_rising_and_falling_six_bin_sequence():
    """Verify signal display tracks rising and falling 6-bin Wow! sequence (A08 Check 2)."""
    holdout = DishDefenseHoldout(total_duration=72.0)
    holdout.start()

    expected_codes = ["6", "E", "Q", "U", "J", "5"]
    expected_snrs = [6, 14, 26, 30, 19, 5]

    observed_codes = []
    observed_snrs = []

    # Sample mid-point of each 12-second bin
    for b_idx in range(6):
        sample_time = (b_idx * 12.0) + 6.0
        # Step holdout to sample time
        delta = sample_time - holdout.elapsed_time
        if delta > 0:
            holdout.update(delta)

        disp = holdout.get_signal_display()
        assert disp["bin"] == b_idx
        assert disp["code"] == expected_codes[b_idx]
        assert disp["snr"] == expected_snrs[b_idx]
        observed_codes.append(disp["code"])
        observed_snrs.append(disp["snr"])

    # Verify complete 6EQUJ5 sequence
    assert observed_codes == expected_codes
    assert "".join(observed_codes) == "6EQUJ5"

    # Verify bell-curve intensity profile (strictly rising then strictly falling)
    # Rising: 6 -> E -> Q -> U (6 < 14 < 26 < 30)
    assert observed_snrs[0] < observed_snrs[1] < observed_snrs[2] < observed_snrs[3]
    # Peak at U (30 sigma)
    assert observed_snrs[3] == 30
    # Falling: U -> J -> 5 (30 > 19 > 5)
    assert observed_snrs[3] > observed_snrs[4] > observed_snrs[5]


def test_holdout_wave_scheduling_and_jammed_feedhorn_interaction():
    """Verify enemy waves trigger on schedule and jammed feedhorn can be unjammed (A08)."""
    holdout = DishDefenseHoldout(total_duration=72.0)
    holdout.start()

    # Tick 1: t=0.0s triggers Wave 1 (Scout Probe)
    ev1 = holdout.update(0.1)
    spawn1 = [e for e in ev1 if e["type"] == "SPAWN_WAVE"]
    assert len(spawn1) == 1
    assert spawn1[0]["wave"]["wave_id"] == "wave_01"
    assert holdout.is_jammed is False

    # Step to t=24.0s: triggers Wave 2 (Peak Attack) and jams feedhorn
    ev2 = holdout.update(23.9)
    spawn2 = [e for e in ev2 if e["type"] == "SPAWN_WAVE"]
    assert len(spawn2) == 1
    assert spawn2[0]["wave"]["wave_id"] == "wave_02"
    assert holdout.is_jammed is True

    # Jamming causes automated dish integrity decay
    init_hp = holdout.dish_integrity
    holdout.update(2.0)
    assert holdout.dish_integrity < init_hp

    # Unjamming arrests integrity decay
    holdout.unjam()
    assert holdout.is_jammed is False
    unjammed_hp = holdout.dish_integrity
    holdout.update(2.0)
    assert holdout.dish_integrity == unjammed_hp

    # Step to t=48.0s: triggers Wave 3 (Flank Siege)
    holdout.update(20.1)
    assert "wave_03" in holdout.spawned_waves


def test_failure_and_retry_clears_wave_state_and_restores_geometry():
    """Verify failure/retry clears wave state and restores geometry (A08 Check 3)."""
    holdout = DishDefenseHoldout(total_duration=72.0)
    holdout.start()

    # Step into Wave 2
    holdout.update(25.0)
    assert len(holdout.spawned_waves) == 2
    assert holdout.is_jammed is True

    # Dish takes fatal damage
    holdout.damage_dish(150.0)
    assert holdout.state == HOLDOUT_FAILED
    assert holdout.is_failed is True
    assert holdout.dish_integrity == 0.0

    # Updates while failed do nothing
    assert holdout.update(1.0) == []

    # Reset holdout (simulate checkpoint retry)
    holdout.reset()
    assert holdout.state == HOLDOUT_IDLE
    assert holdout.elapsed_time == 0.0
    assert holdout.dish_integrity == 100.0
    assert holdout.is_jammed is False
    assert len(holdout.spawned_waves) == 0
    assert holdout.failure_reason == ""

    # Verify clean restart
    holdout.start()
    assert holdout.is_active
    assert holdout.elapsed_time == 0.0


def test_pause_freezes_holdout_time_and_accumulates_gameplay_time_only():
    """Verify objective time freezes completely during pause."""
    holdout = DishDefenseHoldout(total_duration=72.0)
    holdout.start()

    # 10 seconds of paused game time
    ev_paused = holdout.update(10.0, is_paused=True)
    assert ev_paused == []
    assert holdout.elapsed_time == 0.0

    # 5 seconds of active gameplay time
    ev_active = holdout.update(5.0, is_paused=False)
    assert holdout.elapsed_time == pytest.approx(5.0)


def test_completion_reward_applies_once_atomically():
    """Verify completion reward applies once atomically to campaign state (A08 Check 4)."""
    campaign = Campaign(save_id="test_defense_reward")
    assert not campaign.state.room_flags.get("dish_defense_completed", False)

    holdout = DishDefenseHoldout(total_duration=72.0)
    holdout.start()
    holdout.update(72.0)
    assert holdout.is_completed is True

    # First reward claim succeeds
    cert_before = campaign.state.meters["scientific_certainty"]
    agency_before = campaign.state.meters["human_agency"]
    ok = holdout.apply_completion_reward(campaign)
    assert ok is True
    assert campaign.state.room_flags["dish_defense_completed"] is True
    assert campaign.state.meters["scientific_certainty"] == cert_before + 10
    assert campaign.state.meters["human_agency"] == agency_before + 5

    # Re-claim reward is idempotent and returns False
    ok_dup = holdout.apply_completion_reward(campaign)
    assert ok_dup is False
    assert campaign.state.meters["scientific_certainty"] == cert_before + 10


def test_dish_catwalk_level_schema_and_geometry_validity():
    """Verify dish_catwalk.json room schema, dimensions, and spawn clearance."""
    pygame.init()
    level_path = config.DATA_DIR / "levels" / "act_01" / "dish_catwalk.json"
    assert level_path.exists(), f"Level file missing: {level_path}"

    room = Room.load_from_file(level_path)
    campaign_data = load_campaign_data()
    errors = room.validate(campaign_data=campaign_data)
    assert errors == [], f"Level validation failed with errors: {errors}"

    # Verify spawn clearance (neither overlaps SOLID nor HAZARD)
    for s_name, sp in room.spawns.items():
        player_rect = pygame.Rect(int(sp.x), int(sp.y), 16, 32)
        col = room.check_rect_collision(player_rect)
        assert not col["solid"], f"Spawn '{s_name}' overlaps solid collision"
        assert not col["hazard"], f"Spawn '{s_name}' overlaps hazard collision"


def test_catwalk_defense_is_wired_to_field_scene_and_retry(tmp_path, monkeypatch):
    """Entering via the bunker runs a real holdout, including pause and retry."""
    from video_game.engine import config
    from video_game.engine.crt_renderer import CRTRenderer
    from video_game.engine.state_machine import GameStateMachine

    monkeypatch.setenv("SIX_GAME_SAVE_DIR", str(tmp_path / "saves"))
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    machine = GameStateMachine(CRTRenderer(), development=False)
    try:
        assert machine.start_new_game()[0]
        assert machine.campaign.apply_event({"event_id": "collect", "type": "collect_analog_coupler"})
        assert machine.campaign.apply_event({"event_id": "repair", "type": "repair_dish_feedhorn"})
        bunker = machine.current_scene
        bunker.mateo_x = 348.0
        assert bunker.interact_with_station()
        field = machine.current_scene
        assert field.holdout and field.holdout.is_active
        machine.update(0.1)
        assert len(field.enemy_manager.enemies) == 2
        assert "wave_01" in field.holdout.spawned_waves

        machine.open_pause()
        before = field.holdout.elapsed_time
        machine.update(1.0)
        assert field.holdout.elapsed_time == before
        machine.pause.active = False

        field.holdout.damage_dish(200)
        assert field.holdout.is_failed
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
        assert field.holdout.is_active and field.holdout.elapsed_time == 0
        assert not field.enemy_manager.enemies
        assert not field.player.is_dead

        # Run the real scene loop; neutralize spawned enemies as a combat fixture.
        # This verifies scene wiring and campaign persistence, not player skill.
        for _ in range(721):
            for enemy in field.enemy_manager.enemies:
                enemy.take_damage(10000, hit_id=f"fixture_{enemy.target_id}")
            if field.holdout.is_jammed:
                field.player.x = 300
                machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
                assert not field.holdout.is_jammed
            machine.update(0.1)
            if field.holdout.is_completed:
                break
        assert field.holdout.is_completed
        assert field.holdout.spawned_waves == {"wave_01", "wave_02", "wave_03"}
        assert machine.campaign.state.room_flags["dish_defense_completed"]
        assert machine.save_store.load().campaign.state.room_flags["dish_defense_completed"]
        assert not field.holdout.apply_completion_reward(machine.campaign)
        machine.change_state(config.STATE_BUNKER_HUB)
        bunker.mateo_x = 348.0
        assert bunker.interact_with_station()
        assert machine.current_state_name == config.STATE_BOSS_BOUNTY
    finally:
        machine.close()


def test_defense_rejects_reward_before_completion():
    campaign = Campaign(save_id="premature_reward")
    defense = DishDefenseHoldout()
    defense.start()
    assert not defense.apply_completion_reward(campaign)
    assert not campaign.state.room_flags.get("dish_defense_completed", False)


def test_catwalk_defense_pressure_and_player_casualty(tmp_path, monkeypatch):
    """Surviving enemies damage the dish; a casualty fails and retry resets it."""
    from video_game.engine import config
    from video_game.engine.crt_renderer import CRTRenderer
    from video_game.engine.state_machine import GameStateMachine

    monkeypatch.setenv("SIX_GAME_SAVE_DIR", str(tmp_path / "saves"))
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    machine = GameStateMachine(CRTRenderer(), development=False)
    try:
        machine.start_new_game()
        machine.campaign.apply_event({"event_id": "collect", "type": "collect_analog_coupler"})
        machine.campaign.apply_event({"event_id": "repair", "type": "repair_dish_feedhorn"})
        machine.current_scene.mateo_x = 348
        machine.current_scene.interact_with_station()
        field = machine.current_scene
        machine.update(0.1)
        field._defense_pressure_delay = 0
        old_integrity = field.holdout.dish_integrity
        machine.update(0.1)
        assert field.holdout.dish_integrity < old_integrity
        field.player.take_damage(10000, ignore_invulnerable=True)
        machine.update(0.1)
        assert field.holdout.is_failed
        assert field.holdout.failure_reason == "PLAYER CASUALTY"
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
        assert field.holdout.is_active and field.holdout.dish_integrity == 100
        assert not field.player.is_dead and field.player.health == field.player.cfg.max_health
    finally:
        machine.close()


def test_approach_exit_loads_salvage_yard_and_pickup(tmp_path, monkeypatch):
    """The approach and service edge route to the room containing the coupler."""
    from video_game.engine import config
    from video_game.engine.crt_renderer import CRTRenderer
    from video_game.engine.state_machine import GameStateMachine

    monkeypatch.setenv("SIX_GAME_SAVE_DIR", str(tmp_path / "saves"))
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    machine = GameStateMachine(CRTRenderer(), development=False)
    try:
        machine.start_new_game()
        machine.current_scene.mateo_x = 348
        machine.current_scene.interact_with_station()
        field = machine.current_scene
        assert field.room.room_id == "act_01_approach"
        # Position fixtures cover each adjacent exit; the earned route walks them.
        for target_room in ("act_01_ohio_campus", "act_01_salvage_yard"):
            exit_trigger = next(e for e in field.room.exits if e.target_room == target_room)
            field.player.x, field.player.y = exit_trigger.rect.x, exit_trigger.rect.y
            machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
            assert field.room.room_id == target_room
        depot = next(obj for obj in field.room.objects if obj.id == "analog_coupler_depot")
        assert (field.coupler_x, field.coupler_y) == (depot.x + depot.width / 2, depot.y + depot.height / 2)
        assert field.coupler_size == (depot.width, depot.height)
        field.player.x, field.player.y = field.coupler_x, field.coupler_y
        machine.update(1 / 60)
        assert machine.campaign.state.inventory.get("analog_coupler") == 1
        field.load_room("act_01/salvage_yard.json")
        field.player.x, field.player.y = field.coupler_x, field.coupler_y
        machine.update(1 / 60)
        assert machine.campaign.state.inventory.get("analog_coupler") == 1
        machine.save_checkpoint()
        assert machine.save_store.load().campaign.state.inventory.get("analog_coupler") == 1
    finally:
        machine.close()


def test_objective_change_updates_hud_without_a_duplicate_banner():
    from video_game.engine.objectives import ObjectiveTracker

    campaign = Campaign(save_id='objective_notice_fixture')
    tracker = ObjectiveTracker()
    tracker.last_objective_id = 'previous_objective'
    tracker.update(0, campaign)
    objective = tracker.get_active_objective(campaign)
    assert tracker.active_notification is None
    assert tracker.last_objective_id == objective.id
    assert objective.hint
