"""
MODULE: video_game/tools/act_01_traversal.py
PURPOSE: Exercise bounded fresh-save traversal through real input events.
CALLED BY: CLI and traversal regression tests.
HOW TO MODIFY: Extend ordinary event actions and record their observations.

Bounded fresh-save traversal using real scene events, not route acceptance.

The driver performs offline contact and formal validation, then uses observed
player coordinates as a timing aid. It holds right and
fire, holds jump through each obstacle, and interacts at the salvage exit.
Use a disposable save directory; this does not verify art, audio or G2.
"""
import argparse
import json
import os
import tempfile
import time
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore


def traverse(probe_yard=False, through_repair=False, through_defense=False, complete=False, output_dir=None, recovery=False):
    if recovery:
        complete = True
    if probe_yard and (through_repair or through_defense or complete):
        raise ValueError('Choose either the yard probe or the route through repair')
    with tempfile.TemporaryDirectory() as save:
        return _traverse_in_directory(save, probe_yard=probe_yard, through_repair=through_repair or through_defense or complete, through_defense=through_defense or complete, complete=complete, output_dir=output_dir, recovery=recovery)


def _traverse_in_directory(save, probe_yard=False, through_repair=False, through_defense=False, complete=False, output_dir=None, recovery=False):
    owned_pygame = not pygame.get_init()
    if owned_pygame:
        pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((480, 270))
    machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(save),
                               settings_store=SettingsStore(save))
    trace = []
    start = time.perf_counter()
    ticks = 0
    def key(code, down=True):
        machine.handle_event(pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP, key=code))
    def tick():
        nonlocal ticks
        ticks += 1
        machine.update(1 / 60)
        machine.input.begin_frame()
    try:
        def tap(code):
            key(code); tick(); key(code, False); tick()
        def submit(value):
            machine.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=value))
            tap(pygame.K_RETURN)
        tap(pygame.K_n)
        tap(pygame.K_e)  # Receiver at the fresh bunker spawn.
        assert machine.current_state_name == 'CRT_TERMINAL'
        submit('/offline')
        submit('2')  # Authored evidence channel.
        assert 'FASR-001' in machine.campaign.state.extracted_fragments
        trace.append({'action': 'contact', 'civilization': 'FASR-001', 'channel': 'offline 2'})
        tap(pygame.K_ESCAPE)
        key(pygame.K_a)
        for _ in range(30): tick()
        key(pygame.K_a, False)
        tap(pygame.K_e)
        assert machine.current_state_name == 'SCIENCE_LAB'
        # Answers follow the first scenario's visible claim/evidence/checks.
        for code in (pygame.K_3, pygame.K_1, pygame.K_2, pygame.K_RETURN,
                     pygame.K_1, pygame.K_2, pygame.K_RETURN, pygame.K_1):
            tap(code)
        assert any(r['scenario_id'] == 'formal_fasr_001' for r in machine.campaign.state.validation_records)
        trace.append({'action': 'formal_validation', 'scenario': 'formal_fasr_001'})
        tap(pygame.K_ESCAPE)
        key(pygame.K_d)
        for _ in range(120): tick()
        key(pygame.K_d, False)
        key(pygame.K_e)
        field = machine.current_scene
        assert machine.current_state_name == 'FIELD_OPS'
        key(pygame.K_d)
        key(pygame.K_x)
        jumped = set()
        release_at = None
        for frame in range(600):
            player = field.player
            for name, low, high in [('sump', 275, 280), ('wall', 545, 550)]:
                if name not in jumped and low < player.x < high and player.is_grounded:
                    key(pygame.K_SPACE)
                    jumped.add(name)
                    release_at = frame + 40
                    trace.append({'action': 'jump', 'obstacle': name, 'frame': frame, 'x': round(player.x, 2)})
            if frame == release_at:
                key(pygame.K_SPACE, False)
            if player.x >= 910:
                key(pygame.K_d, False)
                key(pygame.K_x, False)
                exit_x, health = round(player.x, 2), player.health
                key(pygame.K_e)
                trace.append({'action': 'exit_interaction', 'frame': frame, 'x': exit_x, 'health': health, 'room': field.room.room_id})
                break
            tick()
        if field.room.room_id != 'act_01_salvage_yard':
            raise RuntimeError(f'Approach traversal did not reach salvage yard: x={field.player.x:.1f}, health={field.player.health}')
        if through_repair:
            def capture(name):
                if output_dir is None:
                    return
                machine.render()
                surface = machine.crt.render_surface
                pygame.image.save(surface, str(output_dir / (name + '_native.png')))
                pygame.image.save(pygame.transform.scale(surface, (1920, 1080)),
                                  str(output_dir / (name + '_2x.png')))
            tap(pygame.K_r)  # Select the validated time-dilation ability.
            assert field.player.abilities.selected_ability_id == 'time_dilation'
            key(pygame.K_d)
            activated = dashed = jumped = returning = False
            for frame in range(350):
                p = field.player
                if not returning and p.x >= 565:
                    key(pygame.K_d, False); key(pygame.K_a); returning = True
                if not activated and p.x >= 190:
                    key(pygame.K_k); activated = True
                elif activated:
                    key(pygame.K_k, False)
                if not dashed and p.x >= 290:
                    key(pygame.K_LSHIFT); dashed = True
                elif dashed:
                    key(pygame.K_LSHIFT, False)
                if not jumped and p.x >= 255 and p.is_grounded:
                    key(pygame.K_SPACE); jumped = True
                elif jumped and p.x >= 380:
                    key(pygame.K_SPACE, False)
                if frame % 16 == 0: key(pygame.K_x)
                if frame % 16 == 1: key(pygame.K_x, False)
                tick()
                if machine.campaign.state.inventory.get('analog_coupler', 0):
                    trace.append({'action': 'coupler_pickup', 'frame': frame,
                                  'x': round(p.x, 2), 'health': p.health})
                    capture('coupler_pickup')
                    break
            else:
                raise RuntimeError('Yard route did not collect the coupler')
            key(pygame.K_a, False)
            tap(pygame.K_ESCAPE)
            assert machine.current_state_name == 'BUNKER_HUB'
            key(pygame.K_a)
            for _ in range(30): tick()
            key(pygame.K_a, False)
            tap(pygame.K_e)
            assert machine.campaign.state.room_flags.get('feedhorn_repaired')
            trace.append({'action': 'feedhorn_repaired'})
            capture('repair')
            key(pygame.K_d)
            for _ in range(30): tick()
            key(pygame.K_d, False)
            tap(pygame.K_e)
            assert field.room.room_id == 'act_01_dish_catwalk' and field.holdout.is_active
            trace.append({'action': 'defense_started', 'elapsed_seconds': field.holdout.elapsed_time})
            capture('defense_started')
        if recovery:
            # Wait for enemy-caused failure; health and damage remain untouched.
            before_pause = field.holdout.elapsed_time
            tap(pygame.K_F2)
            assert machine.pause.active
            capture('defense_paused')
            for _ in range(120): tick()
            after_pause = field.holdout.elapsed_time
            assert after_pause == before_pause
            tap(pygame.K_F2)
            assert not machine.pause.active
            trace.append({'action': 'defense_pause', 'before': before_pause,
                          'after': after_pause, 'paused_frames': 120})
            tap(pygame.K_ESCAPE)
            assert machine.current_state_name == 'BUNKER_HUB'
            saved = SaveStore(save).load()
            assert saved.status == 'ok' and saved.campaign.state.room_flags.get('feedhorn_repaired')
            assert not saved.campaign.state.room_flags.get('dish_defense_completed')
            tap(pygame.K_e)
            assert machine.current_state_name == 'FIELD_OPS' and field.holdout.is_active
            trace.append({'action': 'defense_exit_reentry', 'saved_repair': True,
                          'restarted_elapsed_seconds': field.holdout.elapsed_time})
            for attempt in range(2):
                for frame in range(4500):
                    tick()
                    if field.holdout.is_failed:
                        break
                else:
                    raise RuntimeError('Unattended defense did not fail within 75 seconds')
                trace.append({'action': 'defense_failed' if attempt == 0 else 'defense_failed_again',
                              'frame': frame, 'reason': field.holdout.failure_reason,
                              'elapsed_seconds': field.holdout.elapsed_time,
                              'integrity': field.holdout.dish_integrity,
                              'health': field.player.health})
                assert not machine.campaign.state.room_flags.get('dish_defense_completed')
                capture('defense_failed' if attempt == 0 else 'defense_failed_again')
                if attempt == 0:
                    tap(pygame.K_ESCAPE)
                    assert machine.current_state_name == 'BUNKER_HUB'
                    saved = SaveStore(save).load()
                    assert saved.status == 'ok' and saved.campaign.state.room_flags.get('feedhorn_repaired')
                    assert not saved.campaign.state.room_flags.get('dish_defense_completed')
                    tap(pygame.K_e)
                    assert machine.current_state_name == 'FIELD_OPS' and field.holdout.is_active
                    assert field.holdout.dish_integrity == 100.0
                    assert field.holdout.elapsed_time < 1.0
                    assert field.holdout.spawned_waves == {'wave_01'}
                    trace.append({'action': 'failed_defense_exit_reentry',
                                  'saved_repair': True, 'saved_completion': False,
                                  'integrity': field.holdout.dish_integrity,
                                  'waves': sorted(field.holdout.spawned_waves),
                                  'elapsed_seconds': field.holdout.elapsed_time,
                                  'health': field.player.health})
            before = field.player.abilities.selected_ability_id
            key(pygame.K_r)
            pending = machine.input.pressed('cycle_ability')
            tick()
            key(pygame.K_r, False); tick()
            after = field.player.abilities.selected_ability_id
            assert field.holdout.is_active and field.player.health > 0
            assert not pending and before == after
            trace.append({'action': 'defense_retry', 'ability_edge_pending': pending, 'ability_before': before,
                          'ability_after': after, 'health': field.player.health,
                          'elapsed_seconds': field.holdout.elapsed_time})
        if through_defense:
            moving = False
            jump_release = -1
            shot = ability = -100
            last_health = {}
            hits = []
            for frame in range(4500):
                p, defense = field.player, field.holdout
                living = [e for e in field.enemy_manager.enemies if not e.is_dead]
                drones = [e for e in living if 'Drone' in type(e).__name__]
                hounds = [e for e in living if 'Hound' in type(e).__name__]
                if p.x < 340 and not moving: key(pygame.K_d); moving = True
                if p.x > 355 and moving: key(pygame.K_d, False); moving = False
                if defense.is_jammed and abs(p.rect.centerx - 320) <= 56:
                    key(pygame.K_e); key(pygame.K_e, False)
                if frame - ability > 550 and drones:
                    key(pygame.K_k); ability = frame
                if frame == ability + 1: key(pygame.K_k, False)
                if frame == jump_release:
                    key(pygame.K_w, False); key(pygame.K_x, False)
                if frame - shot > 15 and p.is_grounded:
                    mx, my = p.get_muzzle_world_pos()
                    aligned = [e for e in drones if e.rect.centerx > mx and
                               abs((e.rect.centerx - mx) - (my - e.rect.centery)) < 15]
                    if aligned:
                        if not moving: key(pygame.K_d); moving = True
                        key(pygame.K_w); key(pygame.K_x)
                        shot = frame; jump_release = frame + 1
                    elif hounds and p.x < min(e.x for e in hounds):
                        key(pygame.K_x); shot = frame
                if frame == shot + 1: key(pygame.K_x, False)
                tick()
                for enemy in field.enemy_manager.enemies:
                    before = last_health.get(enemy.target_id, enemy.health)
                    if enemy.health < before:
                        hits.append({'frame': frame, 'target': enemy.target_id,
                                     'before': before, 'after': enemy.health})
                    last_health[enemy.target_id] = enemy.health
                if not defense.is_active:
                    break
            key(pygame.K_d, False)
            trace.append({'action': 'defense_result', 'completed': defense.is_completed,
                          'elapsed_seconds': defense.elapsed_time,
                          'integrity': defense.dish_integrity, 'health': p.health,
                          'waves': sorted(defense.spawned_waves), 'hits': hits})
            if not defense.is_completed:
                raise RuntimeError('Defense did not complete: ' + defense.failure_reason)
            assert machine.campaign.state.room_flags.get('dish_defense_completed')
            if recovery:
                saved = SaveStore(save).load()
                assert saved.status == 'ok' and saved.campaign.state.room_flags.get('dish_defense_completed')
                trace.append({'action': 'defense_saved', 'completed': True})
            capture('defense_completed')
        if complete:
            tap(pygame.K_ESCAPE)
            tap(pygame.K_e)
            assert machine.current_state_name == 'BOSS_BOUNTY'
            boss_scene = machine.current_scene
            capture('boss_entry')
            if recovery:
                for attempt in range(2):
                    key(pygame.K_d)
                    for _ in range(600):
                        if boss_scene.player.x >= 250:
                            break
                        tick()
                    else:
                        raise RuntimeError('Could not reach boss attack range')
                    key(pygame.K_d, False)
                    for death_frame in range(4500):
                        tick()
                        if boss_scene.player.is_dead:
                            break
                    else:
                        raise RuntimeError('Unattended boss did not defeat player within 75 seconds')
                    trace.append({'action': 'boss_death' if attempt == 0 else 'boss_death_again',
                                  'frame': death_frame, 'boss_health': boss_scene.boss.health})
                    assert not machine.campaign.state.room_flags.get('act_01_completed')
                    capture('boss_death' if attempt == 0 else 'boss_death_again')
                    if attempt == 0:
                        tap(pygame.K_ESCAPE)
                        assert machine.current_state_name == 'BUNKER_HUB'
                        saved = SaveStore(save).load()
                        assert saved.status == 'ok' and saved.campaign.state.room_flags.get('dish_defense_completed')
                        assert not saved.campaign.state.room_flags.get('act_01_completed')
                        tap(pygame.K_e)
                        assert machine.current_state_name == 'BOSS_BOUNTY'
                        assert not boss_scene.player.is_dead and boss_scene.player.health == 100
                        assert boss_scene.boss.health == 300 and boss_scene.boss.current_phase == 1
                        trace.append({'action': 'boss_death_exit_reentry',
                                      'saved_defense': True, 'saved_completion': False,
                                      'health': boss_scene.player.health,
                                      'boss_health': boss_scene.boss.health,
                                      'boss_phase': boss_scene.boss.current_phase})
                before = boss_scene.player.abilities.selected_ability_id
                tap(pygame.K_r)
                after = boss_scene.player.abilities.selected_ability_id
                assert not boss_scene.player.is_dead and boss_scene.boss.health == 300
                assert before == after
                trace.append({'action': 'boss_retry', 'ability_before': before,
                              'ability_after': after, 'health': boss_scene.player.health,
                              'boss_health': boss_scene.boss.health})
            key(pygame.K_d)
            moving = True
            changes = []
            last_health = boss_scene.boss.health
            for frame in range(2500):
                player, boss = boss_scene.player, boss_scene.boss
                if player.x >= 250 and moving:
                    key(pygame.K_d, False); moving = False
                if frame % 15 == 0: key(pygame.K_x)
                if frame % 15 == 1: key(pygame.K_x, False)
                tick()
                if boss.health != last_health:
                    changes.append({'frame': frame, 'health': boss.health,
                                    'phase': boss.current_phase})
                    last_health = boss.health
                if player.is_dead or boss.is_defeated: break
            if not boss.is_defeated:
                raise RuntimeError('Boss attempt ended without victory')
            tick()  # Resolve the defeat event through the boss scene.
            assert machine.campaign.state.room_flags.get('act_01_completed')
            trace.append({'action': 'boss_defeated', 'frame': frame,
                          'health': player.health, 'boss_changes': changes})
            capture('boss_defeated')
            if recovery:
                saved = SaveStore(save).load()
                assert saved.status == 'ok' and saved.campaign.state.room_flags.get('act_01_completed')
                saved_bytes = SaveStore(save).path.read_bytes()
                before_replay = machine.campaign.to_dict()
                tap(pygame.K_r)
                assert boss_scene.boss.health == 300
                key(pygame.K_d)
                moving = True
                for replay_frame in range(2500):
                    if boss_scene.player.x >= 250 and moving:
                        key(pygame.K_d, False); moving = False
                    if replay_frame % 15 == 0: key(pygame.K_x)
                    if replay_frame % 15 == 1: key(pygame.K_x, False)
                    tick()
                    if boss_scene.player.is_dead or boss_scene.boss.is_defeated: break
                assert boss_scene.boss.is_defeated
                tick()
                assert machine.campaign.to_dict() == before_replay
                assert SaveStore(save).path.read_bytes() == saved_bytes
                trace.append({'action': 'boss_replay_idempotent', 'frame': replay_frame,
                              'saved_before_exit': True})
            tap(pygame.K_ESCAPE)
            if recovery:
                saved = SaveStore(save).load()
                assert saved.status == 'ok' and saved.campaign.state.room_flags.get('act_01_completed')
                trace.append({'action': 'boss_exit_saved', 'completed': True})
            key(pygame.K_a)
            for _ in range(74): tick()
            key(pygame.K_a, False)
            tap(pygame.K_e)
            assert machine.current_state_name == 'CRT_TERMINAL'
            for _ in range(6): tap(pygame.K_TAB)
            assert machine.contact_session.active_civ_id == 'FASR-007'
            submit('2')
            assert 'FASR-007' in machine.campaign.state.extracted_fragments
            trace.append({'action': 'contact', 'civilization': 'FASR-007', 'channel': 'offline 2'})
            capture('fasr_007')
            tap(pygame.K_ESCAPE)
            tap(pygame.K_F5)
            script = """import json, sys, pygame
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
pygame.init()
pygame.display.set_mode((480, 270))
machine = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(sys.argv[1]),
                           settings_store=SettingsStore(sys.argv[1]))
machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c))
state = machine.campaign.state
result = {'scene': machine.current_state_name, 'fragments': state.extracted_fragments,
          'flags': state.room_flags, 'validations': [r['scenario_id'] for r in state.validation_records]}
machine.close()
pygame.quit()
print(json.dumps(result))
"""
            child_env = dict(os.environ, PYGAME_HIDE_SUPPORT_PROMPT='1')
            child = subprocess.run([sys.executable, '-c', script, str(save)],
                                   check=True, capture_output=True, text=True, env=child_env)
            reloaded = json.loads(child.stdout)
            assert reloaded['scene'] == 'BUNKER_HUB'
            assert {'FASR-001', 'FASR-007'} <= set(reloaded['fragments'])
            assert reloaded['flags'].get('act_01_completed') and reloaded['flags'].get('act_02_unlocked')
            assert 'formal_fasr_001' in reloaded['validations']
            trace.append({'action': 'separate_process_save_load', 'state': reloaded})
        if probe_yard:
            # Bounded diagnostic, using ordinary directional aim and shooting events.
            # Aiming is timed from observed enemy and muzzle positions.
            key(pygame.K_d)
            last_shot = -100
            hits = []
            for frame in range(245):
                player = field.player
                drones = [e for e in field.enemy_manager.enemies
                          if type(e).__name__ == 'CoreReconDrone' and not e.is_dead]
                if drones and frame - last_shot > 14 and player.is_grounded:
                    drone = drones[0]
                    mx, my = player.get_muzzle_world_pos()
                    dx, dy = drone.rect.centerx - mx, my - drone.rect.centery
                    if dx > 0 and abs(dx - dy) < 10:
                        key(pygame.K_w); key(pygame.K_x)
                        last_shot = frame
                if frame == last_shot + 1:
                    key(pygame.K_x, False); key(pygame.K_w, False)
                before = drones[0].health if drones else None
                tick()
                if drones and drones[0].health != before:
                    hits.append({'frame': frame, 'remaining_health': drones[0].health})
            key(pygame.K_d, False)
            trace.append({'action': 'bounded_yard_combat', 'frames': 245, 'drone_hits': hits,
                          'coupler': machine.campaign.state.inventory.get('analog_coupler', 0),
                          'health': field.player.health})
        return {'room': field.room.room_id, 'field_health': field.player.health,
                'final_scene': machine.current_state_name, 'trace': trace,
                'simulated_seconds': round(ticks / 60, 3),
                'wall_seconds': round(time.perf_counter() - start, 3),
                'gate_g2': 'not verified', 'driver': 'headless coordinate-timed keyboard events, 60 Hz'}
    finally:
        machine.close()
        if owned_pygame:
            pygame.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--probe-yard', action='store_true', help='Run the bounded experimental combat diagnostic')
    mode.add_argument('--through-repair', action='store_true', help='Experimental route through pickup and defense entry')
    mode.add_argument('--through-defense', action='store_true', help='Experimental route through actual defense completion')
    mode.add_argument('--complete', action='store_true', help='Experimental full input route and child-process save load')
    parser.add_argument('--recovery', action='store_true', help='Exercise actual failure, pause and retry before the complete route')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = traverse(probe_yard=args.probe_yard, through_repair=args.through_repair, through_defense=args.through_defense, complete=args.complete, output_dir=args.output_dir, recovery=args.recovery)
    (args.output_dir / 'traversal.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
