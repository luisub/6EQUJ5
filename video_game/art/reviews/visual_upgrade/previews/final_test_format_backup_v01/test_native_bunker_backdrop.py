"""PURPOSE: Verify validated native bunker backgrounds and unchanged scene ordering.
CALLED BY: pytest.
HOW TO MODIFY: Use temporary asset/save roots, physical key events and complete fallback checks.
"""
import hashlib
import json
import shutil
from pathlib import Path

import pygame
import pytest

from video_game.engine import config
from video_game.engine.assets import AssetCache
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.native_room_assets import load_native_opaque_backdrop
from video_game.engine.room_art_contracts import backdrop_manifest_template
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


@pytest.fixture
def bunker_assets(tmp_path):
    pygame.init(); pygame.display.set_mode((960, 540))
    root = tmp_path/'assets'
    shutil.copytree(config.ASSETS_DIR, root, ignore=shutil.ignore_patterns('ohio_bunker_v1'))
    base = root/'environments/ohio_bunker_v1'; base.mkdir(parents=True)
    doc = backdrop_manifest_template('ohio_bunker_v1')
    image = pygame.Surface((960,540)); image.fill((15,30,45))
    image.set_at((20,120), (220,5,4)); image.set_at((21,120), (5,4,220))
    path = base/doc['backdrop']['file']; pygame.image.save(image, str(path))
    doc['backdrop']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    (base/'manifest.json').write_text(json.dumps(doc))
    yield root
    pygame.quit()


def test_backdrop_validation_fallback_and_crop_are_atomic(bunker_assets, tmp_path):
    root = bunker_assets; base = root/'environments/ohio_bunker_v1'; manifest = base/'manifest.json'
    old = manifest.read_bytes(); doc = json.loads(old)
    family = load_native_opaque_backdrop(root,'bunker_hub',(480,270))
    assert family is not None
    assert load_native_opaque_backdrop(root,'other',(480,270)) is None
    assert load_native_opaque_backdrop(root,'bunker_hub',(481,270)) is None
    class Recorder:
        def __init__(self): self.calls = []
        def composite_opaque_background(self, *a, **kw): self.calls.append((a,kw))
    recorder = Recorder()
    for x,y in ((-.25,0),(0,-.25),(.25,0),(0,.25),(float('nan'),0)):
        assert not family.render(recorder,x,y) and not recorder.calls
    assert family.render(recorder,0,0) and len(recorder.calls)==1
    for mutate in ('metadata','wrongtype','hash'):
        doc=json.loads(old)
        if mutate=='metadata':doc['backdrop']['dimensions']=[959,540]
        if mutate=='wrongtype':doc['backdrop']['repeat']=0
        if mutate=='hash':doc['backdrop']['sha256']='0'*64
        manifest.write_text(json.dumps(doc))
        assert load_native_opaque_backdrop(root,'bunker_hub',(480,270)) is None
    manifest.write_bytes(old)
    source=base/doc['backdrop']['file']; original=source.read_bytes()
    source.unlink(); assert load_native_opaque_backdrop(root,'bunker_hub',(480,270)) is None
    outside=tmp_path/'outside.png';outside.write_bytes(original);source.symlink_to(outside)
    assert load_native_opaque_backdrop(root,'bunker_hub',(480,270)) is None
    source.unlink();source.write_bytes(original)
    journal=root.parent/f'.{root.name}-asset-build-pending.json';journal.write_text('{}')
    assert load_native_opaque_backdrop(root,'bunker_hub',(480,270)) is None
    journal.unlink();assert load_native_opaque_backdrop(root,'bunker_hub',(480,270)) is not None
    translucent=pygame.Surface((960,540),pygame.SRCALPHA);translucent.fill((5,6,7,255));translucent.set_at((3,3),(5,6,7,254));pygame.image.save(translucent,str(source))
    doc=json.loads(old);doc['backdrop']['sha256']=hashlib.sha256(source.read_bytes()).hexdigest();manifest.write_text(json.dumps(doc))
    assert load_native_opaque_backdrop(root,'bunker_hub',(480,270)) is None


def test_bunker_scene_layers_palette_reentry_and_input(bunker_assets, tmp_path, monkeypatch):
    game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp_path/'save'),settings_store=SettingsStore(tmp_path/'save'))
    try:
        game.assets=AssetCache(bunker_assets);assert game.start_new_game()[0]
        game.change_state(config.STATE_BUNKER_HUB);scene=game.current_scene;scene.on_enter()
        assert scene.native_backdrop is not None
        # Controlled actor and foreground prove that both remain above native art.
        transparent=pygame.Surface((480,270),pygame.SRCALPHA)
        scene.layers=[transparent.copy() for _ in range(6)]
        actor=pygame.Surface((1056,128),pygame.SRCALPHA);actor.fill((0,0,0,0));pygame.draw.rect(actor,(240,20,30,255),(0,0,10,10))
        scene.strips=[actor,actor,actor];scene.outfit_idx=0;scene.pose_idx=0;scene.mateo_x=140
        pygame.draw.rect(scene.layers[4],(10,240,20,255),(140,122,2,2))
        pygame.draw.rect(scene.layers[5],(10,20,240,255),(143,122,2,2))
        with monkeypatch.context() as patch:
            original_open=Path.open
            def no_family_io(path,*a,**kw):
                if path.is_relative_to(bunker_assets/'environments/ohio_bunker_v1'):pytest.fail('family read during frame')
                return original_open(path,*a,**kw)
            patch.setattr(Path,'open',no_family_io)
            patch.setattr(pygame.image,'load',lambda *a,**kw:pytest.fail('image loaded during frame'))
            game.render()
        frame=game.crt.render_surface
        assert frame.get_at((20,120))[:3] == (220,5,4)
        assert frame.get_at((21,120))[:3] == (5,4,220)
        assert frame.get_at((280,244))[:3] == (10,240,20)
        assert frame.get_at((286,244))[:3] == (10,20,240)
        assert frame.get_at((290,248))[:3] == (240,20,30)
        # Palette mode returns before the native background path.
        scene.palette_surf=pygame.Surface((480,270));scene.palette_surf.fill((80,90,100));scene.view_mode=2;game.render()
        assert game.crt.render_surface.get_at((20,120))[:3] == (80,90,100)
        scene.view_mode=0;game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB));assert scene.dossier_open
        game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB));assert not scene.dossier_open
        game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e));assert game.current_state_name==config.STATE_SCIENCE_LAB
        manifest=bunker_assets/'environments/ohio_bunker_v1/manifest.json';manifest.unlink()
        game.change_state(config.STATE_BUNKER_HUB);assert game.current_scene.native_backdrop is None
        game.render();assert game.crt.render_surface.get_at((20,120))[:3] != (220,5,4)
    finally:game.close()
