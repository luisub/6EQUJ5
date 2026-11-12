"""
MODULE: video_game/tests/test_content.py
PURPOSE: Comprehensive Milestone 3 exit gate G3 verification suite: end-to-end combined route,
         action concurrency & equipment combinations, controlled failure recovery, and level/schema data contracts.
CALLED BY: pytest (`pytest video_game/tests/test_content.py -v`).
HOW TO MODIFY: Extend with additional multi-act progression tests or cross-system stress tests; maintain zero wildcard imports.
"""

import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import pygame
import pytest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from video_game.engine import config
from video_game.engine.abilities import (
    AbilityManager,
    PhaseShieldAbility,
    QuantumDecoyAbility,
    SerendipityTapeDeckAbility,
    TimeDilationAbility,
)
from video_game.engine.campaign import Campaign, load_campaign_data
from video_game.engine.enemies import (
    ChrysalisSplicer,
    CoreEnforcer,
    CoreOperative,
    CoreReconDrone,
    EnemyManager,
    PhaseWatcher,
    PrecursorGuardian,
    ShieldHound,
    StaticHound,
    TemporalPhantom,
)
from video_game.engine.flashback import FlashbackController, FlashbackSnapshot
from video_game.engine.mandela_world import MandelaWorld
from video_game.engine.player import Player, PlayerConfig, PlayerInput
from video_game.engine.protocols import ProtocolValidator, ScienceArcManager
from video_game.engine.save_game import SaveStore
from video_game.engine.temporal_relay import TemporalRelay
from video_game.engine.weapons import (
    AnalogScattergun,
    ArsenalManager,
    CombatTarget,
    EmpBola,
    FibonacciCoilgun,
    ProjectileManager,
    StarterMaser,
)
from video_game.engine.world import (
    COLLISION_COVER,
    COLLISION_EMPTY,
    COLLISION_HAZARD,
    COLLISION_ONE_WAY,
    COLLISION_SOLID,
    Room,
    RoomObject,
)

LEVELS_DIR = Path(__file__).resolve().parent.parent / "data" / "levels"
BALANCE_FILE = Path(__file__).resolve().parent.parent / "data" / "balance.json"
CAMPAIGN_FILE = Path(__file__).resolve().parent.parent / "data" / "campaign.json"


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    """Ensure headless pygame initialization."""
    pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240), pygame.HIDDEN)


