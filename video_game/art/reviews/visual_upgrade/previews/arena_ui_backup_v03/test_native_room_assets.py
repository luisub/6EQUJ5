"""PURPOSE: Verify native approach family validation, routing and camera alignment.
CALLED BY: pytest.
HOW TO MODIFY: Use temporary assets; test complete fallback and no gameplay mutation.
"""
import json
import hashlib
import logging
import shutil
from pathlib import Path
import pygame
import pytest
from video_game.engine import config
from video_game.engine.native_room_assets import NativeApproachFamily, load_approach_family
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.assets import AssetCache
from video_game.engine.world import Camera
from video_game.tools.build_approach_family import build_family


@pytest.fixture
def display():
    pygame.init();pygame.display.set_mode((960,540))
    yield
    pygame.quit()


@pytest.fixture
def family_root(tmp_path, display):
    root=tmp_path/'assets';root.mkdir()
    far=pygame.Surface((1152,544),pygame.SRCALPHA);far.fill((15,40,90,255)); far.set_at((300,120),(230,5,4,255));far.set_at((301,120),(5,4,230,255))
    world=pygame.Surface((1920,576),pygame.SRCALPHA);world.fill((0,0,0,0));pygame.draw.rect(world,(11,225,33,255),(400,120,20,20))
    world.set_at((300,490),(11,225,33,255));world.set_at((10,10),(11,225,33,255))
    fs=tmp_path/'source_far.png';ws=tmp_path/'source_world.png';pygame.image.save(far,str(fs));pygame.image.save(world,str(ws))
    result=build_family(assets_dir=root, archive_dir=tmp_path/'archive',far=fs,world=ws,promote=True)
    assert result['status']=='promoted'
    return root


def test_builder_promoted_fixture_loads_exact_validated_family(family_root):
    family=load_approach_family(family_root,'act_01_approach',(960,288))
    assert family is not None
    assert family.far.get_size()==(1152,544) and family.world.get_size()==(1920,576)
    assert load_approach_family(family_root,'act_01_salvage_yard',(960,288)) is None
    assert load_approach_family(family_root,'act_01_approach',(640,288)) is None


def test_invalid_partial_pending_and_symlink_fall_back_whole_family(family_root, tmp_path, caplog):
    base=family_root/'environments/ohio_approach_v1'; manifest=base/'manifest.json';old=manifest.read_bytes();data=json.loads(old)
    data['layers'][1]['file']='../escape.png';manifest.write_text(json.dumps(data))
    with caplog.at_level(logging.WARNING):
        assert load_approach_family(family_root,'act_01_approach',(960,288)) is None
    assert 'fallback' in caplog.text.lower()
    for mutate in ('density','dimensions'):
        data=json.loads(old)
        if mutate=='density': data['density']=3
        else: data['layers'][1]['dimensions']=[1919,576]
        manifest.write_text(json.dumps(data))
        assert load_approach_family(family_root,'act_01_approach',(960,288)) is None
    manifest.write_bytes(old)
    far=base/'far_1152x544.png'; payload=far.read_bytes();far.write_bytes(payload+b'bad')
    assert load_approach_family(family_root,'act_01_approach',(960,288)) is None
    far.write_bytes(payload)
    world=base/'world_architecture_1920x576.png'; original=world.read_bytes();world.unlink()
    assert load_approach_family(family_root,'act_01_approach',(960,288)) is None
    substitute=tmp_path/'linked.png';substitute.write_bytes(original);world.symlink_to(substitute)
    assert load_approach_family(family_root,'act_01_approach',(960,288)) is None
    world.unlink();world.write_bytes(original)
    journal=family_root.parent/f'.{family_root.name}-asset-build-pending.json';journal.write_text('{}')
    assert load_approach_family(family_root,'act_01_approach',(960,288)) is None
    journal.unlink(); assert load_approach_family(family_root,'act_01_approach',(960,288)) is not None
    # Even a correctly hashed all-opaque world image is not this layered contract.
    opaque=pygame.Surface((1920,576),pygame.SRCALPHA);opaque.fill((1,2,3,255));pygame.image.save(opaque,str(world))
    data=json.loads(old);data['layers'][1]['sha256']=hashlib.sha256(world.read_bytes()).hexdigest();manifest.write_text(json.dumps(data))
    assert load_approach_family(family_root,'act_01_approach',(960,288)) is None


