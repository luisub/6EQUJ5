"""
# PURPOSE: Playable Boss Arena Scene managing sector boss encounters, camera framing, health bars, and defeat flow.
# CALLED BY: video_game.engine.state_machine, video_game.tests.test_combat.
# HOW TO MODIFY: Adjust camera tracking bounds, boss HUD layout, pre-boss checkpoint restore, or defeat reward triggers.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pygame

from video_game.engine import config
from video_game.engine.animation import AnimationPlayer, load_mateo_animations
from video_game.engine.effects import EffectManager
from video_game.engine.bosses.base import (
    PHASE_1,
    PHASE_2,
    PHASE_3,
    PHASE_DEFEATED,
    STATE_DEFEATED,
    STATE_VULNERABLE,
)
from video_game.engine.bosses.greenkeeper import Greenkeeper
from video_game.engine.objectives import Objective
from video_game.engine.player import Player, PlayerConfig, PlayerInput
from video_game.engine.scenes.base import BaseScene
from video_game.engine.ui.hud import render_global_hud
from video_game.engine.weapons import ArsenalManager, ProjectileManager, StarterMaser
from video_game.engine.abilities import AbilityManager
from video_game.engine.world import Camera, Room

LEVELS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "levels"


class BossScene(BaseScene):
    """
    Playable Sector Boss Arena Scene.

    Manages arena geometry, player combat locomotion, sector boss lifecycle,
    phase transitions, pre-boss checkpoint resets, and defeat reward progression.
    """

    def __init__(self, machine: Any, room_relative_path: str = "act_01/greenkeeper_arena.json"):
        super().__init__(machine)
        self.room_path = LEVELS_DIR / room_relative_path
        self.room = Room.load_from_file(self.room_path)
        self.camera = Camera(config.INTERNAL_WIDTH, config.INTERNAL_HEIGHT)
        self.camera.set_world_bounds(self.room.width_px, self.room.height_px)

        # Player setup
        self.player = Player(64.0, 208.0)
        self.player_input = PlayerInput()

        # Wire animation player
        try:
            clips = load_mateo_animations(self.machine.assets.root, outfit="olive_field")
            self.player.animator = AnimationPlayer(
                clips=clips,
                default_state="idle",
                scale_factor=0.25,
            )
        except Exception:
            self.player.animator = None

        # Weapons setup
        self.proj_mgr = ProjectileManager()
        self.player.arsenal = ArsenalManager()
        self.player.abilities = AbilityManager()
        self.player.weapon = self.player.arsenal.active_weapon
        self.effects = EffectManager()
        self._prev_boss_proj_count: int = 0
        self._prev_player_hp: int = self.player.health
        self._prev_is_grounded: bool = False
        self._prev_is_sliding: bool = False

        # Boss setup
        self.boss = Greenkeeper(x=460.0, y=192.0)

        # Encounter tracking
        self.checkpoint_pos: Tuple[float, float] = (64.0, 208.0)
        self.is_fight_active: bool = False
        self.is_defeated_sequence: bool = False
        self.defeat_banner_timer: float = 0.0
        self.simultaneous_death_occurred: bool = False

    def on_enter(self, **kwargs):
        """Prepare arena on transition enter."""
        spawn_id = kwargs.get("spawn", "arena_checkpoint")
        if spawn_id in self.room.spawns:
            sp = self.room.spawns[spawn_id]
            self.checkpoint_pos = (sp.x, sp.y)
        else:
            self.checkpoint_pos = (64.0, 208.0)

        self.player.arsenal.sync_unlocks(self.machine.campaign)
        self.player.abilities.sync_unlocks(self.machine.campaign)
        self.player.weapon = self.player.arsenal.active_weapon
        self.player.set_checkpoint("pre_boss", self.checkpoint_pos[0], self.checkpoint_pos[1])
        self.player.respawn_at_checkpoint(self.room)
        self.camera.snap_to(self.player.x, self.player.y)
        self.boss.reset_to_pristine()
        self.boss.skip_intro()
        self.is_fight_active = True
        self.is_defeated_sequence = False
        self.defeat_banner_timer = 0.0
        self.simultaneous_death_occurred = False

    def on_exit(self):
        """Purge lingering projectiles, effects, and state upon leaving."""
        self.proj_mgr.clear()
        self.effects.clear()
        self.boss.telegraphs.clear()
        self.boss.projectiles.clear()

    def handle_event(self, event: pygame.Event):
        """Process player combat inputs and debug keys."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.machine.change_state(config.STATE_BUNKER_HUB)
                return

            if event.key == pygame.K_r and (self.player.is_dead or self.boss.is_defeated):
                # Retry owns R; do not cycle an ability on the next update.
                self.machine.input.release_all()
                self.retry_from_checkpoint()
                return

    def update(self, dt: float):
        """Execute fixed-step combat simulation across player, boss, and arena."""
        # Use the same focused, edge-triggered action mapper as field gameplay.
        if self.player.is_dead:
            return  # R explicitly restarts the encounter; do not silently respawn in phase 3.
        self.player_input = PlayerInput.from_input_manager(self.machine.input)

        is_paused = getattr(self.machine, "is_paused", False) or getattr(getattr(self.machine, "pause", None), "active", False)

        # Trigger jump audio and dust
        if self.player_input.jump_pressed and (self.player.is_grounded or self.player.coyote_timer > 0.0):
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("player_jump")
            self.effects.add_dust_puff(self.player.x + 8.0, self.player.y + 32.0, count=4)

        prev_proj_len = len(self.proj_mgr.projectiles)

        # 2. Update player kinematics and weapon discharge
        self.player.update(
            dt,
            self.player_input,
            self.room,
            projectile_manager=self.proj_mgr,
            is_paused=is_paused,
        )

        # Trigger audio and muzzle flash on weapon discharge
        if len(self.proj_mgr.projectiles) > prev_proj_len:
            new_proj = self.proj_mgr.projectiles[-1]
            sfx_name = "maser_charge" if new_proj.is_charged else "maser_tap"
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx(sfx_name)
            self.effects.add_muzzle_flash(new_proj.x, new_proj.y, direction=self.player.facing, is_charged=new_proj.is_charged)

        # Trigger landing and slide dust / audio
        if not self._prev_is_grounded and self.player.is_grounded:
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("player_land")
            self.effects.add_dust_puff(self.player.x + 8.0, self.player.y + 32.0, count=5)
        if not self._prev_is_sliding and self.player.is_sliding:
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("player_slide")
            self.effects.add_dust_puff(self.player.x + 8.0, self.player.y + 32.0, count=4)

        self._prev_is_grounded = self.player.is_grounded
        self._prev_is_sliding = self.player.is_sliding

        # 3. Resolve player maser projectiles against world and boss
        if self.player.is_dashing and self.player.dash_attack_rect.colliderect(self.boss.rect):
            self.player.apply_dash_attack(self.boss)
        if not self.boss.is_dead:
            targets = [self.boss]
            hits = self.proj_mgr.update(dt, self.room, targets=targets, is_paused=is_paused)
            if hits:
                for hit in hits:
                    if hasattr(self.machine, "audio") and self.machine.audio:
                        self.machine.audio.play_sfx("impact_spark")
                    self.effects.add_impact_sparks(hit.hit_x, hit.hit_y, count=6)

        # 5. Update Boss AI and attack cycles
        if not self.player.is_dead and not self.boss.is_dead:
            self.boss.update(dt, player_pos=(self.player.x, self.player.y))

            # Trigger mortar launch sfx and smoke
            curr_boss_projs = len(self.boss.projectiles)
            if curr_boss_projs > self._prev_boss_proj_count:
                if hasattr(self.machine, "audio") and self.machine.audio:
                    self.machine.audio.play_sfx("boss_mortar_launch")
                self.effects.add_mortar_smoke(self.boss.x + 24.0, self.boss.y + 8.0, count=5)
            self._prev_boss_proj_count = curr_boss_projs

            # Check for exploding mortar shells reaching ground level
            for bp in self.boss.projectiles:
                if bp.y >= 216.0 and bp.lifetime > 0.0:
                    self.effects.add_mortar_smoke(bp.x, 228.0, count=3)
                    self.effects.add_impact_sparks(bp.x, 228.0, count=4, is_charged=True)

            # 6. Check boss attack hitboxes against player
            dmg = self.boss.check_attack_collisions(self.player.rect)
            if dmg > 0 and self.player.invulnerable_timer <= 0.0:
                kb_x = -80.0 if self.player.facing == "right" else 80.0
                self.player.take_damage(dmg, knockback_vx=kb_x, knockback_vy=-60.0)

        # Check player damage taken
        if self.player.health < self._prev_player_hp:
            if hasattr(self.machine, "audio") and self.machine.audio:
                self.machine.audio.play_sfx("player_hurt")
            self.effects.add_impact_sparks(self.player.x + 8.0, self.player.y + 16.0, count=8, is_charged=True)
        self._prev_player_hp = self.player.health

        # Step bounded effects
        self.effects.update(dt, room=self.room, is_paused=is_paused)

        # 7. Check simultaneous death edge case
        resolution = self.boss.resolve_simultaneous_death(not self.player.is_dead)
        if resolution == "PLAYER_DIED":
            # Player defeat takes priority
            if self.boss.is_defeated:
                self.simultaneous_death_occurred = True

        elif resolution == "BOSS_DEFEATED":
            if not self.is_defeated_sequence:
                self.is_defeated_sequence = True
                self.defeat_banner_timer = 2.5
                if self.boss.apply_defeat_reward(self.machine.campaign):
                    self.machine.save_checkpoint()

        # 8. Defeat timer tick
        if self.is_defeated_sequence:
            self.defeat_banner_timer = max(0.0, self.defeat_banner_timer - dt)

        # 9. Update camera smooth tracking
        self.camera.update(self.player.x, self.player.y)

    def retry_from_checkpoint(self):
        """Restore pristine encounter state and respawn player at arena entrance."""
        self.player.set_checkpoint("pre_boss", self.checkpoint_pos[0], self.checkpoint_pos[1])
        self.player.respawn_at_checkpoint(self.room)
        self.boss.reset_to_pristine()
        self.boss.skip_intro()
        self.proj_mgr.clear()
        self.effects.clear()
        self.is_fight_active = True
        self.is_defeated_sequence = False
        self.defeat_banner_timer = 0.0
        self.simultaneous_death_occurred = False

    def render(self, crt: Any):
        """Render complete boss arena view: background, terrain, boss, player, and boss HUD."""
        crt.clear()
        # 1. Parallax background
        self.room.render_background(crt.canvas, self.camera)

        # 2. Collision tiles & platforms
        self.room.render_tiles(crt.canvas, self.camera)

        # 3. Level objects & props
        self.room.render_objects(crt.canvas, self.camera)

        # 4. Boss entity & telegraphs
        self.boss.render(crt.canvas, self.camera)

        # 5. Player projectiles
        self.proj_mgr.render(crt.canvas, self.camera)

        # 6. Player character
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
                pygame.draw.rect(crt.canvas, config.COLOR_FIBO_GOLD, (screen_px, screen_py, self.player.width, self.player.height), 2)
                pygame.draw.circle(crt.canvas, config.COLOR_FIBO_GOLD, (screen_px + 8, screen_py + 8), 6)

        # 6.2 Visual combat particles, mortar smoke, sparks, and flashes
        if hasattr(self, "effects"):
            self.effects.render(crt.canvas, self.camera)

        # 6.5 Atmospheric weather mist
        self.room.render_weather(crt.canvas, self.camera)

        # 7. Boss HUD (Top Bar overlay)
        self._render_boss_hud(crt)

        # 8. Standard global HUD footer
        obj = Objective(
            id="defeat_greenkeeper",
            title="NEUTRALIZE GREENKEEPER",
            description="Expose Core power cell and breach the reflector basin",
            hint=("BOSS DEFEATED" if self.boss.is_defeated else
                  f"PHASE {self.boss.current_phase}/3 // WEAK POINT: OVERHEAD CORE"),
        )
        footer = "[A/D] MOVE  [W/SPACE] JUMP  [S] DUCK  [SHIFT] DASH  [J] FIRE  [ESC] RETREAT"
        render_global_hud(
            crt,
            self.machine.campaign,
            location_label="DEEP REFLECTOR BASIN // SECTOR BOSS ARENA",
            footer_text=footer,
            player=self.player,
            objective=obj,
            threat_level="LOCKED" if not self.boss.is_defeated else None,
        )

        # 9. Defeat victory banner
        if self.is_defeated_sequence:
            self._render_defeat_banner(crt)

        # 10. Player Death banner
        if self.player.is_dead:
            self._render_player_death_banner(crt)

    def _render_boss_hud(self, crt: Any):
        """Render boss health bar, phase markers, and weak point status."""
        bar_x = 120
        bar_y = 22
        bar_w = 240
        bar_h = 10

        # Background frame
        pygame.draw.rect(crt.canvas, (10, 14, 18), (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 18))
        pygame.draw.rect(crt.canvas, config.COLOR_CORE_STEEL, (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 18), 1)

        # Health fill
        hp_pct = max(0.0, self.boss.health / float(self.boss.max_health))
        fill_w = int(bar_w * hp_pct)
        hp_color = config.COLOR_EHMAN_RED if hp_pct <= 0.33 else (config.COLOR_AMBER_1977 if hp_pct <= 0.66 else config.COLOR_CRT_GREEN)
        pygame.draw.rect(crt.canvas, hp_color, (bar_x, bar_y, fill_w, bar_h))
        pygame.draw.rect(crt.canvas, (40, 50, 60), (bar_x, bar_y, bar_w, bar_h), 1)

        # Phase threshold notch ticks
        tick_p2 = bar_x + int(bar_w * 2 / 3)
        tick_p3 = bar_x + int(bar_w / 3)
        pygame.draw.line(crt.canvas, (255, 255, 255), (tick_p2, bar_y - 2), (tick_p2, bar_y + bar_h + 2), 1)
        pygame.draw.line(crt.canvas, (255, 255, 255), (tick_p3, bar_y - 2), (tick_p3, bar_y + bar_h + 2), 1)

        # Boss title & phase readout
        title_str = (f"{self.boss.title} [DEFEATED]" if self.boss.is_defeated else
                     f"{self.boss.title} [PHASE {self.boss.current_phase}/3]")
        crt.draw_text(title_str, bar_x, bar_y + 11, color=config.COLOR_FIBO_GOLD, size="sm")

        # Weak point indicator
        if self.boss.weak_point_exposed:
            crt.draw_text("[!] CORE VULNERABLE", bar_x + 140, bar_y + 11, color=(255, 80, 80), size="sm")

    def _render_defeat_banner(self, crt: Any):
        """Render victory notification banner."""
        banner_rect = pygame.Rect(80, 110, 320, 50)
        pygame.draw.rect(crt.canvas, (10, 24, 16), banner_rect)
        pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, banner_rect, 2)
        crt.draw_text("SECTOR BOSS NEUTRALIZED", 130, 118, color=config.COLOR_CRT_GREEN, size="lg")
        crt.draw_text("CORE OVERSEER PURGED // ACT II UNLOCKED", 112, 140, color=config.COLOR_FIBO_GOLD, size="sm")

    def _render_player_death_banner(self, crt: Any):
        """Render casualty notification and retry prompt."""
        banner_rect = pygame.Rect(90, 110, 300, 50)
        pygame.draw.rect(crt.canvas, (28, 8, 8), banner_rect)
        pygame.draw.rect(crt.canvas, config.COLOR_EHMAN_RED, banner_rect, 2)
        crt.draw_text("MATEO FALLEN // CRITICAL CASUALTY", 112, 118, color=config.COLOR_EHMAN_RED, size="sm")
        crt.draw_text("PRESS [R] TO RETRY FROM PRE-BOSS CHECKPOINT", 102, 138, color=config.COLOR_AMBER_1977, size="sm")
