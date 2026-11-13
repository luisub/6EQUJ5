"""
MODULE: video_game/engine/animation.py
PURPOSE: Animation clip management, frame-rate independent playback,
         foot pivot anchoring, hurtbox transformation, and weapon attachment tracking.
CALLED BY: Player, FieldOpsScene, BunkerHubScene, preview tools.
HOW TO MODIFY: Add clip properties or state mapping rules in AnimationPlayer.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pygame


class AnimationClip:
    """Immutable metadata and loaded surface frames for a single animation state."""

    def __init__(
        self,
        name: str,
        frames: List[pygame.Surface],
        frame_durations_ms: List[int],
        loop: bool = True,
        cell_size: Tuple[int, int] = (96, 128),
        foot_pivot: Tuple[int, int] = (48, 124),
        hurtbox: Optional[pygame.Rect] = None,
        attachments: Optional[Dict[str, Tuple[int, int]]] = None,
        review_status: str = "reviewed",
        review_notes: str = "",
    ):
        self.name = name
        self.frames = list(frames)
        self.frame_durations_ms = list(frame_durations_ms)
        self.loop = loop
        self.cell_size = tuple(cell_size)
        self.foot_pivot = tuple(foot_pivot)
        self.hurtbox = hurtbox if hurtbox is not None else pygame.Rect(36, 16, 24, 108)
        self.attachments = dict(attachments) if attachments is not None else {}
        self.review_status = review_status
        self.review_notes = review_notes

        # Precompute duration metrics
        if not self.frame_durations_ms and self.frames:
            self.frame_durations_ms = [0] * len(self.frames)
        self.total_duration_ms = sum(self.frame_durations_ms)
        self.total_duration_s = self.total_duration_ms / 1000.0

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    def get_frame_index(self, time_seconds: float) -> int:
        """Calculate deterministic frame index for given elapsed time in seconds."""
        if self.frame_count <= 1:
            return 0
        if self.total_duration_ms <= 0:
            return 0

        t_ms = time_seconds * 1000.0
        if self.loop:
            cycle_ms = t_ms % float(self.total_duration_ms)
        else:
            cycle_ms = min(t_ms, float(self.total_duration_ms - 0.001))

        accum_ms = 0.0
        for idx, dur in enumerate(self.frame_durations_ms):
            accum_ms += float(dur)
            if cycle_ms < accum_ms:
                return idx
        return self.frame_count - 1


class AnimationPlayer:
    """Manages active animation state, frame-rate independent timing, and rendering."""

    def __init__(
        self,
        clips: Dict[str, AnimationClip],
        default_state: str = "idle",
        scale_factor: float = 0.25,
        facing: str = "right",
    ):
        self.clips = dict(clips)
        self.current_state = default_state if default_state in self.clips else "idle"
        self.time_accumulated = 0.0
        self.scale_factor = float(scale_factor)
        self.facing = facing
        self.attachment_facing = facing
        self._scaled_cache: Dict[Tuple[int, float, bool], pygame.Surface] = {}

    def set_state(self, state: str, reset: bool = False):
        """Switch active animation state, optionally restarting elapsed timer."""
        target_state = state if state in self.clips else "idle"
        if target_state != self.current_state or reset:
            self.current_state = target_state
            self.time_accumulated = 0.0

    def set_facing(self, facing: str):
        """Set display and, by default, attachment direction."""
        if facing in ("left", "right"):
            self.facing = facing
            self.attachment_facing = facing

    def set_attachment_facing(self, facing: str):
        """Orient world attachments and rig hurtbox independently of the body."""
        if facing in ("left", "right"):
            self.attachment_facing = facing

    def set_scale_factor(self, scale: float):
        """Set render scaling relative to native 96x128 cell."""
        if scale > 0.0 and scale != self.scale_factor:
            self.scale_factor = float(scale)
            self._scaled_cache.clear()

    def update(self, dt_seconds: float):
        """Advance animation timeline by frame-rate independent delta seconds."""
        self.time_accumulated += max(0.0, float(dt_seconds))

    @property
    def current_clip(self) -> AnimationClip:
        """Active clip or fallback to idle."""
        return self.clips.get(self.current_state) or self.clips.get("idle") or next(iter(self.clips.values()))

    @property
    def current_frame_index(self) -> int:
        """Current zero-based frame index within the active clip."""
        return self.current_clip.get_frame_index(self.time_accumulated)

    @property
    def current_surface(self) -> pygame.Surface:
        """Current frame surface, scaled and horizontally mirrored if facing left."""
        return self.surface_for_density(1)

    def surface_for_density(self, density: int) -> pygame.Surface:
        """Sample the source at display density without changing world geometry."""
        if density < 1:
            raise ValueError('density must be positive')
        clip = self.current_clip
        idx = self.current_frame_index
        base_surf = clip.frames[idx]
        is_flipped = (self.facing == "left")
        render_scale = self.scale_factor * density
        cache_key = (id(base_surf), render_scale, is_flipped)

        if cache_key not in self._scaled_cache:
            target_w = max(1, round(clip.cell_size[0] * render_scale))
            target_h = max(1, round(clip.cell_size[1] * render_scale))
            if render_scale != 1.0 or base_surf.get_size() != (target_w, target_h):
                scaled = pygame.transform.scale(base_surf, (target_w, target_h))
            else:
                scaled = base_surf
            if is_flipped:
                scaled = pygame.transform.flip(scaled, True, False)
            self._scaled_cache[cache_key] = scaled

        return self._scaled_cache[cache_key]

    def get_foot_pivot(self) -> Tuple[float, float]:
        """Effective foot pivot on the scaled/flipped surface."""
        clip = self.current_clip
        cell_w = float(clip.cell_size[0])
        px, py = float(clip.foot_pivot[0]), float(clip.foot_pivot[1])

        if self.facing == "left":
            eff_px = (cell_w - 1.0 - px) * self.scale_factor
        else:
            eff_px = px * self.scale_factor
        eff_py = py * self.scale_factor
        return eff_px, eff_py

    def get_render_dest(
        self,
        foot_world_x: float,
        foot_world_y: float,
        camera: Optional[Any] = None,
    ) -> Tuple[int, int]:
        """Compute pixel blit coordinates so sprite foot pivot matches world foot anchor."""
        if camera is not None and hasattr(camera, "world_to_screen"):
            screen_x, screen_y = camera.world_to_screen(foot_world_x, foot_world_y)
        else:
            screen_x, screen_y = foot_world_x, foot_world_y

        piv_x, piv_y = self.get_foot_pivot()
        dest_x = round(screen_x - piv_x)
        dest_y = round(screen_y - piv_y)
        return dest_x, dest_y

    def get_render_dest_for_density(self, foot_world_x, foot_world_y, camera, density):
        """Return native pixel coordinates, rounding only after density conversion."""
        if camera is not None and hasattr(camera, 'world_to_screen'):
            screen_x, screen_y = camera.world_to_screen(foot_world_x, foot_world_y)
        else:
            screen_x, screen_y = foot_world_x, foot_world_y
        piv_x, piv_y = self.get_foot_pivot()
        return round((screen_x - piv_x) * density), round((screen_y - piv_y) * density)

    def get_attachment_world_pos(
        self,
        name: str,
        foot_world_x: float,
        foot_world_y: float,
    ) -> Optional[Tuple[float, float]]:
        """Compute world coordinates of named attachment point (e.g. 'muzzle')."""
        clip = self.current_clip
        if name not in clip.attachments:
            return None

        ax, ay = clip.attachments[name]
        px, py = clip.foot_pivot
        dx = float(ax - px) * self.scale_factor
        dy = float(ay - py) * self.scale_factor

        if self.attachment_facing == "left":
            world_x = foot_world_x - dx
        else:
            world_x = foot_world_x + dx
        world_y = foot_world_y + dy
        return world_x, world_y

    def get_hurtbox(
        self,
        foot_world_x: float,
        foot_world_y: float,
    ) -> pygame.Rect:
        """Compute world-space hurtbox derived from clip metadata and foot pivot."""
        clip = self.current_clip
        hx = float(clip.hurtbox.x)
        hy = float(clip.hurtbox.y)
        hw = float(clip.hurtbox.width)
        hh = float(clip.hurtbox.height)
        px, py = float(clip.foot_pivot[0]), float(clip.foot_pivot[1])

        scaled_w = max(1, round(hw * self.scale_factor))
        scaled_h = max(1, round(hh * self.scale_factor))
        rel_y = (hy - py) * self.scale_factor

        if self.attachment_facing == "right":
            rel_x = (hx - px) * self.scale_factor
        else:
            cell_w = float(clip.cell_size[0])
            mirrored_hx = cell_w - (hx + hw)
            mirrored_px = cell_w - 1.0 - px
            rel_x = (mirrored_hx - mirrored_px) * self.scale_factor

        world_hx = round(foot_world_x + rel_x)
        world_hy = round(foot_world_y + rel_y)
        return pygame.Rect(world_hx, world_hy, scaled_w, scaled_h)


_LOADED_ANIM_CACHE: Dict[Tuple[str, str], Dict[str, AnimationClip]] = {}


def load_mateo_animations(
    asset_root: Path,
    outfit: str = "olive_field",
) -> Dict[str, AnimationClip]:
    """Load and cache animation clips for specified outfit from manifest.json."""
    asset_root = Path(asset_root).resolve()
    cache_key = (str(asset_root), outfit)
    if cache_key in _LOADED_ANIM_CACHE:
        return _LOADED_ANIM_CACHE[cache_key]

    manifest_file = asset_root / "sprites" / "mateo" / "manifest.json"
    if not manifest_file.is_file():
        raise FileNotFoundError(f"Missing Mateo animation manifest: {manifest_file}")

    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    outfits = manifest_data.get("outfits", {})
    if outfit not in outfits:
        outfit = "olive_field" if "olive_field" in outfits else next(iter(outfits))

    outfit_entry = outfits[outfit]
    cell_size = tuple(outfit_entry.get("cell_size", [96, 128]))
    default_pivot = tuple(outfit_entry.get("default_foot_pivot", [48, 124]))
    anim_entries = outfit_entry.get("animations", {})

    loaded_clips: Dict[str, AnimationClip] = {}
    for anim_name, a_data in anim_entries.items():
        frames: List[pygame.Surface] = []
        for frame_rel in a_data.get("frames", []):
            frame_path = asset_root / frame_rel
            if frame_path.is_file():
                surf = pygame.image.load(str(frame_path)).convert_alpha()
                frames.append(surf)
            else:
                # Safe transparent placeholder surface
                surf = pygame.Surface(cell_size, pygame.SRCALPHA)
                frames.append(surf)

        # Durations
        dur_ms = a_data.get("frame_duration_ms", 100)
        if isinstance(dur_ms, list):
            dur_list = list(dur_ms)
        else:
            dur_list = [int(dur_ms)] * len(frames)

        loop = bool(a_data.get("loop", False))
        foot_piv = tuple(a_data.get("foot_pivot", default_pivot))
        hb_list = a_data.get("hurtbox", [36, 16, 24, 108])
        hurtbox = pygame.Rect(hb_list[0], hb_list[1], hb_list[2], hb_list[3])
        attachments = {k: tuple(v) for k, v in a_data.get("attachment_points", {}).items()}
        review_status = a_data.get("review_status", "reviewed")
        review_notes = a_data.get("review_notes", "")

        clip = AnimationClip(
            name=anim_name,
            frames=frames,
            frame_durations_ms=dur_list,
            loop=loop,
            cell_size=cell_size,
            foot_pivot=foot_piv,
            hurtbox=hurtbox,
            attachments=attachments,
            review_status=review_status,
            review_notes=review_notes,
        )
        loaded_clips[anim_name] = clip

    _LOADED_ANIM_CACHE[cache_key] = loaded_clips
    return loaded_clips