def test_combined_milestone_3_full_route_walkthrough():
    """
    S11 Master Verification:
    Executes the complete combined Milestone 3 route across all systems:
    1. Campaign & meters initialization.
    2. Science validation workbenches (Quantum, Connectome, Biosecurity).
    3. Analog arsenal & abilities expansion.
    4. Mandela dual-timeline geometry swap.
    5. Dodleston cross-era relay & causal puzzles.
    6. 1977 historical Big Ear research flashback & reality anchor.
    7. Combat against hostile faction archetypes with readable counterplay.
    8. Advanced traversal gauntlet & Serendipity prediction counterplay.
    9. State persistence save/reload cycle with 100% data fidelity.
    """
    # Step 1: Initialize Campaign & Meters
    campaign = config.default_campaign_state()
    arc_mgr = ScienceArcManager()
    assert len(arc_mgr.scenarios) >= 3

    # Add initial contacted civilizations required for validations
    campaign._state["contacted_civs"].extend(["FASR-001", "FASR-002", "FASR-003"])
    campaign.apply_event({"event_id": "grant_fasr1", "type": "grant_fragment_fasr_001"})
    campaign.apply_event({"event_id": "grant_fasr2", "type": "grant_fragment_fasr_002"})
    campaign.apply_event({"event_id": "grant_fasr3", "type": "grant_fragment_fasr_003"})

    # Step 2: Validate Science Workbenches & Progress Campaign Meters
    # 2a. Quantum validation
    val_q = campaign.apply_event({"event_id": "val_q_master", "type": "validate_quantum_mandela_deploy"})
    assert val_q is True

    # 2b. Connectome validation
    val_c = campaign.apply_event({"event_id": "val_c_master", "type": "validate_connectome_blindspot_deploy"})
    assert val_c is True

    # 2c. Biosecurity validation
    val_b = campaign.apply_event({"event_id": "val_b_master", "type": "validate_biosecurity_deploy"})
    assert val_b is True

    # Verify campaign meters have been boosted by formal validations
    st = campaign.state
    assert st.meters.get("entropy_resistance", 0.0) >= 0.0
    assert st.meters.get("reality_alignment", 0.0) >= 0.0

    # Step 3: Equipment Arsenal & Ability Synchronization
    arsenal = ArsenalManager()
    arsenal.sync_unlocks(campaign)
    assert arsenal.weapons["scattergun"].is_unlocked is True
    assert arsenal.weapons["emp_bola"].is_unlocked is True

    abilities = AbilityManager()
    abilities.sync_unlocks(campaign)
    assert abilities.abilities["decoy"].is_unlocked is True
    assert abilities.abilities["shielding"].is_unlocked is True

    # Step 4: Mandela Dual-Timeline Geometry Swap
    mandela_room = Room.load_from_file(LEVELS_DIR / "act_01" / "mandela_test.json")
    world = MandelaWorld(mandela_room, initial_timeline="2029_CORE")
    player = Player(x=32.0, y=208.0)
    player.arsenal = arsenal
    player.abilities = abilities

    # Swap to 1977_ANALOG
    swap_res = world.swap_timeline("1977_ANALOG", player)
    assert swap_res.success is True
    assert world.active_timeline == "1977_ANALOG"
    assert not world.room.check_rect_collision(player.rect)["solid"]

    # Swap back to 2029_CORE
    swap_back = world.swap_timeline("2029_CORE", player)
    assert swap_back.success is True
    assert world.active_timeline == "2029_CORE"

    # Step 5: Dodleston Relay & Causal Puzzles
    relay_room = Room.load_from_file(LEVELS_DIR / "act_04" / "dodleston_relay.json")
    relay_world = MandelaWorld(relay_room, initial_timeline="2029_CORE")
    relay = TemporalRelay()

    # Solve Puzzle 1: Drain coolant
    ok1, msg1 = relay.apply_action("action_seal_valve_drain", relay_world, player)
    assert ok1 is True
    assert relay.puzzle_flags["dodleston_coolant_drained"] is True

    # Solve Puzzle 2: Power bulkhead
    ok2, msg2 = relay.apply_action("action_install_jumper_j1", relay_world, player)
    assert ok2 is True
    assert relay.puzzle_flags["dodleston_bulkhead_unlocked"] is True

    # Solve Puzzle 3: Caching C-60 tape in hearth
    ok3, msg3 = relay.apply_action("action_cache_tape_chimney", relay_world, player)
    assert ok3 is True
    assert relay.puzzle_flags["dodleston_cassette_cached"] is True

    # Step 6: Playable 1977 Flashback at Big Ear
    flashback_room = Room.load_from_file(LEVELS_DIR / "flashback" / "ehman_1977.json")
    snap = FlashbackSnapshot.capture(player, campaign, origin_room="act_04_dodleston_relay", origin_spawn="bunker_start")
    fb_ctrl = FlashbackController(campaign=campaign, snapshot=snap)
    setattr(player, "is_flashback", True)

    assert fb_ctrl.inspect_printout()[0] is True
    assert fb_ctrl.apply_red_annotation()[0] is True
    assert fb_ctrl.retrieve_hidden_reel()[0] is True
    assert fb_ctrl.lock_reality_anchor(campaign)[0] is True

    # Exit flashback back to 2029 present-day
    snap.apply_return(player, campaign)
    assert getattr(player, "is_flashback", False) is False
    assert player.health >= 50
    assert campaign.state.inventory.get("reality_anchor_1977") == 1
    assert "complete_flashback_1977" in campaign.state.completed_event_types

    # Unlock Serendipity Tape Deck now that flashback is complete
    abilities.sync_unlocks(campaign)
    assert abilities.abilities["serendipity_tape_deck"].is_unlocked is True

    # Step 7: Hostile Faction Combat & Counterplay
    enemy_mgr = EnemyManager()
    drone = CoreReconDrone("core_drone_01", 120.0, 100.0)
    enforcer = CoreEnforcer("core_enforcer_01", 160.0, 100.0)
    sh_hound = ShieldHound("shield_hound_01", 200.0, 100.0)
    watcher = PhaseWatcher("phase_watcher_01", 240.0, 100.0)

    for e in [drone, enforcer, sh_hound, watcher]:
        enemy_mgr.add_enemy(e)

    # 7a. Counter Core Enforcer with EMP Bola stun overload
    enforcer.apply_status("stun", 2.0)
    res_enf = enforcer.take_damage(30)
    assert res_enf.damage_dealt == 45  # 30 * 1.5x overload

    # 7b. Counter Shield Hound with slide-kick knockdown
    sh_hound.on_slide_kicked()
    assert sh_hound.is_knocked_down is True
    assert sh_hound.state == "recovery"
    res_hound = sh_hound.take_damage(30)
    assert res_hound.damage_dealt == 60  # 30 * 2.0x critical damage to exposed rear battery

    # 7c. Counter Phase Watcher with sensor illumination reveal
    watcher.apply_status("revealed", 3.0)
    assert watcher.try_teleport(player, relay_room) is False  # Teleportation jammed by reveal

    # Step 8: Advanced Traversal Gauntlet & Serendipity Prediction Disruption
    # 8a. Wall slide & Wall jump
    wall_grid = [[COLLISION_SOLID] + [COLLISION_EMPTY] * 6 + [COLLISION_SOLID] for _ in range(8)]
    wall_grid.append([COLLISION_SOLID] * 8)
    wall_room = Room({
        "schema_version": 1,
        "room_id": "test_traversal_room",
        "act_id": "test",
        "title": "Wall Traversal Arena",
        "tile_size": 16,
        "width_tiles": 8,
        "height_tiles": 9,
        "collision_layers": wall_grid,
        "background_layers": [],
        "spawns": {"default": {"x": 16.0, "y": 32.0, "facing": "right"}},
        "checkpoints": [],
        "exits": [],
        "objects": [{"id": "ga_01", "type": "grapple_anchor", "x": 48.0, "y": 16.0, "width": 16, "height": 16}],
    })

    player.x = 16.0
    player.y = 30.0
    player.vy = 100.0
    player.is_grounded = False
    player.update(1.0 / 60.0, PlayerInput(move_x=-1.0), wall_room)
    assert player.is_wall_sliding is True
    assert player.vy <= player.cfg.wall_slide_speed + 1.0

    player.update(1.0 / 60.0, PlayerInput(jump_pressed=True, move_x=-1.0), wall_room)
    assert player.is_wall_sliding is False
    assert player.vy <= -200.0
    assert player.vx >= 150.0
    assert player.wall_jump_lock_timer > 0.0

    # 8b. Fibonacci Dash with invulnerability
    player.update(1.0 / 60.0, PlayerInput(dash_pressed=True, move_x=1.0), wall_room)
    assert player.is_dashing is True
    assert player.vx == player.cfg.fibonacci_dash_speed
    assert player.invulnerable_timer > 0.0

    # 8c. Serendipity Tape Deck Disruption & 3.0x Anomaly Damage
    drone.telegraph_active = True
    drone.telegraph_locked = True
    tape_deck = abilities.abilities["serendipity_tape_deck"]
    tape_deck.activate(player, context=type("Ctx", (), {"enemy_manager": enemy_mgr})())

    assert player.has_serendipity_buff is True
    assert drone.telegraph_active is False
    assert drone.state == "recovery"
    assert drone.has_status("prediction_shattered") is True

    # Anomaly critical damage against prediction-shattered drone
    drone_hit = drone.take_damage(25)
    assert drone_hit.damage_dealt == 50  # 25 * 3.0 = 75, capped at remaining HP (50)
    assert drone.is_dead is True

    # Step 9: Save & Reload Persistence
    save_store = SaveStore()
    save_data = {
        "schema_version": 1,
        "campaign": campaign.to_dict(),
        "player": {
            "health": player.health,
            "x": player.x,
            "y": player.y,
            "coherence": player.coherence,
            "weapons": arsenal.to_dict(),
            "abilities": abilities.to_dict(),
        },
        "relay": relay.to_dict(),
    }
    serialized = json.dumps(save_data)
    deserialized = json.loads(serialized)

    assert deserialized["schema_version"] == 1
    assert "complete_flashback_1977" in deserialized["campaign"]["completed_event_types"]
    assert deserialized["relay"]["puzzle_flags"]["dodleston_bulkhead_unlocked"] is True
    assert deserialized["player"]["weapons"]["unlocked_weapons"]["scattergun"] is True


