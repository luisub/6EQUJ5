"""MODULE: tools/build_room_family.py
PURPOSE: Explicitly stage and promote one allowlisted native room-art family.
CALLED BY: python -m tools.build_room_family or its transaction tests.
HOW TO MODIFY: Preserve shared contracts, lock/recovery, full validation and manifest-last promotion.
"""
import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

from video_game.engine.asset_transactions import fcntl, promote_group, recover_pending
from video_game.engine.config import ASSETS_DIR
from video_game.engine.room_art_contracts import (
    OPAQUE_BACKDROP_FAMILIES, ROOM_ART_FAMILIES, backdrop_manifest_template, manifest_template,
)
from tools.build_approach_family import _check_pending, _no_symlinks, _relative, _sha, _validate_image


def _records(template):
    return [template['backdrop']] if template['schema_version'] == 3 else template['layers'] + template['props']


def _paths(family_id, template):
    """Derive only the exact ordered targets in the allowlisted contract."""
    directory = Path('environments') / family_id
    names = [item['file'] for item in _records(template)] + ['manifest.json']
    if len(names) != len(set(names)) or any(not isinstance(name, str) or Path(name).name != name for name in names):
        raise ValueError('Unsafe or duplicate room family filenames')
    return tuple(_relative(directory / name) for name in names)


def _check_paths(root, paths):
    clean = tuple(_relative(path) for path in paths)
    if len(clean) != len(set(clean)):
        raise ValueError('Duplicate room family paths')
    for path in clean:
        _no_symlinks(root / path)
    return clean


def _source_manifest(template, sources):
    records = _records(template)
    if len(records) != len(sources):
        raise ValueError('Incorrect number of prop sources for room family')
    paths = []
    for record, source in zip(records, sources):
        path = _validate_image(source, tuple(record['dimensions']), record['alpha'] == 'opaque')
        paths.append(path)
    if len(set(paths)) != len(paths):
        raise ValueError('Duplicate reviewed source paths')
    for record, path in zip(records, paths):
        record['sha256'] = _sha(path)
    return template, paths


def _build(family_id, template_factory, sources, *, assets_dir, archive_dir, promote):
    """Shared lock, complete source validation, staged revalidation and transaction."""
    template = template_factory(family_id)
    paths = _paths(family_id, template)
    root = _no_symlinks(assets_dir)
    if not root.is_dir():
        raise FileNotFoundError(f'Asset root does not exist: {root}')
    archive = _no_symlinks(archive_dir or (Path(__file__).resolve().parent.parent / '_trash' if root == ASSETS_DIR.resolve() else root.parent / '_trash'))
    if archive == root or archive.is_relative_to(root):
        raise ValueError('Archive must be outside asset root')
    if fcntl is None:
        raise RuntimeError('Room family building requires fcntl locking')
    has_sources = bool(sources)
    if promote and not has_sources:
        raise ValueError('Explicit promotion requires complete reviewed sources')
    descriptor = os.open(root, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f'Another asset build is active: {root}') from exc
        pending = _check_pending(root)
        if pending and not promote:
            raise RuntimeError('Pending asset transaction requires recovery before review')
        if pending:
            recover_pending(root)
        _check_paths(root, paths)
        if not has_sources:
            presence = {path.as_posix(): (root / path).is_file() for path in paths}
            count = sum(presence.values())
            status = ('absent' if count == 0 else 'present_not_inspected' if count == len(paths)
                      else 'partial_not_inspected')
            return {'status': status, 'integrity': 'not_inspected', 'files': presence}
        manifest, sources = _source_manifest(template, sources)
        if not promote:
            return {'status': 'validated', 'manifest': manifest}
        with tempfile.TemporaryDirectory(prefix='room-art-stage-', dir=root.parent) as temporary:
            stage = _no_symlinks(temporary)
            _check_paths(stage, paths)
            directory = stage / 'environments' / family_id
            directory.mkdir(parents=True)
            for source, relative in zip(sources, paths[:-1]):
                shutil.copyfile(source, stage / relative)
            staged, _ = _source_manifest(template_factory(family_id),
                                         [stage / path for path in paths[:-1]])
            if staged != manifest:
                raise IOError('Staged image hash differs from reviewed source')
            (stage / paths[-1]).write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
            _check_paths(stage, paths)
            _check_paths(root, paths)
            saved = promote_group(root, stage, archive, family_id, paths)
        return {'status': 'promoted', 'archive': str(saved), 'manifest': manifest}
    finally:
        os.close(descriptor)


def build_family(family_id, *, assets_dir=ASSETS_DIR, archive_dir=None, far=None,
                 world=None, props=None, promote=False):
    """Report presence without inspection, validate complete sources, or explicitly promote."""
    template = manifest_template(family_id)
    prop_sources = list(props or ())
    has_sources = far is not None or world is not None or bool(prop_sources)
    if has_sources and (far is None or world is None or len(prop_sources) != len(template['props'])):
        raise ValueError('Far, world and all ordered prop sources are required together')
    sources = [far, world, *prop_sources] if has_sources else []
    return _build(family_id, manifest_template, sources, assets_dir=assets_dir,
                  archive_dir=archive_dir, promote=promote)


def build_backdrop_family(family_id, *, assets_dir=ASSETS_DIR, archive_dir=None,
                          backdrop=None, promote=False):
    """Review or explicitly promote a complete single-image opaque backdrop family."""
    return _build(family_id, backdrop_manifest_template, [backdrop] if backdrop is not None else [],
                  assets_dir=assets_dir, archive_dir=archive_dir, promote=promote)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', choices=ROOM_ART_FAMILIES + OPAQUE_BACKDROP_FAMILIES, required=True)
    parser.add_argument('--assets-dir', type=Path, default=ASSETS_DIR)
    parser.add_argument('--archive-dir', type=Path)
    parser.add_argument('--far', type=Path)
    parser.add_argument('--world', type=Path)
    parser.add_argument('--prop', type=Path, action='append', default=[])
    parser.add_argument('--backdrop', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--promote', action='store_true', help='Explicitly promote the complete selected family')
    mode.add_argument('--dry-run', action='store_true', help='Without sources report presence only; with complete sources validate without writes')
    args = parser.parse_args(argv)
    if args.family in OPAQUE_BACKDROP_FAMILIES:
        if args.far is not None or args.world is not None or args.prop:
            parser.error('Opaque backdrop families accept only --backdrop')
        result = build_backdrop_family(args.family, assets_dir=args.assets_dir, archive_dir=args.archive_dir,
                                       backdrop=args.backdrop, promote=args.promote)
    else:
        if args.backdrop is not None:
            parser.error('Layered room families do not accept --backdrop')
        result = build_family(args.family, assets_dir=args.assets_dir, archive_dir=args.archive_dir,
                              far=args.far, world=args.world, props=args.prop, promote=args.promote)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
