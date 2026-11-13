"""PURPOSE: Exercise faction encounters and counters through the real field router.
CALLED BY: pytest tests/test_faction_integration.py.
HOW TO MODIFY: Disclose fixture prerequisites and use physical-key events for counters.
"""
import pygame
import pytest

from video_game.engine import config
from video_game.engine.audio import AudioManager
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.enemies import STATE_DEATH, STATE_RECOVERY
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


@pytest.fixture
def game(tmp_path, monkeypatch):
    # Combat fixtures do not exercise audio; avoid background mixer work during teardown.
    monkeypatch.setattr(AudioManager, "_init_mixer", lambda self: None)
    pygame.init()
    pygame.display.set_mode((480, 270))
    machine = GameStateMachine(CRTRenderer(), development=False,
                               save_store=SaveStore(tmp_path), settings_store=SettingsStore(tmp_path))
    assert machine.start_new_game()[0]
    yield machine
    machine.close()
    pygame.quit()


def key(game, code):
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))
    game.update(1 / 60)
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=code))


def annex(game):
    # Public event supplies the Act I prerequisite, not a completed playthrough.
    game.campaign.apply_event({"event_id": "s09-fixture", "type": "defeat_greenkeeper"})
    key(game, pygame.K_m)
    assert game.current_scene.room.room_id == "act_01_mandela_test"
    return game.current_scene


@pytest.mark.parametrize("pair_index", [0, 1])
@pytest.mark.parametrize("lethal", [False, True])
def test_keyboard_slide_interrupt_preserves_counter_and_death(game, pair_index, lethal):
    field = annex(game)
    for _ in range(pair_index + 1):
        key(game, pygame.K_n)
    target = field.enemy_manager.enemies[0]
    # Controlled placement on annex floor isolates the counter, not normal traversal.
    target.x = target.spawn_x = 130
    target.y = target.spawn_y = 240 - target.cfg.height
    target.rect.topleft = (int(target.x), int(target.y))
    target.patrol_left = target.patrol_right = 130
    target.cooldown_timer = 99
    field.enemy_manager.enemies = [target]
    if lethal:
        target.health = 1
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
    for frame in range(60):
        game.input.begin_frame()
        if frame == 15:
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c))
        game.update(1 / 60)
        if target.target_id in field.player.slide_damaged_targets:
            break
    else:
        pytest.fail("physical movement and crouch did not land a slide kick")
    assert target.state == (STATE_DEATH if lethal else STATE_RECOVERY)
    if not lethal:
        assert target.state_timer == pytest.approx(1.2)
        assert not target.telegraph_active
        if pair_index == 1:
            assert target.is_knocked_down
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_c))
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_d))


def test_annex_cycle_pause_and_exit_reset(game):
    field = annex(game)
    pairs = []
    for _ in range(4):
        key(game, pygame.K_n)
        assert len(field.enemy_manager.enemies) == 2
        pairs.append(tuple(type(enemy).__name__ for enemy in field.enemy_manager.enemies))
    assert pairs == [("CoreEnforcer", "CoreOperative"), ("ShieldHound", "PhaseWatcher"),
                     ("ChrysalisSplicer", "PrecursorGuardian"), ("TemporalPhantom", "CoreReconDrone")]
    enemy = field.enemy_manager.enemies[0]
    before = (enemy.x, enemy.y, enemy.state_timer)
    key(game, pygame.K_F2)
    assert game.pause.active
    for _ in range(20):
        game.input.begin_frame(); game.update(1 / 60)
    assert (enemy.x, enemy.y, enemy.state_timer) == before
    key(game, pygame.K_F2)
    assert not game.pause.active
    key(game, pygame.K_ESCAPE)
    assert game.current_state_name == config.STATE_BUNKER_HUB
    assert not field.enemy_manager.projectiles
    key(game, pygame.K_m)
    assert not game.current_scene.enemy_manager.projectiles


