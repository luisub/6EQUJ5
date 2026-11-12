"""
MODULE: video_game/engine/mandela_world.py
PURPOSE: Transactional timeline swaps, aligned 2029/1977 collision validation, safe displacement solver, persistent object state, moving platforms, and atmospheric transitions.
CALLED BY: video_game.engine.scenes.field, video_game.tests.test_timelines.
HOW TO MODIFY: Add timeline-specific physics modifiers or transition shaders; maintain zero wildcard imports.
"""

from copy import deepcopy
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Set, Tuple
import pygame

from .campaign import Campaign
from uuid import uuid4
from .world import (
    Camera,
    COLLISION_COVER,
    COLLISION_EMPTY,
    COLLISION_HAZARD,
    COLLISION_ONE_WAY,
    COLLISION_SOLID,
    Room,
    RoomObject,
)


@dataclass
class SwapResult:
    """Result of a transactional timeline swap attempt."""
    success: bool
    from_timeline: str
    to_timeline: str
    displacement: Tuple[float, float]
    reason: str
    rejection_feedback: str = ""
    overlap_tiles: List[Tuple[int, int, int]] = field(default_factory=list)


@dataclass
class TimelineAtmosphere:
    """Aesthetic, lighting, and audio parameters for an era."""
    timeline_id: str
    label: str
    ambient_color: Tuple[int, int, int]
    light_tint: Tuple[int, int, int]
    crt_preset: str
    mist_intensity: float
    audio_cue: str
    description: str


DEFAULT_ATMOSPHERES: Dict[str, TimelineAtmosphere] = {
    "2029_CORE": TimelineAtmosphere(
        timeline_id="2029_CORE",
        label="2029 POST-COLLAPSE",
        ambient_color=(12, 18, 24),
        light_tint=(70, 190, 240),
        crt_preset="decay_cyan",
        mist_intensity=1.0,
        audio_cue="ambience_bunker",
        description="Cold dusk, radio mist, industrial ruin, high electromagnetic interference",
    ),
    "1977_ANALOG": TimelineAtmosphere(
        timeline_id="1977_ANALOG",
        label="1977 ANALOG FACILITY",
        ambient_color=(36, 28, 18),
        light_tint=(245, 200, 70),
        crt_preset="amber_phosphor",
        mist_intensity=0.0,
        audio_cue="mains_hum_60hz",
        description="Warm incandescent illumination, pristine facility corridors, vacuum-tube warmth",
    ),
}


