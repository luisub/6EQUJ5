"""PURPOSE: Protect native text compositing, reading content, and navigation.
CALLED BY: pytest.
HOW TO MODIFY: Test rendered boundaries and normal UI events, not font internals alone.
"""
from types import SimpleNamespace
import pygame
import pytest
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.ui.text import TextInputBuffer, wrap_text_pixels
from video_game.engine.ui.hud import dossier_lines
from video_game.engine.field_reality import FieldReality


@pytest.fixture
def game(tmp_path):
    pygame.init(); pygame.display.set_mode((960,540))
    machine=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp_path),settings_store=SettingsStore(tmp_path))
    try:
        machine.start_new_game(); yield machine
    finally:
        machine.close(); pygame.quit()


def test_native_text_interleaves_with_logical_layers_and_resets(game):
    crt=game.crt;crt.clear((1,2,3));crt.draw_text('FIRST',10,10,color=(255,255,255),has_shadow=False)
    pygame.draw.rect(crt.canvas,(200,20,20),(10,10,75,12))
    crt.draw_text('X',10,10,color=(20,255,20),has_shadow=False)
    image=crt.finalize_frame(); assert image.get_at((100,30))[:3]==(200,20,20)
    assert any(image.get_at((x,y)).g>150 for x in range(20,40) for y in range(20,42))
    assert not any(image.get_at((x,y)).r>220 and image.get_at((x,y)).g>220 for x in range(20,120) for y in range(20,42))
    crt.clear((3,4,5)); assert crt.finalize_frame().get_at((100,30))[:3]==(3,4,5)


def test_scientific_glyphs_wrap_and_cursor_use_rendered_metrics(game):
    font=game.crt.font_sm
    def signature(ch):
        surf=font.native.render(ch,True,(255,255,255));return surf.get_size(),pygame.image.tobytes(surf,'RGBA')
    for ch in 'σö°±–—': assert signature(ch)!=signature('\ufffd')
    text='ordinary prefix '+('SCIENTIFIC_TOKEN_'*12)+' https://example.org/'+('q'*90)+'\nsecond line σ'
    wrapped=wrap_text_pixels(text,font,110)
    assert all(font.size(line)[0]<=110 for line in wrapped)
    assert ''.join(wrapped).replace(' ','')==text.replace(' ','').replace('\n','')
    assert wrapped[-1]=='second line σ'
    buf=TextInputBuffer(256);buf.set_text('variable width long text '+('M'*40));buf.move_left();visible,pos=buf.get_visible_slice_pixels(font,120)
    assert font.size(visible)[0]<=120 and pos>=0 and pos<=len(visible)


def test_dossier_wrap_and_keyboard_scroll_preserve_long_objective(game):
    game.change_state(config.STATE_BUNKER_HUB);scene=game.current_scene
    obj=SimpleNamespace(title='GREENKEEPER',description='Detailed observation of the feedhorn chamber and all of its protected attack lanes '*8,
                        hint='Read every warning and use the indicated cover '*7)
    scene.objective_tracker.get_active_objective=lambda campaign:obj
    rows=dossier_lines(game.crt,game.campaign,obj)
    assert all(game.crt.font_sm.size(text)[0]<=190 for text,_ in rows)
    complete=''.join(text for text,_ in rows).replace(' ','')
    assert obj.description.replace(' ','') in complete and obj.hint.replace(' ','') in complete
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB))
    for _ in range(50):scene.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_DOWN))
    assert scene.dossier_offset==max(0,len(rows)-15) and scene.dossier_offset>0
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB));assert not scene.dossier_open


def test_lab_full_detail_contains_all_choice_impacts(game):
    game.change_state(config.STATE_SCIENCE_LAB);lab=game.current_scene
    for index in range(len(lab.scenario_keys)):
        lab._select_active(index)
        # Explicit content fixture; later scenarios are locked in a fresh campaign.
        lab.workbench.active_scenario = lab.scenarios[lab.scenario_keys[index]]
        joined=' '.join(lab.get_details_lines()).replace(' ','')
        for choice in lab.workbench.active_scenario.get('deployment_choices',[]):
            impact=str(choice.get('meter_impact',''))
            if impact: assert impact.replace(' ','') in joined


def test_relay_scroll_keeps_complete_long_message(game):
    relay=SimpleNamespace(get_visible_messages=lambda:[SimpleNamespace(era='1985',text='Scientific transmission '+('verylongtoken'*120))])
    scene=SimpleNamespace(machine=game)
    controller=FieldReality(scene);controller.world=object();controller.relay=relay;controller.panel_open=True
    lines=controller.message_lines(game.crt)
    assert len(lines)>8 and all(game.crt.font_sm.size(line)[0]<=440 for line in lines)
    assert ('verylongtoken'*120) in ''.join(lines).replace(' ','')
    for _ in range(100):controller.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_DOWN))
    assert controller.message_scroll==len(lines)-8
    controller.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_LEFT));assert controller.message_scroll==0


