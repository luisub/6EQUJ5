"""PURPOSE: Verify readable, non-colliding ambient service traffic.
CALLED BY: pytest tests/test_environment_activity.py.
HOW TO MODIFY: Preserve authored alpha, ground anchoring, pause and cached rendering.
"""
import pygame
import pytest

from video_game.engine.config import ASSETS_DIR
from video_game.engine.environment_activity import ServiceTraffic
from video_game.engine.world import Camera


@pytest.fixture
def display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.display.quit()


def test_traffic_uses_solid_cutout_with_grounded_wheels_and_no_frame_io(display, monkeypatch):
    traffic = ServiceTraffic(ASSETS_DIR)
    source = pygame.image.load(str(ASSETS_DIR / 'environments/ohio_salvage_v1/wagon_168x76_rgba.png')).convert_alpha()
    expected = pygame.transform.scale(source, (72, 33))
    assert traffic.left.get_size() == (72, 33)
    assert traffic.left.get_alpha() == 255
    assert pygame.image.tobytes(traffic.left, 'RGBA') == pygame.image.tobytes(expected, 'RGBA')
    mask = pygame.mask.from_surface(traffic.left, 254)
    assert 0 < mask.count() < 72 * 33
    visible = pygame.mask.from_surface(traffic.left, 0).count()
    assert pygame.mask.from_surface(traffic.left, 239).count() / visible > 0.9
    assert traffic.left.get_bounding_rect().bottom == 33
    camera = Camera(); camera.set_world_bounds(1280, 288); camera.x = 100; camera.y = 18
    class Recorder:
        def blit(self, image, dest):
            self.image, self.dest = image, dest
    dest = Recorder()
    monkeypatch.setattr(pygame.image, 'load', lambda *_a, **_kw: pytest.fail('render loaded an image'))
    traffic.render(dest, camera)
    assert dest.dest == (204, 189)
    assert dest.dest[1] + dest.image.get_bounding_rect().bottom == 240 - camera.y
    traffic.update(0.1)
    assert traffic.elapsed == pytest.approx(0.1)
    traffic.update(0.1, paused=True)
    assert traffic.elapsed == pytest.approx(0.1)
    assert not hasattr(traffic, 'rect')
