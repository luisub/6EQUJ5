"""PURPOSE: Timed field weapons and reachable, visit-local supply cells.
CALLED BY: ArsenalManager and field/boss scenes. No campaign rewards or save data.
HOW TO MODIFY: Tune PROFILES; preserve collision, pause and transient lifecycle.
"""
import math

import pygame

from .weapons import AnalogWeapon, WeaponConfig, get_muzzle_world_pos, resolve_aim_vector
from .world import COLLISION_ONE_WAY, COLLISION_SOLID


PROFILES = {
    'arc_lance': dict(name='ARC LANCE', damage=90, cadence=.18, duration=18.0,
                      color=(90, 225, 255), spread=(0,), pierce=2),
    'nova_scatter': dict(name='NOVA SCATTER', damage=70, cadence=.23, duration=16.0,
                         color=(255, 169, 65), spread=(0, -10, 10), pierce=1),
}


def style_temporary_flash(flash, weapon_id):
    """Keep temporary muzzle accents compact and consistent with their shots."""
    if weapon_id in PROFILES:
        flash['color'] = (235, 255, 255) if weapon_id == 'arc_lance' else (255, 247, 205)
        flash['glow_color'] = PROFILES[weapon_id]['color']
        flash['radius'] = 7.0


class TemporaryWeapon(AnalogWeapon):
    """Hold either fire input to repeat; release never emits a stored charge."""

    def __init__(self, weapon_id):
        self.profile = PROFILES[weapon_id]
        super().__init__(WeaponConfig(id=weapon_id, name=self.profile['name'],
                                     damage=self.profile['damage'],
                                     fire_cadence=self.profile['cadence']))

    def update(self, dt, p_input, player, room, manager, is_paused=False):
        if is_paused or dt <= 0 or player.is_dead:
            return None
        self.cooldown_timer = max(0, self.cooldown_timer - dt)
        firing = any(getattr(p_input, name, False) for name in
                     ('fire_pressed', 'fire_held', 'auto_fire_pressed', 'auto_fire_held'))
        if not firing or self.cooldown_timer > 0 or not player.can_fire(room):
            return None
        dx, dy = resolve_aim_vector(p_input.move_x, p_input.move_y, player.facing,
                                    player.is_crouching, player.is_grounded,
                                    p_input.aim_x, p_input.aim_y)
        x, y = get_muzzle_world_pos(player)
        volley_hits = set()
        primary = None
        for offset in self.profile['spread']:
            angle = math.atan2(dy, dx) + math.radians(offset)
            shot = manager.spawn(x=x, y=y, dir_x=math.cos(angle), dir_y=math.sin(angle),
                                 speed=500, damage=self.cfg.damage, pierce_count=self.profile['pierce'],
                                 lifetime=1.1, beam_length=30, beam_thickness=2,
                                 weapon_type=self.id, color=self.profile['color'],
                                 volley_hit_target_ids=volley_hits,
                                 is_primary_discharge=offset == 0)
            primary = primary or shot
        self.cooldown_timer = self.cfg.fire_cadence
        player.trigger_fire_recoil(.10)
        return primary


class WeaponPickups:
    """Finite supplies on clear supported floor, collected by walking through."""

    def __init__(self, room, *, enabled=True, arena=False):
        self.items = []
        self.elapsed = 0.0
        if not enabled:
            return
        start = 144 if not arena else 176
        # Keep supplies beyond the dish's authored defense position; collect
        # them on the onward route instead of replacing its opening loadout.
        if room.room_id == 'act_01_dish_catwalk':
            start = min(960, room.width_px - 128)
        spacing = min(1600, max(256, room.width_px // 2)) if not arena else 304
        for index, desired_x in enumerate(range(start, room.width_px - 64, spacing)):
            if len(self.items) >= (2 if arena else 5):
                break
            # Search adjacent floor sites, prioritizing the main traversal height.
            site = None
            rows = sorted(range(3, room.height_tiles), key=lambda row: abs(row * room.tile_size - 240))
            for dx in range(0, 208, 16):
                x = desired_x + dx
                if x >= room.width_px - 48:
                    break
                for row in rows:
                    y = row * room.tile_size
                    rect = pygame.Rect(x - 8, y - 20, 16, 20)
                    clearance = room.check_rect_collision(rect.inflate(8, 16).move(0, -8))
                    if any(clearance[k] for k in ('solid', 'hazard', 'one_way')):
                        continue
                    if all(room.get_tile(col, row) in (COLLISION_SOLID, COLLISION_ONE_WAY)
                           for col in range(rect.left // room.tile_size, (rect.right - 1) // room.tile_size + 1)):
                        site = rect
                        break
                if site:
                    break
            if site:
                self.items.append({'rect': site, 'weapon_id': tuple(PROFILES)[index % 2], 'collected': False})

    def update(self, dt, player, feedback, paused=False):
        if paused or dt <= 0 or player.is_dead:
            return
        self.elapsed += dt
        for item in self.items:
            if item['collected'] or not player.rect.colliderect(item['rect'].inflate(8, 8)):
                continue
            item['collected'] = True
            player.arsenal.equip_temporary(item['weapon_id'])
            player.weapon = player.arsenal.active_weapon
            profile = PROFILES[item['weapon_id']]
            feedback.emit(*item['rect'].center, 'pickup', profile['name'], profile['color'])

    def render(self, crt, camera):
        for item in self.items:
            if item['collected']:
                continue
            x, y = camera.world_to_screen(*item['rect'].center)
            if not -40 <= x <= 520:
                continue
            y += round(2 * math.sin(self.elapsed * 3))
            color = PROFILES[item['weapon_id']]['color']
            pygame.draw.ellipse(crt.canvas, (70, 61, 28), (x - 13, y + 8, 26, 6), 1)
            pygame.draw.polygon(crt.canvas, (7, 22, 34), [(x, y - 10), (x + 9, y), (x, y + 10), (x - 9, y)])
            pygame.draw.polygon(crt.canvas, (255, 219, 128), [(x, y - 10), (x + 9, y), (x, y + 10), (x - 9, y)], 1)
            pygame.draw.lines(crt.canvas, color, False,
                              [(x + 2, y - 6), (x - 3, y), (x + 2, y), (x - 2, y + 6)], 2)
            label = PROFILES[item['weapon_id']]['name']
            width = crt.font_sm.size(label)[0]
            label_rect = pygame.Rect(x - width // 2 - 3, y - 25, width + 6, 12)
            pygame.draw.rect(crt.canvas, (6, 16, 24), label_rect)
            with crt.text_batch(dirty_region=label_rect):
                crt.draw_text(label, x - width // 2, y - 24, color=(255, 219, 128), size='sm')


def render_weapon_timer(crt, arsenal):
    if not arsenal or not arsenal.temporary_id:
        return
    profile = PROFILES[arsenal.temporary_id]
    panel = pygame.Rect(8, 81, 167, 27)
    pygame.draw.rect(crt.canvas, (5, 16, 27), panel)
    color = profile['color'] if arsenal.temporary_remaining > 3 else (255, 210, 110)
    pygame.draw.rect(crt.canvas, (35, 53, 66), (14, 100, 154, 3))
    pygame.draw.rect(crt.canvas, color, (14, 100, round(154 * arsenal.temporary_remaining / profile['duration']), 3))
    with crt.text_batch(dirty_region=panel):
        crt.draw_text(f"{profile['name']}  {math.ceil(arsenal.temporary_remaining)}s", 14, 85, color=color, size='sm')