@pytest.mark.parametrize("swap", [False, True])
def test_spawn_footprints_supported_and_safe_in_each_timeline(game, swap):
    field = annex(game)
    if swap:
        key(game, pygame.K_t)
        assert field.room.active_timeline == "1977_ANALOG"
    grounded = {"CoreEnforcer", "CoreOperative", "ShieldHound", "ChrysalisSplicer", "PrecursorGuardian"}
    for _ in range(4):
        key(game, pygame.K_n)
        first, second = field.enemy_manager.enemies
        assert not first.rect.colliderect(second.rect)
        for enemy in (first, second):
            rect = enemy.rect
            assert pygame.Rect(0, 0, field.room.width_px, field.room.height_px).contains(rect)
            collision = field.room.check_rect_collision(rect)
            assert not collision["solid"] and not collision["hazard"]
            assert not rect.colliderect(field.player.rect)
            if type(enemy).__name__ in grounded:
                support = field.room.check_rect_collision(rect.move(0, 1))
                assert support["solid"] or support["one_way"]


def test_blocked_spawn_keeps_existing_pair_and_index(game, monkeypatch):
    field = annex(game)
    key(game, pygame.K_n)
    existing = tuple(field.enemy_manager.enemies)
    index = field._faction_encounter
    original = field.room.check_rect_collision
    def blocked(rect):
        result = dict(original(rect))
        result["solid"] = True
        return result
    monkeypatch.setattr(field.room, "check_rect_collision", blocked)
    # No update with fake geometry: the key event alone exercises spawn rejection.
    game.input.begin_frame()
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n))
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_n))
    assert tuple(field.enemy_manager.enemies) == existing
    assert field._faction_encounter == index


def test_death_respawn_resets_status_and_projectiles_after_pause(game):
    field = annex(game)
    key(game, pygame.K_n)
    target = field.enemy_manager.enemies[0]
    target.health -= 10
    target.apply_status("stun", 10)
    target.apply_status("revealed", 10)
    field.projectile_manager.spawn(40, 100, 1, 0, 1, 1)
    field.enemy_manager.spawn_enemy_projectile(400, 100, -1, 0, 1, 1, "fixture")
    field.player.health = 0
    field.player.is_dead = True  # Fixture: death at the start of the update.
    count = field.player.respawn_count
    key(game, pygame.K_F2)
    assert game.pause.active and field.player.respawn_count == count
    assert target.has_status("stun") and target.has_status("revealed")
    assert field.projectile_manager.projectiles and field.enemy_manager.projectiles
    key(game, pygame.K_F2)
    assert not game.pause.active and field.player.respawn_count == count + 1
    assert target.health == target.cfg.max_health
    assert not target.status_effects
    assert not field.projectile_manager.projectiles
    assert not field.enemy_manager.projectiles


def test_operative_telegraphs_then_crouch_breaks_lock(game):
    field = annex(game)
    key(game, pygame.K_n)
    operative = field.enemy_manager.enemies[1]
    # Nearby, grounded and unobstructed placement isolates the timing/counter.
    operative.x = operative.spawn_x = 130
    operative.y = operative.spawn_y = 208
    operative.rect.topleft = (130, 208)
    operative.patrol_left = operative.patrol_right = 130
    field.enemy_manager.enemies = [operative]
    for _ in range(15):
        game.input.begin_frame(); game.update(1 / 60)
        if operative.telegraph_active:
            break
    assert operative.telegraph_active and operative.state == "windup"
    key(game, pygame.K_c)
    assert not operative.telegraph_active
    assert operative.state == "patrol"
    assert not field.enemy_manager.projectiles


