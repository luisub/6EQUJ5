"""Measured story pages and consistent next/back controls."""

import pygame

from .text import wrap_text_pixels
from .viewport import window_to_logical

NEXT_BUTTON = pygame.Rect(298, 212, 140, 25)
BACK_BUTTON = pygame.Rect(42, 212, 140, 25)
PAPER = (232, 235, 227)
MUTED = (156, 180, 188)
CYAN = (112, 223, 229)
GOLD = (241, 201, 123)


def paginate(pages, font, width=396, lines_per_page=6):
    """Keep all authored text, splitting long pages at measured line boundaries."""
    result = []
    for page in pages:
        lines = wrap_text_pixels(page['text'], font, width) or ['']
        for start in range(0, len(lines), lines_per_page):
            result.append({**page, 'text': '\n'.join(lines[start:start + lines_per_page])})
    return result


def action(event, crt):
    """Mouse clicks activate buttons only; held-key repeats cannot skip pages."""
    if event.type == pygame.KEYDOWN and not getattr(event, 'repeat', False):
        if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e, pygame.K_F5):
            return 'next'
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            return 'back'
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        point = window_to_logical(event.pos, crt)
        if point is not None:
            if NEXT_BUTTON.collidepoint(point):
                return 'next'
            if BACK_BUTTON.collidepoint(point):
                return 'back'
    return None


def render_dialogue(crt, page, *, eyebrow, progress='', next_label='Next',
                    back_label='Back to observatory', detail='', save_pending=False,
                    portrait=None):
    """Draw readable text above the game without a scrolling terminal transcript."""
    shade = pygame.Surface((480, 270), pygame.SRCALPHA)
    shade.fill((1, 4, 10, 130))
    crt.canvas.blit(shade, (0, 0))
    panel = pygame.Rect(24, 30, 432, 218)
    pygame.draw.rect(crt.canvas, (8, 17, 25), panel, border_radius=4)
    pygame.draw.rect(crt.canvas, (65, 101, 115), panel, 1, border_radius=4)
    pygame.draw.rect(crt.canvas, CYAN, (24, 47, 3, 32))
    crt.draw_text(eyebrow, 42, 42, color=MUTED, size='sm', has_shadow=False)
    crt.draw_text(progress, 438 - crt.font_sm.size(progress)[0], 42,
                  color=MUTED, size='sm', has_shadow=False)
    title_size = 'lg' if crt.font_lg.size(page['title'])[0] <= 396 else 'md'
    crt.draw_text(page['title'], 42, 61, color=CYAN, size=title_size, has_shadow=False)
    left, width = (164, 274) if portrait is not None else (42, 396)
    if portrait is not None:
        crt.composite_native(portrait, (42, 92), (104, 104))
    for index, line in enumerate(wrap_text_pixels(page['text'], crt.font_md, width)):
        crt.draw_text(line, left, 92 + index * 16, color=PAPER, size='md', has_shadow=False)
    if save_pending:
        detail = 'Could not save. Please try again.'
        next_label = 'Retry save'
    crt.draw_text(detail, left, 195, color=GOLD if save_pending else MUTED, size='sm', has_shadow=False)
    for rect, label, primary in ((BACK_BUTTON, back_label, False), (NEXT_BUTTON, next_label, True)):
        pygame.draw.rect(crt.canvas, (38, 49, 51) if primary else (13, 27, 37), rect, border_radius=3)
        pygame.draw.rect(crt.canvas, GOLD if primary else (65, 101, 115), rect, 1, border_radius=3)
        crt.draw_text(label, rect.centerx - crt.font_sm.size(label)[0] // 2, rect.y + 7,
                      color=GOLD if primary else MUTED, size='sm', has_shadow=False)
    crt.draw_text('ENTER / A: NEXT     ESC / B: RETURN', 136, 253,
                  color=MUTED, size='sm', has_shadow=False)