def test_boss_title_alert_and_player_stats_have_disjoint_visible_text(game):
    game.change_state(config.STATE_BOSS_BOUNTY)
    game.update(1.6)  # Real combat begins after the safe reveal.
    game.current_scene.boss.weak_point_exposed=True
    game.current_scene.boss.phase_state = 'ATTACK'  # Explicit active-attack layout fixture.
    crt=game.crt; original=crt.draw_text; drawn=[]
    def record(text,*args,**kwargs):
        rect=original(text,*args,**kwargs); drawn.append((str(text),rect)); return rect
    crt.draw_text=record
    game.render()
    find=lambda substring: next(rect for text,rect in drawn if substring in text)
    assert not find('THE GREENKEEPER').colliderect(find('HP 100'))
    assert not find('THE GREENKEEPER').colliderect(find('LOCK-ON'))
    assert not find('THE GREENKEEPER').colliderect(find('CORE VULNERABLE'))


def test_lab_full_view_scrolls_all_lines_through_real_keys(game):
    game.contact_session.is_offline = True
    game.contact_session.send_message('2')  # authored prerequisite fixture
    game.change_state(config.STATE_SCIENCE_LAB);lab=game.current_scene
    lab.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_h))
    total=len(lab.get_details_lines()); assert total>17
    for _ in range(20):lab.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_DOWN))
    assert lab.details_offset==total-17
    lab.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE)); assert not lab.details_open


def test_text_only_batch_preserves_pixels_and_following_shape_order(game):
    crt=game.crt
    def frame(batched):
        crt.clear((2,3,4));pygame.draw.rect(crt.canvas,(20,40,60),(5,5,120,40))
        if batched:
            with crt.text_batch():
                crt.draw_text('First',10,10);crt.draw_text('Second σ',10,22)
        else:
            crt.draw_text('First',10,10);crt.draw_text('Second σ',10,22)
        pygame.draw.rect(crt.canvas,(220,10,10),(10,10,8,8))
        crt.draw_text('Last',80,10)
        return pygame.image.tobytes(crt.finalize_frame(),'RGBA')
    assert frame(False)==frame(True)


def test_disjoint_dirty_region_batch_matches_full_flush(game):
    crt=game.crt
    def frame(regional):
        crt.clear((1,2,3));crt.draw_text('header',4,2)
        pygame.draw.rect(crt.canvas,(30,50,70),(4,18,126,33))
        pygame.draw.rect(crt.canvas,(90,80,70),(200,70,9,9))
        with crt.text_batch(dirty_region=(4,18,126,33) if regional else None):
            crt.draw_text('HP 100',8,19);crt.draw_text('MASER',8,29)
        return pygame.image.tobytes(crt.finalize_frame(),'RGBA')
    assert frame(False)==frame(True)


def test_hud_known_clean_staging_matches_full_flush(game):
    from video_game.engine.ui.hud import render_global_hud
    crt=game.crt
    def frame(known_clean):
        crt.clear((4,7,9))
        crt.draw_text('scene text',120,224)
        render_global_hud(crt,game.campaign,location_label='FIELD',player=game.scenes[config.STATE_FIELD_OPS].player,
                          threat_level='LOCKED',staging_cleared=known_clean)
        return pygame.image.tobytes(crt.finalize_frame(),'RGBA')
    assert frame(False)==frame(True)


def test_conditional_hud_and_relay_regions_match_full_flush(game, monkeypatch):
    game.change_state(config.STATE_FIELD_OPS)
    scene=game.current_scene
    # Forward encounters arrive after a timed warning, rather than on entry.
    for _ in range(120):
        if scene.enemy_manager.enemies:
            break
        game.input.begin_frame()
        game.update(1 / 60)
    assert scene.enemy_manager.enemies, 'First timed encounter did not arrive'
    scene.prompt_text=''
    scene.player.charge_timer=.4
    scene.enemy_manager.enemies[0].aim_locked=True
    scene.objective_tracker.post_notification('NOTICE','READABLE NOTIFICATION','warning')
    original=game.crt.text_batch
    def compare():
        game.render(); normal=pygame.image.tobytes(game.crt.render_surface,'RGBA')
        with monkeypatch.context() as patch:
            patch.setattr(game.crt,'text_batch',lambda dirty_region=None: original())
            game.render(); full=pygame.image.tobytes(game.crt.render_surface,'RGBA')
        assert normal==full
    compare()
    game.change_state(config.STATE_BUNKER_HUB)
    game.change_state(config.STATE_FIELD_OPS,room='act_04/dodleston_relay.json')
    game.current_scene.reality.panel_open=True
    compare()


def test_initial_full_layer_matches_alpha_bounded_flush_after_partial_clear(game):
    crt=game.crt;crt.clear((30,40,50))
    pygame.draw.rect(crt.canvas,(0,0,0,0),(0,0,100,80))
    pygame.draw.rect(crt.canvas,(200,10,20,128),(12,12,10,10))
    source=crt.logical_canvas.copy();bounds=source.get_bounding_rect()
    expected=pygame.Surface((960,540),pygame.SRCALPHA).convert_alpha();expected.fill((0,0,0,0))
    layer=pygame.transform.scale(source.subsurface(bounds),(bounds.w*2,bounds.h*2))
    expected.blit(layer,(bounds.x*2,bounds.y*2))
    assert pygame.image.tobytes(crt.finalize_frame(),'RGBA')==pygame.image.tobytes(expected,'RGBA')


