"""
# PURPOSE: Act I culminating boss Core Warden Greenkeeper with mortar, sweep, and exposed-weak-point phases.
# CALLED BY: video_game.engine.scenes.boss, video_game.tests.test_combat.
# HOW TO MODIFY: Adjust attack windup times, mortar trajectories, sweep elevations, and weak point vulnerability windows.
"""

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pygame

from video_game.engine import config
from video_game.engine.weapons import HitResult
from video_game.engine.bosses.greenkeeper_art import load_family
from video_game.engine.bosses.base import (
    Boss,
    boss_balance,
    BossAttackTelegraph,
    BossProjectile,
    PHASE_1,
    PHASE_2,
    PHASE_3,
    PHASE_DEFEATED,
    STATE_ATTACK,
    STATE_DEFEATED,
    STATE_IDLE,
    STATE_RECOVERY,
    STATE_TELEGRAPH,
    STATE_TRANSITION,
    STATE_VULNERABLE,
)


class Greenkeeper(Boss):
    """
    Core Warden Greenkeeper: Automated terraforming excavator hijacked by The Core.

    Phase 1: High parabolic mortar barrages + overhead exhaust weak point exposure.
    Phase 2: Low-altitude sweeping energy cutters + bulldozer surge + frontal cowl jam.
    Phase 3: Critical reactor meltdown; continuous weak point exposure with rapid alternations.
    """

    def __init__(self, x: Optional[float] = None, y: Optional[float] = None, *, asset_root: Optional[Path] = None):
        # Explicit coordinates always name the top-left of the selected body.
        root = Path(asset_root) if asset_root is not None else Path(__file__).resolve().parent.parent.parent / 'assets'
        self.heavy_sprites = load_family(root)
        self.heavy_logical_sprites = ({name: pygame.transform.scale(sprite, (128, 96))
                                       for name, sprite in self.heavy_sprites.items()}
                                      if self.heavy_sprites is not None else None)
        heavy = self.heavy_sprites is not None
        x = (428.0 if heavy else 460.0) if x is None else x
        y = (144.0 if heavy else 192.0) if y is None else y
        super().__init__(
            boss_id="greenkeeper_act_01",
            x=x,
            y=y,
            width=128 if heavy else 64,
            height=96 if heavy else 48,
            max_health=boss_balance()['health']['greenkeeper'],
            title="THE GREENKEEPER",
            subtitle="ACT I OVERSEER // TERRAFORMING WARDEN",
        )
        # Attack cycle variables
        self.attack_cycle_timer: float = 1.0
        self.volley_count: int = 0
        self.current_attack_type: str = ""
        self.pending_mortar_targets: List[Tuple[float, float]] = []

        # Sweep beam state
        self.sweep_active: bool = False
        self.sweep_timer: float = 0.0
        self.sweep_x: float = 0.0
        self.sweep_y: float = 224.0

        # Bulldozer kinematics
        self.charge_vx: float = 0.0
        self.charge_duration: float = 0.0

        # Animation state and pixel art sprite cache
        self.anim_timer: float = 0.0
        self.damage_flash_timer: float = 0.0
        self.attack_visual_timer: float = 0.0

        # Initialize weak point rect
        self._update_weak_point()

    def _update_weak_point(self):
        """Update absolute coordinates of the core weak point relative to boss position."""
        x, y, w, h = (62, 49, 23, 19) if self.heavy_sprites is not None else (8, 6, 24, 20)
        self.weak_point_rect = pygame.Rect(
            int(self.x + x), int(self.y + y), w, h,
        )

    @property
    def mortar_muzzle(self) -> Tuple[float, float]:
        """World-space launch effect anchor, registered to the current family."""
        if self.heavy_sprites is not None:
            return (self.x + 39.0, self.y + 16.0)
        return (self.x + 24.0, self.y + 8.0)

    def _heavy_pose(self) -> str:
        if self.is_defeated or self.phase_state == STATE_DEFEATED:
            return 'wreck'
        if self.weak_point_exposed or self.phase_state == STATE_VULNERABLE:
            return 'exposed'
        if self.attack_visual_timer > 0 or self.sweep_active:
            return 'attack'
        return 'idle'

    def reset_to_pristine(self):
        """Reset Greenkeeper state cleanly, purging all attacks and projectiles."""
        super().reset_to_pristine()
        self.attack_cycle_timer = 1.0
        self.volley_count = 0
        self.current_attack_type = ""
        self.pending_mortar_targets.clear()
        self.sweep_active = False
        self.sweep_timer = 0.0
        self.sweep_x = 0.0
        self.charge_vx = 0.0
        self.charge_duration = 0.0
        self.damage_flash_timer = 0.0
        self.attack_visual_timer = 0.0
        self._update_weak_point()

    def take_damage(
        self,
        amount: int,
        hit_id: str = "",
        knockback: Tuple[float, float] = (0.0, 0.0),
        hit_pos: Tuple[float, float] = (0.0, 0.0),
    ) -> HitResult:
        """Process incoming damage and trigger visual impact damage flash."""
        res = super().take_damage(amount, hit_id=hit_id, knockback=knockback, hit_pos=hit_pos)
        if res.hit and res.damage_dealt > 0:
            self.damage_flash_timer = 0.15
        return res

    def update(self, dt: float, player_pos: Tuple[float, float] = (120.0, 208.0)):
        """Update Greenkeeper AI behavior, attack cycles, and sub-systems."""
        super().update(dt)
        self.anim_timer += dt
        if self.damage_flash_timer > 0.0:
            self.damage_flash_timer = max(0.0, self.damage_flash_timer - dt)
        self.attack_visual_timer = max(0.0, self.attack_visual_timer - dt)
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        self._update_weak_point()

        if self.is_dead or self.phase_state in (STATE_TRANSITION, STATE_DEFEATED):
            return

        # Execute sweep attack if active
        if self.sweep_active:
            self.sweep_timer -= dt
            self.sweep_x -= 600.0 * dt
            if self.sweep_timer <= 0.0 or self.sweep_x <= 32.0:
                self.sweep_active = False
                self.sweep_timer = 0.0
                # Overheated cutter enters vulnerability
                self.phase_state = STATE_VULNERABLE
                self.vulnerability_timer = 3.0
                self.weak_point_exposed = True

        # Execute bulldozer charge if active
        if self.charge_duration > 0.0:
            self.charge_duration -= dt
            self.x = max(32.0, self.x + self.charge_vx * dt)
            self.rect.x = int(self.x)
            self._update_weak_point()
            if self.charge_duration <= 0.0:
                self.charge_vx = 0.0
                # Blade jammed in turf
                self.phase_state = STATE_VULNERABLE
                self.vulnerability_timer = 2.5
                self.weak_point_exposed = True

        # Phase AI decision loop
        if self.phase_state == STATE_IDLE:
            self.attack_cycle_timer -= dt
            if self.attack_cycle_timer <= 0.0:
                self._schedule_next_attack(player_pos)

        elif self.phase_state == STATE_TELEGRAPH:
            # Check if active telegraph has finished
            if not self.telegraphs:
                self._execute_telegraphed_attack()

        elif self.phase_state == STATE_RECOVERY:
            self.state_timer -= dt
            if self.state_timer <= 0.0:
                self.phase_state = STATE_IDLE
                self.attack_cycle_timer = 0.8

    def _schedule_next_attack(self, player_pos: Tuple[float, float]):
        """Schedule telegraph warning for phase-specific attacks."""
        px, py = player_pos

        if self.current_phase == PHASE_1:
            # Turf mortar barrage
            self.current_attack_type = "mortar"
            # Reticle 1 at player x clamped to arena floor, Reticle 2 offset by 70px
            reticle_1_x = max(64.0, min(420.0, px))
            reticle_2_x = max(64.0, min(420.0, px + (70.0 if px < 240.0 else -70.0)))
            self.pending_mortar_targets = [
                (reticle_1_x, 232.0),
                (reticle_2_x, 232.0),
            ]
            self.telegraphs.clear()
            for tx, ty in self.pending_mortar_targets:
                self.telegraphs.append(
                    BossAttackTelegraph(
                        attack_type="mortar",
                        duration=0.8,
                        center=(tx, ty),
                        radius=24.0,
                        color=config.COLOR_AMBER_1977,
                    )
                )
            self.phase_state = STATE_TELEGRAPH

        elif self.current_phase == PHASE_2:
            # Alternates between Low Energy Sweep and Bulldozer Charge
            if self.volley_count % 2 == 0:
                self.current_attack_type = "sweep"
                self.telegraphs.clear()
                self.telegraphs.append(
                    BossAttackTelegraph(
                        attack_type="sweep",
                        duration=0.7,
                        target_rect=pygame.Rect(32, 216, 440, 20),
                        color=(255, 60, 60),
                    )
                )
            else:
                self.current_attack_type = "charge"
                self.telegraphs.clear()
                self.telegraphs.append(
                    BossAttackTelegraph(
                        attack_type="charge",
                        duration=0.6,
                        target_rect=pygame.Rect(int(self.x - 80), int(self.y + (48 if self.heavy_sprites is not None else 0)), 80, 48),
                        color=(255, 140, 40),
                    )
                )
            self.phase_state = STATE_TELEGRAPH

        elif self.current_phase == PHASE_3:
            # Overclocked Meltdown: Core is permanently exposed
            self.weak_point_exposed = True
            # Fast alternating attack: rapid mortar or fast pulse
            if self.volley_count % 2 == 0:
                self.current_attack_type = "mortar"
                reticle_x = max(64.0, min(420.0, px))
                self.pending_mortar_targets = [(reticle_x, 232.0)]
                self.telegraphs.clear()
                self.telegraphs.append(
                    BossAttackTelegraph(
                        attack_type="mortar",
                        duration=0.55,
                        center=(reticle_x, 232.0),
                        radius=28.0,
                        color=(255, 80, 80),
                    )
                )
            else:
                self.current_attack_type = "sweep"
                self.telegraphs.clear()
                self.telegraphs.append(
                    BossAttackTelegraph(
                        attack_type="sweep",
                        duration=0.55,
                        target_rect=pygame.Rect(32, 216, 440, 20),
                        color=(255, 60, 60),
                    )
                )
            self.phase_state = STATE_TELEGRAPH

    def _execute_telegraphed_attack(self):
        """Execute the telegraphed attack after warning expires."""
        self.volley_count += 1

        if self.current_attack_type == "mortar":
            self.attack_visual_timer = 0.2
            # Spawn mortar shells falling onto targets
            for idx, (tx, ty) in enumerate(self.pending_mortar_targets):
                self.projectiles.append(
                    BossProjectile(
                        proj_id=f"mortar_{self.volley_count}_{idx}",
                        x=tx,
                        y=50.0,
                        vx=0.0,
                        vy=280.0,  # Hits ground in ~0.65s
                        radius=8.0,
                        damage=25,
                        lifetime=1.0,
                        color=config.COLOR_EHMAN_RED,
                    )
                )
            self.pending_mortar_targets.clear()

            # In Phase 1, every 2 volleys opens exhaust weak point
            if self.current_phase == PHASE_1 and self.volley_count % 2 == 0:
                self.phase_state = STATE_VULNERABLE
                self.vulnerability_timer = 2.5
                self.weak_point_exposed = True
            else:
                self.phase_state = STATE_RECOVERY
                self.state_timer = 0.8

        elif self.current_attack_type == "sweep":
            # Launch active horizontal beam across floor
            self.sweep_active = True
            self.sweep_timer = 0.8
            self.sweep_x = self.x + (5.0 if self.heavy_sprites is not None else 0.0)
            self.sweep_y = self.y + 80.0 if self.heavy_sprites is not None else 224.0
            self.phase_state = STATE_ATTACK

        elif self.current_attack_type == "charge":
            # Surge forward 70px
            self.charge_vx = -160.0
            self.charge_duration = 0.44
            self.phase_state = STATE_ATTACK

    def check_attack_collisions(self, player_rect: pygame.Rect) -> int:
        """
        Check all active boss attacks against the player.
        Returns total damage dealt (or 0 if cleanly evaded).
        """
        damage = 0

        # 1. Projectiles (Mortar shells)
        for p in self.projectiles:
            if p.check_player_collision(player_rect):
                damage += p.damage
                p.is_active = False

        # 2. Sweeping beam collision (Ground floor slice: y in [212, 236])
        if self.sweep_active:
            sweep_rect = pygame.Rect(int(self.sweep_x) - 40, int(self.sweep_y) - 6, 80, 16)
            if sweep_rect.colliderect(player_rect):
                damage += 30
                self.sweep_active = False  # Hits once per pass

        # 3. Charging bulldozer body
        if self.charge_duration > 0.0:
            if self.rect.colliderect(player_rect):
                damage += 30
                self.charge_duration = 0.0
                self.charge_vx = 0.0

        return damage

    def render(self, surface: pygame.Surface, camera: Any, *, crt: Any = None):
        """Render Greenkeeper chassis, weak point, telegraphs, and active attacks."""
        sc_x, sc_y = camera.world_to_screen(self.x, self.y)

        # 1. Render active telegraphs first (underneath boss)
        for t in self.telegraphs:
            if t.attack_type == "mortar":
                cx, cy = camera.world_to_screen(t.center[0], t.center[1])
                # Draw outer warning boundary
                pygame.draw.circle(surface, (80, 20, 20), (cx, cy), int(t.radius), 1)
                # Draw shrinking time-progress ring
                curr_r = max(4, int(t.radius * (1.0 - t.progress)))
                pygame.draw.circle(surface, t.color, (cx, cy), curr_r, 2)
                # Crosshair mark
                pygame.draw.line(surface, t.color, (cx - 6, cy), (cx + 6, cy), 1)
                pygame.draw.line(surface, t.color, (cx, cy - 6), (cx, cy + 6), 1)

            elif t.attack_type == "sweep" and t.target_rect:
                rx, ry = camera.world_to_screen(t.target_rect.x, t.target_rect.y)
                r_rect = pygame.Rect(rx, ry, t.target_rect.width, t.target_rect.height)
                # Flashing warning bar
                alpha_color = (180, 40, 40) if int(t.timer * 10) % 2 == 0 else (255, 60, 60)
                pygame.draw.rect(surface, alpha_color, r_rect, 1)
                pygame.draw.line(surface, (255, 100, 100), (rx, ry + 10), (rx + t.target_rect.width, ry + 10), 1)

            elif t.attack_type == "charge" and t.target_rect:
                rx, ry = camera.world_to_screen(t.target_rect.x, t.target_rect.y)
                r_rect = pygame.Rect(rx, ry, t.target_rect.width, t.target_rect.height)
                pygame.draw.rect(surface, (200, 120, 30), r_rect, 1)

        # 2. Render Greenkeeper Chassis
        sprite = (self.heavy_logical_sprites[self._heavy_pose()] if self.heavy_sprites is not None
                  else None)
        if sprite is not None:
            if self.heavy_sprites is not None and crt is not None:
                crt.composite_native(self.heavy_sprites[self._heavy_pose()], (sc_x, sc_y), (128, 96))
            else:
                surface.blit(sprite, (sc_x, sc_y))
            # Dynamic HUD targeting brackets over exposed weak point core
            if self.weak_point_rect and self.weak_point_exposed:
                wx, wy = camera.world_to_screen(self.weak_point_rect.x, self.weak_point_rect.y)
                reticle_col = config.COLOR_AMBER_1977 if int(self.vulnerability_timer * 8) % 2 == 0 else config.COLOR_EHMAN_RED
                # Corner aiming bracket marks
                pygame.draw.line(surface, reticle_col, (wx, wy), (wx + 4, wy), 1)
                pygame.draw.line(surface, reticle_col, (wx, wy), (wx, wy + 4), 1)
                pygame.draw.line(surface, reticle_col, (wx + self.weak_point_rect.width, wy), (wx + self.weak_point_rect.width - 4, wy), 1)
                pygame.draw.line(surface, reticle_col, (wx + self.weak_point_rect.width, wy), (wx + self.weak_point_rect.width, wy + 4), 1)
                pygame.draw.line(surface, reticle_col, (wx, wy + self.weak_point_rect.height), (wx + 4, wy + self.weak_point_rect.height), 1)
                pygame.draw.line(surface, reticle_col, (wx, wy + self.weak_point_rect.height), (wx, wy + self.weak_point_rect.height - 4), 1)
                pygame.draw.line(surface, reticle_col, (wx + self.weak_point_rect.width, wy + self.weak_point_rect.height), (wx + self.weak_point_rect.width - 4, wy + self.weak_point_rect.height), 1)
                pygame.draw.line(surface, reticle_col, (wx + self.weak_point_rect.width, wy + self.weak_point_rect.height), (wx + self.weak_point_rect.width, wy + self.weak_point_rect.height - 4), 1)
        else:
            # Fallback vector blockout
            # Tank treads (bottom 12px)
            tread_rect = pygame.Rect(sc_x, sc_y + 36, self.width, 12)
            pygame.draw.rect(surface, (18, 22, 26), tread_rect)
            pygame.draw.rect(surface, config.COLOR_CORE_STEEL, tread_rect, 1)
            for tx in range(sc_x + 4, sc_x + self.width - 4, 8):
                pygame.draw.rect(surface, (45, 55, 65), (tx, sc_y + 38, 4, 8))

            # Main armored chassis body
            body_rect = pygame.Rect(sc_x + 6, sc_y + 12, self.width - 6, 26)
            pygame.draw.rect(surface, (28, 36, 44), body_rect)
            pygame.draw.rect(surface, (55, 70, 85), body_rect, 1)

            # Heavy bulldozer excavator scoop on front (left side)
            scoop_points = [
                (sc_x, sc_y + 20),
                (sc_x + 12, sc_y + 20),
                (sc_x + 6, sc_y + 44),
                (sc_x - 4, sc_y + 44),
            ]
            pygame.draw.polygon(surface, (50, 60, 70), scoop_points)
            pygame.draw.polygon(surface, config.COLOR_FIBO_GOLD, scoop_points, 1)

            # Mortar turret housing on top (right side)
            turret_rect = pygame.Rect(sc_x + 24, sc_y + 2, 28, 14)
            pygame.draw.rect(surface, (22, 30, 38), turret_rect)
            pygame.draw.rect(surface, (60, 75, 90), turret_rect, 1)
            # Mortar cannon tube angled up and left
            pygame.draw.line(surface, config.COLOR_CORE_STEEL, (sc_x + 30, sc_y + 8), (sc_x + 18, sc_y - 4), 4)

            # 3. Render Weak Point Core (Reactor Housing)
            if self.weak_point_rect:
                wx, wy = camera.world_to_screen(self.weak_point_rect.x, self.weak_point_rect.y)
                w_rect = pygame.Rect(wx, wy, self.weak_point_rect.width, self.weak_point_rect.height)
                if self.weak_point_exposed:
                    # Open cooling vents - pulsing bright amber/red
                    core_color = config.COLOR_AMBER_1977 if int(self.vulnerability_timer * 8) % 2 == 0 else config.COLOR_EHMAN_RED
                    pygame.draw.rect(surface, core_color, w_rect)
                    pygame.draw.rect(surface, (255, 255, 200), w_rect, 2)
                    # Cross reticle
                    pygame.draw.line(surface, (255, 255, 255), (wx + 4, wy + 10), (wx + 20, wy + 10), 1)
                else:
                    # Armored cowl closed
                    pygame.draw.rect(surface, (36, 44, 52), w_rect)
                    pygame.draw.rect(surface, (20, 26, 32), w_rect, 1)

        # 4. Render Active Projectiles
        for p in self.projectiles:
            px, py = camera.world_to_screen(p.x, p.y)
            pygame.draw.circle(surface, p.color, (px, py), int(p.radius))
            pygame.draw.circle(surface, (255, 240, 200), (px, py), max(1, int(p.radius) - 3))

        # 5. Render Active Sweep Beam
        if self.sweep_active:
            sx, sy = camera.world_to_screen(self.sweep_x, self.sweep_y)
            # High intensity horizontal cutter beam
            pygame.draw.line(surface, (255, 80, 80), (sx - 40, sy), (sx + 40, sy), 5)
            pygame.draw.line(surface, (255, 255, 255), (sx - 30, sy), (sx + 30, sy), 2)