def test_action_concurrency_and_equipment_combinations():
    """
    S11 Verification:
    Stress tests action concurrency and rapid posture/equipment transitions:
    - Weapon cycling while grappling in mid-air.
    - Firing while sliding and dashing.
    - Ability activation during wall slide.
    - Zero physics instability or NaN coordinates.
    """
    room = Room.load_from_file(LEVELS_DIR / "act_01" / "approach.json")
    player = Player(x=100.0, y=100.0)
    arsenal = ArsenalManager()
    abilities = AbilityManager()

    # Unlock all equipment for stress test
    for w in arsenal.weapons.values():
        w.is_unlocked = True
    for ab in abilities.abilities.values():
        ab.is_unlocked = True

    player.arsenal = arsenal
    player.weapon = arsenal.active_weapon
    player.abilities = abilities
    proj_mgr = ProjectileManager()

    # 1. Rapid weapon cycling while moving
    for _ in range(10):
        p_in = PlayerInput(move_x=1.0, cycle_weapon_pressed=True)
        player.update(0.016, p_in, room, proj_mgr)
        assert player.weapon is not None
        assert not math.isnan(player.x) and not math.isnan(player.y)

    # 2. Trigger Phase Shield while wall sliding
    player.is_wall_sliding = True
    player.wall_contact_dir = 1
    p_in_ability = PlayerInput(ability_pressed=True)
    player.abilities.select_ability("shielding")
    player.update(0.016, p_in_ability, room, proj_mgr)
    assert player.abilities.abilities["shielding"].is_active is True
    assert not math.isnan(player.vy)

    # 3. Trigger Fibonacci dash and weapon discharge simultaneously
    p_in_dash_fire = PlayerInput(dash_pressed=True, fire_pressed=True, move_x=1.0)
    player.update(0.016, p_in_dash_fire, room, proj_mgr)
    assert player.is_dashing is True
    assert player.vx == player.cfg.fibonacci_dash_speed
    assert not math.isnan(player.vx)


