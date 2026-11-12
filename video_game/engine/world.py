"""
MODULE: video_game/engine/world.py
PURPOSE: Room loading, schema validation, multi-layer tile/collision maps, camera tracking, and exit/checkpoint triggers.
CALLED BY: video_game.engine.scenes.field, video_game.tools.validate_content, video_game.tests.test_world.
HOW TO MODIFY: Extend collision categories or level object types; maintain zero wildcard imports.
"""

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pygame

# Collision Tile Categories
COLLISION_EMPTY = 0
COLLISION_SOLID = 1
COLLISION_ONE_WAY = 2
COLLISION_HAZARD = 3
COLLISION_COVER = 4

COLLISION_NAMES = {
    COLLISION_EMPTY: "EMPTY",
    COLLISION_SOLID: "SOLID",
    COLLISION_ONE_WAY: "ONE_WAY",
    COLLISION_HAZARD: "HAZARD",
    COLLISION_COVER: "COVER",
}

ENV_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "environments" / "ohio"
_ENV_CACHE: Dict[str, Optional[pygame.Surface]] = {}
_TILE_RECTS = [[pygame.Rect(col * 16, row * 16, 16, 16) for row in range(8)] for col in range(16)]
_AIRLOCK_LABEL_SURF: Optional[pygame.Surface] = None


def get_airlock_label_surf() -> pygame.Surface:
    """Return cached surface for exit airlock text banner."""
    global _AIRLOCK_LABEL_SURF
    if _AIRLOCK_LABEL_SURF is None:
        font = pygame.font.Font(None, 12)
        _AIRLOCK_LABEL_SURF = font.render("AIRLOCK", True, (60, 180, 120))
    return _AIRLOCK_LABEL_SURF


def preload_env_assets():
    """Warm up all environment textures into memory to prevent first-frame render stalls."""
    for asset_name in (
        "tileset_ohio_16x16.png",
        "bg_ohio_sky_twilight.png",
        "bg_ohio_treeline_fence.png",
        "bg_ohio_dish_lattice.png",
        "weather_ohio_mist.png",
    ):
        get_env_asset(asset_name)


def get_env_asset(name: str) -> Optional[pygame.Surface]:
    """Retrieve or load a cached environment texture; returns None if unavailable or display uninitialized."""
    if name in _ENV_CACHE:
        return _ENV_CACHE[name]
    if not pygame.display.get_init() or pygame.display.get_surface() is None:
        return None
    file_path = ENV_ASSETS_DIR / name
    if not file_path.exists():
        _ENV_CACHE[name] = None
        return None
    try:
        surf = pygame.image.load(str(file_path)).convert_alpha()
        _ENV_CACHE[name] = surf
        return surf
    except Exception:
        _ENV_CACHE[name] = None
        return None


@dataclass
class SpawnPoint:
    name: str
    x: float
    y: float
    facing: str = "right"


@dataclass
class RoomExit:
    id: str
    x: float
    y: float
    width: float
    height: float
    target_room: str
    target_spawn: str
    label: str = ""

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))


@dataclass
class RoomCheckpoint:
    id: str
    x: float
    y: float
    name: str = ""

    @property
    def rect(self) -> pygame.Rect:
        # Checkpoint radius / detection zone
        return pygame.Rect(int(self.x) - 16, int(self.y) - 32, 48, 48)


@dataclass
class RoomObject:
    id: str
    type: str
    x: float
    y: float
    width: float
    height: float
    properties: Dict[str, Any] = field(default_factory=dict)
    timeline: str = "all"

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    def is_active_in_timeline(self, timeline_id: str) -> bool:
        """Return True if this object exists in the given timeline."""
        if self.timeline in ("all", "both", "*"):
            return True
        return self.timeline == timeline_id


