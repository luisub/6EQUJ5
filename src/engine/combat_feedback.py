"""PURPOSE: Bounded electric cores, warm destruction and matching local light.
CALLED BY: Field/boss scenes and energy projectile presentation.
HOW TO MODIFY: Keep contrast, native pixel detail and strict event/cache caps.

Native-density overlays keep authored backgrounds intact. No simulation changes,
full-screen flashes, time-based render randomness or unbounded particle pools.
"""
import math

import pygame

CYAN = (82, 220, 255)
GOLD = (255, 210, 100)
ORANGE = (255, 132, 48)


def draw_energy_bolt(surface, start, end, phase=0, color=CYAN):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length < 2:
        return
    nx, ny = -dy / length, dx / length
    points = []
    for i in range(9):
        t = i / 8
        bend = math.sin(i * 2.4 + phase * 1.8) * math.sin(t * math.pi) * min(3, length / 10)
        points.append((round(start[0] + dx * t + nx * bend), round(start[1] + dy * t + ny * bend)))
    pygame.draw.lines(surface, tuple(c // 6 for c in color), False, points, 7)
    pygame.draw.lines(surface, tuple(c // 2 for c in color), False, points, 4)
    pygame.draw.lines(surface, color, False, points, 2)
    pygame.draw.lines(surface, (239, 255, 255), False, points, 1)
    # A finer complementary strand creates an electrical, rather than solid, core.
    thread = [(round(x + nx * 2), round(y + ny * 2)) for x, y in points[1:-1]]
    pygame.draw.lines(surface, (255, 218, 142), False, thread, 1)


class CombatFeedback:
    MAX_EVENTS = 24

    def __init__(self):
        self.events = []
        self.clock = 0.0
        self.glows = {}
        self.stamps = {}

    def clear(self):
        self.events.clear()
        self.clock = 0.0

    def emit(self, x, y, kind='hit', text='', color=None):
        duration = {'hit': .36, 'destroy': .65, 'pickup': 1.0, 'checkpoint': 1.0,
                    'hurt': .45, 'expired': 1.1}.get(kind, .5)
        color = color or (ORANGE if kind in ('destroy', 'hurt') else
                          GOLD if kind in ('pickup', 'checkpoint', 'expired') else CYAN)
        self.events.append(dict(x=x, y=y, kind=kind, text=text, color=color,
                                life=duration, duration=duration))
        self.events[:] = self.events[-self.MAX_EVENTS:]

    def hit(self, result):
        if not result.hit:
            return
        self.emit(result.hit_x, result.hit_y, 'destroy' if result.target_killed else 'hit',
                  f'-{result.damage_dealt}' if result.damage_dealt else 'BLOCKED')

    def update(self, dt, paused=False):
        if paused or dt <= 0:
            return
        self.clock += dt
        for event in self.events:
            event['life'] -= dt
        self.events[:] = [event for event in self.events if event['life'] > 0]

    def _glow(self, color, level):
        key = (color, level)
        if key not in self.glows:
            image = pygame.Surface((128, 96))
            for radius in range(48, 0, -3):
                strength = (1 - radius / 51) ** 2 * level / 7 * .24
                tint = tuple(round(c * strength) for c in color)
                pygame.draw.ellipse(image, tint, (64 - round(radius * 1.3), 48 - radius,
                                                  round(radius * 2.6), radius * 2))
            if len(self.glows) >= 64:
                self.glows.pop(next(iter(self.glows)))
            self.glows[key] = image
        return self.glows[key]

    def _stamp(self, kind, color, frame):
        key = (kind, color, frame)
        if key in self.stamps:
            return self.stamps[key]
        image = pygame.Surface((112, 112), pygame.SRCALPHA)
        t = frame / 11
        cx = cy = 56
        major = kind in ('destroy', 'pickup', 'checkpoint')
        radius = round(5 + t * (40 if major else 21))
        alpha = round(230 * (1 - t))
        pygame.draw.ellipse(image, (*color, alpha), (cx - radius, cy - radius // 3,
                                                    radius * 2, max(2, radius * 2 // 3)), 2)
        # Broad first flash -> broken rays -> drifting square embers.
        for i in range(10 if major else 6):
            angle = i * math.tau / (10 if major else 6) + .18
            inner = radius * .45
            outer = radius * (1.05 + .2 * math.sin(i * 8))
            a = (round(cx + math.cos(angle) * inner), round(cy + math.sin(angle) * inner))
            b = (round(cx + math.cos(angle + .12) * outer), round(cy + math.sin(angle + .12) * outer))
            pygame.draw.line(image, (*color, alpha), a, b, 2)
            pygame.draw.rect(image, (255, 245, 195, alpha), (b[0], b[1], 2, 2))
        if frame < 5:
            core = 10 - frame * 2
            pygame.draw.polygon(image, (235, 255, 255, alpha),
                                [(cx - core * 2, cy), (cx - 2, cy - 2), (cx, cy - core * 2),
                                 (cx + 2, cy - 2), (cx + core * 2, cy), (cx + 2, cy + 2),
                                 (cx, cy + core * 2), (cx - 2, cy + 2)])
        if len(self.stamps) >= 256:
            self.stamps.pop(next(iter(self.stamps)))
        self.stamps[key] = image
        return image

    def render(self, crt, camera, projectiles=(), preceding_layers=()):
        layers = list(preceding_layers)
        # A few moving pools of matching light connect energy to the scene.
        for shot in [p for p in projectiles if p.active and p.is_primary_discharge][-6:]:
            if shot.weapon_type not in ('starter_maser', 'arc_lance', 'nova_scatter'):
                continue
            x, y = camera.world_to_screen(shot.x, shot.y)
            if -64 <= x <= 544 and -48 <= y <= 318:
                glow = self._glow(ORANGE if shot.weapon_type == 'nova_scatter' else CYAN, 3)
                layers.append((glow, (x * 2 - 64, y * 2 - 48), pygame.BLEND_RGB_ADD))
        labels = []
        for event in self.events:
            x, y = camera.world_to_screen(event['x'], event['y'])
            if not (-56 <= x <= 536 and -56 <= y <= 326):
                continue
            t = 1 - event['life'] / event['duration']
            level = max(0, round((1 - t) * 7))
            glow = self._glow(event['color'], level)
            layers.append((glow, (2 * x - 64, 2 * y - 48), pygame.BLEND_RGB_ADD))
            if event['kind'] != 'expired':
                stamp = self._stamp(event['kind'], event['color'], min(11, int(t * 12)))
                layers.append((stamp, (2 * x - 56, 2 * y - 56), 0))
            if event['text']:
                labels.append((event, x, y - 18 - round(t * 18)))
        if layers:
            crt.composite_native_effects(layers)
        # All staged pixels were flushed with the effect layers just above.
        with crt.text_batch(dirty_region=(0, 0, 0, 0)):
            for event, x, y in labels[-8:]:
                width = crt.font_sm.size(event['text'])[0]
                x = max(6, min(474 - width, x - width // 2))
                y = max(112, min(221, y))
                crt.draw_text(event['text'], x, y, color=event['color'], size='sm')


ALIEN_ATMOSPHERES = {
    # Color and motion belong to the environment, below weapon/attack contrast.
    'alien_008': ('dust', (66, 112, 113), -3, 2),
    'alien_009': ('dust', (117, 103, 76), 7, -1),
    'alien_006': ('embers', (116, 87, 70), -5, -6),
    'alien_002': ('drift', (86, 89, 120), 11, 0),
    'alien_scan_h': ('mist', (88, 108, 100), -2, 5),
    'alien_010': ('rain', (71, 104, 95), -7, 26),
    'alien_007': ('signal', (97, 94, 124), 0, -10),
}


class SceneAtmosphere:
    """Sparse far/near weather, drawn behind combat and outside the HUD band."""
    def __init__(self, room_id=''):
        self.elapsed = 0.0
        world_id = room_id.removesuffix('_field').removesuffix('_arena')
        self.profile = ALIEN_ATMOSPHERES.get(world_id)
        self.motes = ()
        if self.profile:
            _, color, _, _ = self.profile
            self.motes = tuple(
                (index * 113 % 480, index * 47 % 156,
                 .55 if index < 8 else 1.0, .08 if index < 8 else .22,
                 tuple(round(channel * (.6 if index < 8 else 1)) for channel in color))
                for index in range(16)
            )

    def update(self, dt, paused=False):
        if not paused and isinstance(dt, (int, float)) and math.isfinite(dt) and dt > 0:
            self.elapsed = (self.elapsed + min(dt, .1)) % 3600

    def render(self, crt, camera):
        if not math.isfinite(camera.x):
            return
        if self.profile is None:
            for index in range(12):
                x = round((index * 67 + self.elapsed * (1 + index % 3) - camera.x * .12) % 480)
                y = round(88 + (index * 31) % 127 + 3 * math.sin(self.elapsed * .35 + index))
                pygame.draw.line(crt.canvas, (78, 103, 113), (x, y), (x + 1, y), 1)
            return
        kind, _, vx, vy = self.profile
        for index, (seed_x, seed_y, speed, parallax, color) in enumerate(self.motes):
            sway = 2 * math.sin(self.elapsed * .45 + index) if kind in ('snow', 'dust', 'embers') else 0
            x = round((seed_x + self.elapsed * vx * speed + sway - camera.x * parallax) % 480)
            y = 68 + round((seed_y + self.elapsed * vy * speed) % 156)
            if kind == 'rain':
                pygame.draw.line(crt.canvas, color, (x, y), (x - 1, y + (4 if speed == 1 else 2)))
            elif kind == 'mist':
                pygame.draw.line(crt.canvas, color, (x, y), (x + 2, y + 1))
            elif kind == 'signal':
                pygame.draw.line(crt.canvas, color, (x, y), (x, y + 2))
            else:
                pygame.draw.line(crt.canvas, color, (x, y), (x + 1, y))
