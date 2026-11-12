"""PURPOSE: Capture disposable bunker and prototype-room visual/geometry diagnostics.
CALLED BY: Run from repo root with dummy SDL and --output-dir NEW_DIR.
HOW TO MODIFY: Preserve temporary saves, explicit fixture labels and original runtime assets.
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import pygame
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.scenes.bunker import BUNKER_STATIONS
from video_game.engine.world import Camera


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    outputs=[]
    guides=[]
    with tempfile.TemporaryDirectory(prefix='6equj5-prototype-guide-') as temporary:
        pygame.init()
        pygame.display.set_mode((960,540))
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(temporary),settings_store=SettingsStore(temporary))
        try:
            game.start_new_game()
            bunker=game.scenes[config.STATE_BUNKER_HUB]
            # Flat registration reference from real layers; this omits the actor and UI.
            base=pygame.Surface((480,270),pygame.SRCALPHA)
            base.fill((6,9,12,255))
            for layer in bunker.layers:
                if layer: base.blit(layer,(0,0))
            native=pygame.transform.scale(base,(960,540))
            base_file=args.output_dir/'bunker_background_flat_960.png'
            pygame.image.save(native,str(base_file))
            marked=native.copy()
            font=pygame.font.Font(None,20)
            colors=[(90,220,255),(250,210,90),(255,150,80),(115,255,140)]
            for (name,station),color in zip(BUNKER_STATIONS.items(),colors):
                x0=round(2*station['x_min']);x1=round(2*station['x_max'])
                pygame.draw.line(marked,color,(x0,519),(x1,519),4)
                marked.blit(font.render(name.upper(),True,color),(x0,520))
            marked_file=args.output_dir/'bunker_station_bounds_960.png'
            pygame.image.save(marked,str(marked_file))
            outputs.extend([{'file':base_file.name,'sha256':sha(base_file),'state':'six real bunker layers flattened; no actor/HUD'},
                            {'file':marked_file.name,'sha256':sha(marked_file),'state':'same flattened layers; colored horizontal bands show mateo_x station triggers, not physical fixture bounds'}])
            for name,station in BUNKER_STATIONS.items():
                bunker.mateo_x=station['center_x']
                game.render()
                path=args.output_dir/f'bunker_{name}_fixture_960.png'
                pygame.image.save(game.crt.render_surface,str(path))
                outputs.append({'file':path.name,'sha256':sha(path),'state':'direct station-position fixture',
                                'mateo_x':bunker.mateo_x,'active_station':bunker.get_active_station()})
            game.change_state(config.STATE_FIELD_OPS)
            scene=game.current_scene
            room_specs=[('annex','act_01/mandela_test.json','default',('2029_CORE','1977_ANALOG')),
                        ('relay','act_04/dodleston_relay.json','relay_entrance',('2029_CORE','1977_ANALOG')),
                        ('flashback','flashback/ehman_1977.json','ehman_entrance',('1977_ANALOG',))]
            for label,relative,spawn,timelines in room_specs:
                scene.load_room(relative,spawn_name=spawn)
                for timeline in timelines:
                    if not scene.room.set_active_timeline(timeline):
                        raise ValueError(f'missing room timeline {timeline}')
                    if scene.reality.world:
                        scene.reality.world.active_timeline=timeline
                    camera=Camera(480,288)
                    camera.set_world_bounds(scene.room.width_px,scene.room.height_px)
                    diagnostic=pygame.Surface((480,288),pygame.SRCALPHA)
                    diagnostic.fill((8,12,16,255))
                    scene.room.render_tiles(diagnostic,camera)
                    objects=[]
                    for index,obj in enumerate(scene.room.objects,1):
                        if not obj.is_active_in_timeline(timeline): continue
                        rect=pygame.Rect(round(obj.x),round(obj.y),round(obj.width),round(obj.height))
                        pygame.draw.rect(diagnostic,(80,220,245),rect,1)
                        objects.append({'number':index,'id':obj.id,'type':obj.type,'rect':list(rect),'timeline':obj.timeline})
                        diagnostic.blit(pygame.font.Font(None,12).render(str(index),True,(255,220,90)),(rect.x,rect.y-9))
                    for exit_info in scene.room.exits:
                        pygame.draw.rect(diagnostic,(255,150,80),exit_info.rect,1)
                    guide=args.output_dir/f'{label}_{timeline}_geometry_960x576.png'
                    pygame.image.save(pygame.transform.scale(diagnostic,(960,576)),str(guide))
                    guides.append({'file':guide.name,'sha256':sha(guide),'room':scene.room.room_id,'timeline':timeline,
                                   'objects':objects,'exits':[{'id':ex.id,'rect':list(ex.rect)} for ex in scene.room.exits],
                                   'note':'actual collision tiles, numbered cyan authored-object bounds, orange exit trigger; annotations are diagnostic, not runtime art'})
                    scene.camera.x=0;scene.camera.y=18
                    game.render()
                    view=args.output_dir/f'{label}_{timeline}_fixture_960.png'
                    pygame.image.save(game.crt.render_surface,str(view))
                    outputs.append({'file':view.name,'sha256':sha(view),'state':'direct room/timeline fixture',
                                    'room':scene.room.room_id,'timeline':timeline,'player_rect':list(scene.player.rect),'camera':[0,18]})
            # Actual flashback controller under direct scene/desk fixture; E events operate the modal.
            scene.load_room('flashback/ehman_1977.json',spawn_name='ehman_desk')
            for _ in range(30):
                game.input.begin_frame();game.update(1/60)
            for name in ('inspect','annotate'):
                game.input.begin_frame()
                game.handle_event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e))
                game.handle_event(pygame.event.Event(pygame.KEYUP,key=pygame.K_e))
                game.update(1/60)
                game.render()
                path=args.output_dir/f'flashback_printout_{name}_fixture_960.png'
                pygame.image.save(game.crt.render_surface,str(path))
                outputs.append({'file':path.name,'sha256':sha(path),'state':'direct desk entry + E key',
                                'stage':scene.flashback.stage.value,'printout_open':scene.flashback.is_printout_open,
                                'player_rect':list(scene.player.rect)})
            info={'outputs':outputs,'geometry_guides':guides,'bunker_station_ranges':BUNKER_STATIONS,
                  'fixture':'dummy SDL, temporary saves, direct position/room entry, direct timeline fixture; E events for printout; no normal-route claim',
                  'limits':'diagnostic annotations are not authored art; no real-window, full interaction, human quality, timing or art-gate evidence'}
            (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n')
            print(json.dumps({'outputs':len(outputs),'guides':len(guides)},indent=2))
        finally:
            game.close()
            pygame.quit()


if __name__=='__main__':
    main()
