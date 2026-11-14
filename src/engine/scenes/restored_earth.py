"""Earned, peaceful Denver epilogue with a walkable park and living scenery."""
import hashlib
import json
import math
from pathlib import Path

import pygame

from .. import config
from ..alien_journey import journey_data, ledger, save_ledger
from ..animation import AnimationPlayer, load_mateo_animations
from ..campaign_scenery import load_campaign_background
from ..native_room_assets import _inside_without_symlinks
from ..ui.text import wrap_text_pixels
from ..ui.viewport import window_to_logical
from .base import BaseScene

NEXT = pygame.Rect(371, 117, 91, 21)
MESSAGES = pygame.Rect(250, 241, 105, 22)
FINISH = pygame.Rect(363, 241, 105, 22)


def load_families(root):
    """Decode the optional four-pose family strip once on entry."""
    try:
        relative = Path('sprites/people/park_family')
        manifest = json.loads(_inside_without_symlinks(root, relative / 'manifest.json').read_text())
        path = _inside_without_symlinks(root, relative / 'walk.png')
        if manifest['dimensions'] != [512, 96] or hashlib.sha256(path.read_bytes()).hexdigest() != manifest['sha256']:
            return ()
        strip = pygame.image.load(str(path)).convert_alpha()
        if strip.get_size() != (512, 96):
            return ()
        return tuple(strip.subsurface((i * 128, 0, 128, 96)).copy() for i in range(4))
    except (OSError, ValueError, KeyError, TypeError, pygame.error):
        return ()


