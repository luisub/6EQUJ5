"""Register four-pose insect masters to existing enemy collision geometry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid

from PIL import Image

from video_game.engine.asset_transactions import fcntl, promote_group
from video_game.engine.config import ASSETS_DIR

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'src/art/source/enemies/cyber_insects'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output):
    output.mkdir(parents=True, exist_ok=False)
    recipe = json.loads((SOURCE / 'recipe.json').read_text())
    manifest = json.loads((ASSETS_DIR / 'sprites/enemies/manifest.json').read_text())
    families = {}
    for row in recipe['families']:
        source = SOURCE / row['key'] / 'master.png'
        image = Image.open(source).convert('RGBA')
        if image.width % 4:
            raise ValueError('Expected four equal horizontal cells')
        width = image.width // 4
        cells = [image.crop((i * width, 0, (i + 1) * width, image.height)) for i in range(4)]
        boxes = [c.getchannel('A').point(lambda a: 255 if a >= 32 else 0).getbbox() for c in cells]
        if not all(boxes):
            raise ValueError('Every motion pose must be visible')
        box = (min(b[0] for b in boxes), min(b[1] for b in boxes),
               max(b[2] for b in boxes), max(b[3] for b in boxes))
        families[row['key']] = ([c.crop(box) for c in cells], box, source)
    for name, role in recipe['roles'].items():
        entry = manifest['enemies'][name]
        width, height = entry['width'] * 2, entry['height'] * 2
        cells, box, source = families[role['family']]
        scale = min((width - 2) / cells[0].width, (height - 1) / cells[0].height)
        size = (round(cells[0].width * scale), round(cells[0].height * scale))
        top = (height - size[1]) // 2 if role['motion'] == 'flight' else height - 1 - size[1]
        paths, hashes = [], {}
        for i, cell in enumerate(cells, 1):
            result = Image.new('RGBA', (width, height))
            result.paste(cell.resize(size, Image.Resampling.NEAREST), ((width - size[0]) // 2, top))
            relative = Path('sprites/enemies') / name / f'patrol_{i}.png'
            path = output / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            result.save(path)
            paths.append(str(relative)); hashes[str(relative)] = digest(path)
        for state, clip in entry['animations'].items():
            clip['frames'] = paths if state == 'patrol' else [paths[0]]
        entry.update(name=role['name'], density=2, source_facing='left', motion=role['motion'],
                     stride_length=24, frame_hashes=hashes,
                     provenance={'family':role['family'], 'source':str(source.relative_to(ROOT)),
                                 'source_sha256':digest(source), 'shared_crop':list(box),
                                 'frame_size':[width,height], 'registered_size':list(size),
                                 'recipe':'src/art/source/enemies/cyber_insects/recipe.json',
                                 'builder':'tools/build_cyber_insects.py'})
    (output / 'sprites/enemies/manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return sorted(p.relative_to(output) for p in output.rglob('*') if p.is_file())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--promote', action='store_true')
    args = parser.parse_args()
    files = build(args.output)
    if not args.promote:
        print(f'Staged {len(files)} exports in {args.output}')
        return
    archive_root = ROOT / '_trash'
    descriptor = os.open(ASSETS_DIR, os.O_RDONLY)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        archive = promote_group(ASSETS_DIR, args.output, archive_root, 'earth_cyber_insects', files)
        archived = [(p, Path('src/assets') / p.relative_to(archive / 'video_game/assets'))
                    for p in (archive / 'video_game/assets').rglob('*') if p.is_file()]
        # Retired poses are no longer referenced by the promoted manifest.
        unused = archive_root / ('2026-11-14_cyber_insects_' + uuid.uuid4().hex[:8])
        for name in json.loads((SOURCE / 'recipe.json').read_text())['roles']:
            for old in (ASSETS_DIR / 'sprites/enemies' / name).glob('*.png'):
                relative = old.relative_to(ASSETS_DIR)
                if relative not in files:
                    target = unused / 'src/assets' / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(old, target)
                    if digest(target) != digest(old):
                        raise ValueError(f'Archive verification failed: {old}')
                    old.unlink()
                    archived.append((target, Path('src/assets') / relative))
        index_path = ROOT / 'docs/maintenance/archive-manifest.json'
        index = json.loads(index_path.read_text())
        for path, original in archived:
            index.append({'original_path':str(original), 'archive_path':str(path.relative_to(ROOT)),
                          'sha256':digest(path), 'reason':'Replaced block robot poses with native cyber-insect motion.',
                          'restoration':'Verify hash and preserve current files, then restore the old family and matching manifest together.'})
        index_path.write_text(json.dumps(index, indent=2)+'\n')
        with (archive_root/'TRASH_LOG.md').open('a') as log:
            log.write(f'\n2026-11-14 — Earth cyber-insects: {len(archived)} former exports preserved. Full paths, hashes and restoration instructions are in docs/maintenance/archive-manifest.json.\n')
    finally:
        os.close(descriptor)
    print(f'Promoted {len(files)} exports; archived {len(archived)} former files.')


if __name__ == '__main__':
    main()