def test_lazy_logical_snapshot_is_exact_and_refreshes_after_clear(game):
    crt=game.crt;crt.clear((1,2,3));crt.draw_text('Snapshot σ',12,15)
    native=crt.finalize_frame();expected=pygame.transform.scale(native,(480,270))
    assert crt._snapshot_dirty
    snapshot=crt.canvas
    assert snapshot is crt.logical_canvas and not crt._snapshot_dirty
    assert pygame.image.tobytes(snapshot,'RGBA')==pygame.image.tobytes(expected,'RGBA')
    before=native.get_at((0,0));snapshot.fill((200,30,40));assert native.get_at((0,0))==before
    crt.clear((8,9,10));crt.finalize_frame()
    assert crt.logical_canvas.get_at((0,0))[:3]==(8,9,10)
    game.change_state(config.STATE_FIELD_OPS);game.pause.open();game.render()
    expected=pygame.transform.scale(crt.render_surface,(480,270))
    assert pygame.image.tobytes(crt.canvas,'RGBA')==pygame.image.tobytes(expected,'RGBA')


def test_bunker_station_prompts_fit_measured_screen_bounds(game, monkeypatch):
    from video_game.engine.scenes.bunker import BUNKER_STATIONS
    game.change_state(config.STATE_BUNKER_HUB)
    scene = game.current_scene; seen = []
    original = game.crt.draw_text
    def record(text, x, y, *args, **kwargs):
        if y == 102 and str(text).startswith('E: USE '):
            seen.append((str(text), x, y))
        return original(text, x, y, *args, **kwargs)
    monkeypatch.setattr(game.crt, 'draw_text', record)
    for station in BUNKER_STATIONS.values():
        scene.mateo_x = station['center_x']; game.render()
    scene.mateo_x = BUNKER_STATIONS['repair']['center_x']
    assert game.campaign.apply_event({'event_id':'ui_collect','type':'collect_analog_coupler'}); game.render()
    assert game.campaign.apply_event({'event_id':'ui_repair','type':'repair_dish_feedhorn'}); game.render()
    assert len(seen) == 6
    assert {text for text, _, _ in seen} == {
        'E: USE LAB', 'E: USE RECEIVER', 'E: USE REPAIR', 'E: USE AIRLOCK'}
    for text, x, _ in seen:
        assert x >= 8 and x + game.crt.font_sm.size(text)[0] <= config.INTERNAL_WIDTH - 8


def test_boss_exposure_label_has_own_line_and_fits_panel(game, monkeypatch):
    game.change_state(config.STATE_BOSS_BOUNTY)
    game.update(1.6)  # Real combat begins after the safe reveal.
    scene = game.current_scene; scene.boss.weak_point_exposed = True; seen = {}
    scene.boss.phase_state = 'ATTACK'  # Explicit active-attack layout fixture.
    original = game.crt.draw_text
    def record(text, x, y, *args, **kwargs):
        seen[str(text)] = (x, y)
        return original(text, x, y, *args, **kwargs)
    monkeypatch.setattr(game.crt, 'draw_text', record); game.render()
    label = '[!] CORE VULNERABLE'; x,y = seen[label]
    assert (x,y) == (140,44)
    assert x + game.crt.font_sm.size(label)[0] <= 364
    title = next(key for key in seen if 'GREENKEEPER' in key and '[PHASE' in key)
    assert seen[title][1] < y
    assert seen['[!] LOCK-ON: EVADE NOW!'][1] >= y + game.crt.font_sm.size(label)[1]


def test_field_room_and_checkpoint_use_authored_names(game, monkeypatch):
    game.change_state(config.STATE_FIELD_OPS, room='act_01/salvage_yard.json', spawn='yard_entrance')
    scene = game.current_scene
    scene.player.x = 64  # Activate the real checkpoint outside the adjacent exit trigger.
    for _ in range(30): game.update(1/60)
    assert scene.player.active_checkpoint_id == 'yard_start'
    assert next(c for c in scene.room.checkpoints if c.id == 'yard_start').name == 'SALVAGE YARD // SECURITY GATE'
    assert scene.prompt_text == 'CHECKPOINT'
    locations = []; texts = []
    original_hud = game.render_global_hud; original_text = game.crt.draw_text
    def hud(*args, **kwargs):
        locations.append(kwargs['location_label']); return original_hud(*args, **kwargs)
    def draw(text, *args, **kwargs):
        texts.append(str(text)); return original_text(text, *args, **kwargs)
    monkeypatch.setattr(game, 'render_global_hud', hud)
    monkeypatch.setattr(game.crt, 'draw_text', draw)
    game.render()
    assert locations == [scene.room.title]
    assert not any(scene.player.arsenal.active_weapon.name in value and
                   scene.player.abilities.selected_ability.name in value for value in texts)
    assert scene.player.active_checkpoint_id == 'yard_start'