def test_fractional_camera_quantization_coverage_and_atomic_fallback(display):
    far=pygame.Surface((1152,544),pygame.SRCALPHA);world=pygame.Surface((1920,576),pygame.SRCALPHA)
    # Unique sample colors distinguish crop offsets at each native x.
    for x in range(1152): pygame.draw.line(far,(x%251,3,4,255),(x,0),(x,543))
    for x in range(1920): pygame.draw.line(world,(x%251,5,6,255),(x,0),(x,575))
    family=NativeApproachFamily(far,world); camera=Camera(480,270);camera.set_world_bounds(960,288)
    for x in (0,.25,.5,.75,1.5,239.5,480):
        for y in (0,.25,.5,.75,1.5,18):
            camera.x=x;camera.y=y
            f,w=family.crops(camera)
            assert f.get_at((0,0))==far.get_at((round(2*.1*x),round(2*.05*y)))
            assert w.get_at((0,0))==world.get_at((2*round(x),2*round(y)))
            sx,sy=camera.world_to_screen(480,240)
            assert (2*sx,2*sy)==(960-2*round(x),480-2*round(y))
    recorder=SimpleRecorder();camera.x=481
    assert family.render(recorder,camera) is False and recorder.calls==[]


class SimpleRecorder:
    def __init__(self): self.calls=[]
    def composite_opaque_background(self,*args,**kwargs): self.calls.append((args,kwargs))


def test_opaque_background_batch_matches_two_native_composites(display):
    far=pygame.Surface((960,540),pygame.SRCALPHA);far.fill((70,80,90,255))
    world=pygame.Surface((960,540),pygame.SRCALPHA);world.fill((0,0,0,0))
    pygame.draw.rect(world,(220,15,25,96),(20,20,200,100))
    crt=CRTRenderer(scale=1)
    crt.clear((2,3,4));crt.composite_native(far,(0,0),(480,270));crt.composite_native(world,(0,0),(480,270))
    pygame.draw.rect(crt.canvas,(5,180,5),(60,45,10,10));crt.draw_text('HUD',5,5)
    prior=pygame.image.tobytes(crt.finalize_frame(),'RGBA')
    crt.clear((2,3,4));crt.composite_opaque_background(far.convert(),world,known_clean=True)
    pygame.draw.rect(crt.canvas,(5,180,5),(60,45,10,10));crt.draw_text('HUD',5,5)
    assert pygame.image.tobytes(crt.finalize_frame(),'RGBA')==prior
    with pytest.raises(RuntimeError):crt.composite_opaque_background(far,world)
    # The default path flushes any prior logical drawings rather than assuming
    # the caller has not written to the canvas since clear().
    crt.clear((2,3,4));pygame.draw.rect(crt.canvas,(255,0,0),(5,5,10,10))
    crt.composite_opaque_background(far,world)
    assert crt.finalize_frame().get_at((10,10))[:3]==(70,80,90)
    crt.clear((8,9,10));assert crt.finalize_frame().get_at((30,30))[:3]==(8,9,10)