def test_keyboard_scattergun_reveals_watcher(game):
    # Contact event ID is a synthetic unlock fixture; it is not a contact playthrough.
    game.campaign.apply_event({"event_id": "FASR-002", "type": "record_contact",
                               "payload": {"civilization_id": "FASR-002"}})
    field = annex(game)
    key(game, pygame.K_n); key(game, pygame.K_n)
    watcher = field.enemy_manager.enemies[1]
    watcher.x = watcher.spawn_x = 130
    watcher.y = watcher.spawn_y = 204
    watcher.rect.topleft = (130, 204)
    watcher.patrol_left = watcher.patrol_right = 130
    watcher.cooldown_timer = 99
    field.enemy_manager.enemies = [watcher]
    key(game, pygame.K_q)
    assert field.player.arsenal.active_weapon_id == "scattergun"
    key(game, pygame.K_x)
    for _ in range(30):
        game.input.begin_frame(); game.update(1 / 60)
        if watcher.has_status("revealed"):
            break
    assert watcher.has_status("revealed")
    position = (watcher.x, watcher.y)
    assert not watcher.try_teleport(field.player, field.room)
    assert (watcher.x, watcher.y) == position


@pytest.mark.parametrize("kind", ["solid", "hazard"])
def test_hound_pounce_does_not_enter_new_wall(game, monkeypatch, kind):
    field = annex(game)
    key(game, pygame.K_n); key(game, pygame.K_n)
    hound = field.enemy_manager.enemies[0]
    # Controlled grounded position; a new wall models a changing room after windup.
    hound.x = hound.spawn_x = 160
    hound.y = hound.spawn_y = 216
    hound.rect.topleft = (160, 216)
    hound.patrol_left, hound.patrol_right = 150, 170
    field.enemy_manager.enemies = [hound]
    for _ in range(150):
        game.input.begin_frame(); game.update(1 / 60)
        if hound.state == "attack":
            break
    assert hound.state == "attack"
    wall = pygame.Rect(100, 0, 16, 240)
    original = field.room.check_rect_collision
    def add_wall(rect):
        result = dict(original(rect))
        result[kind] = result[kind] or rect.colliderect(wall)
        return result
    monkeypatch.setattr(field.room, "check_rect_collision", add_wall)
    for _ in range(80):
        game.input.begin_frame(); game.update(1 / 60)
        assert not hound.rect.colliderect(wall)
        if hound.state != "attack":
            break
    assert hound.state == STATE_RECOVERY
    prior_y = hound.y
    for _ in range(180):
        game.input.begin_frame(); game.update(1 / 60)
        assert not hound.rect.colliderect(wall)
        assert abs(hound.y - prior_y) <= 7
        prior_y = hound.y
        if hound.is_grounded:
            break
    assert hound.is_grounded
    support = field.room.check_rect_collision(hound.rect.move(0, 1))
    assert support["solid"] or support["one_way"]
    assert not hound.is_dead
    # Continue through recovery back to patrol; no snap back to patrol bounds.
    for _ in range(120):
        before = (hound.x, hound.y)
        game.input.begin_frame(); game.update(1 / 60)
        assert abs(hound.x - before[0]) <= 7 and abs(hound.y - before[1]) <= 7
        assert not hound.rect.colliderect(wall)


@pytest.mark.parametrize("swap", [False, True])
def test_hound_patrol_stays_out_of_geometry_in_both_timelines(game, swap):
    field = annex(game)
    if swap:
        key(game, pygame.K_t)
    key(game, pygame.K_n); key(game, pygame.K_n)
    for _ in range(1800):
        game.input.begin_frame(); game.update(1 / 60)
        for enemy in field.enemy_manager.enemies:
            collision = field.room.check_rect_collision(enemy.rect)
            assert not collision["solid"] and not collision["hazard"]
            assert pygame.Rect(0, 0, field.room.width_px, field.room.height_px).contains(enemy.rect)