class RestoredEarthScene(BaseScene):
    def __init__(self, machine):
        super().__init__(machine)
        self.elapsed = 0.0
        self.page = 0
        self.pages = []
        self.save_pending = False
        self.background = None
        self.families = ()
        self.animator = None
        self.hero_x = 400.0
        self.camera_x = 160.0

    def on_enter(self, **kwargs):
        progress = ledger(self.machine.campaign)
        if progress.get('stage') != 'complete' or not self.machine.campaign.state.room_flags.get('earth_ai_defeated'):
            self.machine.change_state(config.STATE_BUNKER_HUB)
            return
        root = self.machine.assets.root
        self.background = load_campaign_background(root, 'denver_restored')
        self.view = pygame.Surface((960, 540)).convert()
        self.light = pygame.Surface((960, 540), pygame.SRCALPHA)
        self.families = load_families(root)
        self.families_left = tuple(pygame.transform.flip(f, True, False) for f in self.families)
        # A separate animation player avoids leaking park movement into combat.
        clips = load_mateo_animations(root, outfit='olive_field')
        self.animator = AnimationPlayer(clips, scale_factor=.25)
        content = journey_data()['final_earth'].get('restoration', {})
        self.pages = content.get('pages', [])
        value = progress.get('restoration_page', 0)
        self.page = value if type(value) is int and 0 <= value <= len(self.pages) else 0
        self.save_pending = False
        self.elapsed = 0.0
        self.hero_x, self.camera_x = 400.0, 160.0
        self.machine.input.release_all()
        self.water = []
        if self.background is not None:
            for i in range(80):
                x, y = 350 + (i * 113 % 1250), 277 + (i * 31 % 110)
                r, g, b, *_ = self.background.get_at((x, y))
                if b > 85 and g > r * 1.15 and b > r:
                    self.water.append((x, y, i * 1.71))

    def on_exit(self):
        self.machine.input.release_all()

    def _advance(self):
        if self.page >= len(self.pages):
            self.page = 0  # Optional replay; completion remains earned and saved.
            return
        prior = ledger(self.machine.campaign)
        updated = dict(prior, restoration_page=self.page + 1)
        save_ledger(self.machine.campaign, updated)
        if not self.machine.save_checkpoint():
            save_ledger(self.machine.campaign, prior)
            self.save_pending = True
            return
        self.page += 1
        self.save_pending = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and not getattr(event, 'repeat', False):
            if event.key in (pygame.K_RETURN, pygame.K_e, pygame.K_F5):
                self._advance()
            elif event.key == pygame.K_ESCAPE:
                self.machine.change_state(config.STATE_TITLE_BOOT)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = window_to_logical(event.pos, self.machine.crt)
            if point is None:
                return
            if self.page < len(self.pages) and NEXT.collidepoint(point):
                self._advance()
            elif self.page >= len(self.pages):
                if FINISH.collidepoint(point):
                    self.machine.change_state(config.STATE_TITLE_BOOT)
                elif MESSAGES.collidepoint(point):
                    self._advance()

    def update(self, dt_seconds):
        if not math.isfinite(dt_seconds) or dt_seconds <= 0:
            return
        dt = min(dt_seconds, .1)
        self.elapsed += dt
        direction = int(self.machine.input.held('move_right')) - int(self.machine.input.held('move_left'))
        previous = self.hero_x
        self.hero_x = max(32, min(928, self.hero_x + direction * 58 * dt))
        moving = self.hero_x != previous
        self.animator.set_state('walk' if moving else 'idle')
        if moving:
            self.animator.set_facing('right' if direction > 0 else 'left')
        self.animator.update(dt)
        self.camera_x = max(0, min(480, self.hero_x - 240))

    def _fallback_park(self):
        self.view.fill((148, 206, 214))
        pygame.draw.rect(self.view, (66, 130, 78), (0, 170, 960, 370))
        pygame.draw.ellipse(self.view, (72, 157, 174), (120, 250, 720, 170))
        pygame.draw.rect(self.view, (203, 190, 148), (0, 420, 960, 38))
        for x in range(20, 960, 160):
            pygame.draw.rect(self.view, (88, 86, 52), (x, 150, 15, 185))
            pygame.draw.circle(self.view, (40, 112, 65), (x + 8, 150), 74)

    def render(self, crt):
        crt.clear()
        offset = round(self.camera_x * 2)
        if self.background is not None:
            self.view.blit(self.background, (0, 0), (offset, 0, 960, 540))
        else:
            self._fallback_park()
        # Reflection glints stay within water-colored pixels sampled at entry.
        for x, y, phase in self.water:
            strength = max(0, math.sin(self.elapsed * 1.8 + phase))
            if strength > .55:
                color = (round(120 + strength * 100), round(191 + strength * 55), 211)
                pygame.draw.line(self.view, color, (x - offset, y), (x - offset + 3 + round(strength * 6), y))
        crt.composite_opaque_background(self.view, known_clean=True)
        # Independent gait timing follows each family's traveled distance.
        for index, (start, speed) in enumerate(((160, 10), (560, -8), (850, 12))):
            x = (start + self.elapsed * speed + 80) % 1120 - 80
            pose = int(self.elapsed * abs(speed) / 5) % 4
            frames = self.families if speed > 0 else self.families_left
            if frames:
                crt.composite_native(frames[pose], (x - self.camera_x - 32, 177 + index % 2 * 2), (64, 48))
            else:
                # Missing optional art still leaves a living, leg-animated park.
                for person, height in enumerate((24, 15, 23)):
                    sx = round(x - self.camera_x + person * 9)
                    stride = round(math.sin(self.elapsed * 5 + person) * 3)
                    pygame.draw.circle(crt.canvas, (175, 126, 83), (sx, 221 - height), 3)
                    pygame.draw.line(crt.canvas, (52, 97 + person * 25, 104), (sx, 224 - height), (sx, 214), 5)
                    pygame.draw.lines(crt.canvas, (48, 62, 64), False, [(sx - stride, 222), (sx, 214), (sx + stride, 222)], 2)
        # Birds alternate lifted/downstroke wings and short glides.
        for i in range(9):
            x = (i * 73 + self.elapsed * (13 + i % 3 * 3)) % 540 - 30
            y = 82 + i % 3 * 14 + math.sin(self.elapsed * .8 + i) * 5
            wing = round(math.sin(self.elapsed * 6 + i) * 3)
            wings = [(x - 4, y - wing), (x, y), (x + 4, y - wing)]
            pygame.draw.lines(crt.canvas, (39, 79, 85), False, wings, 2)
            pygame.draw.lines(crt.canvas, (235, 237, 211), False, wings, 1)
            pygame.draw.line(crt.canvas, (235, 237, 211), (x, y), (x + 2, y + 1))
        sprite = self.animator.surface_for_density(2)
        px, py = self.animator.get_render_dest(self.hero_x - self.camera_x, 222)
        crt.composite_native(sprite, (px, py), self.animator.current_surface.get_size())
        self.light.fill((0, 0, 0, 0))
        for i in range(22):
            x = (i * 71 + self.elapsed * 7) % 960
            y = 130 + (i * 43 % 280) + math.sin(self.elapsed + i) * 4
            pygame.draw.circle(self.light, (255, 236, 152, 55), (round(x), round(y)), 1)
        crt.composite_native(self.light, (0, 0), (480, 270))
        pygame.draw.rect(crt.canvas, (15, 42, 32), (12, 9, 267, 19), border_radius=3)
        crt.draw_text('EARTH IS FREE  /  CENTRAL PARK, DENVER', 19, 14, color=(236, 234, 200), size='sm', has_shadow=False)
        if self.elapsed < 8:
            pygame.draw.rect(crt.canvas, (15, 42, 32), (309, 9, 159, 19), border_radius=3)
            crt.draw_text('THREE SPRINGS LATER', 320, 14, color=(236, 234, 200), size='sm', has_shadow=False)
        if self.page < len(self.pages):
            page = self.pages[self.page]
            pygame.draw.rect(crt.canvas, (13, 37, 30), (12, 36, 456, 108), border_radius=4)
            pygame.draw.rect(crt.canvas, (149, 189, 123), (12, 36, 456, 108), 1, border_radius=4)
            crt.draw_text(page['title'], 23, 46, color=(241, 222, 150), size='md', has_shadow=False)
            for n, line in enumerate(wrap_text_pixels(page['text'], crt.font_md, 424)):
                crt.draw_text(line, 23, 68 + n * 14, color=(228, 239, 218), size='md', has_shadow=False)
            pygame.draw.rect(crt.canvas, (49, 79, 49), NEXT, border_radius=3)
            crt.draw_text('Retry save' if self.save_pending else 'Next  >', NEXT.x + 14, NEXT.y + 6,
                          color=(247, 229, 166), size='sm', has_shadow=False)
            detail = 'Could not save. Please try again.' if self.save_pending else f'{self.page + 1} / {len(self.pages)}   ENTER / A: NEXT'
            crt.draw_text(detail, 23, 125, color=(193, 207, 179), size='sm', has_shadow=False)
        else:
            for rect, label in ((MESSAGES, 'Read messages'), (FINISH, 'Return to title')):
                pygame.draw.rect(crt.canvas, (17, 48, 34), rect, border_radius=3)
                crt.draw_text(label, rect.x + 9, rect.y + 7, color=(232, 234, 197), size='sm', has_shadow=False)
        pygame.draw.rect(crt.canvas, (17, 48, 34), (12, 241, 230, 22), border_radius=3)
        crt.draw_text('ARROWS: WALK   F2: PAUSE   ESC: TITLE', 18, 248, color=(232, 234, 197), size='sm', has_shadow=False)
