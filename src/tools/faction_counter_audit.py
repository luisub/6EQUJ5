"""PURPOSE: Capture fixture-based faction counter states via field key events.
CALLED BY: python -m video_game.tools.faction_counter_audit --output-dir PATH.
HOW TO MODIFY: Disclose fixtures; do not treat frames as progression or art review.
"""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

import pygame
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    pygame.init(); pygame.display.set_mode((480, 270))
    with TemporaryDirectory(prefix='6equj5-counter-audit-') as directory:
        game = GameStateMachine(CRTRenderer(), development=False, save_store=SaveStore(directory),
                                settings_store=SettingsStore(directory))
        def tick():
            game.input.begin_frame(); game.update(1 / 60)
        def key(code):
            game.input.begin_frame()
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))
            game.update(1 / 60)
            game.handle_event(pygame.event.Event(pygame.KEYUP, key=code))
        def until(predicate, limit=180):
            for _ in range(limit):
                tick()
                if predicate(): return
            raise RuntimeError('counter frame condition timed out')
        def capture(name):
            game.render(); native = game.crt.render_surface.copy()
            for suffix, surface in (('native', native), ('2x', pygame.transform.scale(native, (1920, 1080)))):
                path = output / f'{name}_{suffix}.png'
                with path.open('xb') as stream: pygame.image.save(surface, stream, path.name)
        try:
            assert game.start_new_game()[0]
            for eid, civ in [('FASR-001', 'FASR-001'), ('FASR-002', 'FASR-002'), ('FASR-004', 'FASR-004'),
                             ('reality_anchor_1977', 'FASR-001')]:
                game.campaign.apply_event({'event_id': eid, 'type': 'record_contact',
                                           'payload': {'civilization_id': civ}})
            game.campaign.apply_event({'event_id': 'capture-fixture', 'type': 'defeat_greenkeeper'})
            key(pygame.K_m); field = game.current_scene
            key(pygame.K_t); capture('cover_1977')
            key(pygame.K_t)
            for index in range(4):
                key(pygame.K_n); capture(f'hint_pair_{index + 1}')
            for _ in range(4):
                if field.player.abilities.selected_ability_id == 'time_dilation': break
                key(pygame.K_r)
            assert field.player.abilities.selected_ability_id == 'time_dilation'
            key(pygame.K_k)
            assert field.player.abilities.selected_ability.is_active
            capture('ability_active_hint')
            until(lambda: not field.player.abilities.selected_ability.is_active, limit=180)
            assert field.player.abilities.selected_ability.cooldown_timer > 0
            capture('ability_cooldown_hint')
            def select(pair, index, x=130, y=None):
                # N cycles; pair is relative to the current selection.
                for _ in range(pair): key(pygame.K_n)
                target = field.enemy_manager.enemies[index]
                target.x = target.spawn_x = x
                target.y = target.spawn_y = 240 - target.cfg.height if y is None else y
                target.rect.topleft = (int(target.x), int(target.y))
                target.patrol_left = target.patrol_right = x
                field.enemy_manager.enemies = [target]
                return target
            watcher = select(2, 1, y=204); watcher.teleport_cooldown = 99
            until(lambda: watcher.is_channeling); capture('watcher_channel')
            key(pygame.K_q); key(pygame.K_q); key(pygame.K_x)
            assert field.player.arsenal.active_weapon_id == 'emp_bola'
            until(lambda: watcher.has_status('stun')); tick(); capture('watcher_emp')
            guardian = select(1, 1)
            until(lambda: guardian.telegraph_active); capture('guardian_windup')
            until(lambda: bool(field.enemy_manager.projectiles))
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
            for _ in range(6): tick()
            capture('guardian_jump')
            game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))
            # Wait for player to land before showing the splicer projectile.
            for _ in range(60): tick()
            splicer = select(4, 0, x=180)
            until(lambda: splicer.telegraph_active); capture('splicer_windup')
            until(lambda: bool(field.enemy_manager.projectiles)); capture('splicer_acid')
            phantom = select(1, 0, y=204); phantom.cooldown_timer = 99
            for _ in range(4):
                if field.player.arsenal.active_weapon_id == 'scattergun': break
                key(pygame.K_q)
            assert field.player.arsenal.active_weapon_id == 'scattergun'
            key(pygame.K_x); until(lambda: phantom.has_status('revealed')); capture('phantom_revealed')
            operative = select(1, 1)
            until(lambda: operative.telegraph_active); capture('operative_windup')
            for _ in range(4):
                if field.player.abilities.selected_ability_id == 'serendipity_tape_deck': break
                key(pygame.K_r)
            key(pygame.K_k)
            assert operative.has_status('prediction_shattered') and not operative.telegraph_active
            capture('operative_tape')
            # Inspect the shared HUD in the boss scene; direct route is a layout fixture.
            game.change_state('BOSS_BOUNTY')
            capture('boss_hud')
        finally:
            game.close(); pygame.quit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    run(parser.parse_args().output_dir)


if __name__ == '__main__': main()
