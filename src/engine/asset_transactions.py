"""
MODULE: video_game/engine/asset_transactions.py
PURPOSE: Archive and safely promote a validated asset group with recovery.
CALLED BY: video_game.main, video_game.tools.build_assets, video_game.tools.preview_assets.
HOW TO MODIFY: Keep the recovery journal durable before the first replacement;
  never delete the original copies needed by the archive restoration procedure.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import uuid
from datetime import date

try:
    import fcntl
except ImportError:  # The currently supported builder host is macOS.
    fcntl = None


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path, value):
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _restore(journal):
    for entry in journal['files']:
        target = Path(journal['asset_root']) / entry['path']
        if entry['existed']:
            archived = Path(journal['archive']) / 'video_game' / 'assets' / entry['path']
            if _sha256(archived) != entry['sha256']:
                raise RuntimeError(f'Backup hash mismatch; manual recovery needed: {archived}')
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + '.f03-recovery')
            shutil.copy2(archived, temporary)
            os.replace(temporary, target)
        else:
            target.unlink(missing_ok=True)


def recover_pending(asset_root):
    """Roll an interrupted promotion back before another build begins."""
    journal_path = Path(asset_root).parent / f'.{Path(asset_root).name}-asset-build-pending.json'
    if not journal_path.exists():
        return False
    journal = json.loads(journal_path.read_text(encoding='utf-8'))
    if Path(journal['asset_root']) != Path(asset_root).resolve():
        raise RuntimeError(f'Unexpected asset root in recovery journal: {journal_path}')
    _restore(journal)
    journal_path.unlink()
    return True


def recover_before_load(asset_root):
    """Recover an interrupted build before a game or preview loads assets."""
    asset_root = Path(asset_root).resolve()
    if fcntl is None:
        journal = asset_root.parent / f'.{asset_root.name}-asset-build-pending.json'
        if journal.exists():
            raise RuntimeError(f'Asset recovery requires a supported builder host: {journal}')
        return False
    descriptor = os.open(asset_root, os.O_RDONLY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"Cannot load assets while a build is active: {asset_root}") from exc
        return recover_pending(asset_root)
    finally:
        os.close(descriptor)


def promote_group(asset_root, stage_root, archive_root, group, relative_paths):
    """Save originals, journal the transaction, then promote or restore all files."""
    asset_root = Path(asset_root).resolve()
    stage_root = Path(stage_root).resolve()
    archive_root = Path(archive_root).resolve()
    journal_path = asset_root.parent / f'.{asset_root.name}-asset-build-pending.json'
    if journal_path.exists():
        raise RuntimeError(f'Pending transaction requires recovery: {journal_path}')
    archive = archive_root / f'{date.today().isoformat()}_F03' / uuid.uuid4().hex
    entries = []
    for relative in relative_paths:
        relative = Path(relative)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError(f'Invalid asset path: {relative}')
        source = stage_root / relative
        if not source.is_file():
            raise FileNotFoundError(f'Staged file is missing: {source}')
        target = asset_root / relative
        if not target.resolve().is_relative_to(asset_root):
            raise ValueError(f'Asset path escapes root: {relative}')
        existed = target.is_file()
        entry = {'path': relative.as_posix(), 'existed': existed, 'sha256': _sha256(target) if existed else None,
                 'replacement_sha256': _sha256(source)}
        if existed:
            backup = archive / 'video_game' / 'assets' / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
            if _sha256(backup) != entry['sha256']:
                raise IOError(f'Backup failed verification: {target}')
        entries.append(entry)
    archive.mkdir(parents=True, exist_ok=True)
    record = {'group': group, 'reason': 'Explicit selected replacement', 'asset_root': str(asset_root),
              'archive': str(archive), 'files': entries,
              'references_updated': 'Existing asset paths and manifest references retained.',
              'checks': 'Staged files validated before promotion; archived originals hash-verified.',
              'restore': 'Verify each archived SHA-256, copy it to its original asset path, remove files marked absent, then rerun the loader and checkpoint suites.'}
    _write_json(archive / 'manifest.json', record)
    log = archive_root / 'TRASH_LOG.md'
    with log.open('a', encoding='utf-8') as stream:
        stream.write(f'\n- Asset replacement archive: [{group}]({archive.relative_to(archive_root).as_posix()}/manifest.json); see manifest for hashes and restoration.\n')
    _write_json(journal_path, record)
    try:
        for relative in relative_paths:
            target = asset_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage_root / relative, target)
    except BaseException:
        _restore(record)
        journal_path.unlink()
        raise
    journal_path.unlink()
    return archive
