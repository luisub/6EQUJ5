"""PURPOSE: Produce disposable, registered two-plane approach-art review fixtures.
CALLED BY: From repository root with dummy SDL, --source, --transform and --output-dir NEW_DIR.
HOW TO MODIFY: Preserve origin disclosure, temporary saves, exact hashes and fresh-output guard.
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

FAR = Path('video_game/art/reviews/visual_upgrade/previews/approach_far_registration_v01/far_native_1152x544.png')
TARGET = (1920, 576)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform_image(source, mode):
    width, height = source.size
    if mode == 'exact':
        if width * TARGET[1] != height * TARGET[0]:
            raise ValueError('exact requires a 10:3 source aspect; choose a disclosed crop or padding')
        output = source.resize(TARGET, Image.Resampling.LANCZOS)
        return output, {'mode':mode,'scaled_size':list(TARGET),'crop':None,'padding':None}
    ratio = (min if mode == 'contain-top-left' else max)(TARGET[0] / width, TARGET[1] / height)
    scaled_size = (max(1, round(width * ratio)), max(1, round(height * ratio)))
    scaled = source.resize(scaled_size, Image.Resampling.LANCZOS)
    if mode == 'contain-top-left':
        out = Image.new('RGBA', TARGET, (0, 0, 0, 0))
        out.paste(scaled, (0, 0))
        return out, {'mode':mode,'scaled_size':list(scaled_size), 'crop':None,
                     'padding':[0,0,TARGET[0]-scaled_size[0],TARGET[1]-scaled_size[1]]}
    if scaled_size[0] < TARGET[0] or scaled_size[1] < TARGET[1]:
        raise ValueError('rounded proportional crop does not cover target')
    return scaled.crop((0,0,*TARGET)), {'mode':mode,'scaled_size':list(scaled_size),
                                      'crop':[0,0,*TARGET],'padding':None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--transform',required=True,choices=('exact','crop-top-left','contain-top-left'))
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    with Image.open(args.source) as src:
        if src.mode != 'RGBA':
            raise ValueError('source must be an RGBA master; no silent conversion')
        source_size=src.size
        architecture, mapping=transform_image(src,args.transform)
    with Image.open(FAR) as far:
        if far.size != (1152,544):
            raise ValueError('far plate must be 1152x544')
    args.output_dir.mkdir(parents=True,exist_ok=False)
    arch_path=args.output_dir/'architecture_rgba_1920x576.png'
    architecture.save(arch_path)
    results=[]
    with tempfile.TemporaryDirectory(prefix='6equj5-architecture-v02-') as tmp:
        pygame.init()
        pygame.display.set_mode((960,540))
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
        try:
            game.start_new_game()
            game.change_state(config.STATE_FIELD_OPS)
            scene=game.current_scene
            for _ in range(30):
                game.update(1/60)
            far_surf=pygame.image.load(str(FAR)).convert_alpha()
            arch_surf=pygame.image.load(str(arch_path)).convert_alpha()
            def fixture_background(surface,camera):
                far_origin=(round(2*.1*camera.x),round(2*.05*camera.y))
                arch_origin=(round(2*camera.x),round(2*camera.y))
                game.crt.composite_native(far_surf.subsurface(pygame.Rect(*far_origin,960,540)),(0,0),(480,270))
                game.crt.composite_native(arch_surf.subsurface(pygame.Rect(*arch_origin,960,540)),(0,0),(480,270))
            scene.room.render_background=fixture_background
            for cx,spawn in ((0,'bunker_exit'),(240,'approach_checkpoint'),(480,'dish_perimeter')):
                point=scene.room.spawns[spawn]
                scene.player.x,scene.player.y=point.x,point.y
                scene.player.facing=point.facing
                scene.player.vx=scene.player.vy=0
                scene.player.is_grounded=False
                for _ in range(30):
                    game.update(1/60)
                for cy in (0,18):
                    scene.camera.x,scene.camera.y=cx,cy
                    game.render()
                    native=args.output_dir/f'camera_x{cx}_y{cy}_native_960.png'
                    review=args.output_dir/f'camera_x{cx}_y{cy}_review_1920.png'
                    pygame.image.save(game.crt.render_surface,str(native))
                    pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                    results.append({'camera':[cx,cy],'far_crop_native':[round(.2*cx),round(.1*cy),960,540],
                                    'architecture_crop_native':[2*cx,2*cy,960,540],
                                    'fixture_spawn':spawn,'player_rect':list(scene.player.rect),
                                    'native':native.name,'native_sha256':digest(native),
                                    'review':review.name,'review_sha256':digest(review)})
            info={'architecture_source':str(args.source),'architecture_source_sha256':digest(args.source),
                  'architecture_source_size':list(source_size),'architecture_source_mode':'RGBA',
                  'architecture_export':arch_path.name,'architecture_export_sha256':digest(arch_path),
                  'export_size':list(TARGET),'transform':mapping,'resampling':'Lanczos; no masks, painting, cleanup or manual alpha changes',
                  'origin':'source top-left mapped to world/native (0,0); crop or transparent padding only at right and/or bottom',
                  'far_source':str(FAR),'far_source_sha256':digest(FAR),
                  'composition':'fixture-local render_background callback, native far then architecture behind actual room tiles/objects, runtime actors/effects/weather/HUD',
                  'fixture':'dummy display/audio; temporary save; direct field entry and 30 ticks; each authored spawn teleported then settled 30 ticks; camera forced x0/240/480 and y0/18',
                  'outputs':results,'limits':'static fixture; not normal-input motion, native-display, performance, alignment or art-gate acceptance'}
            (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n')
            print(json.dumps(info,indent=2))
        finally:
            game.close()
            pygame.quit()


if __name__=='__main__':
    main()