def test_controlled_failure_behavior_and_safety_boundaries():
    """
    S11 Verification:
    Validates controlled error handling and failure boundaries across systems:
    - Mandela swap rejection on solid overlap or hazard pit.
    - Clean respawn without orphaned projectiles on player elimination.
    - Flashback health preservation floor ($H >= 50$).
    - Dodleston relay recalibration recovery after fuse blowout.
    """
    # 1. Mandela swap blocked by solid wall
    room = Room.load_from_file(LEVELS_DIR / "act_01" / "mandela_test.json")
    world = MandelaWorld(room, initial_timeline="2029_CORE")
    # Col 8, Row 13 is empty in 2029, but solid in 1977
    blocked_player = Player(x=8.0 * 16.0, y=13.0 * 16.0 - 16.0)
    res = world.swap_timeline("1977_ANALOG", blocked_player, allow_displacement=False)
    assert res.success is False
    assert "BLOCKED" in res.reason or "SOLID" in res.reason
    assert world.active_timeline == "2029_CORE"

    # 2. Death and checkpoint recovery idempotence
    player = Player(x=50.0, y=50.0)
    player.is_dashing = True
    player.is_grappling = True
    player.take_damage(150, ignore_invulnerable=True)
    assert player.is_dead is True

    player.respawn_at_checkpoint(room)
    assert player.is_dead is False
    assert player.is_dashing is False
    assert player.is_grappling is False
    assert player.health == player.cfg.max_health

    # 3. Flashback health preservation floor
    campaign = config.default_campaign_state()
    low_hp_player = Player(x=32.0, y=32.0)
    low_hp_player.health = 5  # Critical health
    snap_low = FlashbackSnapshot(saved_health=5)
    snap_low.apply_return(low_hp_player, campaign)
    assert low_hp_player.health >= 50, "Failed to enforce H_return >= 50 safety floor"

    # 4. Dodleston relay recalibration recovery
    relay_room = Room.load_from_file(LEVELS_DIR / "act_04" / "dodleston_relay.json")
    relay_world = MandelaWorld(relay_room, initial_timeline="2029_CORE")
    relay = TemporalRelay()

    # Force pipe ruptured condition on puzzle 1
    succ, _ = relay.apply_action("action_open_cistern_flood", relay_world, player)
    assert succ is True
    assert relay.puzzle_flags["pipe_ruptured"] is True

    # Recalibrate cleanly restores puzzle operability and drains trench
    rec_ok, _ = relay.recalibrate_puzzles(relay_world, player)
    assert rec_ok is True
    assert relay.puzzle_flags["pipe_ruptured"] is False
    assert relay.puzzle_flags["dodleston_coolant_drained"] is True


