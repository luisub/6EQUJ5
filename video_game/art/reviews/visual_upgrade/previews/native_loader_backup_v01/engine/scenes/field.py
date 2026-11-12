"""
MODULE: video_game/engine/scenes/field.py
PURPOSE: Playable side-scrolling Field Operations scene for 2D platforming, combat traversal, and room navigation.
CALLED BY: video_game.engine.state_machine, video_game.engine.scenes.bunker.
HOW TO MODIFY: Integrate player physics, animation states, combat projectiles, and camera triggers.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pygame

from video_game.engine import config
from video_game.engine.abilities import AbilityManager
from video_game.engine.animation import AnimationPlayer, load_mateo_animations
from video_game.engine.effects import EffectManager
from video_game.engine.enemies import CoreReconDrone, EnemyManager, StaticHound
from video_game.engine.flashback import FlashbackController, FlashbackSnapshot, FlashbackStage
from video_game.engine.field_reality import FieldReality
from video_game.engine.objectives import DishDefenseHoldout, ObjectiveTracker
from video_game.engine.player import Player, PlayerConfig, PlayerInput
from video_game.engine.scenes.base import BaseScene
from video_game.engine.ui.text import wrap_text_pixels
from video_game.engine.weapons import ArsenalManager, ProjectileManager, StarterMaser
from video_game.engine.world import (
    Camera,
    COLLISION_COVER,
    COLLISION_EMPTY,
    COLLISION_HAZARD,
    COLLISION_ONE_WAY,
    COLLISION_SOLID,
    preload_env_assets,
    Room,
    RoomCheckpoint,
    RoomExit,
)

LEVELS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "levels"


class FieldOpsScene(BaseScene):
    """
    Playable 2D Field Operations scene.

    Renders multi-layer parallax backgrounds, tile-grid terrain, obstacles,
    cover blocks, checkpoints, exit triggers, and tracks the player with
    a bounded smooth-tracking camera.
    """

    def __init__(self, machine: Any, room_relative_path: str = "act_01/approach.json"):
        super().__init__(machine)
        self.room_path = LEVELS_DIR / room_relative_path
        self.room = Room.load_from_file(self.room_path)
        self.camera = Camera(config.INTERNAL_WIDTH, config.INTERNAL_HEIGHT)
        self.camera.set_world_bounds(self.room.width_px, self.room.height_px)
        preload_env_assets()

        # Kinematic player entity
        self.player = Player(48.0, 192.0)
        self.prompt_text: str = ""

        # Wire animation player
        try:
            clips = load_mateo_animations(self.machine.assets.root, outfit="olive_field")
            self.player.animator = AnimationPlayer(
                clips=clips,
                default_state="idle",
                scale_factor=0.25,
                facing=self.player.facing,
            )
        except Exception:
            self.player.animator = None

        # Input tracking
        self.keys_held: Dict[int, bool] = {}
        self._jump_pressed: bool = False
        self._jump_released: bool = False
        self._fire_pressed: bool = False
        self._fire_released: bool = False

        # Projectiles, arsenal, abilities and combat
        self.projectile_manager: ProjectileManager = ProjectileManager()
        self.player.arsenal = ArsenalManager()
        self.player.abilities = AbilityManager()
        self.player.weapon = self.player.arsenal.active_weapon
        self.effects: EffectManager = EffectManager()
        self._prev_is_grounded: bool = False
        self._prev_is_sliding: bool = False
        self._prev_hp: int = self.player.health
        self._prev_alarm_locked: bool = False
        self._prev_telegraph: bool = False

        # Enemies and encounter manager
        self.enemy_manager: EnemyManager = EnemyManager()
        self._setup_encounter()

        # Mission objectives and collectible parts
        self.objective_tracker: ObjectiveTracker = ObjectiveTracker()
        self.coupler_x: float = 0.0
        self.coupler_y: float = 0.0
        self.coupler_size = (16, 16)
        self.holdout: Optional[DishDefenseHoldout] = None
        self._defense_respawns = self.player.respawn_count
        self._defense_pressure_delay = 0.0
        self.flashback: Optional[FlashbackController] = None
        self.reality = FieldReality(self)
        self._faction_encounter = 0
        self.player.combat_context = self

        # Place player at default spawn
        self.reset_to_spawn("bunker_exit")

        # Initialize flashback state if starting directly in 1977 observatory room
        if self.room.room_id == "flashback_ehman_1977" or "ehman_1977" in self.room_path.name:
            snap = FlashbackSnapshot.capture(
                self.player,
                self.machine.campaign if hasattr(self.machine, "campaign") else None,
                origin_room="bunker_hub",
                origin_spawn="bunker_start",
            )
            self.flashback = FlashbackController(
                campaign=self.machine.campaign if hasattr(self.machine, "campaign") else None,
                snapshot=snap,
            )
            self.player.is_flashback = True
            self.enemy_manager.clear()
            self.projectile_manager.clear()

    def _setup_encounter(self):
        """Populate the approach or salvage encounter with room-specific positions."""
        self.enemy_manager.clear()
        drone = CoreReconDrone("drone_trench_01", x=440.0, y=120.0, patrol_left=380.0, patrol_right=500.0)
        # The salvage yard is only 640 pixels wide; use an in-bounds patrol.
        if self.room.room_id == "act_01_salvage_yard":
            hound = StaticHound("hound_yard_01", x=560.0, y=192.0, patrol_left=480.0, patrol_right=600.0)
        else:
            hound = StaticHound("hound_trench_01", x=660.0, y=192.0, patrol_left=580.0, patrol_right=760.0)
        self.enemy_manager.add_enemy(drone)
        self.enemy_manager.add_enemy(hound)

    # Compatibility properties mapping to Player
    @property
    def player_x(self) -> float:
        return self.player.x

    @player_x.setter
    def player_x(self, val: float):
        self.player.x = float(val)

    @property
    def player_y(self) -> float:
        return self.player.y

    @player_y.setter
    def player_y(self, val: float):
        self.player.y = float(val)

    @property
    def vx(self) -> float:
        return self.player.vx

    @vx.setter
    def vx(self, val: float):
        self.player.vx = float(val)

    @property
    def vy(self) -> float:
        return self.player.vy

    @vy.setter
    def vy(self, val: float):
        self.player.vy = float(val)

    @property
    def facing(self) -> str:
        return self.player.facing

    @facing.setter
    def facing(self, val: str):
        self.player.facing = val

    @property
    def is_grounded(self) -> bool:
        return self.player.is_grounded

    @is_grounded.setter
    def is_grounded(self, val: bool):
        self.player.is_grounded = val

    @property
    def is_crouching(self) -> bool:
        return self.player.is_crouching

    @is_crouching.setter
    def is_crouching(self, val: bool):
        self.player.is_crouching = val

    @property
    def active_checkpoint_id(self) -> Optional[str]:
        return self.player.active_checkpoint_id

    @active_checkpoint_id.setter
    def active_checkpoint_id(self, val: Optional[str]):
        self.player.active_checkpoint_id = val

    @property
    def player_rect(self) -> pygame.Rect:
        """Player world-space bounding box."""
        return self.player.rect

    def reset_to_spawn(self, spawn_name: str = "bunker_exit"):
        """Place player at designated spawn point and center camera."""
        self.player.cancel_traversal()
        sp = self.room.spawns.get(spawn_name)
        if sp:
            self.player.x = sp.x
            self.player.y = sp.y
            self.player.facing = sp.facing
            self.player.spawn_x = sp.x
            self.player.spawn_y = sp.y
        else:
            self.player.x = 48.0
            self.player.y = 192.0
            self.player.facing = "right"
            self.player.spawn_x = 48.0
            self.player.spawn_y = 192.0

        self.player.vx = 0.0
        self.player.vy = 0.0
        self.player.is_grounded = False
        self.player.is_crouching = False
        if hasattr(self, "projectile_manager"):
            self.projectile_manager.clear()
        if hasattr(self, "enemy_manager"):
            self.enemy_manager.reset_all()
        self.camera.snap_to(self.player.x + 8.0, self.player.y + 16.0)

    def load_room(self, room_relative_path: str, spawn_name: Optional[str] = None, **kwargs):
        """Switch active 2D tile-grid room within field operations."""
        self.reality.persist()
        self.keys_held.clear()
        self.machine.input.release_all()
        self._jump_pressed = self._jump_released = False
        self._fire_pressed = self._fire_released = False
        self.room_path = LEVELS_DIR / room_relative_path
        self.room = Room.load_from_file(self.room_path)
        if self.room.room_id == "act_01_salvage_yard":
            depot = next(obj for obj in self.room.objects if obj.id == "analog_coupler_depot")
            self.coupler_x = depot.x + depot.width / 2
            self.coupler_y = depot.y + depot.height / 2
            self.coupler_size = (int(depot.width), int(depot.height))
        self.player.active_checkpoint_id = None
        self.camera.set_world_bounds(self.room.width_px, self.room.height_px)
        if spawn_name and spawn_name in self.room.spawns:
            self.reset_to_spawn(spawn_name)
        elif "default" in self.room.spawns:
            self.reset_to_spawn("default")
        elif self.room.spawns:
            first_sp = next(iter(self.room.spawns.keys()))
            self.reset_to_spawn(first_sp)

        is_flashback = (self.room.room_id == "flashback_ehman_1977" or "ehman_1977" in self.room_path.name)
        if is_flashback:
            origin_room = kwargs.get("origin_room", "bunker_hub")
            origin_spawn = kwargs.get("origin_spawn", "bunker_start")
            snap = FlashbackSnapshot.capture(
                self.player,
                self.machine.campaign if hasattr(self.machine, "campaign") else None,
                origin_room=origin_room,
                origin_spawn=origin_spawn,
            )
            self.flashback = FlashbackController(
                campaign=self.machine.campaign if hasattr(self.machine, "campaign") else None,
                snapshot=snap,
            )
            self.player.is_flashback = True
            if hasattr(self, "enemy_manager"):
                self.enemy_manager.clear()
            if hasattr(self, "projectile_manager"):
                self.projectile_manager.clear()
        else:
            if self.flashback is not None:
                self.player.is_flashback = False
                self.flashback = None

        self._configure_room_encounter()
        self.reality.load()

    def exit_flashback(self):
        """Safely exit 1977 flashback and return to present-day origin room."""
        if self.flashback and self.flashback.snapshot:
            snap = self.flashback.snapshot
            campaign = self.machine.campaign if hasattr(self.machine, "campaign") else None
            snap.apply_return(self.player, campaign)
            self.player.is_flashback = False
            target_room = snap.origin_room
            target_spawn = snap.origin_spawn
            self.flashback = None
            if target_room == "bunker_hub":
                self.machine.change_state(config.STATE_BUNKER_HUB)
            elif target_room.startswith("act_01_"):
                slug = target_room.replace("act_01_", "")
                self.load_room(f"act_01/{slug}.json", spawn_name=target_spawn)
            elif target_room.startswith("act_04_"):
                slug = target_room.replace("act_04_", "")
                self.load_room(f"act_04/{slug}.json", spawn_name=target_spawn)
            else:
                self.machine.change_state(config.STATE_BUNKER_HUB)
        else:
            self.player.is_flashback = False
            self.flashback = None
            self.machine.change_state(config.STATE_BUNKER_HUB)

    def _configure_room_encounter(self):
        """Start a fresh defense on the catwalk, or restore normal room enemies."""
        self.holdout = None
        if self.flashback is not None or "ehman_1977" in self.room_path.name:
            if hasattr(self, "enemy_manager"):
                self.enemy_manager.clear()
        elif self.room_path.name == "dish_catwalk.json":
            self.enemy_manager.clear()
            flags = self.machine.campaign.state.room_flags
            if flags.get("feedhorn_repaired", False) and not flags.get("dish_defense_completed", False):
                self.holdout = DishDefenseHoldout()
                self._start_defense()
        elif self.room_path.name in ("mandela_test.json", "dodleston_relay.json"):
            self.enemy_manager.clear()
        else:
            self._setup_encounter()

    def _start_defense(self):
        self.enemy_manager.clear()
        self.projectile_manager.clear()
        self.holdout.start()
        self._defense_respawns = self.player.respawn_count
        self._defense_pressure_delay = 8.0
        self.objective_tracker.post_notification(
            "DEFEND THE ARRAY", "72s // CLEAR JAMS AT FEEDHORN WITH E", "warning", 5.0)

    def _spawn_defense_wave(self, wave):
        """Spawn the scheduled enemies at the edges of the catwalk."""
        wave_id = wave["wave_id"]
        for i in range(wave["drone_count"]):
            x = 440.0 + i * 50.0
            self.enemy_manager.add_enemy(CoreReconDrone(
                f"{wave_id}_drone_{i}", x=x, y=155.0,
                patrol_left=max(24.0, x - 48.0), patrol_right=min(self.room.width_px - 32.0, x + 48.0)))
        for i in range(wave["hound_count"]):
            x = 500.0 + i * 40.0
            self.enemy_manager.add_enemy(StaticHound(
                f"{wave_id}_hound_{i}", x=x, y=208.0,
                patrol_left=max(24.0, x - 80.0), patrol_right=min(self.room.width_px - 32.0, x + 40.0)))
        self._defense_pressure_delay = 8.0
        self.objective_tracker.post_notification("INCOMING WAVE", wave["name"], "warning", 3.0)

    def _update_defense(self, dt: float, is_paused: bool):
        defense = self.holdout
        if defense is None or not defense.is_active or is_paused:
            return
        if self.player.is_dead or self.player.respawn_count != self._defense_respawns:
            defense.fail("PLAYER CASUALTY")
        else:
            for event in defense.update(dt):
                if event["type"] == "SPAWN_WAVE":
                    self._spawn_defense_wave(event["wave"])
                elif event["type"] == "COMPLETED":
                    if defense.apply_completion_reward(self.machine.campaign):
                        self.machine.save_checkpoint()
                    self.enemy_manager.clear()
                    self.objective_tracker.post_notification(
                        "ARRAY SECURED", "RETURN TO BUNKER FOR GREENKEEPER", "success", 6.0)
            if defense.is_active:
                self._defense_pressure_delay = max(0.0, self._defense_pressure_delay - dt)
                if self._defense_pressure_delay == 0.0:
                    alive = sum(not enemy.is_dead for enemy in self.enemy_manager.enemies)
                    defense.damage_dish(alive * 0.65 * dt)
        if defense.is_failed:
            self.enemy_manager.clear()
            self.projectile_manager.clear()
            self.objective_tracker.post_notification("DEFENSE FAILED", defense.failure_reason + " // R TO RETRY", "warning", 8.0)

    def on_enter(self, previous_state_id: Optional[str] = None, **kwargs):
        """Reset keys, combat state, and snap camera on scene entry."""
        self.keys_held.clear()
        self._jump_pressed = False
        self._jump_released = False
        self._fire_pressed = False
        self._fire_released = False
        if hasattr(self, "projectile_manager"):
            self.projectile_manager.clear()
        if hasattr(self, "enemy_manager"):
            self.enemy_manager.reset_all()
        if hasattr(self, "effects"):
            self.effects.clear()
        if hasattr(self.player, "arsenal") and self.player.arsenal and hasattr(self.machine, "campaign"):
            self.player.arsenal.sync_unlocks(self.machine.campaign)
            self.player.weapon = self.player.arsenal.active_weapon
        if hasattr(self.player, "abilities") and self.player.abilities and hasattr(self.machine, "campaign"):
            self.player.abilities.sync_unlocks(self.machine.campaign)

        if "room" in kwargs:
            self.load_room(kwargs["room"], spawn_name=kwargs.get("spawn"))
        elif previous_state_id == config.STATE_BUNKER_HUB:
            if "bunker_exit" in self.room.spawns:
                self.reset_to_spawn("bunker_exit")
            elif self.room.spawns:
                self.reset_to_spawn(next(iter(self.room.spawns.keys())))
        self._configure_room_encounter()

    def on_exit(self):
        """Purge lingering combat effects and projectiles upon exiting field scene."""
        self.reality.persist()
        self.player.cancel_traversal()
        if hasattr(self, "effects"):
            self.effects.clear()
        if hasattr(self.player, "arsenal") and self.player.arsenal and hasattr(self.machine, "campaign"):
            self.player.arsenal.sync_unlocks(self.machine.campaign)
            self.player.weapon = self.player.arsenal.active_weapon
        if hasattr(self.player, "abilities") and self.player.abilities and hasattr(self.machine, "campaign"):
            self.player.abilities.sync_unlocks(self.machine.campaign)
        if hasattr(self, "projectile_manager"):
            self.projectile_manager.clear()

    def handle_event(self, event: pygame.event.Event):
        """Process movement, jumping, crouching, combat firing, and interaction keys."""
        if getattr(self.machine, "input", None) is not None:
            self.machine.input.handle_event(event)
        if self.reality.handle_event(event):
            return
        if event.type == pygame.KEYDOWN:
            if self.reality.world:
                if event.key == pygame.K_F6:
                    self.load_room("act_04/dodleston_relay.json", "relay_entrance")
                    return
                if event.key == pygame.K_F7:
                    self.load_room("flashback/ehman_1977.json", "ehman_entrance",
                                   origin_room=self.room.room_id, origin_spawn=next(iter(self.room.spawns)))
                    return
                if event.key == pygame.K_F8:
                    self.load_room("act_01/mandela_test.json", "default")
                    return
                if event.key == pygame.K_n:
                    self._load_faction_encounter()
                    return
            self.keys_held[event.key] = True

            # Dedicated 1977 flashback interaction handling
            if self.flashback is not None:
                if event.key == pygame.K_ESCAPE:
                    if self.flashback.is_printout_open:
                        self.flashback.is_printout_open = False
                    else:
                        self.exit_flashback()
                    return

                if event.key in (pygame.K_RETURN, pygame.K_e):
                    px = self.player.x
                    if self.flashback.EXIT_ZONE[0] <= px <= self.flashback.EXIT_ZONE[1]:
                        self.exit_flashback()
                        return
                    elif self.flashback.PRINTER_ZONE[0] <= px <= self.flashback.PRINTER_ZONE[1]:
                        if self.flashback.stage == FlashbackStage.ENTERED:
                            self.flashback.inspect_printout()
                            self.objective_tracker.post_notification("IBM 1130 TELEMETRY", "CHANNEL 2: 6EQUJ5 DETECTED", "warning", 4.0)
                        elif self.flashback.stage == FlashbackStage.PRINTOUT_INSPECTED:
                            self.flashback.apply_red_annotation()
                            self.objective_tracker.post_notification("WOW! ANNOTATION", "CIRCLED IN RED BALLPOINT PEN", "success", 4.0)
                        else:
                            self.flashback.inspect_printout()
                        return
                    elif self.flashback.VAULT_ZONE[0] <= px <= self.flashback.VAULT_ZONE[1]:
                        if self.flashback.stage == FlashbackStage.ANNOTATION_APPLIED:
                            self.flashback.retrieve_hidden_reel()
                            self.objective_tracker.post_notification("ANALOG REEL RETRIEVED", "UNQUANTIZED RF BASEBAND CAPTURED", "success", 4.0)
                        elif self.flashback.stage == FlashbackStage.REEL_RETRIEVED:
                            self.flashback.lock_reality_anchor(self.machine.campaign if hasattr(self.machine, "campaign") else None)
                            self.objective_tracker.post_notification("REALITY ANCHOR LOCKED", "TEMPORAL COLLAPSE // RETURNING TO 2029", "success", 5.0)
                            self.exit_flashback()
                        return
                    elif self.flashback.is_printout_open:
                        self.flashback.is_printout_open = False
                        return

                # Suppress combat firing inside 1977 historical flashback
                if event.key in (pygame.K_x, pygame.K_j, pygame.K_LCTRL):
                    return

            if self.holdout and self.holdout.is_failed and event.key == pygame.K_r:
                # Retry owns R; discard its mapped ability-cycle edge and held controls.
                self.machine.input.release_all()
                self.keys_held.clear()
                self.player.active_checkpoint_id = None
                self.reset_to_spawn("catwalk_start")
                self.player.respawn_at_checkpoint(self.room)
                self._start_defense()
                return
            if (self.holdout and self.holdout.is_active and self.holdout.is_jammed
                    and event.key in (pygame.K_RETURN, pygame.K_e)
                    and abs(self.player.rect.centerx - 320) <= 56):
                self.holdout.unjam()
                self.objective_tracker.post_notification("JAM CLEARED", "FEEDHORN RESTORED", "success", 3.0)
                return

            # Exit to bunker hub
            if event.key == pygame.K_ESCAPE:
                self.machine.change_state(config.STATE_BUNKER_HUB)
                return

            # Interact / Enter exit
            if event.key in (pygame.K_RETURN, pygame.K_e):
                exit_trigger = self.room.check_exit_trigger(self.player.rect)
                if exit_trigger:
                    target_room = exit_trigger.target_room
                    if target_room == "bunker_hub":
                        self.machine.change_state(config.STATE_BUNKER_HUB)
                        return
                    elif target_room == "act_01_greenkeeper_arena":
                        if self.machine.campaign.state.room_flags.get("dish_defense_completed", False):
                            self.machine.change_state(config.STATE_BOSS_BOUNTY)
                            return
                        else:
                            self.objective_tracker.post_notification(
                                title="ARENA SEALED",
                                text="DEFEND DISH FOR 72s BEFORE ENTERING BASIN",
                                kind="warning",
                            )
                            return
                    elif target_room.startswith("act_01_"):
                        target_slug = target_room.replace("act_01_", "")
                        if target_slug == "dish_catwalk" and not self.machine.campaign.state.room_flags.get("feedhorn_repaired", False):
                            self.objective_tracker.post_notification(
                                title="CATWALK LOCKED",
                                text="REPAIR FEEDHORN AT BUNKER WORKBENCH FIRST",
                                kind="warning",
                            )
                            return
                        self.load_room(f"act_01/{target_slug}.json", spawn_name=exit_trigger.target_spawn)
                        return
                    elif target_room == "flashback_ehman_1977" or target_room.startswith("flashback_"):
                        self.load_room("flashback/ehman_1977.json", spawn_name=exit_trigger.target_spawn, origin_room=self.room.room_id)
                        return
                    else:
                        self.machine.change_state(config.STATE_BUNKER_HUB)
                        return

            # Jump trigger
            if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                self._jump_pressed = True

            # Crouch toggle
            if event.key in (pygame.K_c, pygame.K_s, pygame.K_DOWN):
                self.player.is_crouching = True

            # Fire trigger
            if event.key in (pygame.K_x, pygame.K_j, pygame.K_LCTRL):
                self._fire_pressed = True

        elif event.type == pygame.KEYUP:
            self.keys_held[event.key] = False
            if event.key in (pygame.K_c, pygame.K_s, pygame.K_DOWN):
                self.player.is_crouching = False
            if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                self._jump_released = True
            if event.key in (pygame.K_x, pygame.K_j, pygame.K_LCTRL):
                self._fire_released = True

    def update(self, dt_seconds: float):
        """Execute fixed-step kinematic integration, weapon discharge, and collision detection."""
        if self.reality.panel_open:
            return
        # Build action-level input
        p_input = PlayerInput.from_input_manager(self.machine.input)
        if self.keys_held.get(pygame.K_LEFT) or self.keys_held.get(pygame.K_a):
            p_input.move_x = -1.0
        elif self.keys_held.get(pygame.K_RIGHT) or self.keys_held.get(pygame.K_d):
            p_input.move_x = 1.0

        if self.keys_held.get(pygame.K_UP) or self.keys_held.get(pygame.K_w):
            p_input.move_y = -1.0
        elif self.keys_held.get(pygame.K_DOWN) or self.keys_held.get(pygame.K_s):
            p_input.move_y = 1.0

        if self._jump_pressed:
            p_input.jump_pressed = True
            p_input.jump_held = True
            self._jump_pressed = False
        if self._jump_released:
            p_input.jump_released = True
            self._jump_released = False

        if self._fire_pressed:
            p_input.fire_pressed = True
            p_input.fire_held = True
            self._fire_pressed = False
        elif (
            self.keys_held.get(pygame.K_x)
            or self.keys_held.get(pygame.K_j)
            or self.keys_held.get(pygame.K_LCTRL)
        ):
            p_input.fire_held = True

        if self._fire_released:
            p_input.fire_released = True
            self._fire_released = False

        p_input.crouch_held = self.machine.input.held("crouch")

        # Suppress weapon fire inside 1977 flashback
        if self.flashback is not None:
            p_input.fire_pressed = False
            p_input.fire_held = False
            p_input.fire_released = False

        is_paused = getattr(self.machine, "is_paused", False) or getattr(getattr(self.machine, "pause", None), "active", False)

        # Trigger audio and dust on player jump
        if p_input.jump_pressed and (self.player.is_grounded or self.player.coyote_timer > 0.0):
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("player_jump")
            if hasattr(self, "effects"):
                self.effects.add_dust_puff(self.player.x + 8.0, self.player.y + 32.0, count=4)

        prev_proj_len = len(self.projectile_manager.projectiles)

        # Step player simulation and weapon discharge
        previous_player_rect = self.player.rect.copy()
        previous_respawns = self.player.respawn_count
        self.player.update(
            dt_seconds,
            p_input,
            self.room,
            projectile_manager=self.projectile_manager,
            is_paused=is_paused,
        )
        if self.player.respawn_count != previous_respawns:
            # Player.update may have cleared is_dead during automatic respawn.
            self.enemy_manager.reset_all()
            self.projectile_manager.clear()
        self.player.dash_sweep_rect = (previous_player_rect.union(self.player.rect)
                                       if self.player.is_dashing else None)

        # Trigger audio and muzzle flash on weapon discharge
        if len(self.projectile_manager.projectiles) > prev_proj_len:
            new_proj = self.projectile_manager.projectiles[-1]
            sfx_name = "maser_charge" if new_proj.is_charged else "maser_tap"
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx(sfx_name)
            if hasattr(self, "effects"):
                self.effects.add_muzzle_flash(new_proj.x, new_proj.y, direction=self.player.facing, is_charged=new_proj.is_charged)

        # Trigger dust and audio on landing and slide
        if not self._prev_is_grounded and self.player.is_grounded:
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("player_land")
            if hasattr(self, "effects"):
                self.effects.add_dust_puff(self.player.x + 8.0, self.player.y + 32.0, count=5)

        if not self._prev_is_sliding and self.player.is_sliding:
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("player_slide")
            if hasattr(self, "effects"):
                self.effects.add_dust_puff(self.player.x + 8.0, self.player.y + 32.0, count=4)

        self._prev_is_grounded = self.player.is_grounded
        self._prev_is_sliding = self.player.is_sliding

        # Step projectile ray collisions against world and enemies
        targets = self.enemy_manager.enemies if hasattr(self, "enemy_manager") else ()
        hits_recorded = self.projectile_manager.update(
            dt_seconds,
            self.room,
            targets=targets,
            is_paused=is_paused,
        )
        if hits_recorded:
            for hit in hits_recorded:
                if hasattr(self.machine, "audio") and self.machine.audio:
                    self.machine.audio.play_sfx("impact_spark")
                if hasattr(self, "effects"):
                    self.effects.add_impact_sparks(hit.hit_x, hit.hit_y, count=6)

        # Trigger hurt audio and sparks on player health reduction
        if self.player.health < self._prev_hp:
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("player_hurt")
            if hasattr(self, "effects"):
                self.effects.add_impact_sparks(self.player.x + 8.0, self.player.y + 16.0, count=8, is_charged=True)
        self._prev_hp = self.player.health

        # Step enemy logic, predictive targeting, and enemy attacks
        if hasattr(self, "enemy_manager"):
            self.enemy_manager.update(
                dt_seconds,
                self.player,
                self.room,
                camera=self.camera,
                is_paused=is_paused,
            )
            if self.player.is_dead:
                self.enemy_manager.reset_all()

            # Trigger aim lock and telegraph audio cues
            any_locked = any(getattr(e, "aim_locked", False) or getattr(e, "telegraph_locked", False) for e in self.enemy_manager.enemies)
            if any_locked and not self._prev_alarm_locked:
                if hasattr(self.machine, "audio") and self.machine.audio:
                    self.machine.audio.play_sfx("alarm_lock")
            self._prev_alarm_locked = any_locked

            any_telegraph = any(getattr(e, "state", "").lower() == "windup" for e in self.enemy_manager.enemies)
            if any_telegraph and not self._prev_telegraph:
                if hasattr(self.machine, "audio") and self.machine.audio:
                    self.machine.audio.play_sfx("enemy_telegraph")
            self._prev_telegraph = any_telegraph

        self._update_defense(dt_seconds, is_paused)
        if not is_paused:
            self.reality.update(dt_seconds)

        # Update bounded particle effects
        if hasattr(self, "effects"):
            self.effects.update(dt_seconds, room=self.room, is_paused=is_paused)

        # Advance objective tracker
        self.objective_tracker.update(dt_seconds, self.machine.campaign)

        # Collectible analog coupler pickup
        if self.room_path.name == "salvage_yard.json" and not self.machine.campaign.state.room_flags.get("trench_coupler_collected", False):
            coupler_rect = pygame.Rect(0, 0, *self.coupler_size)
            coupler_rect.center = (int(self.coupler_x), int(self.coupler_y))
            if self.player.rect.colliderect(coupler_rect):
                evt = {
                    "event_id": f"collect_coupler_{self.machine.campaign.state.save_id}",
                    "type": "collect_analog_coupler",
                }
                if self.machine.campaign.apply_event(evt):
                    self.objective_tracker.post_notification(
                        title="ITEM RECOVERED",
                        text="ANALOG FEEDHORN COUPLER (RETURN TO BUNKER REPAIR BENCH)",
                        kind="success",
                        duration=4.0,
                    )

        # Update smooth camera tracking
        self.camera.update(self.player.x + 8.0, self.player.y + 16.0, smoothing=0.15)

        # Triggers: Exit & Cover detection
        ex = self.room.check_exit_trigger(self.player.rect)
        cov = self.room.get_cover_at(self.player.rect)
        if self.flashback is not None:
            self.prompt_text = self.flashback.get_prompt(self.player.x)
        elif ex:
            self.prompt_text = ex.label or "[ENTER / ESC] RETURN TO BUNKER"
        elif any(getattr(e, "telegraph_locked", False) for e in getattr(self.enemy_manager, "enemies", [])):
            self.prompt_text = "WARNING: CORE AIM LOCK // DUCK INTO COVER OR DODGE!"
        elif self.player.in_cover:
            self.prompt_text = "CONCEALED IN RECESSED ALCOVE // COVER ACTIVE"
        elif cov and cov.get("cover_type") == "background":
            self.prompt_text = "DOORWAY RECESS // [UP / E] CONCEAL IN COVER"
        elif cov and cov.get("cover_type") == "low":
            self.prompt_text = "FORTIFIED COVER EMPLACEMENT // [CROUCH] TO DUCK"
        elif self.player.is_sliding:
            self.prompt_text = "TACTICAL SLIDE-KICK ACTIVE"
        elif self.player.invulnerable_timer > 0.0 or self.room.check_rect_collision(self.player.rect)["hazard"]:
            self.prompt_text = "WARNING: HIGH VOLTAGE HAZARD DETECTED"
        elif self.player.active_checkpoint_id:
            self.prompt_text = f"CHECKPOINT ACTIVE // {self.player.active_checkpoint_id}"
        else:
            self.prompt_text = ""

    def render(self, crt: Any):
        """Render multi-layer parallax environment, tiles, objects, Mateo, and HUD."""
        crt.clear()
        # 1. Background parallax layers
        if self.reality.world:
            self.reality.world.render(crt.canvas, self.camera)
        else:
            self.room.render_background(crt.canvas, self.camera)

        # 2. Collision tiles (with clean partial bottom tile support)
        if not self.reality.world:
            self.room.render_tiles(crt.canvas, self.camera)

        # 3. Room objects & props
            self.room.render_objects(crt.canvas, self.camera)

        # The annex's low cover is a non-solid protection volume in both timelines.
        for obj in self.room.get_objects_for_timeline():
            if obj.id == "annex_low_cover":
                sx, sy = self.camera.world_to_screen(obj.x, obj.y)
                rect = pygame.Rect(sx, sy, int(obj.width), int(obj.height))
                pygame.draw.rect(crt.canvas, (35, 49, 42), rect)
                pygame.draw.rect(crt.canvas, (154, 171, 105), rect, 1)
                pygame.draw.line(crt.canvas, (154, 171, 105), (rect.left + 3, rect.top + 3),
                                 (rect.right - 4, rect.top + 3), 1)

        # 1977 Flashback ambient tint & line-printer telemetry overlay
        if self.flashback is not None:
            self.flashback.render_overlay(crt.canvas, crt, self.camera)

        # Collectible analog coupler item in approach trench
        if self.room_path.name == "salvage_yard.json" and not self.machine.campaign.state.room_flags.get("trench_coupler_collected", False):
            sc_x, sc_y = self.camera.world_to_screen(self.coupler_x, self.coupler_y)
            if -20 <= sc_x <= config.INTERNAL_WIDTH + 20 and -20 <= sc_y <= config.INTERNAL_HEIGHT + 20:
                # Pulsing golden halo
                ticks = pygame.time.get_ticks()
                halo_r = 7 + int((ticks % 800) / 160)
                pygame.draw.circle(crt.canvas, (50, 42, 10), (int(sc_x), int(sc_y)), halo_r)
                # Outer casing and vacuum tube
                pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, (int(sc_x - 4), int(sc_y - 6), 8, 12))
                pygame.draw.rect(crt.canvas, (255, 240, 160), (int(sc_x - 2), int(sc_y - 4), 4, 8))
                pygame.draw.rect(crt.canvas, config.COLOR_CRT_DIM, (int(sc_x - 4), int(sc_y - 6), 8, 12), 1)

        # 4. Enemies, telegraph lasers, and enemy projectiles
        if hasattr(self, "enemy_manager"):
            self.enemy_manager.render(crt.canvas, self.camera)

        # Show the actual grapple path before drawing the player over its origin.
        if self.player.is_grappling and self.player.grapple_anchor_pos is not None:
            player_screen = self.camera.world_to_screen(
                self.player.x + self.player.width / 2, self.player.y + self.player.height / 2)
            anchor_screen = self.camera.world_to_screen(*self.player.grapple_anchor_pos)
            pygame.draw.line(crt.canvas, config.COLOR_FIBO_GOLD, player_screen, anchor_screen, 1)
            pygame.draw.circle(crt.canvas, config.COLOR_FIBO_GOLD, anchor_screen, 3, 1)

        # 5. Render Mateo sprite
        decoy = self.player.abilities.get_active_decoy()
        if decoy:
            dx, dy = self.camera.world_to_screen(decoy.x, decoy.y)
            pygame.draw.rect(crt.canvas, (90, 200, 245), (dx, dy, decoy.width, decoy.height), 1)
        # Invulnerability flash
        flash_hide = (self.player.invulnerable_timer > 0.0 and int(self.player.invulnerable_timer * 20) % 2 == 0)

        if not flash_hide:
            if self.player.animator is not None:
                foot_wx = self.player.x + (self.player.width / 2.0)
                foot_wy = self.player.y + 32.0
                dest_x, dest_y = self.player.animator.get_render_dest_for_density(foot_wx, foot_wy, self.camera, config.RENDER_DENSITY)
                sprite = self.player.animator.surface_for_density(config.RENDER_DENSITY)
                logical_size = self.player.animator.current_surface.get_size()
                crt.composite_native(sprite, (dest_x / config.RENDER_DENSITY, dest_y / config.RENDER_DENSITY), logical_size)
            else:
                screen_px, screen_py = self.camera.world_to_screen(self.player.x, self.player.y)
                mateo_surf = None
                try:
                    mateo_surf = self.machine.assets.bunker_sprite("mateo_idle", (48, 64))
                except Exception:
                    pass

                if mateo_surf:
                    sprite = pygame.transform.scale(mateo_surf, (24, 32))
                    if self.player.facing == "left":
                        sprite = pygame.transform.flip(sprite, True, False)
                    crt.canvas.blit(sprite, (screen_px - 4, screen_py))
                else:
                    # Fallback stylized Mateo bounding silhouette
                    m_col = config.COLOR_FIBO_GOLD
                    pygame.draw.rect(crt.canvas, m_col, (screen_px, screen_py, self.player.width, self.player.height), 2)
                    pygame.draw.circle(crt.canvas, m_col, (screen_px + 8, screen_py + 8), 6)

        # 5. Projectiles and waveguide maser beams
        if hasattr(self, "projectile_manager"):
            self.projectile_manager.render(crt.canvas, self.camera)

        # 5.5. Visual combat particles, flashes, dust, and ricochet sparks
        if hasattr(self, "effects"):
            self.effects.render(crt.canvas, self.camera)

        # 6. Atmospheric weather mist overlay
        self.room.render_weather(crt.canvas, self.camera)

        if self.holdout:
            defense = self.holdout
            info = defense.get_signal_display()
            line = f"DISH {info['dish_integrity']:.0f}%  {info['remaining']:.0f}s  SIGNAL {info['code']} {info['snr']}σ"
            pygame.draw.rect(crt.canvas, (4, 10, 9), (6, 54, 245, 24))
            crt.draw_text(line, 10, 56, color=config.COLOR_FIBO_GOLD, size="sm")
            if defense.is_jammed:
                crt.draw_text("JAMMED: GO TO FEEDHORN // E", 10, 67, color=config.COLOR_AMBER_1977, size="sm")
            elif defense.is_failed:
                crt.draw_text("DEFENSE FAILED // R: RETRY", 10, 67, color=config.COLOR_AMBER_1977, size="sm")
            elif defense.is_active:
                crt.draw_text("HOSTILES DAMAGE ARRAY", 10, 67, color=config.COLOR_CRT_GREEN, size="sm")

        # 7. On-screen interaction prompt
        if self.prompt_text:
            p_col = config.COLOR_AMBER_1977 if "WARN" in self.prompt_text else config.COLOR_FIBO_GOLD
            prompt_lines = wrap_text_pixels(self.prompt_text, crt.font_sm, 350)
            top = 224 - (len(prompt_lines) - 1) * 11
            width = max(crt.font_sm.size(line)[0] for line in prompt_lines)
            pygame.draw.rect(crt.canvas, (5, 14, 9), (116, top - 2, width + 8, len(prompt_lines) * 11 + 3))
            for i, line in enumerate(prompt_lines):
                crt.draw_text(line, 120, top + i * 11, color=p_col, size="sm")

        # 7. Threat feedback detection
        threat_level = None
        if hasattr(self, "enemy_manager"):
            if any(getattr(e, "aim_locked", False) for e in self.enemy_manager.enemies):
                threat_level = "LOCKED"
            elif any(getattr(e, "state", "").lower() == "windup" for e in self.enemy_manager.enemies):
                threat_level = "AIMING"

        # 8. Global HUD Footer
        if self.flashback is not None:
            loc_label = "OHIO STATE RADIO OBSERVATORY // BIG EAR 1977 FLASHBACK"
            footer = "[ARROWS/WASD] MOVE  [SPACE] JUMP  [E] INSPECT / ANNOTATE  [ESC] RETURN"
        else:
            loc_label = "OHIO FIELD OPERATIONS // ACT I ACCESS TRENCH"
            footer = "[ARROWS/WASD] MOVE  [SPACE] JUMP  [X/J] FIRE  [C] CROUCH  [ESC] BUNKER"
        self.machine.render_global_hud(
            crt,
            location_label=loc_label,
            footer_text=footer,
            player=None if self.flashback is not None and self.flashback.is_printout_open else self.player,
            objective=self.objective_tracker.get_active_objective(self.machine.campaign),
            notification=self.objective_tracker.active_notification,
            threat_level=threat_level,
            staging_cleared=bool(self.prompt_text),
        )
        # The HUD has flushed its footer; any pending charge bar is disjoint
        # from these labels, so no viewport-wide scan is needed here.
        with crt.text_batch(dirty_region=(0, 0, 0, 0)):
            if self.reality.world:
                crt.draw_text("[T] SWAP [E] RELAY [N] ENCOUNTER [F6/F7/F8] ROOMS", 8, 52)
            if self.player.is_grappling and self.player.grapple_anchor_pos is not None:
                crt.draw_text("[G / SPACE] RELEASE GRAPPLE", 8, 64, color=config.COLOR_FIBO_GOLD)
            crt.draw_text(f"[Q] {self.player.arsenal.active_weapon_id} [R/K] {self.player.abilities.selected_ability_id} E:{self.player.abilities.energy:.0f}", 8, 240)
        self.reality.render_panel(crt)

    def _load_faction_encounter(self):
        """Start the next bounded pair only when both positions are safe."""
        from video_game.engine.enemies import (CoreEnforcer, CoreOperative, ShieldHound,
            PhaseWatcher, ChrysalisSplicer, PrecursorGuardian, TemporalPhantom)

        groups = ((CoreEnforcer, CoreOperative), (ShieldHound, PhaseWatcher),
                  (ChrysalisSplicer, PrecursorGuardian), (TemporalPhantom, CoreReconDrone))
        aerial = (PhaseWatcher, TemporalPhantom, CoreReconDrone)
        group = groups[self._faction_encounter % len(groups)]
        placed = []
        occupied = [self.player.rect.inflate(32, 16)]
        tile = self.room.tile_size
        default_spawn = self.room.spawns.get('default')
        preferred_floor = (default_spawn.y + self.player.height if default_spawn
                           else self.player.rect.bottom)

        def safe(rect, grounded):
            if not pygame.Rect(0, 0, self.room.width_px, self.room.height_px).contains(rect):
                return False
            # Reserve hover clearance for the drone's six-pixel bob.
            clearance = rect if grounded else rect.inflate(0, 12)
            if not pygame.Rect(0, 0, self.room.width_px, self.room.height_px).contains(clearance):
                return False
            collision = self.room.check_rect_collision(clearance)
            if collision['solid'] or collision['hazard'] or collision['one_way']:
                return False
            if any(clearance.colliderect(other) for other in occupied):
                return False
            if grounded:
                row = rect.bottom // tile
                cols = range(rect.left // tile, (rect.right - 1) // tile + 1)
                if rect.bottom % tile or not all(
                    self.room.get_tile(col, row) in (COLLISION_SOLID, COLLISION_ONE_WAY)
                    for col in cols
                ):
                    return False
            return True

        for index, enemy_type in enumerate(group):
            enemy = enemy_type(f"annex_{index}", 0.0, 0.0)
            grounded = enemy_type not in aerial
            xs = sorted(range(0, self.room.width_px - enemy.rect.width + 1, 8),
                        key=lambda x: abs(x - (352 + index * 64)))
            floors = sorted(range(tile, self.room.height_px, tile),
                            key=lambda y: abs(y - preferred_floor)) if grounded else [128]
            rect = next((pygame.Rect(x, floor - enemy.rect.height if grounded else floor,
                                     enemy.rect.width, enemy.rect.height)
                         for floor in floors for x in xs
                         if safe(pygame.Rect(x, floor - enemy.rect.height if grounded else floor,
                                             enemy.rect.width, enemy.rect.height), grounded)), None)
            if rect is None:
                self.objective_tracker.post_notification(
                    "ENCOUNTER UNAVAILABLE", "NO SAFE SPAWN IN THIS TIMELINE", "warning")
                return
            enemy.x = enemy.spawn_x = float(rect.x)
            enemy.y = enemy.spawn_y = float(rect.y)
            enemy.rect = rect
            # Keep normal patrol within the contiguous safe span at this height.
            left = right = rect.x
            while left >= 8 and rect.x - left < 80 and safe(rect.move(left - rect.x - 8, 0), grounded):
                left -= 8
            while right + 8 + rect.width <= self.room.width_px and right - rect.x < 80 and safe(rect.move(right - rect.x + 8, 0), grounded):
                right += 8
            enemy.patrol_left, enemy.patrol_right = float(left), float(right)
            placed.append(enemy)
            occupied.append(rect.inflate(16, 8))

        self.enemy_manager.clear()
        self.projectile_manager.clear()
        for enemy in placed:
            self.enemy_manager.add_enemy(enemy)
        hints = (
            "ENFORCER: SLIDE / OPERATIVE: CROUCH",
            "HOUND: SLIDE / WATCHER: EMP OR REVEAL",
            "SPLICER: CROUCH IN COVER / GUARDIAN: JUMP",
            "PHANTOM: SCATTERGUN / DRONE: BREAK SIGHT",
        )
        hint = hints[self._faction_encounter % len(hints)]
        self._faction_encounter += 1
        self.objective_tracker.post_notification("COUNTERS", hint, duration=8.0)
