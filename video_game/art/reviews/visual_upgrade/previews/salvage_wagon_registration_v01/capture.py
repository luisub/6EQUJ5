"""PURPOSE: Register a disposable wagon preview behind the actual salvage-yard geometry.
CALLED BY: Run from repository root with dummy SDL and --output-dir NEW_DIR.
HOW TO MODIFY: Preserve original alpha, native placement, temporary saves and fresh-output guard.
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import pygame
from PIL import Image
from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine

SOURCE=Path('video_game/art/source/visual_upgrade/candidates/salvage_wagon_v01/source/salvage_wagon_generated_master.png')
FAR=Path('video_game/art/reviews/visual_upgrade/previews/approach_far_registration_v01/far_native_1152x544.png')
YARD=Path('video_game/art/reviews/visual_upgrade/previews/salvage_registration_director_v02/capture_v01/yard_world_layer_1280x576.png')
CROP=(98,186,1764,769)
CELL=(168,76)
ANCHOR=(392,404)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    with Image.open(SOURCE) as source:
        if source.mode!='RGBA' or source.size!=(1862,845):
            raise ValueError('source must be original 1862x845 RGBA')
        alpha=source.getchannel('A')
        strong=alpha.point(lambda n:255 if n>127 else 0)
        bbox=strong.getbbox()
        crop=source.crop(CROP)
        full_hist=alpha.histogram()
        crop_hist=alpha.crop(CROP).histogram()
        excluded=sum(full_hist[1:])-sum(crop_hist[1:])
        excluded_strong=sum(full_hist[128:])-sum(crop_hist[128:])
        width=158
        height=round(crop.height*width/crop.width)
        sampled=crop.resize((width,height),Image.Resampling.NEAREST)
    cell=Image.new('RGBA',CELL,(0,0,0,0))
    position=((CELL[0]-width)//2,CELL[1]-height)
    cell.paste(sampled,position)
    a=cell.getchannel('A')
    strong=a.point(lambda n:255 if n>127 else 0)
    if strong.getbbox() is None or strong.getbbox()[3]!=76:
        raise ValueError('substantive wheel pixels must reach bottom row')
    args.output_dir.mkdir(parents=True,exist_ok=False)
    cell_file=args.output_dir/'wagon_168x76_rgba.png'
    cell.save(cell_file)
    matte_files=[]
    for name,color in [('light',(224,220,206,255)),('dark',(12,18,28,255))]:
        image=Image.alpha_composite(Image.new('RGBA',CELL,color),cell).convert('RGB')
        path=args.output_dir/f'wagon_{name}_matte_4x.png'
        image.resize((672,304),Image.Resampling.NEAREST).save(path)
        matte_files.append({'file':path.name,'sha256':sha(path),'color':list(color)})
    samples=[]
    crossing=[]
    with tempfile.TemporaryDirectory(prefix='6equj5-wagon-fixture-') as tmp:
        pygame.init()
        pygame.display.set_mode((960,540))
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
        try:
            game.start_new_game()
            game.change_state(config.STATE_FIELD_OPS)
            scene=game.current_scene
            scene.load_room('act_01/salvage_yard.json',spawn_name='yard_midpoint')
            for _ in range(30):
                game.input.begin_frame()
                game.update(1/60)
            wagon_rect=pygame.Rect(196,202,84,38)
            collision=scene.room.check_rect_collision(wagon_rect)
            if collision.get('hazard'):
                raise ValueError('wagon cell overlaps a hazard collision')
            far=pygame.image.load(str(FAR)).convert_alpha()
            yard=pygame.image.load(str(YARD)).convert_alpha()
            wagon=pygame.image.load(str(cell_file)).convert_alpha()
            def background(_surface,camera):
                f=(round(.2*camera.x),round(.1*camera.y))
                w=(round(2*camera.x),round(2*camera.y))
                game.crt.composite_native(far.subsurface(pygame.Rect(*f,960,540)),(0,0),(480,270))
                game.crt.composite_native(yard.subsurface(pygame.Rect(*w,960,540)),(0,0),(480,270))
                dest=((ANCHOR[0]-2*camera.x)/2,(ANCHOR[1]-2*camera.y)/2)
                game.crt.composite_native(wagon,dest,(84,38))
            scene.room.render_background=background
            def take(name,cx=80):
                scene.camera.x,scene.camera.y=cx,18
                game.render()
                native=args.output_dir/f'{name}_native_960.png'
                review=args.output_dir/f'{name}_review_1920.png'
                pygame.image.save(game.crt.render_surface,str(native))
                pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                return {'camera':[cx,18],'player_rect':list(scene.player.rect),
                        'grounded':scene.player.is_grounded,'health':scene.player.health,
                        'coupler_collected':bool(game.campaign.state.room_flags.get('trench_coupler_collected',False)),
                        'native':native.name,'native_sha256':sha(native),'review':review.name,'review_sha256':sha(review)}
            for cx in (0,80,160): samples.append(take(f'camera_x{cx}_y18',cx))
            # Room entry is a fixture; physical-key events drive the bounded crossing.
            def step(key=None,down=True):
                game.input.begin_frame()
                if key is not None:
                    game.handle_event(pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP,key=key))
                game.update(1/60)
            step(pygame.K_a)
            for _ in range(45):
                if scene.player.x<=200: break
                step()
            step(pygame.K_a,False)
            crossing.append({'tag':'left','sample':take('crossing_left')})
            step(pygame.K_d)
            for target in (225,250,275,290):
                frames=0
                while scene.player.x<target and frames<80 and not scene.player.is_dead:
                    step();frames+=1
                crossing.append({'tag':str(target),'steps':frames,'reached':scene.player.x>=target,'sample':take(f'crossing_{target}')})
            step(pygame.K_d,False)
            info={'source':str(SOURCE),'source_sha256':sha(SOURCE),'source_size':[1862,845],
                  'threshold_for_crop_only':127,'source_strong_bbox_exclusive':list(bbox),
                  'crop_box_exclusive':list(CROP),'crop_size':list(crop.size),
                  'excluded_nonzero_alpha':excluded,'excluded_alpha_over_127':excluded_strong,
                  'resampling':f'nearest neighbor proportional {width}x{height}, integer rounding; no alpha thresholding/painting',
                  'cell':cell_file.name,'cell_sha256':sha(cell_file),'cell_size':list(CELL),
                  'sampled_in_cell':[*position,width,height], 'nonzero_bbox_exclusive':list(a.getbbox()),
                  'strong_bbox_exclusive':list(strong.getbbox()),'bottom_row_75':'substantive alpha present',
                  'native_world_anchor':list(ANCHOR),'world_rect':[196,202,84,38],
                  'initial_collision_query':collision,'far_sha256':sha(FAR),'yard_sha256':sha(YARD),
                  'far_use':'interim fixture, not approved yard sky','mattes':matte_files,'samples':samples,'crossing':crossing,
                  'placement':'native far then salvage v02 then wagon, followed by actual room tiles/objects/actors/weather/HUD',
                  'fixture':'dummy display/audio, temporary save, direct yard_midpoint scene entry, 30 ticks to settle; camera forced for stills; bounded crossing uses actual A/D key events and physics after fixture entry',
                  'limits':'static fixture and short scripted input, not full normal playthrough, native display, visual/motion/cover fairness or art acceptance'}
            (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n')
            print(json.dumps(info,indent=2))
        finally:
            game.close()
            pygame.quit()


if __name__=='__main__':
    main()
