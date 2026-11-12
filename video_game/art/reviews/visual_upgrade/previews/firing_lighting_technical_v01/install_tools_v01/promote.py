"""PURPOSE: Record an explicitly authorized flash-family transaction and byte verification.
CALLED BY: python promote.py --output-dir NEW_DIRECTORY --archive-dir NEW_DIRECTORY.
HOW TO MODIFY: Preserve pre-existing asset hashes, exact argv, manifest and journal checks.
"""
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from video_game.engine.config import ASSETS_DIR
from video_game.engine.firing_lighting import FLASH_FAMILY, FLASH_MANIFEST, FLASH_NAME


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--archive-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    root = Path(ASSETS_DIR).resolve()
    family = root / FLASH_FAMILY
    if family.exists() or family.is_symlink():
        raise RuntimeError('Expected an absent family; refuse to replace it')
    journal = root.parent / f'.{root.name}-asset-build-pending.json'
    if journal.exists() or journal.is_symlink():
        raise RuntimeError('Pending journal before transaction')
    before = {str(p.relative_to(root)): digest(p) for p in root.rglob('*') if p.is_file()}
    temp = tempfile.mkdtemp(prefix='6equj5-flash-promote-')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', TMPDIR=temp,
               SIX_GAME_SAVE_DIR=temp + '/save')
    source = 'video_game/art/reviews/visual_upgrade/previews/firing_flash_registration_v01/cell_v01/firing_flash_64x32.png'
    argv = ['/opt/anaconda3/envs/6equj5_game/bin/python', '-m', 'video_game.tools.build_firing_flash',
            '--archive-dir', str(args.archive_dir.resolve()), '--source', source, '--promote']
    result = subprocess.run(argv, env=env, text=True, capture_output=True)
    (args.output_dir / 'stdout.txt').write_text(result.stdout)
    (args.output_dir / 'stderr.txt').write_text(result.stderr)
    (args.output_dir / 'before_hashes.json').write_text(json.dumps(before, indent=2, sort_keys=True) + '\n')
    after = {name: digest(root / name) if (root / name).is_file() else None for name in before}
    manifest = json.loads((family / 'manifest.json').read_text()) if result.returncode == 0 else None
    details = {'argv': argv, 'cwd': os.getcwd(),
               'environment': {k: env[k] for k in ('SDL_VIDEODRIVER', 'SDL_AUDIODRIVER', 'TMPDIR', 'SIX_GAME_SAVE_DIR')},
               'exit_code': result.returncode, 'previous_file_count': len(before),
               'all_previous_files_unchanged': before == after,
               'new_png_sha256': digest(family / FLASH_NAME) if (family / FLASH_NAME).is_file() else None,
               'manifest_sha256': digest(family / 'manifest.json') if (family / 'manifest.json').is_file() else None,
               'manifest_matches_contract': manifest == FLASH_MANIFEST,
               'journal_absent': not journal.exists() and not journal.is_symlink()}
    (args.output_dir / 'verification.json').write_text(json.dumps(details, indent=2) + '\n')
    if result.returncode or before != after or manifest != FLASH_MANIFEST or not details['journal_absent']:
        raise RuntimeError('Transaction or byte verification failed; inspect logs')
    print(json.dumps(details, indent=2))


if __name__ == '__main__':
    main()
