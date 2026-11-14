"""Capture native insect motion and a mapped jump past the Beacon Forger."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import tempfile

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from PIL import Image
import pygame

from video_game.engine import config
from video_game.engine.alien_journey import dispatch, journey_data, save_ledger
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.enemies import CoreReconDrone, CoreEnforcer, StaticHound
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def capture(output):
    output.mkdir(parents=True, exist_ok=False)
    pygame.init(); pygame.display.set_mode((960,540)); random.seed(1977)
    records = []
    with tempfile.TemporaryDirectory(prefix='6equj5-cyber-motion-') as temp:
        game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(Path(temp)/'save'),
                                settings_store=SettingsStore(Path(temp)/'settings'))
        game.change_settings(scale=1, crt_effects=False)
        def step():
            game.update(1/60); game.input.begin_frame()
        def key(code, down=True):
            game.handle_event(pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP, key=code))
        def frame():
            game.render(); surface=game.crt.render_surface
            return Image.frombytes('RGB',surface.get_size(),pygame.image.tobytes(surface,'RGB'))
        def still(name, setup):
            frame().save(output/name)
            records.append({'file':name,'size':[960,540],'setup':setup})
        def movie(name, frames, setup):
            palette=frames[len(frames)//2].quantize(colors=256,dither=Image.Dither.NONE)
            images=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
            images[0].save(output/name,save_all=True,append_images=images[1:],duration=100,loop=0,disposal=1)
            records.append({'file':name,'size':list(frames[0].size),'frames':len(frames),
                            'frame_duration_ms':100,'setup':setup})
        try:
            assert game.start_new_game(replace_existing=True)[0]
            game.change_state(config.STATE_FIELD_OPS,room='act_01/approach.json',spawn='bunker_exit')
            scene=game.current_scene
            scene.enemy_manager.clear()
            scene.forward_encounter=None; scene.world_hazards=None
            scene.player.x=90;scene.player.y=208
            insects=[CoreEnforcer('mantis',190,208,patrol_left=170,patrol_right=215),
                     StaticHound('beetle',275,220,patrol_left=250,patrol_right=295),
                     CoreReconDrone('wasp',385,150,patrol_left=365,patrol_right=420)]
            for insect in insects:
                insect.cooldown_timer=1000
                scene.enemy_manager.add_enemy(insect)
            frames=[]
            for tick in range(240):
                step()
                if tick%6==0:frames.append(frame())
                if tick==48:still('earth-cyber-insects.png','Ohio fixture with three insect roles, fixed player and extended enemy attack cooldowns; actual patrol updates.')
            movie('earth-cyber-insects.gif',frames,'Four seconds of actual patrol, wing and leg motion; staged actors/cooldowns, native pixels.')
            worlds=journey_data()['worlds']; world=worlds[-1]
            game.campaign.apply_event({'event_id':'capture_portal','type':'defeat_portal_warden'})
            for previous in worlds[:-1]:
                game.campaign.apply_event({'event_id':'capture_'+previous['id'],'type':previous['defeat_event']})
            save_ledger(game.campaign,{'version':1,'world_id':world['id'],'stage':'guardian','checkpoint':None,
                                       'receipts':[w['civ_id'] for w in worlds[:-1]]})
            assert dispatch(game)
            scene=game.current_scene; scene.boss.cooldown=1000
            scene.player.x=250;scene.player.y=208;scene.player.vx=scene.player.vy=0
            for _ in range(10):step()
            still('beacon-forger-left.png','Prior ten victories/receipts and left-side player position staged; no boss defeat injected.')
            frames=[]; facings=set()
            key(pygame.K_RIGHT);key(pygame.K_SPACE)
            for tick in range(150):
                step();facings.add(scene.boss.facing)
                if tick==2:key(pygame.K_SPACE,False)
                if tick==105:key(pygame.K_RIGHT,False)
                if tick%6==0:frames.append(frame())
            key(pygame.K_RIGHT,False)
            assert facings=={'left','right'} and not scene.player.is_dead
            still('beacon-forger-right.png','Mapped Right and Space cross the guardian; body turns right through normal updates.')
            movie('beacon-forger-turn.gif',frames,'Mapped jump and movement from a disclosed left-side fixture; extended boss cooldown; normal facing updates.')
            for r in records:
                path=output/r['file'];r['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();r['bytes']=path.stat().st_size
            (output/'capture.json').write_text(json.dumps({'purpose':'Staged enemy motion review, not a campaign playthrough',
                'isolated_saves':True,'drivers':'dummy','crt':False,'captures':records},indent=2)+'\n')
        finally:
            game.close();pygame.quit()
    print(f'Captured {len(records)} previews in {output}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    capture(parser.parse_args().output)