def test_hound_pounce_stops_at_room_edge_and_lands(game):
    field = annex(game)
    key(game, pygame.K_n); key(game, pygame.K_n)
    hound = field.enemy_manager.enemies[0]
    # Fixture models the instant before a leftward pounce crosses the room edge.
    hound.x = 1.0
    hound.y = 200.0
    hound.spawn_y = 216.0
    hound.rect.topleft = (1, 200)
    hound.state = "attack"
    hound.state_timer = 1.0
    hound.vx = -200.0
    hound.vy = 0.0
    hound.is_grounded = False
    hound.attack_hitbox_active = True
    field.enemy_manager.enemies = [hound]
    for _ in range(180):
        before = (hound.x, hound.y)
        game.input.begin_frame(); game.update(1 / 60)
        assert 0 <= hound.x and hound.x + hound.cfg.width <= field.room.width_px
        assert abs(hound.x - before[0]) <= 4 and abs(hound.y - before[1]) <= 7
        if hound.is_grounded:
            break
    assert hound.is_grounded and not hound.is_dead
    support = field.room.check_rect_collision(hound.rect.move(0, 1))
    assert support["solid"] or support["one_way"]


def unlock_fixture(game, event_id):
    # Synthetic public contact ID supplies equipment prerequisites only.
    game.campaign.apply_event({"event_id": event_id, "type": "record_contact",
                               "payload": {"civilization_id": event_id}})


def isolate(field, pair, index, x=130, y=None):
    for _ in range(pair):
        key(field.machine, pygame.K_n)
    target = field.enemy_manager.enemies[index]
    target.x = target.spawn_x = x
    target.y = target.spawn_y = (240 - target.cfg.height if y is None else y)
    target.rect.topleft = (int(target.x), int(target.y))
    target.patrol_left = target.patrol_right = x
    field.enemy_manager.enemies = [target]
    return target


def tick_until(game, predicate, limit=180):
    for _ in range(limit):
        game.input.begin_frame(); game.update(1 / 60)
        if predicate():
            return
    pytest.fail('condition did not occur within fixture frame budget')


def test_keyboard_emp_breaks_actual_watcher_channel(game):
    unlock_fixture(game, 'FASR-004')
    field = annex(game)
    watcher = isolate(field, 2, 1, y=204)
    watcher.teleport_cooldown = 99
    tick_until(game, lambda: watcher.is_channeling)
    start = field.player.coherence
    tick_until(game, lambda: field.player.coherence < start)
    key(game, pygame.K_q)
    assert field.player.arsenal.active_weapon_id == 'emp_bola'
    key(game, pygame.K_x)
    tick_until(game, lambda: watcher.has_status('stun'))
    # Projectile collision occurs after enemy update; the following tick interrupts.
    game.input.begin_frame(); game.update(1 / 60)
    assert not watcher.is_channeling and not watcher.telegraph_active
    stopped_at = field.player.coherence
    for _ in range(30):
        game.input.begin_frame(); game.update(1 / 60)
    assert field.player.coherence == pytest.approx(stopped_at)


def test_keyboard_scattergun_reveals_phantom_and_increases_hit_damage(game, monkeypatch):
    unlock_fixture(game, 'FASR-002')
    field = annex(game)
    phantom = isolate(field, 4, 0, y=204)
    phantom.cooldown_timer = 99
    # Measure the actual starter-maser hit before reveal.
    hits = []
    original_take_damage = phantom.take_damage
    def observe_hit(amount, *args, **kwargs):
        revealed = phantom.has_status("revealed")
        result = original_take_damage(amount, *args, **kwargs)
        hits.append((amount, revealed, result.damage_dealt))
        return result
    monkeypatch.setattr(phantom, "take_damage", observe_hit)
    before = phantom.health
    key(game, pygame.K_x)
    tick_until(game, lambda: phantom.health < before)
    phased_damage = before - phantom.health
    for _ in range(30):
        game.input.begin_frame(); game.update(1 / 60)
    key(game, pygame.K_q)
    assert field.player.arsenal.active_weapon_id == 'scattergun'
    key(game, pygame.K_x)
    tick_until(game, lambda: phantom.has_status('revealed'))
    assert phantom.health < before and phased_damage > 0
    # Inspect actual per-hit inputs/results, excluding invulnerable zero-damage pellets.
    assert any(not revealed and dealt == max(1, int(amount * .25))
               for amount, revealed, dealt in hits if dealt)
    scatter_damage = field.player.weapon.cfg.damage
    assert any(revealed and amount == scatter_damage and dealt == int(amount * 1.5)
               for amount, revealed, dealt in hits if dealt)