def test_actual_field_native_order_and_room_change_fallback(family_root, tmp_path, monkeypatch):
    game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp_path/'save'),settings_store=SettingsStore(tmp_path/'save'))
    try:
        game.start_new_game();game.change_state(config.STATE_FIELD_OPS);field=game.current_scene
        field.native_approach=load_approach_family(family_root,'act_01_approach',(960,288))
        monkeypatch.setattr(field.room,'render_weather',lambda *args:None)
        field.camera.x=0;field.camera.y=0;field.prompt_text='';game.render()
        # Native 1px checker survives; world alpha is above far in the same scene.
        assert game.crt.render_surface.get_at((300,120))[:3]==(230,5,4)
        assert game.crt.render_surface.get_at((301,120))[:3]==(5,4,230)
        assert game.crt.render_surface.get_at((400,120))[:3]==(11,225,33)
        # Opaque gameplay tiles and HUD remain above the native world plane.
        assert game.crt.render_surface.get_at((300,490))[:3]!=(11,225,33)
        assert game.crt.render_surface.get_at((10,10))[:3]!=(11,225,33)
        monkeypatch.setattr(game.assets, 'root', family_root)
        field.load_room('act_01/salvage_yard.json',spawn_name='yard_entrance')
        assert field.native_approach is None
        field.load_room('act_01/approach.json',spawn_name='bunker_exit')
        assert field.native_approach is not None
        world=family_root/'environments/ohio_approach_v1/world_architecture_1920x576.png'
        original=world.read_bytes();world.write_bytes(original+b'corrupt')
        field.load_room('act_01/approach.json',spawn_name='bunker_exit')
        assert field.native_approach is None
        game.render();assert game.crt.render_surface.get_at((300,120))[:3]!=(230,5,4)
        world.write_bytes(original)
        field.load_room('act_01/approach.json',spawn_name='bunker_exit')
        assert field.native_approach is not None
        # Active frames use validated surfaces without reopening any image.
        with monkeypatch.context() as patch:
            patch.setattr(pygame.image,'load',lambda *a,**kw: pytest.fail('frame reloaded an image'))
            patch.setattr(Path,'open',lambda *a,**kw: pytest.fail('frame reopened an asset'))
            game.render()
    finally: game.close()


def test_configured_root_new_bunker_reentry_and_continue(family_root, tmp_path):
    shutil.copytree(config.ASSETS_DIR, family_root, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('ohio_approach_v1'))
    save=tmp_path/'save_route'
    first=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
    try:
        first.assets=AssetCache(family_root);assert first.start_new_game()[0]
        assert first.scenes[config.STATE_FIELD_OPS].native_approach is not None
        first.change_state(config.STATE_FIELD_OPS,room='act_01/approach.json',spawn='bunker_exit')
        assert first.current_scene.native_approach is not None
        first.change_state(config.STATE_BUNKER_HUB);assert first.save_checkpoint()
        first.change_state(config.STATE_FIELD_OPS,room='act_01/approach.json',spawn='bunker_exit')
        assert first.current_scene.native_approach is not None
        first.change_state(config.STATE_BUNKER_HUB)
    finally:first.close()
    second=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(save),settings_store=SettingsStore(save))
    try:
        second.assets=AssetCache(family_root);assert second.continue_game().status == 'ok'
        second.change_state(config.STATE_FIELD_OPS,room='act_01/approach.json',spawn='bunker_exit')
        assert second.current_scene.native_approach is not None
    finally:second.close()


