"""PURPOSE: Verify campaign scenery loading, staging, views and pause behavior.
CALLED BY: pytest tests/test_campaign_scenery.py.
HOW TO MODIFY: Preserve safety, camera, crop and corruption assertions.
"""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from PIL import Image
import pygame
import pytest

from video_game.engine.campaign_scenery import (
    ALIEN_BACKGROUND_IDS, BACKGROUND_IDS, BOSS_IDS, GUARDIAN_IDS,
    CampaignScenery, load_campaign_background, load_campaign_boss,
    load_profile_blockout, _load_existing_guardian,
)
from video_game.engine.config import ASSETS_DIR
from video_game.engine.world import Camera
from tools.build_campaign_art import build


@pytest.fixture
def display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    pygame.display.init(); pygame.display.set_mode((1, 1))
    yield
    pygame.display.quit()


def test_background_builder_validation_and_loader_integrity(tmp_path, display):
    root = tmp_path / 'assets'; root.mkdir()
    source = tmp_path / 'source.png'
    Image.new('RGB', (1920, 540), (30, 42, 53)).save(source)
    result = build('background', 'neo_denver_v1', source, {'source': 'test'}, assets_dir=root)
    assert result['status'] == 'validated'
    family = root / 'environments/campaign_worlds/neo_denver_v1'; family.mkdir(parents=True)
    (family / 'background.png').write_bytes(source.read_bytes())
    (family / 'manifest.json').write_text(json.dumps(result['manifest']))
    assert load_campaign_background(root, 'neo_denver_v1') is not None
    scene = CampaignScenery(root, SimpleNamespace(act_id='act_02', room_id='act_02_street', width_px=3840))
    class CRT:
        canvas = pygame.Surface((480, 270))
        def composite_opaque_background(self, surface, **kwargs):
            self.pixel = surface.get_at((0, 0))
    crt = CRT(); camera = Camera(); camera.set_world_bounds(3840, 288)
    camera.x = 3360
    assert scene.render_background(crt, camera) and crt.pixel[:3] == (30, 42, 53)
    scene.update(0.1); old = scene.elapsed; scene.update(0.1, paused=True); assert scene.elapsed == old
    (family / 'background.png').write_bytes(b'corrupted')
    assert load_campaign_background(root, 'neo_denver_v1') is None
    with pytest.raises(FileExistsError):
        build('background', 'neo_denver_v1', source, {'source':'test'}, assets_dir=root)


def test_boss_loader_rejects_corruption_and_unknown_ids(tmp_path, display):
    root = tmp_path / 'assets'; root.mkdir()
    source = tmp_path / 'body.png'
    image = Image.new('RGBA', (256, 192), (0, 0, 0, 0))
    image.paste((120, 20, 40, 255), (50, 30, 200, 180)); image.save(source)
    result = build('boss', 'synchronicity', source, {'source':'test'}, assets_dir=root)
    family = root / 'sprites/bosses/campaign/synchronicity'; family.mkdir(parents=True)
    (family / 'body.png').write_bytes(source.read_bytes())
    (family / 'manifest.json').write_text(json.dumps(result['manifest']))
    assert load_campaign_boss(root, 'synchronicity').get_size() == (256, 192)
    assert load_campaign_boss(root, '../synchronicity') is None
    (family / 'body.png').write_bytes(b'bad')
    assert load_campaign_boss(root, 'synchronicity') is None


def test_builder_rejects_pending_journal_symlink_and_non_rgba(tmp_path, display):
    root = tmp_path / 'assets'; root.mkdir()
    source = tmp_path / 'background.png'
    Image.new('RGB', (1920, 540), (1, 2, 3)).save(source)
    journal = tmp_path / '.assets-asset-build-pending.json'
    journal.write_text(json.dumps({'asset_root': str(root.resolve()), 'archive': str(tmp_path / 'archive'), 'files': []}))
    with pytest.raises(RuntimeError, match='Pending'):
        build('background', 'neo_denver_v1', source, {'source':'test'}, assets_dir=root)
    assert load_campaign_background(root, 'neo_denver_v1') is None
    journal.unlink()
    family_parent = root / 'environments/campaign_worlds'; family_parent.mkdir(parents=True)
    outside = tmp_path / 'elsewhere'; outside.mkdir()
    (family_parent / 'neo_denver_v1').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='[Ss]ymlink'):
        build('background', 'neo_denver_v1', source, {'source':'test'}, assets_dir=root)
    assert load_campaign_background(root, 'neo_denver_v1') is None
    wrong = tmp_path / 'opaque_boss.png'
    Image.new('RGB', (256, 192), (3, 4, 5)).save(wrong)
    with pytest.raises(ValueError, match='RGBA'):
        build('boss', 'synchronicity', wrong, {'source':'test'}, assets_dir=root)


