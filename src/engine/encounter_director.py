"""PURPOSE: Finite, room-specific forward combat encounters in the existing Act I.
CALLED BY: video_game.engine.scenes.field.FieldScene.
HOW TO MODIFY: Author safe trigger and spawn coordinates in data/act_01_encounters.json.
"""
from dataclasses import replace
import json
import math
from pathlib import Path

import pygame

from video_game.engine.enemies import CoreEnforcer, CoreReconDrone, EnemyConfig, StaticHound
from video_game.engine.world import COLLISION_ONE_WAY, COLLISION_SOLID

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "act_01_encounters.json"
TYPES = {"drone": (CoreReconDrone, "core_recon_drone"),
         "hound": (StaticHound, "static_hound"),
         "captain": (CoreEnforcer, "core_enforcer")}
WARNING_SECONDS = 0.6
MIN_DISTANCE = 64


class ForwardEncounter:
    """One visit's monotonic triggers and pending arrivals; no campaign state is stored."""

    def __init__(self, room, manager, assisted=False, data_path=DATA_PATH):
        self.room = room
        self.manager = manager
        self.assisted = assisted
        self.configs = {kind: EnemyConfig.load(cfg_id) for kind, (_, cfg_id) in TYPES.items()}
        self.entries = self._load(data_path)
        # Cache a bounded set of safe sites further along the same route. This
        # lets a delayed arrival catch up without ever appearing behind Mateo.
        self.sites = {}
        for item in self.entries:
            candidates = []
            for offset in range(0, 8 * 64, 64):
                candidate = dict(item, x=item["x"] + offset)
                if self._safe(candidate):
                    candidates.append(candidate)
            self.sites[item["id"]] = candidates
        self.next_trigger = 0
        self.pending = []
        self.warning = None
        self.warning_entry = None
        self.warning_time = 0.0
        self.arrival_delay = 0.0
        self.high_water = -1.0
        self.retired_ids = set()
        self.retired_last_update = 0

    def _load(self, path):
        # Reject an entire invalid room definition; unknown rooms safely remain empty.
        try:
            data = json.loads(Path(path).read_text())
            if data.get("schema_version") != 1 or not isinstance(data["rooms"], dict):
                return []
            entries = data["rooms"].get(self.room.room_id, [])
            if isinstance(entries, dict):
                entries = entries.get("encounters", [])
            if not isinstance(entries, list) or len(entries) > 32:
                return []
            seen = set()
            previous = -1
            for item in entries:
                if not isinstance(item, dict) or item.get("type") not in TYPES:
                    return []
                ident = item.get("id")
                if not isinstance(ident, str) or not ident or ident in seen:
                    return []
                seen.add(ident)
                values = [item.get(k) for k in ("trigger_x", "x", "y")]
                if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
                    return []
                trigger, x, y = values
                if trigger < previous or trigger < 0 or trigger >= self.room.width_px or x - trigger < MIN_DISTANCE:
                    return []
                if not (0 <= x < self.room.width_px and 0 <= y < self.room.height_px):
                    return []
                previous = trigger
                if not self._safe(item):
                    return []
            return entries
        except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
            return []

    def _safe(self, item):
        _, cfg_id = TYPES[item["type"]]
        cfg = self.configs[item["type"]]
        rect = pygame.Rect(item["x"], item["y"], cfg.width, cfg.height)
        # Hover bob and a small stationary patrol require clear surroundings.
        clearance = rect.inflate(16, 12 if item["type"] == "drone" else 0)
        if not pygame.Rect(0, 0, self.room.width_px, self.room.height_px).contains(clearance):
            return False
        collision = self.room.check_rect_collision(clearance)
        if collision["solid"] or collision["hazard"] or collision["one_way"]:
            return False
        if item["type"] != "drone":
            floor_y = rect.bottom
            if floor_y % self.room.tile_size:
                return False
            for col in range(clearance.left // self.room.tile_size, (clearance.right - 1) // self.room.tile_size + 1):
                if self.room.get_tile(col, floor_y // self.room.tile_size) not in (COLLISION_SOLID, COLLISION_ONE_WAY):
                    return False
        return True

    def _available(self, item, player):
        cls, cfg_id = TYPES[item["type"]]
        cfg = self.configs[item["type"]]
        rect = pygame.Rect(item["x"], item["y"], cfg.width, cfg.height)
        if rect.left - player.rect.right < MIN_DISTANCE:
            return False
        return not any(not enemy.is_dead and rect.inflate(48, 48).colliderect(enemy.rect)
                       for enemy in self.manager.enemies)

    def update(self, dt, player, paused=False, camera=None):
        self.retired_last_update = 0
        if paused or dt <= 0 or player.is_dead:
            return
        if camera is not None:
            # A bypassed living enemy that has left the screen behind the player
            # retreats once for this visit. Pending arrivals are never discarded.
            retired = {enemy.target_id for enemy in self.manager.enemies
                       if not enemy.is_dead and enemy.rect.right < camera.x - 32
                       and enemy.rect.right < player.rect.left - 160}
            if retired:
                self.retired_ids.update(retired)
                self.retired_last_update = len(retired)
                self.manager.enemies[:] = [enemy for enemy in self.manager.enemies
                                           if enemy.target_id not in retired]
                self.manager.projectiles[:] = [p for p in self.manager.projectiles
                                               if p.source_id not in retired]
        self.high_water = max(self.high_water, player.rect.centerx)
        # Hard upper bound: the entire data definition is at most 32 entries.
        while self.next_trigger < len(self.entries) and self.entries[self.next_trigger]["trigger_x"] <= self.high_water:
            self.pending.append(self.entries[self.next_trigger])
            self.next_trigger += 1
        if self.arrival_delay > 0:
            self.arrival_delay = max(0.0, self.arrival_delay - dt)
            return
        alive = sum(not enemy.is_dead for enemy in self.manager.enemies)
        if alive >= (5 if self.assisted else 4):
            self.warning = None
            self.warning_entry = None
            self.warning_time = 0.0
            return
        if self.warning is None:
            # A blocked earlier arrival cannot prevent a later safe one from appearing.
            for item in self.pending:
                candidate = next((site for site in self.sites[item["id"]]
                                  if site["x"] - player.rect.right >= MIN_DISTANCE + 84
                                  and self._available(site, player)), None)
                if candidate is not None:
                    self.warning_entry = item
                    self.warning = candidate
                    break
            self.warning_time = 0.0
        if self.warning is None:
            return
        if not self._available(self.warning, player):
            self.warning = None
            self.warning_entry = None
            self.warning_time = 0.0
            return
        self.warning_time += min(dt, 0.1)
        if self.warning_time < WARNING_SECONDS:
            return
        item = self.warning
        cls, cfg_id = TYPES[item["type"]]
        cfg = self.configs[item["type"]]
        if self.assisted:
            cfg = replace(cfg, max_health={"drone": 25, "hound": 25, "captain": 30}[item["type"]])
        elif item["type"] == "captain":
            cfg = replace(cfg, max_health=80)
        if item["type"] == "captain":
            cfg = replace(cfg, windup_time=1.2, lock_window=0.35)
        enemy = cls(item["id"], item["x"], item["y"], cfg=cfg,
                    patrol_left=item["x"] - 8, patrol_right=item["x"] + 8)
        self.manager.add_enemy(enemy)
        self.pending.remove(self.warning_entry)
        self.warning = None
        self.warning_entry = None
        self.warning_time = 0.0
        self.arrival_delay = 0.35 if self.assisted else 0.0
        return enemy

    def render(self, crt, camera):
        if self.warning is None:
            return
        item = self.warning
        cfg = self.configs[item["type"]]
        x, y = camera.world_to_screen(item["x"], item["y"])
        rect = pygame.Rect(int(x) - 3, int(y) - 3, cfg.width + 6, cfg.height + 6)
        pygame.draw.rect(crt.canvas, (255, 190, 65), rect, 1)
        pygame.draw.line(crt.canvas, (255, 190, 65), rect.topleft, rect.bottomright, 1)
        pygame.draw.line(crt.canvas, (255, 190, 65), rect.topright, rect.bottomleft, 1)
        crt.draw_text("INCOMING", int(x) - 4, int(y) - 16,
                      color=(255, 190, 65), size="sm")
