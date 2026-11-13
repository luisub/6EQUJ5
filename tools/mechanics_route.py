"""PURPOSE: Exercise earned Act I and prototype science/reality mechanics through game events.
CALLED BY: CLI and normal-input regression tests.
HOW TO MODIFY: Preserve isolated saves, report observed boundaries and avoid fixture grants.
"""
import argparse
import json
import os
import tempfile
import time
import subprocess
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import pygame
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from tools.act_01_traversal import _traverse_in_directory


def run_route(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='6equj5-s11-') as save:
        act1 = _traverse_in_directory(save, through_repair=True, through_defense=True, complete=True)
        pygame.init()
        pygame.display.set_mode((480, 270))
        game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(save), settings_store=SettingsStore(save))
        trace = []
        ticks = 0
        def tick():
            nonlocal ticks
            game.update(1 / 60)
            game.input.begin_frame()
            ticks += 1
        def down(code):
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))
        def up(code):
            game.handle_event(pygame.event.Event(pygame.KEYUP, key=code))
        def tap(code):
            down(code); tick(); up(code); tick()
        def capture(name):
            game.render()
            canvas = game.crt.render_surface
            pygame.image.save(canvas, str(output_dir / f'{name}_native.png'))
            pygame.image.save(pygame.transform.scale(canvas, (1920, 1080)), str(output_dir / f'{name}_2x.png'))
        def walk(target):
            player = game.current_scene.player
            code = pygame.K_d if player.x < target else pygame.K_a
            down(code)
            for _ in range(1000):
                tick()
                if abs(player.x - target) < 3:
                    break
            up(code)
            if abs(player.x - target) >= 4:
                raise RuntimeError(f'Walking to {target} stopped at {player.x:.1f}')
        try:
            tap(pygame.K_c)
            assert game.current_state_name == 'BUNKER_HUB'
            assert game.campaign.state.room_flags.get('act_01_completed')
            trace.append({'action': 'title_continue', 'act_01_completed': True})
            # Continue starts at x=186, walk to the authored laboratory station.
            down(pygame.K_a)
            for _ in range(30): tick()
            up(pygame.K_a); tap(pygame.K_e)
            assert game.current_state_name == 'SCIENCE_LAB'
            lab = game.current_scene
            assert lab.workbench.current_step == 'COMPLETED'
            before_repeat = game.campaign.to_dict()
            tap(pygame.K_m)  # Exercise the retained manual science workbench.
            tap(pygame.K_r); tap(pygame.K_1); tap(pygame.K_RETURN)
            assert game.campaign.to_dict() == before_repeat
            assert len(game.campaign.state.validation_records) == 1
            trace.append({'action': 'formal_repeat', 'count': 1})
            tap(pygame.K_TAB)
            scenario_id = lab.workbench.active_scenario['id']
            initial_step = lab.workbench.current_step
            tap(pygame.K_RETURN)  # Deliberately incomplete experiment, or unanswered claim.
            assert len(game.campaign.state.validation_records) == 1
            assert lab.workbench.current_step == initial_step
            trace.append({'action': 'lab_rejected_incomplete', 'feedback': lab.workbench.feedback_message})
            tap(pygame.K_F2); assert game.pause.active
            tick(); tap(pygame.K_F2); assert not game.pause.active
            tap(pygame.K_ESCAPE); tap(pygame.K_e)
            tap(pygame.K_m); tap(pygame.K_TAB)  # Re-enter manual and the same scenario.
            assert lab.workbench.active_scenario['id'] == scenario_id
            assert lab.workbench.current_step == initial_step
            trace.append({'action': 'lab_incomplete_pause_exit_reset', 'scenario': scenario_id})
            for index in range(1, 8):
                if index > 1: tap(pygame.K_TAB)
                wb = lab.workbench
                scenario = wb.active_scenario
                if wb.current_step == 'EXPERIMENT':
                    for code in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_SPACE, pygame.K_RETURN):
                        tap(code)
                if wb.current_step != 'CLAIM':
                    raise RuntimeError(f"{scenario['id']}: experiment stopped at {wb.current_step}: {wb.feedback_message}")
                tap({'established': pygame.K_1, 'plausible': pygame.K_2, 'speculative': pygame.K_3}[scenario['claim']['correct_tier']])
                for n, obs in enumerate(scenario['evidence_pool']):
                    if obs.get('is_valid', True): tap(pygame.K_1 + n)
                tap(pygame.K_RETURN)
                if wb.current_step != 'REPLICATION':
                    raise RuntimeError(f"{scenario['id']}: evidence rejected: {wb.feedback_message}")
                for n, check in enumerate(scenario['replication_checks']):
                    tap(pygame.K_1 + n)
                    if wb.replication_answers[check['id']] != check['expected']: tap(pygame.K_1 + n)
                tap(pygame.K_RETURN); tap(pygame.K_1)
                if wb.current_step != 'COMPLETED':
                    raise RuntimeError(f"{scenario['id']}: deployment failed: {wb.feedback_message}")
                trace.append({'action': 'lab_validated', 'scenario': scenario['id']})
                capture(f'lab_{index}')
            assert len(game.campaign.state.validation_records) == 8
            tap(pygame.K_ESCAPE)
            tap(pygame.K_m)
            field = game.current_scene
            assert field.room.room_id == 'act_01_mandela_test'
            trace.append({'action': 'annex_entry'})
            # Exercise earned equipment through the same mapper used by play.
            equipped = []
            for _ in range(4):
                tap(pygame.K_q)
                weapon = field.player.arsenal.active_weapon_id
                down(pygame.K_x); tick(); up(pygame.K_x); tick()
                shots = [p.weapon_type for p in field.projectile_manager.projectiles]
                assert weapon in shots, (weapon, shots)
                equipped.append({'weapon': weapon, 'observed_projectiles': shots})
                for _ in range(45): tick()
            assert {item['weapon'] for item in equipped} == {'starter_maser', 'scattergun', 'emp_bola', 'fibonacci_coilgun'}
            trace.append({'action': 'weapon_cycle_fire', 'observations': equipped})
            abilities = []
            for _ in range(3):
                tap(pygame.K_r)
                selected = field.player.abilities.selected_ability_id
                before = field.player.abilities.energy
                tap(pygame.K_k)
                ability = field.player.abilities.selected_ability
                after = field.player.abilities.energy
                assert ability.is_active and after < before, (selected, before, after)
                tap(pygame.K_k)  # An active ability cannot charge twice.
                assert field.player.abilities.energy >= after
                for _ in range(600):
                    if not ability.is_active: break
                    tick()
                assert not ability.is_active and ability.cooldown_timer > 0
                cooldown_energy = field.player.abilities.energy
                tap(pygame.K_k)
                assert field.player.abilities.energy >= cooldown_energy
                abilities.append({'ability': selected, 'energy_before': round(before, 2),
                                  'energy_after': round(after, 2), 'active': True,
                                  'repeat_cost_blocked': True})
                for _ in range(480): tick()
            assert {item['ability'] for item in abilities} == {'shielding', 'time_dilation', 'decoy'}
            trace.append({'action': 'ability_cycle_activate', 'observations': abilities})
            tap(pygame.K_g)
            grappled = field.player.is_grappling
            assert grappled
            capture('grapple_latched')
            tap(pygame.K_g)
            second_g_released = not field.player.is_grappling
            assert second_g_released, "Second G did not release the grapple"
            capture('grapple_released')
            tap(pygame.K_LSHIFT)
            assert field.player.is_dashing
            trace.append({'action': 'mobility', 'grapple_started': grappled,
                          'second_g_released': second_g_released, 'dash_started': True})
            capture('equipment_and_mobility')
            # Room transition must discard a latched anchor and active traversal.
            tap(pygame.K_F8)
            tap(pygame.K_g)
            assert field.player.is_grappling
            tap(pygame.K_F6)
            assert field.room.room_id == 'act_04_dodleston_relay'
            assert not field.player.is_grappling and field.player.grapple_anchor is None
            assert field.player.grapple_anchor_pos is None and not field.player.is_dashing
            capture('grapple_room_reset')
            tap(pygame.K_F8)
            assert field.room.room_id == 'act_01_mandela_test'
            trace.append({'action': 'grapple_room_transition_reset'})
            tap(pygame.K_t); assert field.room.active_timeline == '1977_ANALOG'
            # Climb the first authored low block and jump from the taller wall.
            down(pygame.K_d)
            wall_frame = None
            for frame in range(120):
                if frame == 5: down(pygame.K_SPACE)
                if frame == 17: up(pygame.K_SPACE)
                tick()
                if field.player.is_wall_sliding:
                    wall_frame = frame
                    break
            if wall_frame is None:
                raise RuntimeError('Did not reach the authored 1977 wall slide')
            capture('wall_slide')
            down(pygame.K_SPACE); tick()
            vx, vy = field.player.vx, field.player.vy
            locked = field.player.wall_jump_lock_timer
            assert vx < 0 and vy < 0 and locked > 0, (vx, vy, locked)
            up(pygame.K_SPACE); up(pygame.K_d)
            trace.append({'action': 'wall_jump', 'wall_slide_frame': wall_frame,
                          'launch_vx': vx, 'launch_vy': vy, 'lock_timer': locked})
            capture('wall_jump')
            tap(pygame.K_t); assert field.room.active_timeline == '2029_CORE'
            trace.append({'action': 'timeline_swap_roundtrip'})
            tap(pygame.K_F6)
            assert field.room.room_id == 'act_04_dodleston_relay'
            assert field.room.get_tile(16, 13) == 1
            walk(96); tap(pygame.K_e)
            assert field.reality.panel_open
            tap(pygame.K_2); assert field.reality.relay.puzzle_flags['pipe_ruptured']
            tap(pygame.K_r)
            assert not field.reality.relay.puzzle_flags['pipe_ruptured']
            tap(pygame.K_1); tap(pygame.K_1)
            assert field.reality.relay.puzzle_flags['dodleston_cassette_cached']
            assert field.room.get_tile(16, 13) == 0
            capture('relay_open')
            tap(pygame.K_ESCAPE); walk(384)
            assert game.campaign.state.inventory.get('relay_cipher_cassette') == 1
            trace.append({'action': 'relay_wrong_recover_and_cassette'})
            tap(pygame.K_F8)
            tap(pygame.K_q)  # Preserve a non-default earned weapon across the flashback.
            assert field.player.arsenal.active_weapon_id != 'starter_maser'
            before_flashback = {'health': field.player.health, 'weapon': field.player.arsenal.active_weapon_id}
            tap(pygame.K_F7)
            assert field.flashback
            walk(110); tap(pygame.K_e)
            tap(pygame.K_ESCAPE)  # Close printout, then leave without completing.
            tap(pygame.K_ESCAPE)
            assert field.flashback is None
            assert not game.campaign.state.inventory.get('reality_anchor_1977')
            tap(pygame.K_F7)
            walk(110); tap(pygame.K_e); tap(pygame.K_e)
            capture('flashback_printer')
            walk(375); tap(pygame.K_e); tap(pygame.K_e)
            assert field.flashback is None and game.campaign.state.inventory.get('reality_anchor_1977') == 1
            assert field.player.health == max(before_flashback['health'], 50)
            assert field.player.arsenal.active_weapon_id == before_flashback['weapon']
            tap(pygame.K_F7)
            assert field.flashback
            tap(pygame.K_ESCAPE)
            assert field.flashback is None and game.campaign.state.inventory.get('reality_anchor_1977') == 1
            trace.append({'action': 'flashback_interrupted_completed_reentered',
                          'before': before_flashback, 'after_health': field.player.health,
                          'after_weapon': field.player.arsenal.active_weapon_id, 'anchor_count': 1})
            # The anchor unlocks the tape deck: select and activate it through normal inputs.
            for _ in range(4):
                if field.player.abilities.selected_ability_id == 'serendipity_tape_deck': break
                tap(pygame.K_r)
            assert field.player.abilities.selected_ability_id == 'serendipity_tape_deck'
            energy_before = field.player.abilities.energy
            tap(pygame.K_k)
            assert field.player.abilities.selected_ability.is_active
            energy_after = field.player.abilities.energy
            assert energy_after < energy_before
            tap(pygame.K_k)
            assert field.player.abilities.energy >= energy_after
            trace.append({'action': 'tape_activation', 'energy_before': energy_before,
                          'energy_after': energy_after, 'repeat_cost_blocked': True})
            capture('flashback_return')
            tap(pygame.K_t)
            assert field.room.active_timeline == '1977_ANALOG'
            trace.append({'action': 'timeline_selected_for_save', 'timeline': field.room.active_timeline})
            tap(pygame.K_ESCAPE); tap(pygame.K_F5)
            child_script = """import json, sys, pygame
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
pygame.init(); pygame.display.set_mode((480, 270))
game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(sys.argv[1]), settings_store=SettingsStore(sys.argv[1]))
def tap(key):
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key)); game.update(1/60); game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=key)); game.update(1/60); game.input.begin_frame()
tap(pygame.K_c)
assert game.current_state_name == 'BUNKER_HUB'
state = game.campaign.state
result = {'scene': game.current_state_name, 'validations': [r['scenario_id'] for r in state.validation_records],
          'inventory': state.inventory, 'flags': state.room_flags, 'timeline': state.timeline_mode}
tap(pygame.K_m)
result['annex_timeline'] = game.current_scene.room.active_timeline
tap(pygame.K_F6)
field = game.current_scene
result['relay_restored'] = field.reality.relay.puzzle_flags['dodleston_cassette_cached']
result['door_open'] = field.reality.world.state.get_door_state('door_bulkhead_relay')['open']
game.close(); pygame.quit(); print(json.dumps(result))
"""
            child = subprocess.run([sys.executable, '-c', child_script, save], check=True,
                                   capture_output=True, text=True,
                                   env=dict(os.environ, PYGAME_HIDE_SUPPORT_PROMPT='1'))
            restored = json.loads(child.stdout)
            assert set(restored['validations']) == {r['scenario_id'] for r in game.campaign.state.validation_records}
            assert len(restored['validations']) == 8
            assert restored['inventory'].get('reality_anchor_1977') == 1
            assert restored['inventory'].get('relay_cipher_cassette') == 1
            assert restored['timeline'] == restored['annex_timeline'] == '1977_ANALOG'
            assert restored['relay_restored'] and restored['door_open']
            trace.append({'action': 'child_continue_and_relay_restore', 'state': restored})
            game.close()
            game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(save), settings_store=SettingsStore(save))
            tap(pygame.K_n); tap(pygame.K_y)
            assert game.current_state_name == 'BUNKER_HUB'
            fresh = game.campaign.state
            assert not fresh.validation_records and not fresh.world_states and not fresh.extracted_fragments
            new_field = game.scenes['FIELD_OPS']
            assert not new_field.player.arsenal.weapons['scattergun'].is_unlocked
            trace.append({'action': 'new_game_isolation', 'validations': len(fresh.validation_records),
                          'world_states': len(fresh.world_states), 'fragments': len(fresh.extracted_fragments)})
            return {'act1': act1, 'trace': trace, 'ticks': ticks,
                    'additional_simulated_seconds': round(ticks / 60, 3),
                    'wall_seconds': round(time.perf_counter() - start, 3), 'gate_g3': 'not verified'}
        finally:
            game.close()
            pygame.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    result = run_route(args.output_dir)
    (args.output_dir / 'mechanics_route.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
