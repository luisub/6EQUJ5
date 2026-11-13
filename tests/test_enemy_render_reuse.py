"""
MODULE: tests/test_enemy_render_reuse.py
PURPOSE: Verify enemy render output and bounded reuse of telegraph and sprite surfaces.
CALLED BY: pytest.
HOW TO MODIFY: Preserve pre-change pixel hashes and test observable cache invalidation.
"""

import hashlib

import pygame
import pytest

from video_game.engine.enemies import CoreReconDrone, EnemyManager, ShieldHound, StaticHound
from video_game.engine.world import Camera


@pytest.fixture
def display(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def sprite(seed):
    image = pygame.Surface((11, 9), pygame.SRCALPHA)
    for y in range(9):
        for x in range(11):
            image.set_at((x, y), ((x * 19 + seed) % 256, (y * 23 + seed) % 256,
                                  (x * y + seed * 3) % 256, 50 + (x * 13 + y * 7) % 206))
    return image


def test_render_matches_original_pixels_and_reuses_surfaces(display, monkeypatch):
    manager = EnemyManager()
    manager.sprite_cache.clear()
    manager.sprite_cache.update({"static_hound_patrol_1": sprite(9),
                                 "static_hound_patrol_2": sprite(15),
                                 "shield_hound_patrol_1": sprite(31)})
    drone_a, drone_b = CoreReconDrone("a", 40, 35), CoreReconDrone("b", 40, 35)
    for drone in (drone_a, drone_b):
        drone.telegraph_active = True
        drone.locked_aim_vector = (1.0, 0.0)
    hound, shield = StaticHound("h", 15, 65), ShieldHound("s", 95, 65)
    hound.facing = shield.facing = "right"
    manager.enemies.extend((drone_a, drone_b, hound, shield))
    camera = Camera(160, 100)
    original_surface, original_flip = pygame.Surface, pygame.transform.flip

    def draw(size=(160, 100)):
        output = original_surface(size, pygame.SRCALPHA)
        output.fill((21, 48, 67, 201))
        counts = [0, 0]
        def counted_surface(*args, **kwargs):
            counts[0] += 1
            return original_surface(*args, **kwargs)
        def counted_flip(*args, **kwargs):
            counts[1] += 1
            return original_flip(*args, **kwargs)
        with monkeypatch.context() as patch:
            patch.setattr(pygame, "Surface", counted_surface)
            patch.setattr(pygame.transform, "flip", counted_flip)
            manager.render(output, camera)
        return hashlib.sha256(pygame.image.tobytes(output, "RGBA")).hexdigest(), counts

    # Golden RGBA hashes captured from the original implementation before changes.
    first = "7715729f675f93ffc4771a240cccd6312256ed483c5f23ad904b8e8c3b45e65e"
    assert draw() == (first, [1, 2])
    assert draw() == (first, [0, 0])
    hound.facing = shield.facing = "left"
    assert draw() == ("bbc5bab1e7a9dc82b781dc053736922e19a4d9314f9e26299a66db4d7435af34", [0, 0])
    hound.facing = shield.facing = "right"
    assert draw((200, 120)) == ("58170084ae51b7b6776f6dc0daaa46aa1ec7659cf9abddd1adc9c64fa9642dbc", [1, 0])
    manager.sprite_cache["static_hound_patrol_1"] = sprite(99)
    assert draw((200, 120)) == ("0e64b78fa6495ee9dd89be3d43d83c7350ec9bf49dd76844cd708a709b241fae", [0, 1])
    hound.anim_time = 0.13
    drone_a.telegraph_locked = True
    drone_a.target_aim_pos = (130, 40)
    assert draw((200, 120)) == ("148a866273435d24a1906c19c4f7b34bf9ad67681850e04ac32cbd3ea52dcfeb", [0, 1])
    for key in ("static_hound_patrol_1", "static_hound_patrol_2", "shield_hound_patrol_1"):
        del manager.sprite_cache[key]
    assert draw((200, 120)) == ("41352254e5d2fcf229ba8466614429d02e830a47e63f216d083947d165c60ea6", [0, 0])
    manager.clear()
    assert manager._telegraph_surface is None
    assert not manager._flipped_sprites


def test_reloading_enemy_sprites_invalidates_mirrored_sources(display, monkeypatch, tmp_path):
    import video_game.engine.enemies as enemies

    directory = tmp_path / "static_hound"
    directory.mkdir()
    path = directory / "patrol_1.png"
    pygame.image.save(sprite(9), path)
    monkeypatch.setattr(enemies, "ENEMY_SPRITES_DIR", tmp_path)
    manager = EnemyManager()
    hound = StaticHound("h", 15, 15)
    hound.facing = "right"
    manager.enemies.append(hound)
    target = pygame.Surface((64, 64), pygame.SRCALPHA)
    manager.render(target, Camera(64, 64))
    before = pygame.image.tobytes(target, "RGBA")
    pygame.image.save(sprite(99), path)
    manager._load_sprites()
    target.fill((0, 0, 0, 0))
    manager.render(target, Camera(64, 64))
    assert pygame.image.tobytes(target, "RGBA") != before
    assert manager._flipped_sprites["static_hound_patrol_1"][0] is manager.sprite_cache["static_hound_patrol_1"]
