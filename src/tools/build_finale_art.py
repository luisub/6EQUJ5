"""Register generated finale masters to runtime geometry; stage before promotion."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image

from video_game.engine.asset_transactions import fcntl, promote_group
from video_game.engine.campaign_scenery import background_directory
from video_game.engine.config import ASSETS_DIR

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'src/art/source/finale'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output):
    output.mkdir(parents=True, exist_ok=False)
    recipes = json.loads((SOURCE / 'recipe.json').read_text())['families']
    for row in recipes:
        source = SOURCE / row['key'] / 'master.png'
        image = Image.open(source).convert('RGBA')
        provenance = {'source': str(source.relative_to(ROOT)), 'source_sha256': digest(source),
                      'recipe': 'src/art/source/finale/recipe.json', 'builder': 'tools/build_finale_art.py',
                      'resampling': 'nearest', 'source_dimensions': list(image.size)}
        if row['kind'] == 'background':
            scaled = image.resize((1920, 640), Image.Resampling.NEAREST)
            top = row['crop_top']
            result = scaled.crop((0, top, 1920, top + 540)).convert('RGB')
            directory = output / background_directory(row['id'])
            filename = 'background.png'
            manifest = {'schema_version': 1, 'kind': 'campaign_world_background',
                        'art_id': row['id'], 'viewport': [480, 270], 'density': 2}
            provenance['registration'] = {'resize': [1920, 640], 'crop': [0, top, 1920, top + 540]}
        elif row['kind'] == 'boss':
            box = image.getchannel('A').point(lambda a: 255 if a >= 32 else 0).getbbox()
            body = image.crop(box)
            scale = min(228 / body.width, 180 / body.height)
            body = body.resize((round(body.width * scale), round(body.height * scale)), Image.Resampling.NEAREST)
            result = Image.new('RGBA', (256, 192))
            result.paste(body, ((256 - body.width) // 2, 189 - body.height))
            directory = output / 'sprites/bosses/campaign' / row['id']
            filename = 'body.png'
            manifest = {'schema_version': 1, 'kind': 'campaign_boss', 'boss_id': row['id']}
            provenance['registration'] = {'crop': list(box), 'size': list(body.size), 'foot_y': 189}
        else:
            if image.width % 4:
                raise ValueError('Family master must have four equal cells')
            width = image.width // 4
            cells = [image.crop((i * width, 0, (i + 1) * width, image.height)) for i in range(4)]
            boxes = [cell.getchannel('A').point(lambda a: 255 if a >= 32 else 0).getbbox() for cell in cells]
            if not all(boxes):
                raise ValueError('All family poses must be visible')
            box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
            scale = min(116 / (box[2] - box[0]), 72 / (box[3] - box[1]))
            size = (round((box[2] - box[0]) * scale), round((box[3] - box[1]) * scale))
            result = Image.new('RGBA', (512, 96))
            for i, cell in enumerate(cells):
                result.paste(cell.crop(box).resize(size, Image.Resampling.NEAREST), (i * 128 + (128 - size[0]) // 2, 90 - size[1]))
            directory = output / 'sprites/people/park_family'
            filename = 'walk.png'
            manifest = {'schema_version': 1, 'frames': 4, 'dimensions': [512, 96], 'foot_pivot': [64, 90]}
            provenance['registration'] = {'shared_crop': list(box), 'size': list(size), 'foot_y': 90}
        directory.mkdir(parents=True)
        path = directory / filename
        result.save(path)
        if row['kind'] == 'walk':
            manifest['sha256'] = digest(path)
        else:
            manifest['image'] = {'file': filename, 'dimensions': list(result.size), 'sha256': digest(path)}
        manifest['provenance'] = provenance
        (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return sorted(p.relative_to(output) for p in output.rglob('*') if p.is_file())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New staging directory')
    parser.add_argument('--promote', action='store_true', help='Archive and replace the four reviewed families')
    args = parser.parse_args()
    files = build(args.output)
    if args.promote:
        descriptor = os.open(ASSETS_DIR, os.O_RDONLY)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            archive = promote_group(ASSETS_DIR, args.output, ROOT / '_trash', 'restored_earth_finale', files)
        finally:
            os.close(descriptor)
        # Keep recoverable replacement records in the repository's sole index.
        index_path = ROOT / 'docs/maintenance/archive-manifest.json'
        index = json.loads(index_path.read_text())
        for path in (archive / 'video_game/assets').rglob('*'):
            if path.is_file():
                relative = path.relative_to(archive / 'video_game/assets')
                index.append({'original_path': str(Path('src/assets') / relative),
                              'archive_path': str(path.relative_to(ROOT)), 'sha256': digest(path),
                              'reason': 'Replaced the final Core body with an original green-code projection.',
                              'restoration': 'Verify SHA-256, preserve the current file, then copy to original_path with its matching manifest.'})
        index_path.write_text(json.dumps(index, indent=2) + '\n')
        with (ROOT / '_trash/TRASH_LOG.md').open('a') as log:
            log.write(f'\n2026-11-14 — Finale art promoted; replaced Core files preserved at `{archive.relative_to(ROOT)}`. Hashes and restoration instructions are in docs/maintenance/archive-manifest.json.\n')
        print(f'Promoted {len(files)} files; previous files preserved in {archive}')
    else:
        print(f'Staged {len(files)} files in {args.output}')


if __name__ == '__main__':
    main()
