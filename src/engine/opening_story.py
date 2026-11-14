"""PURPOSE: Show the authored, skippable introduction above the basement.
CALLED BY: BunkerHubScene only for a new game started from the title screen.
HOW TO MODIFY: Preserve short offline pages, readable timing and safe fallback.
"""
import json
import math
from pathlib import Path

import pygame

from .ui.text import wrap_text_pixels
from .galaxy_transit import map_points, leg_points, route_ids
from .galaxy_transit_assets import load_galaxy_transit

PATH = Path(__file__).resolve().parent.parent / 'data' / 'opening_story.json'


def load_opening_pages(path=PATH):
    """Reject malformed story content without blocking the playable bunker."""
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
        pages = data['pages']
        if (type(data.get('schema_version')) is not int or data['schema_version'] != 1
                or not isinstance(pages, list) or not 3 <= len(pages) <= 4):
            return []
        for page in pages:
            if (not isinstance(page, dict) or not {'title', 'text'} <= set(page)
                    or set(page) - {'title', 'text', 'visual'}
                    or page.get('visual') not in (None, 'galaxy_map')
                    or not isinstance(page['title'], str) or not page['title'].strip()
                    or len(page['title']) > 80 or not isinstance(page['text'], str)
                    or not page['text'].strip() or len(page['text']) > 500):
                return []
        return [dict(page) for page in pages]
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return []


class OpeningStory:
    """Story and map share one dialog; Next advances and Skip exits safely."""
    NEXT_BUTTON = pygame.Rect(365, 193, 75, 23)
    SKIP_BUTTON = pygame.Rect(282, 193, 73, 23)

    def __init__(self, pages, seconds_per_page=14.0, asset_root=None):
        self.pages = list(pages)
        self.index = 0
        self.seconds_per_page = seconds_per_page
        self.remaining = seconds_per_page
        assets = load_galaxy_transit(asset_root) if asset_root else None
        self.map_image = (pygame.transform.smoothscale(assets['galaxy_map'], (390, 105))
                          if assets else None)

    def advance(self):
        if not self.done:
            self.index += 1
            self.remaining = self.seconds_per_page

    @property
    def done(self):
        return self.index >= len(self.pages)

    def update(self, dt):
        if self.done or not isinstance(dt, (int, float)) or not math.isfinite(dt) or dt <= 0:
            return
        while not self.done and dt >= self.remaining:
            dt -= self.remaining
            self.index += 1
            self.remaining = self.seconds_per_page
        if not self.done:
            self.remaining -= dt

    def render(self, crt):
        if self.done:
            return
        page = self.pages[self.index]
        panel = pygame.Rect(26, 28, 428, 196)
        pygame.draw.rect(crt.canvas, (5, 13, 17), panel)
        pygame.draw.rect(crt.canvas, (124, 176, 166), panel, 1)
        crt.draw_text(page['title'], 44, 43, color=(110, 215, 218), size='md')
        progress = f'{self.index + 1}/{len(self.pages)}'
        progress_width = crt.font_sm.size(progress)[0]
        crt.draw_text(progress, panel.right - progress_width - 14, 46,
                      color=(150, 183, 177), size='sm')
        if page.get('visual') == 'galaxy_map':
            self._render_map(crt)
            for i, line in enumerate(wrap_text_pixels(page['text'], crt.font_sm, 390)):
                crt.draw_text(line, 44, 166 + 11 * i, color=(235, 228, 207), size='sm')
        else:
            for i, line in enumerate(wrap_text_pixels(page['text'], crt.font_md, 390)):
                crt.draw_text(line, 44, 74 + 19 * i, color=(235, 228, 207), size='md')
        crt.draw_text('N / PAD X: NEXT   ENTER: SKIP', 44, 201,
                      color=(166, 188, 183), size='sm')
        for rect, label in ((self.SKIP_BUTTON, 'SKIP'),
                            (self.NEXT_BUTTON, 'BEGIN >' if self.index == len(self.pages) - 1 else 'NEXT >')):
            pygame.draw.rect(crt.canvas, (21, 42, 43), rect)
            pygame.draw.rect(crt.canvas, (230, 194, 105), rect, 1)
            crt.draw_text(label, rect.x + 9, rect.y + 6, color=(230, 194, 105), size='sm')

    def _render_map(self, crt):
        """Show the signal route inside the opening briefing."""
        area = pygame.Rect(44, 58, 390, 105)
        if self.map_image:
            crt.canvas.blit(self.map_image, area)
        else:
            pygame.draw.rect(crt.canvas, (9, 19, 35), area)
        route = route_ids()
        route_area = (60, 78, 355, 64)
        points = map_points(route_area)
        for source, destination in zip(route, route[1:]):
            if source in points and destination in points:
                pygame.draw.lines(crt.canvas, (73, 125, 148), False,
                                  leg_points(source, destination, route_area), 1)
        for index, loc_id in enumerate(route[:-1]):
            if loc_id not in points:
                continue
            x, y = points[loc_id]
            color = (255, 213, 115) if index == 0 else (115, 236, 255)
            pygame.draw.circle(crt.canvas, (8, 20, 34), (x, y), 5)
            pygame.draw.circle(crt.canvas, color, (x, y), 3, 1)
            label = 'EARTH' if index == 0 else str(index)
            width = crt.font_sm.size(label)[0]
            label_x, label_y = (x - width - 7, y - 6) if index == 0 else (x - width // 2, y + 5)
            pygame.draw.rect(crt.canvas, (5, 13, 23), (label_x - 1, label_y, width + 2, 10))
            crt.draw_text(label, label_x, label_y, color=color, size='sm')
        crt.draw_text('11 WORLDS / 11 GUARDIANS / RETURN TO EARTH', 50, 61,
                      color=(231, 233, 211), size='sm')
