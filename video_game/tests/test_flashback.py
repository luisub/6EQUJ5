"""
MODULE: video_game/tests/test_flashback.py
PURPOSE: Comprehensive unit and integration verification for Task S08 (1977 Big Ear Dr. Jerry Ehman flashback).
CALLED BY: pytest (`pytest video_game/tests/test_flashback.py`).
HOW TO MODIFY: Add test assertions for new historical props, stage transitions, or audio cues; maintain zero wildcard imports.
"""

from copy import deepcopy
from pathlib import Path
import pytest
import pygame

from video_game.engine import config
from video_game.engine.campaign import Campaign, load_campaign_data
from video_game.engine.flashback import FlashbackController, FlashbackSnapshot, FlashbackStage
from video_game.engine.player import Player, PlayerInput
from video_game.engine.scenes.field import FieldOpsScene
from video_game.engine.world import Room


LEVELS_DIR = Path(__file__).resolve().parent.parent / "data" / "levels"


class MockMachine:
    """Mock state machine for testing FieldOpsScene room transitions and campaign sync."""

    def __init__(self, campaign=None):
        self.campaign = campaign or Campaign(save_id="test_flashback_save")
        self.input = None
        self.audio = None
        self.assets = None
        self.is_paused = False
        self.last_state_change = None

    def change_state(self, state_name, **kwargs):
        self.last_state_change = (state_name, kwargs)

    def save_checkpoint(self):
        return True

    def render_global_hud(self, *args, **kwargs):
        pass


def test_flashback_level_schema_and_initial_state():
    """Verify ehman_1977.json satisfies DATA_CONTRACTS.md and campaign registry."""
    path = LEVELS_DIR / "flashback" / "ehman_1977.json"
    assert path.exists(), f"Level file missing at {path}"

    c_data = load_campaign_data()
    room = Room.load_from_file(path)
    errors = room.validate(campaign_data=c_data)
    assert errors == [], f"Level validation failed: {errors}"

    assert room.room_id == "flashback_ehman_1977"
    assert room.act_id == "act_01"
    assert room.width_tiles == 30
    assert room.height_tiles == 18
    assert room.tile_size == 16
    assert room.active_timeline == "1977_ANALOG"

    # Spawns must be collision free
    assert "ehman_entrance" in room.spawns
    assert "ehman_desk" in room.spawns
    assert "ehman_vault" in room.spawns

    for sp_name, sp in room.spawns.items():
        rect = pygame.Rect(int(sp.x), int(sp.y), 16, 32)
        col = room.check_rect_collision(rect)
        assert not col["solid"], f"Spawn {sp_name} overlaps solid geometry"
        assert not col["hazard"], f"Spawn {sp_name} overlaps hazard geometry"

    # Exits must lead to bunker_hub
    assert len(room.exits) >= 1
    assert room.exits[0].target_room == "bunker_hub"


def test_flashback_stage_progression_printout_to_anchor():
    """Verify Dr. Jerry Ehman's 4-step sequence: printout -> annotation -> reel -> reality anchor."""
    campaign = Campaign(save_id="test_save_s08")
    snap = FlashbackSnapshot(origin_room="bunker_hub", origin_spawn="bunker_start", saved_health=85)
    controller = FlashbackController(campaign=campaign, snapshot=snap)

    # Stage 0: Entered
    assert controller.stage == FlashbackStage.ENTERED
    assert "INSPECT" in controller.get_prompt(112.0)

    # Step 1: Inspect printout
    success, msg = controller.inspect_printout()
    assert success is True
    assert controller.stage == FlashbackStage.PRINTOUT_INSPECTED
    assert controller.is_printout_open is True
    assert "6EQUJ5" in msg

    # Step 2: Apply red pen annotation ("Wow!")
    success, msg = controller.apply_red_annotation()
    assert success is True
    assert controller.stage == FlashbackStage.ANNOTATION_APPLIED
    assert "Wow!" in msg

    # Step 3: Retrieve analog magnetic reel
    success, msg = controller.retrieve_hidden_reel()
    assert success is True
    assert controller.stage == FlashbackStage.REEL_RETRIEVED
    assert "magnetic tape reel" in msg

    # Step 4: Lock Reality Anchor
    success, msg = controller.lock_reality_anchor(campaign)
    assert success is True
    assert controller.stage == FlashbackStage.COMPLETED
    assert "Reality Anchor 1977 established" in msg

    # Verify campaign grant event consequences
    assert campaign.state.inventory.get("reality_anchor_1977") == 1
    assert campaign.state.room_flags.get("flashback_1977_completed") is True
    assert campaign.state.meters["scientific_certainty"] == 50  # 40 initial + 10 delta
    assert campaign.state.meters["human_agency"] == 80  # 70 initial + 10 delta


