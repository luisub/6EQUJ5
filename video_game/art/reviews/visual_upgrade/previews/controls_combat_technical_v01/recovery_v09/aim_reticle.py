"""MODULE: video_game/engine/ui/aim_reticle.py
PURPOSE: Show a compact pointer or stick aim marker during combat.
CALLED BY: FieldOpsScene and BossScene before their HUD layers.
HOW TO MODIFY: Keep viewport mapping consistent with PlayerInput and avoid intercepting input.
"""
import pygame
from .. import config


def render_aim_reticle(crt, input_mgr, camera, player):
    source = getattr(input_mgr, 'aim_source', None)
    point = None
    if source == 'mouse' and input_mgr.mouse_position is not None:
        px, py = input_mgr.mouse_position
        if 0 <= px < crt.win_w and 0 <= py < crt.win_h:
            point = (round(px * config.INTERNAL_WIDTH / crt.win_w),
                     round(py * config.INTERNAL_HEIGHT / crt.win_h))
    elif source == 'controller' and input_mgr.controller_aim is not None:
        x, y = camera.world_to_screen(player.x + player.width / 2, player.y + player.height / 2)
        ax, ay = input_mgr.controller_aim
        point = (round(x + 34 * ax), round(y + 34 * ay))
    if point is None:
        return
    x = max(5, min(config.INTERNAL_WIDTH - 6, point[0]))
    y = max(5, min(config.INTERNAL_HEIGHT - 6, point[1]))
    pygame.draw.circle(crt.canvas, (3, 12, 9), (x, y), 5, 2)
    pygame.draw.circle(crt.canvas, (210, 255, 226), (x, y), 4, 1)
    pygame.draw.line(crt.canvas, (210, 255, 226), (x - 6, y), (x - 3, y))
    pygame.draw.line(crt.canvas, (210, 255, 226), (x + 3, y), (x + 6, y))