class DisplacementSolver:
    """
    Computes safe displacement offsets for actors during timeline transitions
    to prevent embedding in solid geometry or landing in hazards.
    """

    @staticmethod
    def find_safe_displacement(
        room: Room,
        target_timeline: str,
        rect: pygame.Rect,
        max_distance: float = 32.0,
        prioritize_upward: bool = True,
    ) -> Optional[Tuple[float, float]]:
        """
        Evaluate candidate displacement offsets (dx, dy) within max_distance.
        Returns (dx, dy) if a legal, collision-free position is found, or None if impossible.
        """
        # 1. Check if current position is already completely valid
        col = room.check_rect_collision_in_timeline(rect, target_timeline)
        if not col["solid"] and not col["hazard"]:
            return (0.0, 0.0)

        # 2. Bounded search grid of candidate displacements
        # Stepping upward onto higher platforms/floors is given high priority
        upward_candidates = [
            (0.0, -2.0), (0.0, -4.0), (0.0, -6.0), (0.0, -8.0),
            (0.0, -10.0), (0.0, -12.0), (0.0, -16.0), (0.0, -20.0),
            (0.0, -24.0), (0.0, -28.0), (0.0, -32.0),
        ]
        lateral_candidates = [
            (-2.0, 0.0), (2.0, 0.0), (-4.0, 0.0), (4.0, 0.0),
            (-6.0, 0.0), (6.0, 0.0), (-8.0, 0.0), (8.0, 0.0),
            (-12.0, 0.0), (12.0, 0.0), (-16.0, 0.0), (16.0, 0.0),
            (-24.0, 0.0), (24.0, 0.0),
        ]
        diagonal_candidates = [
            (-4.0, -4.0), (4.0, -4.0), (-8.0, -4.0), (8.0, -4.0),
            (-4.0, -8.0), (4.0, -8.0), (-8.0, -8.0), (8.0, -8.0),
            (-12.0, -8.0), (12.0, -8.0), (-8.0, -16.0), (8.0, -16.0),
            (-16.0, -16.0), (16.0, -16.0),
        ]
        downward_candidates = [
            (0.0, 2.0), (0.0, 4.0), (0.0, 8.0), (0.0, 16.0),
        ]

        search_queue: List[Tuple[float, float]] = []
        if prioritize_upward:
            search_queue.extend(upward_candidates)
            search_queue.extend(lateral_candidates)
            search_queue.extend(diagonal_candidates)
            search_queue.extend(downward_candidates)
        else:
            search_queue.extend(lateral_candidates)
            search_queue.extend(upward_candidates)
            search_queue.extend(diagonal_candidates)
            search_queue.extend(downward_candidates)

        valid_options: List[Tuple[float, Tuple[float, float]]] = []

        for dx, dy in search_queue:
            dist = math.hypot(dx, dy)
            if dist > max_distance:
                continue

            test_rect = rect.move(int(dx), int(dy))

            # Bounds check inside room
            if test_rect.left < 0 or test_rect.right > room.width_px:
                continue
            if test_rect.top < 0 or test_rect.bottom > room.height_px:
                continue

            test_col = room.check_rect_collision_in_timeline(test_rect, target_timeline)
            if test_col["solid"] or test_col["hazard"]:
                continue

            # Support check: is there solid or one-way floor beneath?
            foot_check = test_rect.move(0, 2)
            foot_col = room.check_rect_collision_in_timeline(foot_check, target_timeline)
            has_ground = foot_col["solid"] or foot_col["one_way"]

            score = dist
            if dy < 0:
                score *= 0.85  # Upward step-up bonus
            elif dy > 0:
                score *= 1.30  # Downward penalty
            if has_ground:
                score *= 0.90  # Solid footing bonus

            valid_options.append((score, (dx, dy)))

        if not valid_options:
            return None

        valid_options.sort(key=lambda item: item[0])
        return valid_options[0][1]


class MovingPlatform:
    """Kinematic moving platform with timeline awareness."""

    def __init__(
        self,
        platform_id: str,
        x: float,
        y: float,
        width: float = 32.0,
        height: float = 12.0,
        timeline: str = "all",
        waypoints: Optional[List[Tuple[float, float]]] = None,
        speed: float = 40.0,
        path_mode: str = "ping_pong",
    ):
        self.id: str = platform_id
        self.x: float = float(x)
        self.y: float = float(y)
        self.width: float = float(width)
        self.height: float = float(height)
        self.timeline: str = timeline
        self.waypoints: List[Tuple[float, float]] = waypoints if waypoints else [(self.x, self.y)]
        self.speed: float = float(speed)
        self.path_mode: str = path_mode
        self.target_idx: int = 1 if len(self.waypoints) > 1 else 0
        self.forward: bool = True
        self.dx: float = 0.0
        self.dy: float = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))

    def is_active_in_timeline(self, timeline_id: str) -> bool:
        if self.timeline in ("all", "both", "*"):
            return True
        return self.timeline == timeline_id

    def update(self, dt: float):
        """Update platform position towards current target waypoint."""
        if len(self.waypoints) <= 1:
            self.dx = 0.0
            self.dy = 0.0
            return

        tx, ty = self.waypoints[self.target_idx]
        delta_x = tx - self.x
        delta_y = ty - self.y
        dist = math.hypot(delta_x, delta_y)

        step = self.speed * dt
        if dist <= step or dist == 0.0:
            self.dx = delta_x
            self.dy = delta_y
            self.x = tx
            self.y = ty

            # Advance waypoint
            if self.path_mode == "ping_pong":
                if self.forward:
                    if self.target_idx + 1 < len(self.waypoints):
                        self.target_idx += 1
                    else:
                        self.forward = False
                        self.target_idx -= 1
                else:
                    if self.target_idx - 1 >= 0:
                        self.target_idx -= 1
                    else:
                        self.forward = True
                        self.target_idx += 1
            else:  # loop
                self.target_idx = (self.target_idx + 1) % len(self.waypoints)
        else:
            self.dx = (delta_x / dist) * step
            self.dy = (delta_y / dist) * step
            self.x += self.dx
            self.y += self.dy

    def is_actor_riding(self, actor_rect: pygame.Rect) -> bool:
        """Return True if actor's feet are resting on top of the platform."""
        actor_bottom = actor_rect.bottom
        plat_top = int(self.y)
        # Check vertical contact tolerance (+/- 3px)
        vert_aligned = abs(actor_bottom - plat_top) <= 3
        # Check horizontal overlap
        horiz_overlap = actor_rect.right > self.x and actor_rect.left < (self.x + self.width)
        return vert_aligned and horiz_overlap

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "timeline": self.timeline,
            "waypoints": [list(w) for w in self.waypoints],
            "speed": self.speed,
            "path_mode": self.path_mode,
            "target_idx": self.target_idx,
            "forward": self.forward,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MovingPlatform":
        plat = cls(
            platform_id=str(data["id"]),
            x=float(data["x"]),
            y=float(data["y"]),
            width=float(data.get("width", 32.0)),
            height=float(data.get("height", 12.0)),
            timeline=str(data.get("timeline", "all")),
            waypoints=[(float(w[0]), float(w[1])) for w in data.get("waypoints", [])],
            speed=float(data.get("speed", 40.0)),
            path_mode=str(data.get("path_mode", "ping_pong")),
        )
        plat.target_idx = int(data.get("target_idx", 0))
        plat.forward = bool(data.get("forward", True))
        return plat


