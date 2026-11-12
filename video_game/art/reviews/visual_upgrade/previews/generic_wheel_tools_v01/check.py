"""PURPOSE: Verify a clean copied-source wheel and isolated installed room families.
CALLED BY: python check.py --output-dir NEW_DIR.
HOW TO MODIFY: Keep source-copy build, resource hashes, isolated cwd and temporary saves.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


def run(argv, cwd, env, out, name, input_text=None):
    result=subprocess.run(argv,cwd=cwd,env=env,text=True,input=input_text,capture_output=True)
    (out/f'{name}.stdout').write_text(result.stdout);(out/f'{name}.stderr').write_text(result.stderr)
    (out/f'{name}.json').write_text(json.dumps({'argv':argv,'cwd':str(cwd),'exit_code':result.returncode},indent=2)+'\n')
    if result.returncode:raise RuntimeError(f'{name} failed')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=False);repo=Path.cwd().resolve()
    temp=Path(tempfile.mkdtemp(prefix='6equj5-generic-wheel-'));source=temp/'source';source.mkdir()
    for name in ('pyproject.toml','README.md'):
        shutil.copy2(repo/name,source/name)
    shutil.copytree(repo/'src',source/'src',ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.egg-info'))
    shutil.copytree(repo/'video_game',source/'video_game',ignore=shutil.ignore_patterns('__pycache__','*.pyc','tests','art','planning','_temp','_trash'))
    env=os.environ.copy();env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',SIX_GAME_SAVE_DIR=str(temp/'save'),TMPDIR=str(temp))
    wheels=temp/'wheels';wheels.mkdir()
    run([sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation','--no-cache-dir','--wheel-dir',str(wheels),str(source)],temp,env,out,'build')
    wheel=next(wheels.glob('*.whl'));target=temp/'installed'
    names=['ohio_approach_v1','ohio_approach_v2','ohio_salvage_v1','ohio_dish_v1']
    verified={}
    with zipfile.ZipFile(wheel) as archive:
        members=set(archive.namelist())
        for module in ('video_game/engine/native_room_assets.py','video_game/engine/room_art_contracts.py','video_game/tools/build_room_family.py'):
            assert module in members,module
        for name in names:
            directory=repo/'video_game/assets/environments'/name
            for file in directory.iterdir():
                if file.is_file():
                    member=f'video_game/assets/environments/{name}/{file.name}'
                    digest=hashlib.sha256(file.read_bytes()).hexdigest()
                    assert hashlib.sha256(archive.read(member)).hexdigest()==digest,member
                    verified[member]=digest
        assert not any(n.startswith(('video_game/tests/','video_game/art/','video_game/planning/')) for n in members)
    run([sys.executable,'-m','pip','install','--no-deps','--target',str(target),str(wheel)],temp,env,out,'install')
    env['PYTHONPATH']=str(target)
    code='''import pygame, video_game\nfrom video_game.main import run_game\nfrom video_game.engine import config\nfrom video_game.engine.native_room_assets import load_native_room_family\nfrom video_game.engine.crt_renderer import CRTRenderer\nfrom video_game.engine.state_machine import GameStateMachine\nprint("installed",video_game.__file__)\nassert run_game(max_frames=2)==2\npygame.init(); pygame.display.set_mode((960,540))\nfor room,size in [("act_01_approach",(960,288)),("act_01_salvage_yard",(640,288)),("act_01_dish_catwalk",(640,288))]:\n assert load_native_room_family(config.ASSETS_DIR,room,size) is not None\nm=GameStateMachine(CRTRenderer(scale=1)); assert m.start_new_game()[0]\nfor room,spawn in [("approach","bunker_exit"),("salvage_yard","yard_entrance"),("dish_catwalk","catwalk_start")]:\n m.change_state(config.STATE_FIELD_OPS,room="act_01/"+room+".json",spawn=spawn); assert m.current_scene.native_approach is not None; m.render()\nm.close();pygame.quit();print("installed game and three room families OK")'''
    run([sys.executable,'-c',code],temp,env,out,'smoke')
    info={'wheel_path':str(wheel),'wheel_sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'temporary_root':str(temp),'verified_members':verified,'environment':{'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy','SIX_GAME_SAVE_DIR':str(temp/'save'),'PYTHONPATH':str(target)},'limitations':'installed dummy SDL smoke, not a native-window or gameplay acceptance'}
    (out/'context.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info,indent=2))


if __name__=='__main__':main()