def _make_v2_family(root, family_id):
    from video_game.engine.room_art_contracts import manifest_template
    doc = manifest_template(family_id)
    base = root / 'environments' / family_id
    base.mkdir(parents=True)
    for item in doc['layers'] + doc['props']:
        image = pygame.Surface(item['dimensions'], pygame.SRCALPHA)
        if item['id'] == 'far':
            image.fill((30, 50, 70, 255))
        else:
            image.fill((0, 0, 0, 0))
            image.set_at((0, 0), (200, 30, 40, 255))
        path = base / item['file']
        pygame.image.save(image, str(path))
        item['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    (base / 'manifest.json').write_text(json.dumps(doc))
    return base, doc


def test_schema2_registered_props_and_full_fallback(family_root):
    from video_game.engine.native_room_assets import load_native_room_family
    base, doc = _make_v2_family(family_root, 'ohio_approach_v2')
    family = load_native_room_family(family_root, 'act_01_approach', (960, 288))
    assert family is not None
    # Native-pixel prop survives at the reviewed world origin over architecture.
    assert family.world.get_at((1608, 416)) == pygame.Color(200, 30, 40, 255)
    assert family.world.get_at((1609, 416)).a == 0
    source = base / doc['props'][0]['file']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == doc['props'][0]['sha256']
    # The installed v1 remains intact when ANY part of v2 is invalid.
    source.write_bytes(source.read_bytes() + b'corrupt')
    fallback = load_native_room_family(family_root, 'act_01_approach', (960, 288))
    assert fallback is not None and fallback.world.get_at((1608, 416)).a == 0
    journal = family_root.parent / f'.{family_root.name}-asset-build-pending.json'
    journal.write_text('{}')
    assert load_native_room_family(family_root, 'act_01_approach', (960, 288)) is None


@pytest.mark.parametrize('family_id,room_id,has_prop', [
    ('ohio_salvage_v1', 'act_01_salvage_yard', True),
    ('ohio_dish_v1', 'act_01_dish_catwalk', False),
])
def test_schema2_room_routing_and_invalid_family_is_atomic(tmp_path, display, family_id, room_id, has_prop):
    from video_game.engine.native_room_assets import load_native_room_family
    root = tmp_path / 'assets'; root.mkdir()
    base, doc = _make_v2_family(root, family_id)
    family = load_native_room_family(root, room_id, (640, 288))
    assert family is not None and family.world.get_size() == (1280, 576)
    if has_prop:
        assert family.world.get_at((392, 404)) == pygame.Color(200, 30, 40, 255)
    assert load_native_room_family(root, room_id, (960, 288)) is None
    assert load_native_room_family(root, 'unrelated', (640, 288)) is None
    camera = Camera(480, 270); camera.set_world_bounds(640, 288)
    for x in (0, .25, .5, .75, 1.5, 80, 160):
        for y in (0, .25, .5, .75, 18):
            camera.x, camera.y = x, y
            far, world = family.crops(camera)
            assert far.get_size() == world.get_size() == (960, 540)
    # Metadata cannot redirect a component or alter its collision semantics.
    if has_prop:
        doc['props'][0]['collision'] = 'cover'
    else:
        doc['layers'][1]['dimensions'] = [1279, 576]
    (base / 'manifest.json').write_text(json.dumps(doc))
    assert load_native_room_family(root, room_id, (640, 288)) is None


def test_generic_builder_to_actual_field_room_routes(tmp_path, display, monkeypatch):
    from video_game.tools.build_room_family import build_family as build_room_family
    source_root = tmp_path / 'source'; source_root.mkdir()
    root = tmp_path / 'assets'
    shutil.copytree(config.ASSETS_DIR, root, ignore=shutil.ignore_patterns(
        'ohio_approach_v1', 'ohio_approach_v2', 'ohio_salvage_v1', 'ohio_dish_v1'))
    cases = [
        ('ohio_approach_v2', 'act_01/approach.json', 'bunker_exit'),
        ('ohio_salvage_v1', 'act_01/salvage_yard.json', 'yard_entrance'),
        ('ohio_dish_v1', 'act_01/dish_catwalk.json', 'catwalk_start'),
    ]
    for family_id, _, _ in cases:
        source, doc = _make_v2_family(source_root, family_id)
        result = build_room_family(family_id, assets_dir=root, archive_dir=tmp_path/'archive',
            far=source/doc['layers'][0]['file'], world=source/doc['layers'][1]['file'],
            props=[source/prop['file'] for prop in doc['props']], promote=True)
        assert result['status'] == 'promoted'
    game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp_path/'save'),
                            settings_store=SettingsStore(tmp_path/'save'))
    try:
        game.assets = AssetCache(root)
        assert game.start_new_game()[0]
        game.change_state(config.STATE_FIELD_OPS)
        field = game.current_scene
        for family_id, room, spawn in cases:
            field.load_room(room, spawn_name=spawn)
            assert field.native_approach is not None, family_id
            assert field.native_approach.far.get_at((0, 0))[:3] == (30, 50, 70)
            with monkeypatch.context() as patch:
                patch.setattr(Path, 'open', lambda *a, **kw: pytest.fail('asset read during frame'))
                patch.setattr(pygame.image, 'load', lambda *a, **kw: pytest.fail('image load during frame'))
                game.render()
        # Non-participating scenes retain the original background.
        field.load_room('act_01/approach.json', spawn_name='bunker_exit')
        assert field.native_approach is not None
    finally:
        game.close()


