"""PURPOSE: Verify planet threat source integrity and safe additive promotion.
CALLED BY: pytest tests/test_planet_threat_assets.py.
HOW TO MODIFY: Preserve strict sprite bounds, manifests, lock and rollback checks.
"""
import hashlib
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw
import pygame
import pytest

from video_game.engine import asset_transactions
from video_game.engine.planet_threat_assets import (FAMILY_ROOT, THREAT_IDS, WORLD_THREAT_IDS,
                                                      load_planet_threat)
from tools import build_planet_threat


@pytest.fixture
def display(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    pygame.display.init(); pygame.display.set_mode((1, 1))
    yield
    pygame.display.quit()


@pytest.fixture
def sources(tmp_path):
    root = tmp_path / 'assets'; root.mkdir()
    source = tmp_path / 'body.png'
    image = Image.new('RGBA', (96, 72), (0, 0, 0, 0))
    ImageDraw.Draw(image).rectangle((12, 12, 83, 63), fill=(220, 190, 140, 253))
    image.save(source)
    return root, source


def test_allowlist_is_exact_and_promotion_is_manifest_last(sources, display, monkeypatch):
    root, source = sources
    assert len(THREAT_IDS) == len(WORLD_THREAT_IDS) == 11
    seen=[]; original=build_planet_threat.promote_group
    def observe(root, stage, archive, group, paths):
        seen.extend(paths); assert all((stage / p).is_file() for p in paths)
        return original(root, stage, archive, group, paths)
    monkeypatch.setattr(build_planet_threat, 'promote_group', observe)
    result=build_planet_threat.build('carrier_wraith', source, {'source':'test'}, assets_dir=root, promote=True)
    family=FAMILY_ROOT/'carrier_wraith'
    assert seen == [family/'body.png', family/'manifest.json']
    assert (root/family/'body.png').read_bytes() == source.read_bytes()
    assert result['manifest']['image']['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    image,bounds,pivot=load_planet_threat(root,'carrier_wraith')
    assert image.get_size()==(96,72) and bounds==(12,12,84,64) and pivot==(48,64)
    assert image.get_at((15,15)).a==253 and image.get_at((0,0)).a==0
    with pytest.raises(FileExistsError):
        build_planet_threat.build('carrier_wraith',source,{'source':'test'},assets_dir=root,promote=True)
    with pytest.raises(ValueError, match='Unknown'):
        build_planet_threat.build('../carrier_wraith',source,{'source':'test'},assets_dir=root,promote=True)


@pytest.mark.parametrize('mutation',['schema','kind','id','pivot','bounds','name','hash','extra','provenance'])
def test_loader_rejects_bad_manifest(sources, display, mutation):
    root,source=sources
    result=build_planet_threat.build('carrier_wraith',source,{'source':'test'},assets_dir=root,promote=True)
    manifest=result['manifest']; directory=root/FAMILY_ROOT/'carrier_wraith'
    if mutation=='schema':manifest['schema_version']=True
    elif mutation=='kind':manifest['kind']='other'
    elif mutation=='id':manifest['art_id']='shard_clipper'
    elif mutation=='pivot':manifest['pivot']=[48,63]
    elif mutation=='bounds':manifest['image']['dimensions']=[95,72]
    elif mutation=='name':manifest['image']['file']='../body.png'
    elif mutation=='hash':manifest['image']['sha256']='0'*64
    elif mutation=='extra':manifest['other']=True
    else:manifest['provenance']={}
    (directory/'manifest.json').write_text(json.dumps(manifest))
    assert load_planet_threat(root,'carrier_wraith') is None


@pytest.mark.parametrize('mode,size,box,opacity',[
    ('RGB',(96,72),(12,12,83,63),255), ('RGBA',(95,72),(12,12,83,63),255),
    ('RGBA',(96,72),(5,12,83,63),255), ('RGBA',(96,72),(12,7,83,63),255),
    ('RGBA',(96,72),(12,12,90,63),255), ('RGBA',(96,72),(12,12,83,64),255),
    ('RGBA',(96,72),(12,12,83,63),100), ('RGBA',(96,72),None,0),
])
def test_invalid_image_rejected_before_promotion(sources,mode,size,box,opacity):
    root,source=sources
    image=Image.new(mode,size,(0,0,0) if mode=='RGB' else (0,0,0,0))
    if box:ImageDraw.Draw(image).rectangle(box,fill=(220,180,140) if mode=='RGB' else (220,180,140,opacity))
    image.save(source)
    with pytest.raises(ValueError):
        build_planet_threat.build('carrier_wraith',source,{'source':'test'},assets_dir=root,promote=True)
    assert not (root/FAMILY_ROOT/'carrier_wraith').exists()


def test_missing_corruption_symlink_pending_and_lock(sources,display):
    root,source=sources
    assert load_planet_threat(root,'carrier_wraith') is None
    build_planet_threat.build('carrier_wraith',source,{'source':'test'},assets_dir=root,promote=True)
    path=root/FAMILY_ROOT/'carrier_wraith/body.png';path.write_bytes(b'bad')
    assert load_planet_threat(root,'carrier_wraith') is None
    path.unlink();path.symlink_to(source)
    assert load_planet_threat(root,'carrier_wraith') is None
    path.unlink();path.write_bytes(source.read_bytes())
    journal=root.parent/'.assets-asset-build-pending.json'
    journal.write_text(json.dumps({'asset_root':str(root),'archive':str(root.parent/'trash'),'files':[]}))
    assert load_planet_threat(root,'carrier_wraith') is None
    with pytest.raises(RuntimeError,match='Pending'):
        build_planet_threat.build('shard_clipper',source,{'source':'test'},assets_dir=root,promote=True)
    journal.unlink()
    if asset_transactions.fcntl is None:pytest.skip('fcntl unavailable')
    fd=os.open(root,os.O_RDONLY)
    try:
        asset_transactions.fcntl.flock(fd,asset_transactions.fcntl.LOCK_EX|asset_transactions.fcntl.LOCK_NB)
        with pytest.raises(RuntimeError,match='Another asset build'):
            build_planet_threat.build('shard_clipper',source,{'source':'test'},assets_dir=root,promote=True)
    finally:os.close(fd)


def test_injected_promotion_failure_rolls_back(sources,monkeypatch):
    root,source=sources;family=FAMILY_ROOT/'carrier_wraith';original=asset_transactions.os.replace
    def fail(src,dst):
        if Path(dst)==root/family/'manifest.json':raise OSError('injected failure')
        return original(src,dst)
    monkeypatch.setattr(asset_transactions.os,'replace',fail)
    with pytest.raises(OSError,match='injected'):
        build_planet_threat.build('carrier_wraith',source,{'source':'test'},assets_dir=root,promote=True)
    assert not (root/family/'body.png').exists() and not (root/family/'manifest.json').exists()
    assert not (root.parent/'.assets-asset-build-pending.json').exists()