def test_anchor_granted_once_idempotence():
    """Verify Reality Anchor is granted exactly once; subsequent re-entry or replay cannot duplicate it."""
    campaign = Campaign(save_id="test_save_idempotence")
    controller = FlashbackController(campaign=campaign)

    # Complete sequence
    controller.inspect_printout()
    controller.apply_red_annotation()
    controller.retrieve_hidden_reel()
    controller.lock_reality_anchor(campaign)

    assert campaign.state.inventory["reality_anchor_1977"] == 1

    # Second call must not increment inventory
    success, msg = controller.lock_reality_anchor(campaign)
    assert success is True
    assert campaign.state.inventory["reality_anchor_1977"] == 1

    # New controller loaded with completed campaign flag
    controller2 = FlashbackController(campaign=campaign)
    assert controller2.stage == FlashbackStage.COMPLETED
    controller2.lock_reality_anchor(campaign)
    assert campaign.state.inventory["reality_anchor_1977"] == 1


def test_explicit_return_rules_health_and_equipment():
    """Verify player equipment and health follow explicit return preservation rules."""
    campaign = Campaign(save_id="test_save_return")
    player = Player(48.0, 208.0)
    player.health = 75

    # Capture snapshot
    snap = FlashbackSnapshot.capture(
        player,
        campaign,
        origin_room="act_01_approach",
        origin_spawn="approach_start",
    )
    assert snap.saved_health == 75
    assert snap.origin_room == "act_01_approach"

    # Simulate entering flashback: player health changes or takes damage
    player.health = 10
    setattr(player, "is_flashback", True)

    # Apply return
    snap.apply_return(player, campaign)

    # Health restored: min 50 HP baseline safety rule applied
    assert player.health == 75
    assert getattr(player, "is_flashback") is False

    # Low health edge case: saved health was 25
    snap_low = FlashbackSnapshot(saved_health=25)
    snap_low.apply_return(player, campaign)
    # Must enforce minimum 50 HP baseline safety threshold
    assert player.health == 50


def test_field_ops_flashback_integration_and_transitions():
    """Verify FieldOpsScene transitions into flashback, disables combat, and exits cleanly."""
    mock_machine = MockMachine()
    scene = FieldOpsScene(mock_machine, room_relative_path="flashback/ehman_1977.json")

    assert scene.flashback is not None
    assert scene.player.is_flashback is True
    assert len(scene.enemy_manager.enemies) == 0

    # Weapon discharge is suppressed
    p_input = PlayerInput()
    p_input.fire_pressed = True
    p_input.fire_held = True
    scene.player.update(0.016, p_input, scene.room, projectile_manager=scene.projectile_manager)
    assert len(scene.projectile_manager.projectiles) == 0

    # Test normal input progression via events
    # 1. Approach printer desk
    scene.player.x = 112.0
    ev_inspect = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e})
    scene.handle_event(ev_inspect)
    assert scene.flashback.stage == FlashbackStage.PRINTOUT_INSPECTED

    # 2. Annotate
    scene.handle_event(ev_inspect)
    assert scene.flashback.stage == FlashbackStage.ANNOTATION_APPLIED

    # 3. Move to vault
    scene.player.x = 380.0
    scene.handle_event(ev_inspect)
    assert scene.flashback.stage == FlashbackStage.REEL_RETRIEVED

    # 4. Lock anchor & auto-return
    scene.handle_event(ev_inspect)
    assert scene.flashback is None or scene.flashback.stage == FlashbackStage.COMPLETED
    assert mock_machine.last_state_change is not None


def test_flashback_checkpoint_reload_and_interruption():
    """Verify player can respawn at flashback checkpoints without collision faults."""
    room = Room.load_from_file(LEVELS_DIR / "flashback" / "ehman_1977.json")
    player = Player(48.0, 208.0)

    # Set checkpoint
    player.active_checkpoint_id = "ehman_desk"
    player.respawn_at_checkpoint(room)
    assert player.x == 112.0
    assert player.y == 208.0

    # Verify footing
    rect = pygame.Rect(int(player.x), int(player.y), 16, 32)
    assert not room.check_rect_collision(rect)["solid"]


def test_flashback_save_and_reload_persistence():
    """Verify FlashbackController state, dialogue log, and snapshot survive serialization."""
    campaign = Campaign(save_id="test_save_persistence")
    snap = FlashbackSnapshot(
        origin_room="bunker_hub",
        origin_spawn="bunker_start",
        saved_health=90,
        saved_inventory={"maser_1420": 1},
    )
    controller = FlashbackController(campaign=campaign, snapshot=snap)
    controller.inspect_printout()
    controller.apply_red_annotation()

    serialized = controller.to_dict()
    restored = FlashbackController.from_dict(serialized, campaign=campaign)

    assert restored.stage == FlashbackStage.ANNOTATION_APPLIED
    assert restored.is_printout_open is True
    assert len(restored.dialogue_log) == 2
    assert restored.snapshot is not None
    assert restored.snapshot.saved_health == 90
    assert restored.snapshot.origin_room == "bunker_hub"