def test_boss_loader_rejects_non_rgba_with_valid_hash(tmp_path, display):
    root = tmp_path / 'assets'; root.mkdir()
    family = root / 'sprites/bosses/campaign/synchronicity'; family.mkdir(parents=True)
    body = family / 'body.png'; Image.new('RGB', (256, 192), (1, 2, 3)).save(body)
    manifest = {'schema_version': 1, 'kind': 'campaign_boss', 'boss_id': 'synchronicity',
                'image': {'file': 'body.png', 'dimensions': [256, 192],
                          'sha256': hashlib.sha256(body.read_bytes()).hexdigest()},
                'provenance': {'source': 'test'}}
    (family / 'manifest.json').write_text(json.dumps(manifest))
    assert load_campaign_boss(root, 'synchronicity') is None


def test_background_ground_tracks_camera_y_without_scaling(tmp_path, display):
    root = tmp_path / 'assets'; root.mkdir()
    source = tmp_path / 'street.png'
    image = Image.new('RGB', (1920, 540), (4, 5, 6))
    image.paste((255, 0, 0), (0, 480, 1920, 481)); image.save(source)
    manifest = build('background', 'neo_denver_v1', source, {'source':'test'}, assets_dir=root)['manifest']
    family = root / 'environments/campaign_worlds/neo_denver_v1'; family.mkdir(parents=True)
    (family / 'background.png').write_bytes(source.read_bytes())
    (family / 'manifest.json').write_text(json.dumps(manifest))
    scene = CampaignScenery(root, SimpleNamespace(act_id='act_02', room_id='act_02_street', width_px=3840))
    class CRT:
        def composite_opaque_background(self, surface, **kwargs):
            self.surface = surface.copy()
    crt = CRT(); camera = Camera(); camera.set_world_bounds(3840, 288)
    camera.y = 18
    assert scene.render_background(crt, camera)
    assert crt.surface.get_at((0, 444))[:3] == (255, 0, 0)
    assert crt.surface.get_at((0, 443))[:3] == (4, 5, 6)
    assert crt.surface.get_at((0, 539))[:3] == (7, 11, 16)
    camera.y = 0
    assert scene.render_background(crt, camera)
    assert crt.surface.get_at((0, 480))[:3] == (255, 0, 0)


def test_room_art_view_uses_authored_source_slice_without_scaling(tmp_path, display):
    root = tmp_path / 'assets'; root.mkdir()
    source = tmp_path / 'street.png'
    image = Image.new('RGB', (1920, 540), (4, 5, 6))
    image.paste((200, 10, 20), (320, 0, 321, 540))
    image.paste((30, 210, 40), (640, 0, 641, 540))
    image.save(source)
    manifest = build('background', 'area_51_hangar_v1', source, {'source':'test'}, assets_dir=root)['manifest']
    family = root / 'environments/campaign_worlds/area_51_hangar_v1'; family.mkdir(parents=True)
    (family / 'background.png').write_bytes(source.read_bytes())
    (family / 'manifest.json').write_text(json.dumps(manifest))
    room = SimpleNamespace(act_id='act_03', room_id='act_03_s4_hangar', width_px=3840)
    scene = CampaignScenery(root, room, {'art_id':'area_51_hangar_v1', 'art_view':[1/3, 2/3]})
    class CRT:
        def composite_opaque_background(self, surface, **kwargs):
            self.surface = surface.copy()
    crt = CRT(); camera = Camera(); camera.set_world_bounds(3840, 288)
    assert scene.render_background(crt, camera)
    assert crt.surface.get_at((0, 0))[:3] == (200, 10, 20)
    camera.x = 3360
    assert scene.render_background(crt, camera)
    assert crt.surface.get_at((0, 0))[:3] == (30, 210, 40)
    assert load_campaign_background(root, 'unapproved_family') is None
    invalid = CampaignScenery(root, room, {'art_id':'area_51_hangar_v1', 'art_view':[-2, 6]})
    assert invalid.art_view == (0.0, 1.0)