def test_prop_bake_preserves_translucent_compositing(tmp_path, display):
    from video_game.engine.native_room_assets import load_native_room_family
    root = tmp_path/'assets'; root.mkdir()
    base, doc = _make_v2_family(root, 'ohio_salvage_v1')
    world_path = base/doc['layers'][1]['file']; prop_path = base/doc['props'][0]['file']
    world = pygame.image.load(str(world_path)).convert_alpha()
    prop = pygame.image.load(str(prop_path)).convert_alpha()
    for i, alpha in enumerate((100, 0, 255)):
        world.set_at((392+i,404), (100,120,140,alpha))
        prop.set_at((i,0), (200,20,30,128))
    pygame.image.save(world, str(world_path)); pygame.image.save(prop, str(prop_path))
    doc['layers'][1]['sha256'] = hashlib.sha256(world_path.read_bytes()).hexdigest()
    doc['props'][0]['sha256'] = hashlib.sha256(prop_path.read_bytes()).hexdigest()
    (base/'manifest.json').write_text(json.dumps(doc))
    family = load_native_room_family(root, 'act_01_salvage_yard', (640,288))
    assert family is not None
    for i in range(3):
        direct = pygame.Surface((1,1)).convert(); direct.fill((50,60,70))
        direct.blit(world, (-392-i,-404)); direct.blit(prop, (-i,0))
        baked = pygame.Surface((1,1)).convert(); baked.fill((50,60,70))
        baked.blit(family.world, (-392-i,-404))
        # Pillow and SDL round integer alpha differently by at most one channel.
        assert all(abs(a-b) <= 1 for a,b in zip(direct.get_at((0,0))[:3], baked.get_at((0,0))[:3]))


def test_arena_native_loader_reentry_and_full_fallback(tmp_path, display, monkeypatch):
    from video_game.tools.build_room_family import build_family as build_room_family
    source_root = tmp_path/'source'; source_root.mkdir()
    source, doc = _make_v2_family(source_root, 'ohio_arena_v1')
    root = tmp_path/'assets'; shutil.copytree(config.ASSETS_DIR,root,ignore=shutil.ignore_patterns('ohio_arena_v1'))
    build_room_family('ohio_arena_v1',assets_dir=root,archive_dir=tmp_path/'archive',
                      far=source/doc['layers'][0]['file'],world=source/doc['layers'][1]['file'],props=[],promote=True)
    game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp_path/'save'),settings_store=SettingsStore(tmp_path/'save'))
    try:
        game.assets=AssetCache(root); assert game.start_new_game()[0]
        game.change_state(config.STATE_BOSS_BOUNTY); scene=game.current_scene
        assert scene.native_room is not None
        with monkeypatch.context() as patch:
            patch.setattr(Path,'open',lambda *a,**kw: pytest.fail('frame asset read'))
            patch.setattr(pygame.image,'load',lambda *a,**kw: pytest.fail('frame image load'))
            game.render()
        game.change_state(config.STATE_BUNKER_HUB)
        world=root/'environments/ohio_arena_v1/world_1280x576.png';old=world.read_bytes();world.write_bytes(old+b'bad')
        game.change_state(config.STATE_BOSS_BOUNTY); assert game.current_scene.native_room is None
        game.render()
        game.change_state(config.STATE_BUNKER_HUB);world.write_bytes(old)
        game.change_state(config.STATE_BOSS_BOUNTY);assert game.current_scene.native_room is not None
    finally:game.close()
