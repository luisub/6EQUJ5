"""PURPOSE: Validate and safely promote one new per-world threat sprite family.
CALLED BY: python -m video_game.tools.build_planet_threat and focused tests.
HOW TO MODIFY: Keep exact IDs, staged validation, transaction lock and manifest last.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from PIL import Image

from video_game.engine.asset_transactions import fcntl, promote_group
from video_game.engine.config import ASSETS_DIR
from video_game.engine.planet_threat_assets import (THREAT_IDS, FAMILY_ROOT, IMAGE_NAME,
                                                   DIMENSIONS, PIVOT, validate_planet_threat_bytes,
                                                   RUN_IMAGE_NAME, RUN_DIMENSIONS,
                                                   validate_planet_threat_run_bytes)
from video_game.tools.asset_build_common import _check_pending, _no_symlinks


def export_run_master(master, output_dir):
    """Register four generated poses with one crop, scale and floor anchor."""
    with Image.open(_no_symlinks(master)) as original:
        if original.mode != 'RGBA' or original.width % 4:
            raise ValueError('Run master must be RGBA with four equal horizontal cells')
        width = original.width // 4
        cells = [original.crop((i * width, 0, (i + 1) * width, original.height)) for i in range(4)]
    bounds = []
    for cell in cells:
        # Remove faint transparent-background residue before nearest-pixel export.
        alpha = cell.getchannel('A').point(lambda value: value if value >= 32 else 0)
        cell.putalpha(alpha)
        box = alpha.getbbox()
        if box is None:
            raise ValueError('Run master has an empty cell')
        bounds.append(box)
    crop = (min(b[0] for b in bounds), min(b[1] for b in bounds),
            max(b[2] for b in bounds), max(b[3] for b in bounds))
    scale = min(84 / (crop[2] - crop[0]), 56 / (crop[3] - crop[1]))
    size = (round((crop[2] - crop[0]) * scale), round((crop[3] - crop[1]) * scale))
    origin = (48 - size[0] // 2, 64 - size[1])
    frames = []
    for cell in cells:
        frame = Image.new('RGBA', DIMENSIONS)
        frame.paste(cell.crop(crop).resize(size, Image.Resampling.NEAREST), origin)
        frames.append(frame)
    sheet = Image.new('RGBA', RUN_DIMENSIONS)
    for index, frame in enumerate(frames):
        sheet.paste(frame, (index * DIMENSIONS[0], 0))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    frames[1].save(output / IMAGE_NAME)
    sheet.save(output / RUN_IMAGE_NAME)
    return {'cell_width': width, 'shared_crop': list(crop), 'content_size': list(size),
            'origin': list(origin), 'resampling': 'nearest', 'alpha_floor': 32, 'idle_frame': 1}


def build(art_id, source, provenance, *, assets_dir=ASSETS_DIR, archive_dir=None, promote=False,
          run_source=None, replace_existing=False):
    """Promote a reviewed family; explicit replacements archive the prior export."""
    if not isinstance(art_id, str) or art_id not in THREAT_IDS:
        raise ValueError('Unknown planet threat ID')
    if not isinstance(provenance, dict) or not provenance:
        raise ValueError('A nonempty provenance object is required')
    json.dumps(provenance, allow_nan=False)
    source = _no_symlinks(source)
    data = source.read_bytes(); validate_planet_threat_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    manifest = {'schema_version': 1, 'kind': 'planet_threat', 'art_id': art_id,
                'pivot': list(PIVOT),
                'image': {'file': IMAGE_NAME, 'dimensions': list(DIMENSIONS), 'sha256': digest},
                'provenance': provenance}
    run_data = None
    if run_source is not None:
        run_data = _no_symlinks(run_source).read_bytes()
        validate_planet_threat_run_bytes(run_data)
        manifest['run'] = {'file': RUN_IMAGE_NAME, 'dimensions': list(RUN_DIMENSIONS),
                           'sha256': hashlib.sha256(run_data).hexdigest()}
    root = _no_symlinks(assets_dir)
    if not root.is_dir():
        raise FileNotFoundError(root)
    archive = _no_symlinks(archive_dir or (Path(__file__).resolve().parents[2] / '_trash' if root == ASSETS_DIR.resolve() else root.parent / '_trash'))
    if archive == root or archive.is_relative_to(root):
        raise ValueError('Archive must be outside the asset root')
    if fcntl is None:
        raise RuntimeError('Planet threat building requires fcntl locking')
    descriptor = os.open(root, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another asset build is active') from exc
        if _check_pending(root):
            raise RuntimeError('Pending transaction requires recovery')
        family = FAMILY_ROOT / art_id
        target = _no_symlinks(root / family)
        if target.exists() and not replace_existing:
            raise FileExistsError(f'Planet threat family already exists: {target}')
        if not promote:
            return {'status': 'validated', 'manifest': manifest}
        with tempfile.TemporaryDirectory(prefix='planet-threat-stage-', dir=root.parent) as temporary:
            stage = Path(temporary); directory = stage / family; directory.mkdir(parents=True)
            staged = directory / IMAGE_NAME; shutil.copyfile(source, staged)
            staged_data = staged.read_bytes()
            if hashlib.sha256(staged_data).hexdigest() != digest:
                raise IOError('Staged image differs from reviewed source')
            validate_planet_threat_bytes(staged_data)
            paths = [family / IMAGE_NAME]
            if run_data is not None:
                (directory / RUN_IMAGE_NAME).write_bytes(run_data)
                paths.append(family / RUN_IMAGE_NAME)
            (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
            paths.append(family / 'manifest.json')
            _no_symlinks(root / family)
            if (root / family).exists() and not replace_existing:
                raise FileExistsError('Planet threat family appeared during staging')
            saved = promote_group(root, stage, archive, f'planet_threat_{art_id}',
                                  tuple(paths))
        return {'status':'promoted', 'manifest':manifest, 'archive':str(saved)}
    finally:
        os.close(descriptor)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--art-id', choices=sorted(THREAT_IDS), required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--source', type=Path)
    source.add_argument('--master', type=Path, help='Four equally spaced run poses in one horizontal row')
    parser.add_argument('--run-source', type=Path)
    parser.add_argument('--replace-existing', action='store_true')
    parser.add_argument('--provenance', type=Path, required=True)
    parser.add_argument('--assets-dir', type=Path, default=ASSETS_DIR)
    parser.add_argument('--archive-dir', type=Path)
    parser.add_argument('--promote', action='store_true')
    args = parser.parse_args(argv)
    provenance = json.loads(args.provenance.read_text(encoding='utf-8'))
    options = dict(assets_dir=args.assets_dir, archive_dir=args.archive_dir, promote=args.promote,
                   replace_existing=args.replace_existing)
    if args.master:
        if args.run_source:
            parser.error('--run-source cannot be combined with --master')
        with tempfile.TemporaryDirectory(prefix='planet-threat-export-') as temporary:
            provenance['export'] = export_run_master(args.master, temporary)
            result = build(args.art_id, Path(temporary) / IMAGE_NAME, provenance,
                           run_source=Path(temporary) / RUN_IMAGE_NAME, **options)
    else:
        result = build(args.art_id, args.source, provenance, run_source=args.run_source, **options)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