def test_short_arena_pan_is_bounded_and_static_view_is_supported(display):
    room = SimpleNamespace(act_id='act_02', room_id='act_02_arena', width_px=640)
    class CRT:
        def composite_opaque_background(self, surface, **kwargs):
            self.pixel = surface.get_at((0, 0))
    scene = CampaignScenery(None, room, {'art_view':[0, 1]})
    scene.background = pygame.Surface((1920, 540)).convert()
    for x in range(1920):
        pygame.draw.line(scene.background, (x % 256, 0, 0), (x, 0), (x, 539))
    scene._background_view = pygame.Surface((960, 540)).convert()
    camera = Camera(); camera.set_world_bounds(640, 288); crt = CRT()
    assert scene.render_background(crt, camera); first = crt.pixel.r
    camera.x = 40
    assert scene.render_background(crt, camera); assert 0 <= crt.pixel.r - first <= 8
    scene.art_view = (0.5, 0.5)
    camera.x = 0; scene.render_background(crt, camera); first = crt.pixel
    camera.x = 160; scene.render_background(crt, camera); assert crt.pixel == first
    static = CampaignScenery(None, room, {'art_view':[0.5, 0.5]})
    assert static.art_view == (0.5, 0.5)


def test_earth_panorama_continues_at_the_next_area_boundary(display):
    class CRT:
        def composite_opaque_background(self, surface, **kwargs):
            self.pixels = pygame.image.tobytes(surface, 'RGB')
    background = pygame.Surface((1920, 540)).convert()
    for x in range(1920):
        pygame.draw.line(background, (x % 256, x // 256, 0), (x, 0), (x, 539))
    crt = CRT()
    camera = Camera()
    camera.set_world_bounds(960, 288)
    views = []
    for name, art_view, x in [('street', (0, 1/3), 480), ('rooftops', (1/3, 2/3), 0)]:
        room = SimpleNamespace(act_id='act_02', room_id='act_02_' + name, width_px=960)
        scene = CampaignScenery(None, room, {'art_view': art_view})
        scene.background = background
        scene._background_view = pygame.Surface((960, 540)).convert()
        camera.x = x
        assert scene.render_background(crt, camera)
        views.append(crt.pixels)
    assert views[0] == views[1]


def test_alien_world_allowlists_and_explicit_metadata(tmp_path, display):
    assert len(BACKGROUND_IDS) == 18 and len(ALIEN_BACKGROUND_IDS) == 11
    assert len(GUARDIAN_IDS) == 11 and len(BOSS_IDS) == 17
    assert 'realm_fasr_001_v1' in ALIEN_BACKGROUND_IDS
    assert 'realm_fasr_scan_h_v1' in ALIEN_BACKGROUND_IDS
    assert 'guardian_fasr_scan_h' in GUARDIAN_IDS and {'earth_core_ai', 'portal_warden'} <= BOSS_IDS
    assert 'realm_fasr_011_v1' not in BACKGROUND_IDS and 'guardian_fasr_011' not in BOSS_IDS
    root = tmp_path / 'assets'; root.mkdir()
    source = tmp_path / 'realm.png'
    Image.new('RGB', (1920, 540), (12, 25, 35)).save(source)
    manifest = build('background', 'realm_fasr_001_v1', source, {'source':'test'}, assets_dir=root)['manifest']
    family = root / 'environments/campaign_worlds/realm_fasr_001_v1'; family.mkdir(parents=True)
    (family / 'background.png').write_bytes(source.read_bytes())
    (family / 'manifest.json').write_text(json.dumps(manifest))
    room = SimpleNamespace(act_id='act_05', room_id='alien_001_field', width_px=3840)
    scene = CampaignScenery(root, room, {'art_id':'realm_fasr_001_v1', 'art_view':[0, .5]})
    assert scene.background is not None and scene.art_view == (0, .5)
    assert scene.vehicle is None and scene.person is None
    assert CampaignScenery(root, room, {}).background is None
    assert CampaignScenery(root, room, {'art_id':'gobekli_tepe_v1'}).background is None
    assert CampaignScenery(root, room, {'art_id':'realm_fasr_011_v1'}).background is None
    with pytest.raises(ValueError, match='Unknown'):
        build('background', 'realm_fasr_011_v1', source, {'source':'test'}, assets_dir=root)


def test_guardian_body_uses_strict_manifest_and_corruption_fallback(tmp_path, display):
    root = tmp_path / 'assets'; root.mkdir()
    source = tmp_path / 'guardian.png'
    image = Image.new('RGBA', (256, 192), (0, 0, 0, 0))
    image.paste((70, 100, 120, 255), (50, 20, 210, 175)); image.save(source)
    manifest = build('boss', 'guardian_fasr_scan_h', source, {'source':'test'}, assets_dir=root)['manifest']
    family = root / 'sprites/bosses/campaign/guardian_fasr_scan_h'; family.mkdir(parents=True)
    (family / 'body.png').write_bytes(source.read_bytes())
    (family / 'manifest.json').write_text(json.dumps(manifest))
    assert load_campaign_boss(root, 'guardian_fasr_scan_h') is not None
    assert load_campaign_boss(root, 'guardian_fasr_011') is None
    (family / 'body.png').write_bytes(b'corrupted')
    assert load_campaign_boss(root, 'guardian_fasr_scan_h') is None
    with pytest.raises(ValueError, match='Unknown'):
        build('boss', 'guardian_fasr_011', source, {'source':'test'}, assets_dir=root)


def test_existing_profile_and_guardian_blockouts_are_distinct_and_verified(display):
    background_hashes = set()
    guardian_hashes = set()
    for art_id in sorted(ALIEN_BACKGROUND_IDS):
        image = load_profile_blockout(ASSETS_DIR, art_id)
        assert image is not None and image.get_size() == (1920, 540)
        background_hashes.add(hashlib.sha256(pygame.image.tobytes(image, 'RGBA')).hexdigest())
    for guardian in sorted(GUARDIAN_IDS):
        image = _load_existing_guardian(ASSETS_DIR, guardian)
        assert image is not None and image.get_size() == (256, 192)
        guardian_hashes.add(hashlib.sha256(pygame.image.tobytes(image, 'RGBA')).hexdigest())
    assert len(background_hashes) == 11
    assert len(guardian_hashes) >= 9  # Nine existing authored enemy silhouettes are reused.


def test_profile_blockout_is_per_realm_and_rejects_tampering(tmp_path, display):
    import shutil
    root = tmp_path / 'assets'; directory = root / 'civilizations'; directory.mkdir(parents=True)
    shutil.copy2(ASSETS_DIR / 'civilizations/manifest.json', directory / 'manifest.json')
    shutil.copy2(ASSETS_DIR / 'civilizations/fasr-002_env.png', directory / 'fasr-002_env.png')
    room = SimpleNamespace(act_id='act_05', room_id='alien_002_field', width_px=3840)
    scene = CampaignScenery(root, room, {'art_id':'realm_fasr_002_v1'})
    assert scene.background is not None
    assert scene.background_source == {'kind':'profile_blockout', 'art_id':'realm_fasr_002_v1'}
    assert scene.person is None and scene.vehicle is None
    (directory / 'fasr-002_env.png').write_bytes(b'corrupted')
    assert load_profile_blockout(root, 'realm_fasr_002_v1') is None
    assert CampaignScenery(root, room, {'art_id':'realm_fasr_002_v1'}).background is None


@pytest.mark.parametrize('art_id', ['area_51_hangar_v1'])
def test_interior_has_staff_but_no_driving_vehicle(display, art_id):
    room = SimpleNamespace(act_id='act_03', room_id='act_03_test', width_px=3840)
    interior = CampaignScenery(ASSETS_DIR, room, {'art_id':art_id})
    exterior = CampaignScenery(ASSETS_DIR, room, {'art_id':'area_51_v1'})
    assert interior.background is not None and interior.person is not None
    assert interior.vehicle is None
    assert exterior.background is not None and exterior.person is not None and exterior.vehicle is not None


def test_activity_preserves_source_opacity_scale_and_ground_anchor(display, monkeypatch):
    room = SimpleNamespace(act_id='act_02', room_id='act_02_blackout_street', width_px=3840)
    scene = CampaignScenery(ASSETS_DIR, room, {'art_id':'neo_denver_v1'})
    originals = (
        ('vehicle', 'environments/ohio_salvage_v1/wagon_168x76_rgba.png', (72, 33)),
        ('person', 'sprites/mateo/navy_chore/idle_1.png', (21, 28)),
    )
    for attr, path, size in originals:
        image = getattr(scene, attr)
        source = pygame.image.load(str(ASSETS_DIR / path)).convert_alpha()
        expected = pygame.transform.scale(source, size)
        assert image.get_size() == size and image.get_alpha() == 255
        assert pygame.image.tobytes(image, 'RGBA') == pygame.image.tobytes(expected, 'RGBA')
        assert 0 < pygame.mask.from_surface(image, 254).count() < size[0] * size[1]
        visible = pygame.mask.from_surface(image, 0).count()
        assert pygame.mask.from_surface(image, 239).count() / visible > 0.9
        assert image.get_bounding_rect().bottom == size[1]
    class Recorder:
        def __init__(self): self.calls = []
        def blit(self, image, dest): self.calls.append((image, dest))
    canvas = Recorder(); crt = SimpleNamespace(canvas=canvas)
    camera = Camera(); camera.set_world_bounds(3840, 288); camera.x = 60; camera.y = 18
    ohio = SimpleNamespace(act_id='act_01', room_id='act_01_ohio_campus', width_px=7680)
    ohio_scene = CampaignScenery(ASSETS_DIR, ohio)
    assert ohio_scene.vehicle is None and ohio_scene.person is not None
    monkeypatch.setattr(pygame.image, 'load', lambda *_a, **_kw: pytest.fail('render loaded an image'))
    scene.render_activity(crt, camera)
    assert len(canvas.calls) == 2
    for image, (_, y) in canvas.calls:
        assert y + image.get_bounding_rect().bottom == 240 - camera.y


@pytest.mark.parametrize('room_id,art_id', [
    ('act_05_pillar_approach', 'gobekli_tepe_v1'),
    ('act_05_buried_archive', 'gobekli_archive_v1'),
    ('act_05_crust_waveguide', 'gobekli_archive_v1'),
    ('act_05_core_prime_arena', 'gobekli_tepe_v1'),
    ('earth_finale_core_prime_arena', 'gobekli_tepe_v1'),
    ('act_05_pillar_approach', None),
    # A metadata override must not bypass the act's site policy.
    ('act_05_pillar_approach', 'neo_denver_v1'),
])
def test_gobekli_has_no_reused_modern_activity(display, room_id, art_id):
    room = SimpleNamespace(act_id='act_05', room_id=room_id, width_px=3840)
    meta = {'art_id': art_id} if art_id else {}
    scene = CampaignScenery(ASSETS_DIR, room, meta)
    assert scene.vehicle is None and scene.person is None
    if art_id == 'gobekli_archive_v1':
        assert scene.background is not None  # Preserve the installed archive backdrop.
    if art_id in ('gobekli_tepe_v1', None) and scene.background is not None:
        assert scene.background_source == {'kind':'native', 'art_id':'gobekli_tepe_v2'}
    class NoBlits:
        def blit(self, *_args): pytest.fail('site activity must not render')
    scene.render_activity(SimpleNamespace(canvas=NoBlits()), Camera())


@pytest.mark.parametrize('act_id,room_id,art_id', [
    ('act_02', 'act_02_blackout_street', 'neo_denver_v1'),
    ('act_03', 'act_03_desert_perimeter', 'area_51_v1'),
    ('act_04', 'act_04_array_approach', 'vla_rift_v1'),
])
def test_modern_outdoor_activity_remains_available(display, act_id, room_id, art_id):
    room = SimpleNamespace(act_id=act_id, room_id=room_id, width_px=3840)
    scene = CampaignScenery(ASSETS_DIR, room, {'art_id':art_id})
    assert scene.vehicle is not None and scene.person is not None


@pytest.mark.parametrize('art_id', ['gobekli_tepe_v1', 'gobekli_archive_v1'])
def test_archaeological_art_override_never_adds_modern_activity(display, art_id):
    room = SimpleNamespace(act_id='act_03', room_id='act_03_test', width_px=3840)
    scene = CampaignScenery(ASSETS_DIR, room, {'art_id':art_id})
    assert scene.background is not None
    assert scene.vehicle is None and scene.person is None


@pytest.mark.parametrize('act_id,art_id', [
    ('act_03', 'unrecognized_scene_v1'),
    ('act_03', []),
    ('act_99', 'area_51_v1'),
])
def test_unrecognized_setting_does_not_spawn_reused_activity(display, act_id, art_id):
    room = SimpleNamespace(act_id=act_id, room_id='unrecognized', width_px=3840)
    scene = CampaignScenery(ASSETS_DIR, room, {'art_id':art_id})
    assert scene.vehicle is None and scene.person is None


def test_act_v_uses_only_verified_car_free_v2_not_v1_fallback(tmp_path, display):
    root=tmp_path/'assets';root.mkdir()
    old=tmp_path/'old.png';new=tmp_path/'new.png'
    Image.new('RGB',(1920,540),(51,20,12)).save(old)
    Image.new('RGB',(1920,540),(17,32,49)).save(new)
    build('background','gobekli_tepe_v1',old,{'source':'fixture'},assets_dir=root,promote=True)
    room=SimpleNamespace(act_id='act_05',room_id='act_05_pillar_approach',width_px=3840)
    scene=CampaignScenery(root,room,{'art_id':'gobekli_tepe_v1'})
    assert scene.background is None  # Never silently expose the old baked vehicle.
    assert scene.vehicle is None and scene.person is None
    build('background','gobekli_tepe_v2',new,{'source':'fixture'},assets_dir=root,promote=True)
    scene=CampaignScenery(root,room,{'art_id':'gobekli_tepe_v1'})
    assert scene.background is not None
    assert scene.background_source=={'kind':'native','art_id':'gobekli_tepe_v2'}
    assert scene.background.get_at((0,0))[:3]==(17,32,49)
    assert scene.vehicle is None and scene.person is None
    (root/'environments/campaign_worlds/gobekli_tepe_v2/background.png').write_bytes(b'bad')
    scene=CampaignScenery(root,room,{'art_id':'gobekli_tepe_v1'})
    assert scene.background is None  # Corrupt v2 must not expose v1.
    assert load_campaign_background(root,'gobekli_tepe_v1') is not None


def test_guardian_loader_rejects_empty_and_fully_opaque_even_with_valid_hash(tmp_path, display):
    import shutil
    root = tmp_path / 'assets'; root.mkdir()
    image = Image.new('RGBA', (256, 192), (0, 0, 0, 0))
    image.paste((150, 100, 70, 255), (40, 20, 200, 180))
    source = tmp_path / 'valid.png'; image.save(source)
    result = build('boss', 'guardian_fasr_003', source, {'source':'fixture'}, assets_dir=root, promote=True)
    directory = root / 'sprites/bosses/campaign/guardian_fasr_003'
    assert load_campaign_boss(root, 'guardian_fasr_003', allow_fallback=False) is not None
    # Preserve the existing manifest-backed fallback so allow_fallback is verified too.
    enemy_root = root / 'sprites/enemies'
    (enemy_root / 'chrysalis_splicer').mkdir(parents=True)
    shutil.copy2(ASSETS_DIR / 'sprites/enemies/manifest.json', enemy_root / 'manifest.json')
    shutil.copy2(ASSETS_DIR / 'sprites/enemies/chrysalis_splicer/patrol_1.png',
                 enemy_root / 'chrysalis_splicer/patrol_1.png')
    expected_fallback = _load_existing_guardian(root, 'guardian_fasr_003')
    assert expected_fallback is not None
    for alpha in (0, 255):
        invalid = Image.new('RGBA', (256,192), (90,120,150,alpha))
        invalid.save(directory / 'body.png')
        manifest = dict(result['manifest'])
        manifest['image'] = dict(manifest['image'])
        manifest['image']['sha256'] = hashlib.sha256((directory / 'body.png').read_bytes()).hexdigest()
        (directory / 'manifest.json').write_text(json.dumps(manifest))
        assert load_campaign_boss(root, 'guardian_fasr_003', allow_fallback=False) is None
        fallback = load_campaign_boss(root, 'guardian_fasr_003', allow_fallback=True)
        assert fallback is not None
        assert pygame.image.tobytes(fallback, 'RGBA') == pygame.image.tobytes(expected_fallback, 'RGBA')