@pytest.mark.parametrize('pair,index', [(2, 0), (2, 1), (3, 0), (3, 1), (4, 0)])
def test_lost_line_of_sight_on_last_windup_frame_cancels_attack(game, monkeypatch, pair, index):
    field = annex(game)
    enemy = isolate(field, pair, index, y=204 if (pair, index) in ((2, 1), (4, 0)) else None)
    if pair == 2:
        enemy.teleport_cooldown = 99
    tick_until(game, lambda: enemy.state == 'windup' and enemy.telegraph_active)
    # Controlled boundary: target becomes occluded at the last windup update.
    enemy.state_timer = 1 / 120
    monkeypatch.setattr(enemy, 'check_line_of_sight', lambda *args: False)
    game.input.begin_frame(); game.update(1 / 60)
    assert enemy.state == 'patrol'
    assert not enemy.telegraph_active
    assert not getattr(enemy, 'is_channeling', False)
    assert not field.enemy_manager.projectiles


def test_splicer_normal_attack_launches_rising_then_falling_acid(game):
    field = annex(game)
    splicer = isolate(field, 3, 0, x=180)
    tick_until(game, lambda: splicer.telegraph_active)
    tick_until(game, lambda: bool(field.enemy_manager.projectiles))
    acid = field.enemy_manager.projectiles[0]
    assert acid.source_id == splicer.target_id and acid.gravity == 380
    assert acid.vy < 0
    initial_y, initial_vy = acid.y, acid.vy
    tick_until(game, lambda: acid.vy > 0, limit=45)
    assert acid.y < initial_y and acid.vy > initial_vy
    # Continue through the descending arc, unless room geometry or the player absorbs it.
    apex_y = acid.y
    lowest_y = acid.y
    for _ in range(45):
        game.input.begin_frame(); game.update(1 / 60)
        if acid not in field.enemy_manager.projectiles:
            break
        lowest_y = max(lowest_y, acid.y)
    assert lowest_y > apex_y  # observed descent before collision or expiry


@pytest.mark.parametrize('jump', [False, True])
def test_guardian_shockwave_keyboard_jump_counter(game, jump):
    field = annex(game)
    guardian = isolate(field, 3, 1, x=130)
    tick_until(game, lambda: guardian.telegraph_active)
    tick_until(game, lambda: bool(field.enemy_manager.projectiles))
    waves = [p for p in field.enemy_manager.projectiles if p.source_id == guardian.target_id]
    assert len(waves) == 2 and all(p.ground_only and p.is_shockwave for p in waves)
    initial_health = field.player.health
    if jump:
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    for _ in range(50):
        game.input.begin_frame(); game.update(1 / 60)
        if not field.enemy_manager.projectiles:
            break
    if jump:
        game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE))
        assert field.player.health == initial_health
    else:
        assert field.player.health < initial_health


