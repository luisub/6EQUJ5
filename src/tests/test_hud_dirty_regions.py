"""PURPOSE: Verify the bounded HUD flush has exact full-flush pixel parity.
CALLED BY: pytest tests/test_hud_dirty_regions.py.
HOW TO MODIFY: Cover caller staging, threat extents, presentation and scene overlays.
"""
from itertools import product
from types import SimpleNamespace

import pygame
import pytest

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.ui.hud import render_global_hud


@pytest.fixture
def display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.init(); pygame.display.set_mode((960, 540))
    yield
    pygame.quit()


def test_hud_regional_batch_matches_full_flush_in_144_states_and_crt_modes(display):
    crt = CRTRenderer(scale=1)
    target = pygame.Surface((960, 540)).convert()
    threats = ((None, 19), ('LOCKED', 19), ('LOCKED', 65),
               ('AIMING', 34), ('AIMING', 65), ('LOCKED', 120))
    cases = list(product((1, 25, 50, 100), (0.0, .4), threats, (None, 'warning', 'danger')))
    assert len(cases) == 144

    def draw(regional, hp, charge, threat, y, kind):
        crt.clear((5, 9, 15))
        pygame.draw.rect(crt.canvas, (52, 76, 105), (0, 100, 480, 170))
        pygame.draw.rect(crt.canvas, (140, 70, 30, 100), (245, 14, 60, 70))
        # Text forces a full prior scene flush, satisfying staging_cleared.
        crt.draw_text('SCENE // PROMPT', 110, 215)
        player = SimpleNamespace(health=hp, charge_timer=charge, charge_threshold=.6)
        objective = SimpleNamespace(title='A LONG STATUS PROMPT WITH A WIDE LABEL')
        notice = None if kind is None else SimpleNamespace(kind=kind, title='NOTICE', text='POSSIBLE OVERLAP')
        render_global_hud(crt, None, player=player, objective=objective,
                          notification=notice, threat_level=threat, threat_y=y,
                          staging_cleared=regional)
        # A later logical draw must retain its ordering over the HUD output.
        pygame.draw.rect(crt.canvas, (13, 190, 210), (400, 240, 9, 7))
        native = pygame.image.tobytes(crt.finalize_frame(), 'RGBA')
        presented = []
        for enabled in (False, True):
            crt.is_crt_enabled = enabled
            crt.present(target)
            presented.append(pygame.image.tobytes(target, 'RGBA'))
        return native, presented

    for hp, charge, (threat, y), notice in cases:
        full = draw(False, hp, charge, threat, y, notice)
        bounded = draw(True, hp, charge, threat, y, notice)
        assert full == bounded, (hp, charge, threat, y, notice)
    print('144 HUD states matched at native density and in CRT on/off presentation')


@pytest.mark.parametrize('scene_kind,intro_or_prompt,paused', [
    ('field', 'CHECKPOINT', False), ('field', 'CHECKPOINT', True),
    ('field', 'HIT', False), ('field', 'HIT', True),
    ('field', 'context', False), ('field', 'context', True),
    ('boss', 'intro', False), ('boss', 'intro', True),
    ('boss', 'combat', False), ('boss', 'combat', True),
])
def test_real_scene_hud_matches_full_flush_with_pause_intro_and_prompts(
        display, tmp_path, monkeypatch, scene_kind, intro_or_prompt, paused):
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path),
                               settings_store=SettingsStore(tmp_path))
    try:
        assert machine.start_new_game()[0]
        if scene_kind == 'field':
            machine.change_state(config.STATE_FIELD_OPS)
            scene = machine.current_scene
            if intro_or_prompt == 'context':
                scene.player.x = 20; scene.player.y = 192
                scene.player.rect.topleft = (20, 192)
                scene.prompt_text = 'AIRLOCK'
            else:
                scene.prompt_text = intro_or_prompt
            scene.player.health = 47
            scene.player.charge_timer = .4
            scene.objective_tracker.post_notification('WARNING', 'OVERLAPPING HUD TEST', 'warning')
        else:
            machine.change_state(config.STATE_BOSS_BOUNTY)
            scene = machine.current_scene
            scene.encounter_intro_remaining = 1.0 if intro_or_prompt == 'intro' else 0.0
            scene.boss.weak_point_exposed = True
            monkeypatch.setattr(scene, '_active_threat', lambda: 'LOCKED')
        if paused:
            machine.open_pause()
        machine.crt.glitch_timer_ms = 0
        original = machine.crt.text_batch
        with monkeypatch.context() as patch:
            patch.setattr(machine.crt, 'text_batch', lambda dirty_region=None: original())
            machine.render()
            baseline = pygame.image.tobytes(machine.crt.render_surface, 'RGBA')
        machine.render()
        actual = pygame.image.tobytes(machine.crt.render_surface, 'RGBA')
        assert actual == baseline
    finally:
        machine.close()
