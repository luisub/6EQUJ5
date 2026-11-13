"""MODULE: video_game/engine/ui/viewport.py
PURPOSE: Map actual window coordinates to the renderer's drawn logical viewport.
CALLED BY: PlayerInput, the aim reticle and the pause overlay.
HOW TO MODIFY: Match CRTRenderer.present's origin, scaling and clipped window behavior.
"""
import pygame
from .. import config


def window_to_logical(position, crt):
    """Return a logical point only when the window pixel shows rendered content."""
    if position is None or crt.win_w <= 0 or crt.win_h <= 0:
        return None
    surface = pygame.display.get_surface()
    surface_size = surface.get_size() if surface is not None else (crt.win_w, crt.win_h)
    try:
        window_size = pygame.display.get_window_size() if surface is not None else surface_size
    except pygame.error:
        window_size = surface_size
    if min(*surface_size, *window_size) <= 0:
        return None
    x, y = position
    if not (0 <= x < window_size[0] and 0 <= y < window_size[1]):
        return None
    sx = x * surface_size[0] / window_size[0]
    sy = y * surface_size[1] / window_size[1]
    if sx >= crt.win_w or sy >= crt.win_h:
        return None
    return (sx * config.INTERNAL_WIDTH / crt.win_w,
            sy * config.INTERNAL_HEIGHT / crt.win_h)