def test_tape_keyboard_interrupts_real_operative_and_empowers_shot(game):
    # Synthetic event ID unlocks tape; FASR-001 is the valid contact payload.
    game.campaign.apply_event({'event_id': 'reality_anchor_1977', 'type': 'record_contact',
                               'payload': {'civilization_id': 'FASR-001'}})
    field = annex(game)
    operative = isolate(field, 1, 1)
    tick_until(game, lambda: operative.telegraph_active)
    for _ in range(4):
        if field.player.abilities.selected_ability_id == 'serendipity_tape_deck':
            break
        key(game, pygame.K_r)
    assert field.player.abilities.selected_ability_id == 'serendipity_tape_deck'
    key(game, pygame.K_k)
    assert operative.has_status('prediction_shattered')
    assert operative.state == STATE_RECOVERY and not operative.telegraph_active
    before = operative.health
    key(game, pygame.K_x)
    tick_until(game, lambda: operative.health < before)
    assert before - operative.health == min(before, field.player.weapon.cfg.damage * 3)


@pytest.mark.parametrize('crouch', [False, True])
def test_annex_authored_cover_blocks_actual_splicer_acid(game, monkeypatch, crouch):
    field = annex(game)
    cover = next(obj for obj in field.room.get_objects_for_timeline() if obj.id == 'annex_low_cover')
    assert cover.rect == pygame.Rect(48, 224, 16, 16)
    assert not field.room.check_rect_collision(cover.rect)['solid']
    # Walk to authored cover using normal input, then allow momentum to settle.
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
    tick_until(game, lambda: field.player.x >= 40)
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_d))
    for _ in range(25):
        game.input.begin_frame(); game.update(1 / 60)
    assert field.room.get_cover_at(field.player.rect)['id'] == 'annex_low_cover'
    if crouch:
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c))
        game.input.begin_frame(); game.update(1 / 60)
        assert field.player.is_crouching
    splicer = isolate(field, 3, 0, x=205)
    observed = []
    original = field.player.is_protected_from_attack
    def observe(room, direction):
        result = original(room, direction)
        observed.append((direction, result))
        return result
    monkeypatch.setattr(field.player, 'is_protected_from_attack', observe)
    health = field.player.health
    tick_until(game, lambda: bool(observed), limit=180)
    assert observed[0] == ('right', crouch)
    assert (field.player.health == health) is crouch
    if not crouch:
        assert field.player.health < health
    if crouch:
        game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_c))


@pytest.mark.parametrize("swap", [False, True])
def test_annex_low_cover_safely_reachable_in_both_timelines(game, swap):
    field = annex(game)
    if swap:
        key(game, pygame.K_t)
    cover = next(obj for obj in field.room.get_objects_for_timeline() if obj.id == "annex_low_cover")
    assert not cover.rect.colliderect(field.player.rect)
    assert not field.room.check_rect_collision(cover.rect)["solid"]
    assert not field.room.check_rect_collision(cover.rect)["hazard"]
    support = field.room.check_rect_collision(cover.rect.move(0, 1))
    assert support["solid"] or support["one_way"]
    for obj in field.room.get_objects_for_timeline():
        if obj.id != cover.id:
            assert not cover.rect.colliderect(obj.rect)
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d))
    tick_until(game, lambda: field.player.x >= 40)
    game.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_d))
    assert field.room.get_cover_at(field.player.rect)["id"] == cover.id


def test_pair_hints_fit_actual_hud_and_persist(game):
    field = annex(game)
    hints = ["ENFORCER: SLIDE / OPERATIVE: CROUCH", "HOUND: SLIDE / WATCHER: EMP OR REVEAL",
             "SPLICER: CROUCH IN COVER / GUARDIAN: JUMP", "PHANTOM: SCATTERGUN / DRONE: BREAK SIGHT"]
    for expected in hints:
        key(game, pygame.K_n)
        notification = field.objective_tracker.active_notification
        assert notification.title == "COUNTERS" and notification.text == expected
        assert notification.timer > 7.9
        assert game.crt.font_sm.size(f"[COUNTERS] {expected}")[0] <= 322
        for enemy in field.enemy_manager.enemies:
            enemy.cooldown_timer = 99
        for _ in range(240):
            game.input.begin_frame(); game.update(1 / 60)
        assert field.objective_tracker.active_notification is notification
        assert notification.timer > 3.9
