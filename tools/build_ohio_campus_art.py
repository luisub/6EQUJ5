"""MODULE: tools/build_ohio_campus_art.py
PURPOSE: Rebuild and safely promote the reviewed Ohio campus art family.
CALLED BY: python -m tools.build_ohio_campus_art [--promote].
HOW TO MODIFY: Preserve approved master hashes, transforms, output hash and group transaction.
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from PIL import Image
from video_game.engine.config import ASSETS_DIR
from tools.build_room_family import build_family

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'art/source/visual_upgrade/candidates/ohio_campus_extension_v01/source'
FAR_MASTER = ROOT / 'art/source/visual_upgrade/candidates/fitzsimons_campus_v01/source/fitzsimons_campus_generated_master_v02.png'
MASTERS = {
    'ohio_campus_west_staff_revision_master.png': '77531bda8c17fe06ddf7084056fa9f3c6af02f2491d044538e813a5f5b7faf04',
    'ohio_campus_east_revision_master.png': 'fc11e1775ff6cf70c9191408b32a6894a54f004de30d1ba53bace1831dfb3083',
    'ohio_campus_transition_generated_master.png': 'cebd7f16bcc3b951db8031614bde8e95d3194db25b70dfdc518bc66895bcb275',
}
FAR_MASTER_HASH = 'e303e5f71b3e2a51fa0da30ceaa57596e3b9419920a56fb2779d63accccce529'
FAR_HASH = '201353a9d2be77ad7f583e800e88baada55bdcc94702875caae3ec3b5fdc4e7a'
WORLD_HASH = '8b3f82966bbed8df0399ce7ec185f94cf7846063b7fa0adf2ceb5a65d2a0362c'


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _panel(name, expected_size, size, y, canvas_size):
    path = SOURCE / name
    if _sha(path) != MASTERS[name]:
        raise ValueError(f'Unexpected master hash: {name}')
    with Image.open(path) as original:
        if original.mode != 'RGBA' or original.size != expected_size:
            raise ValueError(f'Unexpected master format: {name}')
        image = original.resize(size, Image.Resampling.LANCZOS)
    image.putalpha(image.getchannel('A').point(lambda a: 0 if a < 16 else 255 if a >= 240 else a))
    canvas = Image.new('RGBA', canvas_size, (0, 0, 0, 0))
    canvas.paste(image, (0, y))
    return canvas


def build_world(path):
    """Apply only reviewed proportional transforms, hard join and authored overlay."""
    west = _panel('ohio_campus_west_staff_revision_master.png', (2172, 724), (1440, 480), 54, (1440, 576))
    east = _panel('ohio_campus_east_revision_master.png', (1983, 793), (1440, 576), -28, (1440, 576))
    transition = _panel('ohio_campus_transition_generated_master.png', (1122, 1402), (256, 320), 33, (256, 320))
    world = Image.new('RGBA', (2560, 576), (0, 0, 0, 0))
    world.paste(west.crop((0, 0, 1280, 576)), (0, 0))
    world.paste(east.crop((160, 0, 1440, 576)), (1280, 0))
    world.alpha_composite(transition, (1264, 160))
    world.save(path)
    if _sha(path) != WORLD_HASH:
        raise ValueError('Rebuilt world differs from reviewed fixture')


def build_far(path, master=None):
    """Rebuild the reviewed opaque far plate from the locked image master."""
    source = FAR_MASTER if master is None else Path(master)
    if _sha(source) != FAR_MASTER_HASH:
        raise ValueError('Unexpected far master hash')
    with Image.open(source) as original:
        if original.mode != 'RGB' or original.size != (1825, 862):
            raise ValueError('Unexpected far master format')
        image = original.crop((12, 12, 1812, 862)).resize((1152, 544), Image.Resampling.NEAREST)
    image.save(path)
    if _sha(path) != FAR_HASH:
        raise ValueError('Rebuilt far plate differs from reviewed fixture')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--promote', action='store_true', help='Promote the validated family transactionally')
    parser.add_argument('--assets-dir', type=Path, default=ASSETS_DIR)
    parser.add_argument('--archive-dir', type=Path)
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix='campus-build-', dir=ROOT) as temporary:
        far = Path(temporary) / 'far_1152x544.png'
        world = Path(temporary) / 'world_2560x576.png'
        build_far(far)
        build_world(world)
        result = build_family('ohio_campus_v1', assets_dir=args.assets_dir, archive_dir=args.archive_dir,
                              far=far, world=world, promote=args.promote)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