@dataclass
class PersistentObjectState:
    """State container tracking collected items and doors across repeated swaps."""
    collected_pickups: Set[str] = field(default_factory=set)
    door_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    room_flags: Dict[str, Any] = field(default_factory=dict)
    active_checkpoint_id: Optional[str] = None

    def is_collected(self, pickup_id: str) -> bool:
        return pickup_id in self.collected_pickups

    def mark_collected(self, pickup_id: str) -> bool:
        """Mark pickup as collected. Returns True if newly collected, False if already collected."""
        if pickup_id in self.collected_pickups:
            return False
        self.collected_pickups.add(pickup_id)
        return True

    def get_door_state(self, door_id: str) -> Dict[str, Any]:
        return self.door_states.setdefault(door_id, {"open": False, "locked": False})

    def set_door_state(self, door_id: str, is_open: bool, is_locked: Optional[bool] = None):
        st = self.get_door_state(door_id)
        st["open"] = is_open
        if is_locked is not None:
            st["locked"] = is_locked

    def to_dict(self) -> Dict[str, Any]:
        return {
            "collected_pickups": sorted(list(self.collected_pickups)),
            "door_states": deepcopy(self.door_states),
            "room_flags": deepcopy(self.room_flags),
            "active_checkpoint_id": self.active_checkpoint_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersistentObjectState":
        return cls(
            collected_pickups=set(data.get("collected_pickups", [])),
            door_states=deepcopy(data.get("door_states", {})),
            room_flags=deepcopy(data.get("room_flags", {})),
            active_checkpoint_id=data.get("active_checkpoint_id"),
        )


class MandelaWorld:
    """
    Coordinator managing dual-timeline room geometry, transactional swapping,
    persistent object state, moving platforms, and atmospheric transitions.
    """

    def __init__(
        self,
        room: Room,
        initial_timeline: str = "2029_CORE",
        campaign: Optional[Campaign] = None,
    ):
        self.room: Room = room
        self.active_timeline: str = initial_timeline
        self.room.set_active_timeline(self.active_timeline)
        self.state: PersistentObjectState = PersistentObjectState()
        self.moving_platforms: Dict[str, MovingPlatform] = {}
        self.atmospheres: Dict[str, TimelineAtmosphere] = dict(DEFAULT_ATMOSPHERES)
        self.campaign: Optional[Campaign] = campaign
        self.transition_timer: float = 0.0
        self.transition_duration: float = 0.30

        # Parse moving platforms from room objects if present
        self._load_platforms_from_room()

        # Synchronize with campaign if provided
        if self.campaign:
            self.sync_from_campaign(self.campaign)

    def _load_platforms_from_room(self):
        """Extract moving platform definitions from room objects."""
        for obj in self.room.objects:
            if obj.type == "moving_platform":
                props = obj.properties
                waypoints = props.get("waypoints", [(obj.x, obj.y)])
                plat = MovingPlatform(
                    platform_id=obj.id,
                    x=obj.x,
                    y=obj.y,
                    width=obj.width,
                    height=obj.height,
                    timeline=obj.timeline,
                    waypoints=[(float(w[0]), float(w[1])) for w in waypoints],
                    speed=float(props.get("speed", 40.0)),
                    path_mode=str(props.get("path_mode", "ping_pong")),
                )
                self.moving_platforms[obj.id] = plat

    def get_atmosphere(self, timeline_id: Optional[str] = None) -> TimelineAtmosphere:
        """Return atmosphere configuration for specified or active timeline."""
        t_id = timeline_id or self.active_timeline
        return self.atmospheres.get(t_id, DEFAULT_ATMOSPHERES["2029_CORE"])

    def swap_timeline(
        self,
        target_timeline: str,
        player: Any,
        actors: Optional[List[Any]] = None,
        allow_displacement: bool = True,
    ) -> SwapResult:
        """
        Attempt a transactional timeline swap.
        Evaluates player and actor footprints against target geometry.
        Commits cleanly if safe (applying safe displacement if necessary),
        or rolls back with zero state mutation if blocked.
        """
        actor_list = actors or []

        # 1. No-op if already in target timeline
        if target_timeline == self.active_timeline:
            return SwapResult(
                success=True,
                from_timeline=self.active_timeline,
                to_timeline=target_timeline,
                displacement=(0.0, 0.0),
                reason="ALREADY_ACTIVE",
                rejection_feedback="Target timeline is already active.",
            )

        # 2. Check if timeline exists in room
        if target_timeline not in self.room.timeline_collision_layers:
            return SwapResult(
                success=False,
                from_timeline=self.active_timeline,
                to_timeline=target_timeline,
                displacement=(0.0, 0.0),
                reason="UNKNOWN_TIMELINE",
                rejection_feedback=f"Unknown timeline '{target_timeline}' not registered in room.",
            )

        # 3. Check actor embedding in target timeline
        for actor in actor_list:
            a_rect = getattr(actor, "rect", None)
            if a_rect is not None:
                a_col = self.room.check_rect_collision_in_timeline(a_rect, target_timeline)
                if a_col["solid"] or a_col["hazard"]:
                    return SwapResult(
                        success=False,
                        from_timeline=self.active_timeline,
                        to_timeline=target_timeline,
                        displacement=(0.0, 0.0),
                        reason="ACTOR_EMBEDDED",
                        rejection_feedback=f"Actor '{getattr(actor, 'id', 'companion')}' would be embedded in solid geometry.",
                        overlap_tiles=a_col["tiles"],
                    )

        # 4. Check player footprint in target timeline
        player_rect = player.rect
        p_col = self.room.check_rect_collision_in_timeline(player_rect, target_timeline)

        displacement = (0.0, 0.0)
        if p_col["solid"] or p_col["hazard"]:
            if not allow_displacement:
                reason = "BLOCKED_BY_SOLID" if p_col["solid"] else "BLOCKED_BY_HAZARD"
                return SwapResult(
                    success=False,
                    from_timeline=self.active_timeline,
                    to_timeline=target_timeline,
                    displacement=(0.0, 0.0),
                    reason=reason,
                    rejection_feedback=f"TEMPORAL REJECTED: Player footprint blocked by {reason.replace('BLOCKED_BY_', '').lower()} geometry.",
                    overlap_tiles=p_col["tiles"],
                )

            # Attempt safe displacement
            safe_disp = DisplacementSolver.find_safe_displacement(
                self.room, target_timeline, player_rect, max_distance=32.0, prioritize_upward=True
            )
            if safe_disp is None:
                reason = "BLOCKED_BY_SOLID" if p_col["solid"] else "BLOCKED_BY_HAZARD"
                return SwapResult(
                    success=False,
                    from_timeline=self.active_timeline,
                    to_timeline=target_timeline,
                    displacement=(0.0, 0.0),
                    reason=reason,
                    rejection_feedback=f"TEMPORAL REJECTED: No safe displacement path found in {target_timeline}.",
                    overlap_tiles=p_col["tiles"],
                )
            displacement = safe_disp

        # 5. COMMIT TRANSACTION:
        prev_timeline = self.active_timeline
        self.active_timeline = target_timeline
        self.room.set_active_timeline(target_timeline)

        # Apply displacement to player
        if displacement != (0.0, 0.0):
            player.x += displacement[0]
            player.y += displacement[1]

        # Trigger temporal visual transition pulse
        self.transition_timer = self.transition_duration

        # Sync with campaign if connected
        if self.campaign:
            self.sync_to_campaign(self.campaign)

        reason = "SAFE_DISPLACEMENT_APPLIED" if displacement != (0.0, 0.0) else "SWAP_COMMITTED"
        return SwapResult(
            success=True,
            from_timeline=prev_timeline,
            to_timeline=target_timeline,
            displacement=displacement,
            reason=reason,
            rejection_feedback="",
        )

    def collect_pickup(self, pickup_id: str, player: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        """
        Atomically collect a pickup item.
        Guarantees that repeated timeline swaps cannot duplicate items.
        Returns item properties if newly collected, or None if already collected or not found.
        """
        if self.state.is_collected(pickup_id):
            return None

        # Find object in room
        target_obj = None
        for obj in self.room.objects:
            if obj.id == pickup_id:
                target_obj = obj
                break

        if target_obj is None:
            return None

        # Campaign rewards use registered one-shot events, never inventory mutation.
        if self.campaign and target_obj.properties.get("event_type"):
            self.campaign.apply_event({"event_id": f"pickup_{pickup_id}",
                                       "type": target_obj.properties["event_type"]})
        self.state.mark_collected(pickup_id)

        return dict(target_obj.properties)

    def toggle_door(self, door_id: str, is_open: Optional[bool] = None) -> bool:
        """Toggle or set door state and persist across swaps."""
        st = self.state.get_door_state(door_id)
        new_state = (not st["open"]) if is_open is None else is_open
        self.state.set_door_state(door_id, is_open=new_state)
        return new_state

    def update(self, dt: float, player: Optional[Any] = None, actors: Optional[List[Any]] = None):
        """Update active moving platforms and handle player riding."""
        if self.transition_timer > 0.0:
            self.transition_timer = max(0.0, self.transition_timer - dt)

        # Update moving platforms active in this timeline
        for plat in self.moving_platforms.values():
            if not plat.is_active_in_timeline(self.active_timeline):
                continue

            prev_x, prev_y = plat.x, plat.y
            riding = bool(player and plat.is_actor_riding(player.rect))
            plat.update(dt)
            move_dx = plat.x - prev_x
            move_dy = plat.y - prev_y

            # If player is riding this platform, convey player
            if player:
                feet = player.y + 32
                previous_feet = feet - max(0.0, player.vy) * dt
                above = previous_feet <= prev_y + 2 and feet >= plat.y
                overlaps = player.rect.right > plat.x and player.rect.left < plat.x + plat.width
                if riding or (player.vy >= 0 and above and overlaps):
                    candidate = player.rect.move(move_dx, plat.y - feet)
                    collision = self.room.check_rect_collision(candidate)
                    if not collision['solid'] and not collision['hazard']:
                        player.x += move_dx
                        player.y = plat.y - 32
                        player.vy = 0
                        player.is_grounded = True

            # If actors are riding, convey them
            if actors:
                for actor in actors:
                    a_rect = getattr(actor, "rect", None)
                    if a_rect and plat.is_actor_riding(a_rect):
                        actor.x += move_dx
                        actor.y += move_dy

    def render(self, surface: pygame.Surface, camera: Camera, anim_time: float = 0.0, *, draw_background: bool = True):
        """Render reality layers; callers may supply a validated background first."""
        # Standalone callers retain the original background by default.
        if draw_background:
            self.room.render_background(surface, camera)

        # 2. Render visible collision tiles
        self.room.render_tiles(surface, camera)

        # 3. Render moving platforms active in current timeline
        for plat in self.moving_platforms.values():
            if not plat.is_active_in_timeline(self.active_timeline):
                continue
            screen_x, screen_y = camera.world_to_screen(plat.x, plat.y)
            plat_rect = pygame.Rect(screen_x, screen_y, int(plat.width), int(plat.height))

            # Render styled catwalk platform
            color_body = (30, 50, 42) if self.active_timeline == "2029_CORE" else (55, 45, 25)
            color_border = (60, 110, 85) if self.active_timeline == "2029_CORE" else (160, 130, 50)
            pygame.draw.rect(surface, color_body, plat_rect)
            pygame.draw.rect(surface, color_border, plat_rect, 1)
            pygame.draw.line(surface, color_border, (screen_x + 2, screen_y + 2), (screen_x + int(plat.width) - 3, screen_y + 2), 1)

        # 4. Render timeline objects (filtering collected pickups)
        ts = None
        for obj in self.room.get_objects_for_timeline(self.active_timeline):
            if obj.type == "pickup" and self.state.is_collected(obj.id):
                continue  # Collected pickups are permanently despawned
            if obj.type == "moving_platform":
                continue  # Rendered separately above

            screen_x, screen_y = camera.world_to_screen(obj.x, obj.y)
            obj_rect = pygame.Rect(screen_x, screen_y, int(obj.width), int(obj.height))

            if obj.type == "pickup":
                if obj.properties.get("spawned", True) is False:
                    continue
                # Glowing pickup box
                pulse = int(20 * math.sin(anim_time * 5.0))
                p_color = (60 + pulse, 220, 130) if self.active_timeline == "2029_CORE" else (245, 180 + pulse, 50)
                pygame.draw.rect(surface, (20, 30, 25), obj_rect)
                pygame.draw.rect(surface, p_color, obj_rect, 1)
                pygame.draw.circle(surface, p_color, obj_rect.center, 3)

            elif obj.type == "grapple_anchor":
                pygame.draw.circle(surface, (100, 220, 245), obj_rect.center, 7, 2)

            elif obj.type == "door":
                # Bulkhead door with open/closed state
                door_st = self.state.get_door_state(obj.id)
                d_color = (40, 80, 60) if not door_st["open"] else (20, 40, 30)
                pygame.draw.rect(surface, d_color, obj_rect)
                pygame.draw.rect(surface, (70, 150, 110), obj_rect, 2)
                if not door_st["open"]:
                    pygame.draw.line(surface, (200, 60, 60), (screen_x + 2, screen_y + 2), (screen_x + int(obj.width) - 3, screen_y + int(obj.height) - 3), 1)

        # 5. Render atmospheric mist (2029 only)
        atmos = self.get_atmosphere()
        if atmos.mist_intensity > 0.0:
            self.room.render_weather(surface, camera, anim_time)

        # 6. Render temporal transition flash / aberration if active
        if self.transition_timer > 0.0:
            alpha = int((self.transition_timer / self.transition_duration) * 80)
            flash_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            tint = atmos.light_tint
            flash_surf.fill((tint[0], tint[1], tint[2], alpha))
            surface.blit(flash_surf, (0, 0))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete Mandela world state for save files."""
        return {
            "active_timeline": self.active_timeline,
            "persistent_state": self.state.to_dict(),
            "moving_platforms": {p_id: plat.to_dict() for p_id, plat in self.moving_platforms.items()},
        }

    def from_dict(self, data: Dict[str, Any]):
        """Deserialize Mandela world state from saved data."""
        t_id = data.get("active_timeline", "2029_CORE")
        self.active_timeline = t_id
        self.room.set_active_timeline(t_id)

        if "persistent_state" in data:
            self.state = PersistentObjectState.from_dict(data["persistent_state"])

        if "moving_platforms" in data:
            for p_id, p_data in data["moving_platforms"].items():
                if p_id in self.moving_platforms:
                    self.moving_platforms[p_id].x = float(p_data["x"])
                    self.moving_platforms[p_id].y = float(p_data["y"])
                    self.moving_platforms[p_id].target_idx = int(p_data.get("target_idx", 0))
                    self.moving_platforms[p_id].forward = bool(p_data.get("forward", True))

    def sync_to_campaign(self, campaign: Campaign):
        """Update campaign timeline mode and room flags."""
        if campaign.timeline_mode != self.active_timeline:
            campaign.apply_event({"event_id": uuid4().hex, "type": "timeline_shift",
                                  "payload": {"timeline_mode": self.active_timeline}})

    def sync_from_campaign(self, campaign: Campaign):
        """Restore timeline state from campaign."""
        c_timeline = campaign.timeline_mode
        if c_timeline in self.room.timeline_collision_layers:
            self.active_timeline = c_timeline
            self.room.set_active_timeline(c_timeline)