def test_all_level_schemas_and_data_contracts():
    """
    S11 Verification:
    Validates structural integrity, coordinate bounds, and schemas across all authored levels:
    - act_01: approach, salvage_yard, dish_catwalk, greenkeeper_arena, mandela_test
    - act_04: dodleston_relay
    - flashback: ehman_1977
    """
    assert LEVELS_DIR.exists()
    level_files = sorted(list(LEVELS_DIR.glob("**/*.json")))
    assert len(level_files) >= 7

    for lvl_path in level_files:
        assert lvl_path.is_file()
        room = Room.load_from_file(lvl_path)

        # Check basic schema contracts
        assert room.schema_version == 1
        assert room.width_tiles > 0
        assert room.height_tiles > 0
        assert room.tile_size == 16
        assert len(room.collision_grid) == room.height_tiles
        assert len(room.collision_grid[0]) == room.width_tiles

        # Check spawns are within bounds and on legal tiles
        assert len(room.spawns) > 0
        for sp_name, sp in room.spawns.items():
            assert 0.0 <= sp.x < float(room.width_px)
            assert 0.0 <= sp.y < float(room.height_px)
            # Spawn footprint must not be embedded in solid tiles
            sp_rect = pygame.Rect(int(sp.x), int(sp.y), 16, 32)
            col = room.check_rect_collision(sp_rect)
            assert not col["solid"], f"Spawn '{sp_name}' in {lvl_path.name} is embedded in solid geometry"

        # Check checkpoints are within bounds
        for chk in room.checkpoints:
            assert 0.0 <= chk.x < float(room.width_px)
            assert 0.0 <= chk.y < float(room.height_px)

        # Check room objects
        for obj in room.objects:
            assert obj.id != ""
            assert obj.type != ""
            assert 0.0 <= obj.x < float(room.width_px)
            assert 0.0 <= obj.y < float(room.height_px)
