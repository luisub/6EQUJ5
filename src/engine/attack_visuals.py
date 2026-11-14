"""Animated attack fields that keep danger bounds visible without opaque boxes."""
from functools import lru_cache
import math

import pygame


@lru_cache(maxsize=16)
def _canvas(size):
    # Reused scratch surfaces: rendering never decodes art or allocates each frame.
    return pygame.Surface(size, pygame.SRCALPHA)


def render_attack_field(surface, rect, *, color, progress=1.0, time=0.0,
                        active=False, arrival=False):
    """Draw inside the unchanged screen-space attack bounds; never advance state."""
    rect = pygame.Rect(rect)
    if rect.width < 2 or rect.height < 2 or not surface.get_clip().colliderect(rect):
        return
    field = _canvas(rect.size)
    field.fill((0, 0, 0, 0))
    progress = max(0.0, min(1.0, progress))
    bright = tuple(round(channel * .35 + 255 * .65) for channel in color)
    if arrival:
        # Arrival silhouettes use a ground halo and rising shards, not a hit box.
        floor = pygame.Rect(2, max(0, rect.height - 13), rect.width - 4, 11)
        pygame.draw.ellipse(field, (*color, 65), floor)
        pygame.draw.ellipse(field, (*bright, 130 + round(100 * progress)), floor, 1)
        for i in range(7):
            x = round((i + 1) * (rect.width - 1) / 8)
            y = rect.height - 2 - round(((time * .65 + i * .137) % 1) * (rect.height - 5))
            pygame.draw.line(field, (*color, 65 + round(110 * progress)),
                             (x, y), (x, min(rect.height - 1, y + 4)), 1)
        surface.blit(field, rect.topleft)
        return

    horizontal = rect.width >= rect.height
    length, breadth = rect.size if horizontal else (rect.height, rect.width)
    center = (breadth - 1) / 2

    def point(along, across):
        return (round(along), round(across)) if horizontal else (round(across), round(along))

    # Low-opacity energy fills the *whole* danger band, with a soft cross-section.
    # The background and actors remain legible through both warning and strike.
    for across in range(1, breadth - 1):
        falloff = max(0.0, 1 - abs(across - center) / max(1, center))
        alpha = round((12 + 48 * falloff ** 1.5) if active else (5 + 15 * falloff) * (.5 + progress / 2))
        pygame.draw.line(field, (*color, alpha), point(0, across), point(length - 1, across))

    # Broken boundary marks communicate the exact safe/unsafe edges without a frame.
    edge_alpha = 130 if active else 110 + round(90 * progress)
    for along in range(0, length, 16):
        end = min(length - 1, along + 5)
        for edge in (0, breadth - 1):
            pygame.draw.line(field, (*(color if active else bright), edge_alpha),
                             point(along, edge), point(end, edge))

    if active:
        # Several moving filaments distinguish the live attack from its faint windup.
        for strand, offset in enumerate((-.28, 0, .28)):
            points = []
            for along in range(0, length + 8, 8):
                along = min(length - 1, along)
                wobble = math.sin(along * .13 - time * 22 + strand * 2.2) * min(2, breadth / 8)
                points.append(point(along, center + offset * breadth + wobble))
            pygame.draw.lines(field, (*color, 175), False, points, 3)
            pygame.draw.lines(field, (*bright, 230 if strand == 1 else 150), False, points, 1)
    else:
        for end in (2, length - 3):
            pygame.draw.circle(field, (*bright, 225), point(end, center), 2)
        if not horizontal:
            pygame.draw.ellipse(field, (*bright, 220),
                                (0, rect.height - 8, rect.width, 8), 1)
        # Short traveling sparks accelerate visually as the existing warning expires.
        phase = time * (20 + 35 * progress)
        for i in range(max(2, length // 28)):
            along = (i * 29 + phase) % max(1, length - 5)
            across = center + math.sin(i * 2.1 + time * 3) * breadth * .16
            pygame.draw.line(field, (*bright, 150 + round(100 * progress)),
                             point(along, across), point(min(length - 1, along + 3), across), 1)
    surface.blit(field, rect.topleft)
