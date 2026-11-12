"""PURPOSE: Inspect a clean-copy wheel, all room families and the firing-light family.
CALLED BY: python check.py --output-dir NEW_DIRECTORY [--require-family FAMILY ...].
HOW TO MODIFY: Preserve clean copy, exact hashes, isolated imports and temporary saves.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(argv, cwd, env, output, name):
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True)
    (output / f'{name}.stdout').write_text(result.stdout, encoding='utf-8')
    (output / f'{name}.stderr').write_text(result.stderr, encoding='utf-8')
    record = {'argv': argv, 'cwd': str(cwd), 'exit_code': result.returncode,
              'environment': {key: env.get(key) for key in (
                  'SDL_VIDEODRIVER', 'SDL_AUDIODRIVER', 'PYGAME_HIDE_SUPPORT_PROMPT',
                  'SIX_GAME_SAVE_DIR', 'TMPDIR', 'PYTHONPATH', 'PYTHONNOUSERSITE')}}
    (output / f'{name}.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    if result.returncode:
        raise RuntimeError(f'{name} failed with exit {result.returncode}; inspect recorded output')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--require-family', action='append', default=[])
    args = parser.parse_args()
    repo = Path.cwd().resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    if not (repo / 'pyproject.toml').is_file() or not (repo / 'video_game/engine/room_art_contracts.py').is_file():
        raise RuntimeError('Run from the repository root')
    temp = Path(tempfile.mkdtemp(prefix='6equj5-remaining-wheel-')).resolve()
    source = temp / 'source'
    source.mkdir()
    for name in ('pyproject.toml', 'README.md'):
        shutil.copy2(repo / name, source / name)
    shutil.copytree(repo / 'src', source / 'src', ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.egg-info', 'build', 'dist'))
    shutil.copytree(repo / 'video_game', source / 'video_game', ignore=shutil.ignore_patterns(
        '__pycache__', '*.pyc', '*.egg-info', 'tests', 'art', 'planning', '_temp', '_trash', 'build', 'dist'))
    contract = runpy.run_path(str(source / 'video_game/engine/room_art_contracts.py'))
    allowed = ('ohio_approach_v1', *contract['ROOM_ART_FAMILIES'], *contract['OPAQUE_BACKDROP_FAMILIES'])
    if len(allowed) != len(set(allowed)):
        raise RuntimeError('Duplicate family identifier in allowlists')
    unknown = set(args.require_family) - set(allowed)
    if unknown:
        raise RuntimeError(f'Required family not allowlisted: {sorted(unknown)}')
    environment_dir = source / 'video_game/assets/environments'
    present = []
    for family in allowed:
        directory = environment_dir / family
        if directory.exists():
            if not directory.is_dir() or not (directory / 'manifest.json').is_file():
                raise RuntimeError(f'Incomplete present family: {family}')
            present.append(family)
    absent_required = set(args.require_family) - set(present)
    if absent_required:
        raise RuntimeError(f'Required family not installed: {sorted(absent_required)}')
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', PYGAME_HIDE_SUPPORT_PROMPT='1',
               PYTHONNOUSERSITE='1', SIX_GAME_SAVE_DIR=str(temp / 'save'), TMPDIR=str(temp))
    wheels = temp / 'wheels'
    wheels.mkdir()
    run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation', '--no-cache-dir',
         '--wheel-dir', str(wheels), str(source)], temp, env, output, 'build')
    wheel_files = list(wheels.glob('*.whl'))
    if len(wheel_files) != 1:
        raise RuntimeError(f'Expected one wheel, found {len(wheel_files)}')
    wheel = wheel_files[0]
    verified = {}
    with zipfile.ZipFile(wheel) as archive:
        members = archive.namelist()
        if len(members) != len(set(members)):
            raise RuntimeError('Duplicate wheel member')
        forbidden = ('video_game/tests/', 'video_game/art/', 'video_game/planning/',
                     'video_game/_trash/', 'video_game/_temp/')
        if any(name.startswith(forbidden) for name in members):
            raise RuntimeError('Wheel contains excluded project material')
        for module in ('video_game/engine/native_room_assets.py', 'video_game/engine/room_art_contracts.py',
                       'video_game/tools/build_room_family.py', 'video_game/engine/firing_lighting.py',
                       'video_game/tools/build_firing_flash.py', 'video_game/engine/scenes/field.py',
                       'video_game/engine/weapons.py', 'video_game/engine/effects.py',
                       'video_game/engine/crt_renderer.py'):
            if module not in members:
                raise RuntimeError(f'Missing wheel module: {module}')
            if sha(archive.read(module)) != sha((source / module).read_bytes()):
                raise RuntimeError(f'Wheel module mismatch: {module}')
        for family in present:
            directory = environment_dir / family
            manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
            if manifest.get('schema_version') == 3:
                records = [manifest['backdrop']]
            elif manifest.get('schema_version') in (1, 2):
                records = manifest['layers'] + manifest.get('props', [])
            else:
                raise RuntimeError(f'Unknown family schema: {family}')
            filenames = [record['file'] for record in records]
            if len(filenames) != len(set(filenames)) or any(Path(x).name != x for x in filenames):
                raise RuntimeError(f'Unsafe or repeated component in {family}')
            for record in records:
                if sha((directory / record['file']).read_bytes()) != record['sha256']:
                    raise RuntimeError(f'Source manifest hash mismatch: {family}/{record["file"]}')
            for name in ['manifest.json', *filenames]:
                member = f'video_game/assets/environments/{family}/{name}'
                source_hash = sha((directory / name).read_bytes())
                if sha(archive.read(member)) != source_hash:
                    raise RuntimeError(f'Wheel member mismatch: {member}')
                verified[member] = source_hash
        effect = source / 'video_game/assets/effects/approach_maser_flash_v1'
        effect_manifest = json.loads((effect / 'manifest.json').read_text(encoding='utf-8'))
        if effect_manifest['file'] != 'flash_64x32.png' or sha((effect / 'flash_64x32.png').read_bytes()) != effect_manifest['sha256']:
            raise RuntimeError('Installed firing-flash manifest or hash mismatch')
        for name in ('manifest.json', 'flash_64x32.png'):
            member = f'video_game/assets/effects/approach_maser_flash_v1/{name}'
            source_hash = sha((effect / name).read_bytes())
            if sha(archive.read(member)) != source_hash:
                raise RuntimeError(f'Wheel member mismatch: {member}')
            verified[member] = source_hash
        if len(present) != 9 or len(verified) != 27:
            raise RuntimeError(f'Expected nine room families and 27 family files, got {len(present)} and {len(verified)}')
    target = temp / 'installed'
    run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--target', str(target), str(wheel)],
        temp, env, output, 'install')
    smoke = Path(__file__).with_name('smoke_installed.py').resolve()
    run([sys.executable, '-I', str(smoke), str(target), json.dumps(present)], temp, env, output, 'smoke')
    info = {'wheel_path': str(wheel), 'wheel_sha256': sha(wheel.read_bytes()),
            'member_count': len(members), 'temporary_root': str(temp), 'present_families': present,
            'absent_allowlisted_families': [name for name in allowed if name not in present],
            'required_families': args.require_family, 'verified_members': verified,
            'limitations': 'Dummy SDL, direct scene entry and loader smoke only; no real-window, human-play, audio or performance acceptance.'}
    (output / 'context.json').write_text(json.dumps(info, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(info, indent=2))


if __name__ == '__main__':
    main()