class Camera:
    """
    2D side-scrolling camera with smooth target tracking and world bounds clamping.
    Maintains a 480x270 viewport and handles coordinate transforms with pixel precision.
    """

    def __init__(self, viewport_w: int = 480, viewport_h: int = 270):
        self.viewport_w: int = viewport_w
        self.viewport_h: int = viewport_h
        self.x: float = 0.0
        self.y: float = 0.0
        self.world_w: int = viewport_w
        self.world_h: int = viewport_h

    def set_world_bounds(self, world_w: int, world_h: int):
        """Configure world boundaries in pixels."""
        self.world_w = max(self.viewport_w, world_w)
        self.world_h = max(self.viewport_h, world_h)
        self._clamp()

    def snap_to(self, target_x: float, target_y: float):
        """Snap camera center immediately onto world coordinates."""
        self.x = target_x - self.viewport_w / 2.0
        self.y = target_y - self.viewport_h / 2.0
        self._clamp()

    def update(self, target_x: float, target_y: float, smoothing: float = 0.15):
        """Smoothly track target coordinates towards center of viewport."""
        desired_x = target_x - self.viewport_w / 2.0
        desired_y = target_y - self.viewport_h / 2.0
        self.x += (desired_x - self.x) * smoothing
        self.y += (desired_y - self.y) * smoothing
        self._clamp()

    def _clamp(self):
        """Clamp camera coordinates strictly within world boundary limits."""
        max_x = max(0.0, float(self.world_w - self.viewport_w))
        max_y = max(0.0, float(self.world_h - self.viewport_h))
        self.x = max(0.0, min(self.x, max_x))
        self.y = max(0.0, min(self.y, max_y))

    def world_to_screen(self, wx: float, wy: float) -> Tuple[int, int]:
        """Convert world coordinates into viewport screen space."""
        return int(round(wx - self.x)), int(round(wy - self.y))

    def screen_to_world(self, sx: int, sy: int) -> Tuple[float, float]:
        """Convert viewport screen space back into world coordinates."""
        return float(sx) + self.x, float(sy) + self.y

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.viewport_w, self.viewport_h)

    def get_visible_tile_range(self, tile_size: int = 16) -> Tuple[int, int, int, int]:
        """Calculate visible tile indices (min_col, max_col, min_row, max_row) including partial tiles."""
        min_col = max(0, int(self.x // tile_size))
        max_col = min(self.world_w // tile_size, int((self.x + self.viewport_w + tile_size - 1) // tile_size))
        min_row = max(0, int(self.y // tile_size))
        max_row = min(self.world_h // tile_size, int((self.y + self.viewport_h + tile_size - 1) // tile_size))
        return min_col, max_col, min_row, max_row


class Room:
    """
    Playable 2D tile-grid room with collision maps, spawns, exits, and parallax backgrounds.
    """

    def __init__(self, data: Dict[str, Any]):
        self.raw_data: Dict[str, Any] = data
        self.schema_version: int = data.get("schema_version", 1)
        self.room_id: str = data.get("room_id", "")
        self.act_id: str = data.get("act_id", "")
        self.title: str = data.get("title", "")
        self.tile_size: int = data.get("tile_size", 16)
        self.width_tiles: int = data.get("width_tiles", 30)
        self.height_tiles: int = data.get("height_tiles", 18)
        self.tileset_id: str = data.get("tileset_id", "bunker_tileset")

        self.width_px: int = self.width_tiles * self.tile_size
        self.height_px: int = self.height_tiles * self.tile_size

        # Multi-timeline collision layers support
        self.timeline_collision_layers: Dict[str, List[List[int]]] = {}
        default_grid = data.get("collision_layers", [])
        self.timeline_collision_layers["2029_CORE"] = default_grid

        # Additional or explicit timeline collision layers
        t_layers = data.get("timeline_collision_layers", {})
        for t_id, grid in t_layers.items():
            self.timeline_collision_layers[t_id] = grid

        self.active_timeline: str = data.get("default_timeline", "2029_CORE")
        if self.active_timeline in self.timeline_collision_layers:
            self.collision_grid = self.timeline_collision_layers[self.active_timeline]
        else:
            self.collision_grid = default_grid

        self.background_layers: List[Dict[str, Any]] = data.get("background_layers", [])

        # Parse spawns
        self.spawns: Dict[str, SpawnPoint] = {}
        for s_name, s_info in data.get("spawns", {}).items():
            self.spawns[s_name] = SpawnPoint(
                name=s_name,
                x=float(s_info.get("x", 0.0)),
                y=float(s_info.get("y", 0.0)),
                facing=str(s_info.get("facing", "right")),
            )

        # Parse exits
        self.exits: List[RoomExit] = []
        for e_info in data.get("exits", []):
            self.exits.append(RoomExit(
                id=str(e_info.get("id", "")),
                x=float(e_info.get("x", 0.0)),
                y=float(e_info.get("y", 0.0)),
                width=float(e_info.get("width", 32.0)),
                height=float(e_info.get("height", 48.0)),
                target_room=str(e_info.get("target_room", "")),
                target_spawn=str(e_info.get("target_spawn", "")),
                label=str(e_info.get("label", "")),
            ))

        # Parse checkpoints
        self.checkpoints: List[RoomCheckpoint] = []
        for c_info in data.get("checkpoints", []):
            self.checkpoints.append(RoomCheckpoint(
                id=str(c_info.get("id", "")),
                x=float(c_info.get("x", 0.0)),
                y=float(c_info.get("y", 0.0)),
                name=str(c_info.get("name", "")),
            ))

        # Parse objects
        self.objects: List[RoomObject] = []
        for o_info in data.get("objects", []):
            o_timeline = str(o_info.get("timeline", o_info.get("properties", {}).get("timeline", "all")))
            self.objects.append(RoomObject(
                id=str(o_info.get("id", "")),
                type=str(o_info.get("type", "prop")),
                x=float(o_info.get("x", 0.0)),
                y=float(o_info.get("y", 0.0)),
                width=float(o_info.get("width", 16.0)),
                height=float(o_info.get("height", 16.0)),
                properties=dict(o_info.get("properties", {})),
                timeline=o_timeline,
            ))

    @classmethod
    def load_from_file(cls, path: Path) -> "Room":
        """Load room from a JSON level file."""
        if not path.exists():
            raise FileNotFoundError(f"Room level file not found: {path}")
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON in level file {path}: {exc}") from exc
        return cls(content)

    def validate(self, campaign_data: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Validate room data integrity against DATA_CONTRACTS.md.
        Returns a list of actionable error strings (empty if valid).
        """
        errors = []

        if self.schema_version != 1:
            errors.append(f"Invalid schema_version {self.schema_version}; expected 1")
        if not self.room_id:
            errors.append("Missing required field 'room_id'")
        if not self.act_id:
            errors.append("Missing required field 'act_id'")
        if self.tile_size != 16:
            errors.append(f"Invalid tile_size {self.tile_size}; must be 16")
        if self.width_tiles <= 0 or self.height_tiles <= 0:
            errors.append(f"Invalid room tile dimensions {self.width_tiles}x{self.height_tiles}")

        # Check collision grid dimensions
        if len(self.collision_grid) != self.height_tiles:
            errors.append(f"Collision grid rows ({len(self.collision_grid)}) != height_tiles ({self.height_tiles})")
        for r_idx, row in enumerate(self.collision_grid):
            if len(row) != self.width_tiles:
                errors.append(f"Collision row {r_idx} length ({len(row)}) != width_tiles ({self.width_tiles})")
            for c_idx, tile_val in enumerate(row):
                if tile_val not in COLLISION_NAMES:
                    errors.append(f"Unknown collision code {tile_val} at row {r_idx}, col {c_idx}")

        # Check additional timeline collision layers
        for t_id, t_grid in self.timeline_collision_layers.items():
            if t_id == "2029_CORE":
                continue
            if len(t_grid) != self.height_tiles:
                errors.append(f"Timeline '{t_id}' collision rows ({len(t_grid)}) != height_tiles ({self.height_tiles})")
            for r_idx, row in enumerate(t_grid):
                if len(row) != self.width_tiles:
                    errors.append(f"Timeline '{t_id}' collision row {r_idx} length ({len(row)}) != width_tiles ({self.width_tiles})")
                for c_idx, tile_val in enumerate(row):
                    if tile_val not in COLLISION_NAMES:
                        errors.append(f"Timeline '{t_id}' unknown collision code {tile_val} at row {r_idx}, col {c_idx}")

        # Check that player spawn points exist and are collision-free
        if not self.spawns:
            errors.append("Room defines no spawn points")
        for s_name, sp in self.spawns.items():
            # Check player footprint (16x32 standard collision box)
            player_rect = pygame.Rect(int(sp.x), int(sp.y), 16, 32)
            col_info = self.check_rect_collision(player_rect)
            if col_info["solid"]:
                errors.append(f"Spawn '{s_name}' ({sp.x}, {sp.y}) overlaps SOLID collision geometry")
            if col_info["hazard"]:
                errors.append(f"Spawn '{s_name}' ({sp.x}, {sp.y}) overlaps HAZARD collision geometry")

        # Check exits
        for exit_item in self.exits:
            if not exit_item.target_room:
                errors.append(f"Exit '{exit_item.id}' missing target_room")
            if not exit_item.target_spawn:
                errors.append(f"Exit '{exit_item.id}' missing target_spawn")

        # Validate against campaign registry if provided
        if campaign_data is not None:
            rooms_reg = campaign_data.get("rooms", {})
            if self.room_id not in rooms_reg:
                errors.append(f"Room '{self.room_id}' not registered in campaign.json")
            else:
                registered_checkpoints = set(rooms_reg[self.room_id].get("checkpoints", []))
                for chk in self.checkpoints:
                    if chk.id not in registered_checkpoints:
                        errors.append(f"Checkpoint '{chk.id}' not registered for room '{self.room_id}' in campaign.json")

        return errors

    def set_active_timeline(self, timeline_id: str) -> bool:
        """Switch active collision grid and timeline. Returns True if timeline exists."""
        if timeline_id in self.timeline_collision_layers:
            self.active_timeline = timeline_id
            self.collision_grid = self.timeline_collision_layers[timeline_id]
            return True
        return False

    def get_tile_in_timeline(self, col: int, row: int, timeline_id: Optional[str] = None) -> int:
        """Get collision tile code at (col, row) in specified timeline (or active if None)."""
        t_id = timeline_id or self.active_timeline
        grid = self.timeline_collision_layers.get(t_id, self.collision_grid)
        if 0 <= row < len(grid) and 0 <= col < len(grid[row]):
            return grid[row][col]
        return COLLISION_SOLID

    def check_rect_collision_in_timeline(self, rect: pygame.Rect, timeline_id: Optional[str] = None) -> Dict[str, Any]:
        """Check collision between a bounding rectangle and a specific timeline tile map."""
        t_id = timeline_id or self.active_timeline
        grid = self.timeline_collision_layers.get(t_id, self.collision_grid)
        min_col = int(rect.left // self.tile_size)
        max_col = int(rect.right // self.tile_size)
        min_row = int(rect.top // self.tile_size)
        max_row = int(rect.bottom // self.tile_size)

        result = {
            "solid": False,
            "one_way": False,
            "hazard": False,
            "cover": False,
            "tiles": []
        }

        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                if 0 <= r < len(grid) and 0 <= c < len(grid[r]):
                    code = grid[r][c]
                else:
                    code = COLLISION_SOLID

                if code != COLLISION_EMPTY:
                    tile_rect = pygame.Rect(c * self.tile_size, r * self.tile_size, self.tile_size, self.tile_size)
                    if rect.colliderect(tile_rect):
                        result["tiles"].append((c, r, code))
                        if code == COLLISION_SOLID:
                            result["solid"] = True
                        elif code == COLLISION_ONE_WAY:
                            result["one_way"] = True
                        elif code == COLLISION_HAZARD:
                            result["hazard"] = True
                        elif code == COLLISION_COVER:
                            result["cover"] = True

        return result

    def get_objects_for_timeline(self, timeline_id: Optional[str] = None) -> List[RoomObject]:
        """Return list of objects active in the given timeline (defaults to active timeline)."""
        t_id = timeline_id or self.active_timeline
        return [obj for obj in self.objects if obj.is_active_in_timeline(t_id)]

    def get_nearest_grapple_anchor(self, px: float, py: float, max_range: float = 160.0) -> Optional[RoomObject]:
        """Find closest grapple anchor object active in current timeline within maximum range."""
        best_obj = None
        best_dist = max_range
        for obj in self.get_objects_for_timeline():
            if obj.type in ("grapple_anchor", "magnetic_anchor"):
                ax = obj.x + obj.width / 2.0
                ay = obj.y + obj.height / 2.0
                dist = math.hypot(ax - px, ay - py)
                if dist <= best_dist:
                    best_dist = dist
                    best_obj = obj
        return best_obj

    def get_tile(self, col: int, row: int) -> int:
        """Get collision tile code at (col, row). Out-of-bounds returns SOLID."""
        if 0 <= row < len(self.collision_grid) and 0 <= col < len(self.collision_grid[row]):
            return self.collision_grid[row][col]
        return COLLISION_SOLID

    def get_collision_at_pixel(self, x: float, y: float) -> int:
        """Get collision tile code at world pixel coordinates."""
        col = int(x // self.tile_size)
        row = int(y // self.tile_size)
        return self.get_tile(col, row)

    def check_rect_collision(self, rect: pygame.Rect) -> Dict[str, Any]:
        """
        Check collision between a bounding rectangle and the room tile map.
        Returns dict with collision flags and overlapping tiles.
        """
        min_col = int(rect.left // self.tile_size)
        max_col = int(rect.right // self.tile_size)
        min_row = int(rect.top // self.tile_size)
        max_row = int(rect.bottom // self.tile_size)

        result = {
            "solid": False,
            "one_way": False,
            "hazard": False,
            "cover": False,
            "tiles": []
        }

        for r in range(min_row, max_row + 1):
            for c in range(min_col, max_col + 1):
                code = self.get_tile(c, r)
                if code != COLLISION_EMPTY:
                    tile_rect = pygame.Rect(c * self.tile_size, r * self.tile_size, self.tile_size, self.tile_size)
                    if rect.colliderect(tile_rect):
                        result["tiles"].append((c, r, code))
                        if code == COLLISION_SOLID:
                            result["solid"] = True
                        elif code == COLLISION_ONE_WAY:
                            result["one_way"] = True
                        elif code == COLLISION_HAZARD:
                            result["hazard"] = True
                        elif code == COLLISION_COVER:
                            result["cover"] = True

        return result

    def check_exit_trigger(self, player_rect: pygame.Rect) -> Optional[RoomExit]:
        """Return the first room exit triggered by player bounding box."""
        for ex in self.exits:
            if player_rect.colliderect(ex.rect):
                return ex
        return None

    def check_checkpoint_trigger(self, player_rect: pygame.Rect) -> Optional[RoomCheckpoint]:
        """Return the first checkpoint triggered by player bounding box."""
        for chk in self.checkpoints:
            if player_rect.colliderect(chk.rect):
                return chk
        return None

    def get_cover_at(self, rect: pygame.Rect) -> Optional[Dict[str, Any]]:
        """
        Query cover availability intersecting or immediately adjacent to rect.
        Returns dict with cover_type ('low' or 'background'), protection_directions, and rect, or None.
        """
        query_rect = rect.inflate(16, 0)

        # 1. Check cover objects (background doorway / recess or low barriers)
        for obj in self.objects:
            if obj.type == "cover" and query_rect.colliderect(obj.rect):
                props = obj.properties
                return {
                    "id": obj.id,
                    "cover_type": props.get("cover_type", "low"),
                    "protection_directions": props.get("protection_directions", ["left", "right"]),
                    "rect": obj.rect,
                }

        # 2. Check COLLISION_COVER tiles (low foreground cover)
        col = self.check_rect_collision(query_rect)
        if col["cover"]:
            cover_cols = [c for c, r, code in col["tiles"] if code == COLLISION_COVER]
            if cover_cols:
                min_c = min(cover_cols)
                max_c = max(cover_cols)
                cover_x = min_c * self.tile_size
                dirs = ["right"] if cover_x >= rect.centerx else ["left"]
                return {
                    "id": f"cover_tile_{min_c}",
                    "cover_type": "low",
                    "protection_directions": dirs,
                    "rect": pygame.Rect(min_c * self.tile_size, 0, (max_c - min_c + 1) * self.tile_size, self.height_px),
                }

        return None

    def check_attack_protection(
        self,
        target_rect: pygame.Rect,
        attack_direction: str,
        is_crouching: bool = False,
        in_background_cover: bool = False,
    ) -> bool:
        """
        Determine if an attack from attack_direction ('left', 'right', 'above') is blocked by cover.
        - Low cover blocks if player is crouching/sliding and attack matches cover direction.
        - Background doorway cover blocks horizontal attacks if player is concealed.
        """
        cover = self.get_cover_at(target_rect)
        if not cover:
            return False

        c_type = cover.get("cover_type", "low")
        prot_dirs = cover.get("protection_directions", [])

        if c_type == "background":
            return in_background_cover and attack_direction in ("left", "right")

        if c_type == "low":
            if not is_crouching:
                return False
            return attack_direction in prot_dirs or "both" in prot_dirs

        return False

    def render_background(self, surface: pygame.Surface, camera: Camera):
        """Render multi-layer parallax background."""
        sky = get_env_asset("bg_ohio_sky_twilight.png")
        fence = get_env_asset("bg_ohio_treeline_fence.png")
        dish = get_env_asset("bg_ohio_dish_lattice.png")

        if sky is not None and fence is not None and dish is not None:
            surf_w = surface.get_width()

            # Layer 1: Distant Ohio twilight sky with blinking radio beacons (ratio 0.10, 0.05)
            sky_w = sky.get_width()
            sky_x = -int(camera.x * 0.10) % sky_w
            sky_y = -int(camera.y * 0.05)
            surface.blit(sky, (sky_x - sky_w, sky_y))
            surface.blit(sky, (sky_x, sky_y))
            if sky_x + sky_w < surf_w:
                surface.blit(sky, (sky_x + sky_w, sky_y))

            # Layer 2: Midground security perimeter chainlink fence and treeline (ratio 0.35, 0.15)
            fence_w = fence.get_width()
            fence_x = -int(camera.x * 0.35) % fence_w
            fence_y = -int(camera.y * 0.15)
            surface.blit(fence, (fence_x - fence_w, fence_y))
            surface.blit(fence, (fence_x, fence_y))
            if fence_x + fence_w < surf_w:
                surface.blit(fence, (fence_x + fence_w, fence_y))

            # Layer 3: Near-background Ohio Big Ear dish lattice space-frame (ratio 0.65, 0.25)
            dish_w = dish.get_width()
            dish_x = -int(camera.x * 0.65) % dish_w
            dish_y = -int(camera.y * 0.25)
            surface.blit(dish, (dish_x - dish_w, dish_y))
            surface.blit(dish, (dish_x, dish_y))
            if dish_x + dish_w < surf_w:
                surface.blit(dish, (dish_x + dish_w, dish_y))
        else:
            # Procedural fallback
            surface.fill((10, 16, 24))
            sky_offset_x = int(camera.x * 0.15)
            tower_x = (240 - sky_offset_x) % 600 - 60
            tower_color = (14, 22, 32)
            pygame.draw.line(surface, tower_color, (tower_x, 30), (tower_x, 240), 2)
            pygame.draw.line(surface, tower_color, (tower_x - 14, 240), (tower_x + 14, 240), 2)
            pygame.draw.line(surface, tower_color, (tower_x - 8, 120), (tower_x + 8, 120), 1)
            pygame.draw.line(surface, tower_color, (tower_x - 12, 180), (tower_x + 12, 180), 1)

            fence_offset_x = int(camera.x * 0.45)
            wall_y = 210 - int(camera.y * 0.25)
            pygame.draw.rect(surface, (16, 26, 22), (0, wall_y, surface.get_width(), surface.get_height() - wall_y))
            for fx in range(- (fence_offset_x % 24), surface.get_width() + 24, 24):
                pygame.draw.line(surface, (20, 36, 30), (fx, wall_y - 28), (fx, wall_y), 1)
                pygame.draw.line(surface, (20, 36, 30), (fx, wall_y - 28), (fx + 24, wall_y), 1)

    def render_tiles(self, surface: pygame.Surface, camera: Camera, tileset_surf: Optional[pygame.Surface] = None):
        """
        Render visible collision tiles and blocks.
        Supports modular 16x16 pixel-art tiles from tileset_ohio_16x16.png
        with contextual edge selection, autotiling, and clean procedural fallback.
        """
        ts = tileset_surf or get_env_asset("tileset_ohio_16x16.png")
        min_col, max_col, min_row, max_row = camera.get_visible_tile_range(self.tile_size)

        for r in range(min_row, max_row):
            for c in range(min_col, max_col):
                tile_code = self.get_tile(c, r)
                if tile_code == COLLISION_EMPTY:
                    continue

                world_x = c * self.tile_size
                world_y = r * self.tile_size
                screen_x, screen_y = camera.world_to_screen(world_x, world_y)

                # Skip if completely outside screen rect
                if screen_x + self.tile_size <= 0 or screen_x >= surface.get_width():
                    continue
                if screen_y + self.tile_size <= 0 or screen_y >= surface.get_height():
                    continue

                if ts is not None:
                    # Modular pixel art tile blitting
                    top_code = self.get_tile(c, r - 1)
                    left_code = self.get_tile(c - 1, r)
                    right_code = self.get_tile(c + 1, r)

                    src_col = 0
                    src_row = 0

                    if tile_code == COLLISION_SOLID:
                        # Solid concrete or terrain
                        is_surface = (top_code == COLLISION_EMPTY)
                        if is_surface:
                            if left_code == COLLISION_EMPTY and right_code == COLLISION_SOLID:
                                src_col, src_row = 4, 0  # Top-left corner
                            elif right_code == COLLISION_EMPTY and left_code == COLLISION_SOLID:
                                src_col, src_row = 5, 0  # Top-right corner
                            elif (c + r) % 3 == 0 and "approach" in self.room_id:
                                src_col, src_row = 1, 1  # Autumn grass cap
                            else:
                                src_col, src_row = 1, 0  # Concrete beveled surface
                        else:
                            # Interior fill
                            if (c * 3 + r) % 7 == 0:
                                src_col, src_row = 6, 0  # Cracked rebar
                            elif (c + r * 2) % 5 == 0:
                                src_col, src_row = 7, 0  # Drainage groove
                            else:
                                src_col, src_row = 0, 0  # Interior concrete

                    elif tile_code == COLLISION_ONE_WAY:
                        if "salvage" in self.room_id:
                            src_col, src_row = 0, 3  # Corrugated scrap metal
                        else:
                            # Catwalk grating
                            if left_code == COLLISION_EMPTY and right_code == COLLISION_ONE_WAY:
                                src_col, src_row = 1, 2  # Catwalk stanchion left
                            elif right_code == COLLISION_EMPTY and left_code == COLLISION_ONE_WAY:
                                src_col, src_row = 2, 2  # Catwalk stanchion right
                            else:
                                src_col, src_row = 0, 2  # Catwalk steel grating

                    elif tile_code == COLLISION_HAZARD:
                        # Sump pit
                        if top_code == COLLISION_EMPTY or top_code != COLLISION_HAZARD:
                            src_col, src_row = (2, 4) if (c % 2 == 0) else (0, 4)  # Spark / liquid surface
                        else:
                            src_col, src_row = 1, 4  # Deep liquid

                    elif tile_code == COLLISION_COVER:
                        if (c % 3 == 0):
                            src_col, src_row = 1, 5  # Equipment crate
                        else:
                            src_col, src_row = 0, 5  # Sandbag barrier

                    src_rect = _TILE_RECTS[src_col][src_row] if (0 <= src_col < 16 and 0 <= src_row < 8) else (src_col * 16, src_row * 16, 16, 16)
                    surface.blit(ts, (screen_x, screen_y), src_rect)

                else:
                    if tile_code == COLLISION_SOLID:
                        # Solid concrete / bedrock block
                        pygame.draw.rect(surface, (28, 38, 34), (screen_x, screen_y, self.tile_size, self.tile_size))
                        pygame.draw.rect(surface, (40, 56, 48), (screen_x, screen_y, self.tile_size, self.tile_size), 1)
                        if (c + r) % 2 == 0:
                            pygame.draw.line(surface, (34, 46, 40), (screen_x + 2, screen_y + 2), (screen_x + 13, screen_y + 13), 1)

                    elif tile_code == COLLISION_ONE_WAY:
                        # Catwalk steel grating (top surface solid, passable from below)
                        pygame.draw.line(surface, (60, 96, 76), (screen_x, screen_y), (screen_x + self.tile_size - 1, screen_y), 2)
                        pygame.draw.rect(surface, (22, 42, 34), (screen_x, screen_y + 2, self.tile_size, 4))
                        for gx in range(screen_x + 2, screen_x + self.tile_size, 4):
                            pygame.draw.line(surface, (44, 72, 58), (gx, screen_y + 2), (gx, screen_y + 5), 1)

                    elif tile_code == COLLISION_HAZARD:
                        # Sump pit electrical hazard / sparks
                        pygame.draw.rect(surface, (42, 14, 14), (screen_x, screen_y, self.tile_size, self.tile_size))
                        pygame.draw.line(surface, (180, 42, 36), (screen_x + 2, screen_y + 8), (screen_x + 7, screen_y + 2), 2)
                        pygame.draw.line(surface, (220, 80, 60), (screen_x + 7, screen_y + 2), (screen_x + 13, screen_y + 12), 2)

                    elif tile_code == COLLISION_COVER:
                        # Low sandbag / crate barrier
                        pygame.draw.rect(surface, (54, 48, 32), (screen_x + 1, screen_y + 6, self.tile_size - 2, 10))
                        pygame.draw.rect(surface, (84, 76, 48), (screen_x + 1, screen_y + 6, self.tile_size - 2, 10), 1)
                        pygame.draw.line(surface, (120, 110, 70), (screen_x + 3, screen_y + 8), (screen_x + self.tile_size - 4, screen_y + 8), 1)

    def render_weather(self, surface: pygame.Surface, camera: Camera, anim_time: float = 0.0):
        """Render atmospheric autumn weather mist overlay."""
        mist = get_env_asset("weather_ohio_mist.png")
        if mist is not None:
            mist_w = mist.get_width()
            mist_x = -int(camera.x * 0.85 + anim_time * 16.0) % mist_w
            surface.blit(mist, (mist_x - mist_w, 0))
            surface.blit(mist, (mist_x, 0))
            if mist_x + mist_w < surface.get_width():
                surface.blit(mist, (mist_x + mist_w, 0))

    def render_objects(self, surface: pygame.Surface, camera: Camera):
        """Render level props, terminals, airlock doors, and antenna masts."""
        ts = get_env_asset("tileset_ohio_16x16.png")

        for obj in self.objects:
            if not obj.is_active_in_timeline(self.active_timeline):
                continue
            screen_x, screen_y = camera.world_to_screen(obj.x, obj.y)
            obj_rect = pygame.Rect(screen_x, screen_y, int(obj.width), int(obj.height))

            if obj.type == "terminal":
                # Airlock console
                if ts is not None and obj.width == 16.0 and obj.height == 16.0:
                    surface.blit(ts, (screen_x, screen_y), pygame.Rect(16, 96, 16, 16))
                else:
                    pygame.draw.rect(surface, (20, 40, 32), obj_rect)
                    pygame.draw.rect(surface, (50, 140, 90), obj_rect, 1)
                    pygame.draw.rect(surface, (80, 220, 140), (screen_x + 3, screen_y + 4, 10, 8))
            elif obj.type == "antenna_dish":
                # Big Ear relay dish mast (48x48 from tileset col 8..10, row 0..2)
                if ts is not None:
                    surface.blit(ts, (screen_x, screen_y), pygame.Rect(128, 0, 48, 48))
                else:
                    pygame.draw.line(surface, (60, 90, 80), (screen_x + 24, screen_y), (screen_x + 24, screen_y + 96), 3)
                    pygame.draw.arc(surface, (80, 130, 110), (screen_x, screen_y, 48, 48), 0.2, 2.9, 2)
                    pygame.draw.line(surface, (120, 180, 150), (screen_x + 24, screen_y + 12), (screen_x + 24, screen_y + 24), 2)
            elif obj.type == "hazard_sign":
                # Warning marker (16x16 from tileset col 10, row 3)
                if ts is not None:
                    surface.blit(ts, (screen_x, screen_y), pygame.Rect(160, 48, 16, 16))
                else:
                    pygame.draw.polygon(surface, (200, 160, 20), [
                        (screen_x + 8, screen_y),
                        (screen_x + 16, screen_y + 15),
                        (screen_x, screen_y + 15),
                    ])
                    pygame.draw.polygon(surface, (20, 20, 20), [
                        (screen_x + 8, screen_y),
                        (screen_x + 16, screen_y + 15),
                        (screen_x, screen_y + 15),
                    ], 1)
                    pygame.draw.line(surface, (20, 20, 20), (screen_x + 8, screen_y + 5), (screen_x + 8, screen_y + 10), 1)
            elif obj.type in ("grapple_anchor", "magnetic_anchor"):
                # Overhead magnetic swivel hook
                gx = screen_x + int(obj.width // 2)
                gy = screen_y + int(obj.height // 2)
                pygame.draw.circle(surface, (65, 195, 245), (gx, gy), 6)
                pygame.draw.circle(surface, (235, 240, 245), (gx, gy), 3)
                pygame.draw.circle(surface, (65, 195, 245), (gx, gy), 9, 1)

        # Render Exit doorway
        for ex in self.exits:
            screen_x, screen_y = camera.world_to_screen(ex.x, ex.y)
            exit_rect = pygame.Rect(screen_x, screen_y, int(ex.width), int(ex.height))
            if ts is not None and ex.width == 32.0 and ex.height == 48.0:
                # Heavy bunker bulkhead door (32x48 from tileset cols 8..9, rows 3..5)
                surface.blit(ts, (screen_x, screen_y), pygame.Rect(128, 48, 32, 48))
            else:
                # Heavy bunker airlock frame fallback
                pygame.draw.rect(surface, (14, 28, 22), exit_rect)
                pygame.draw.rect(surface, (40, 120, 80), exit_rect, 2)
                pygame.draw.circle(surface, (80, 160, 110), (screen_x + 16, screen_y + 24), 6, 2)
            # Label
            lbl_surf = get_airlock_label_surf()
            surface.blit(lbl_surf, (screen_x + 2, screen_y - 10))

        # Render Checkpoint markers
        for chk in self.checkpoints:
            screen_x, screen_y = camera.world_to_screen(chk.x, chk.y)
            if ts is not None:
                # Radio relay checkpoint post (16x32 from tileset col 10, rows 4..5)
                surface.blit(ts, (screen_x - 8, screen_y - 24), pygame.Rect(160, 64, 16, 32))
            else:
                # Radio relay antenna post fallback
                pygame.draw.line(surface, (80, 120, 100), (screen_x, screen_y - 24), (screen_x, screen_y + 8), 2)
                pygame.draw.circle(surface, (220, 180, 40), (screen_x, screen_y - 24), 3)
