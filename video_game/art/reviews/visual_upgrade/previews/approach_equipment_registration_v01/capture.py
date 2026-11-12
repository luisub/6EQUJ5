"""PURPOSE: Package and register a disposable approach equipment review fixture.
CALLED BY: Run from repository root with dummy SDL and --output-dir NEW_DIR.
HOW TO MODIFY: Preserve original pixels, placement, temporary saves, hashes and fresh-output guard.
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

SOURCE=Path('video_game/art/source/visual_upgrade/candidates/approach_equipment_v01/source/approach_equipment_generated_master.png')
FAR=Path('video_game/art/reviews/visual_upgrade/previews/approach_far_registration_v01/far_native_1152x544.png')
ARCH=Path('video_game/art/reviews/visual_upgrade/previews/architecture_registration_research_v02/crop_top_left_v01/architecture_rgba_1920x576.png')
CROP=(348,440,1295,909)
CELL=(112,64)
NATIVE_WORLD_ANCHOR=(1608,416)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    with Image.open(SOURCE) as src:
        if src.mode!='RGBA' or src.size!=(1659,948):
            raise ValueError('expected unmodified 1659x948 RGBA source')
        a=src.getchannel('A')
        strong=a.point(lambda n:255 if n>127 else 0)
        strong_bbox=strong.getbbox()
        crop=src.crop(CROP)
        source_hist=a.histogram()
        inside_hist=a.crop(CROP).histogram()
        excluded_nonzero=sum(source_hist[1:])-sum(inside_hist[1:])
        excluded_strong=sum(source_hist[128:])-sum(inside_hist[128:])
        scaled_w=round(crop.width*36/crop.height)
        resized=crop.resize((scaled_w,36),Image.Resampling.NEAREST)
    cell=Image.new('RGBA',CELL,(0,0,0,0))
    position=((CELL[0]-resized.width)//2,28)
    cell.paste(resized,position)
    alpha=cell.getchannel('A')
    strong_cell=alpha.point(lambda n:255 if n>127 else 0)
    if alpha.crop((0,0,112,28)).getbbox() is not None:
        raise ValueError('top 28 rows must be transparent')
    if strong_cell.getbbox() is None or strong_cell.getbbox()[3]!=64:
        raise ValueError('substantive equipment must contact bottom row')
    args.output_dir.mkdir(parents=True,exist_ok=False)
    cell_path=args.output_dir/'equipment_112x64_rgba.png'
    cell.save(cell_path)
    mats=[]
    for name,color in [('light',(224,220,206,255)),('dark',(12,18,28,255))]:
        matte=Image.new('RGBA',CELL,color)
        matte=Image.alpha_composite(matte,cell).convert('RGB')
        path=args.output_dir/f'equipment_{name}_matte_4x.png'
        matte.resize((448,256),Image.Resampling.NEAREST).save(path)
        mats.append({'file':path.name,'sha256':sha(path),'color':list(color)})
    with tempfile.TemporaryDirectory(prefix='6equj5-equipment-preview-') as tmp:
        pygame.init()
        pygame.display.set_mode((960,540))
        game=GameStateMachine(CRTRenderer(scale=1),save_store=SaveStore(tmp),settings_store=SettingsStore(tmp))
        try:
            game.start_new_game()
            game.change_state(config.STATE_FIELD_OPS)
            scene=game.current_scene
            for _ in range(30): game.update(1/60)
            point=scene.room.spawns['dish_perimeter']
            scene.player.x,scene.player.y=point.x,point.y
            scene.player.facing=point.facing
            scene.player.vx=scene.player.vy=0
            scene.player.is_grounded=False
            for _ in range(30): game.update(1/60)
            far=pygame.image.load(str(FAR)).convert_alpha()
            architecture=pygame.image.load(str(ARCH)).convert_alpha()
            equipment=pygame.image.load(str(cell_path)).convert_alpha()
            def background(surface,camera):
                f=(round(.2*camera.x),round(.1*camera.y))
                w=(round(2*camera.x),round(2*camera.y))
                game.crt.composite_native(far.subsurface(pygame.Rect(*f,960,540)),(0,0),(480,270))
                game.crt.composite_native(architecture.subsurface(pygame.Rect(*w,960,540)),(0,0),(480,270))
                dest=((NATIVE_WORLD_ANCHOR[0]-2*camera.x)/2,(NATIVE_WORLD_ANCHOR[1]-2*camera.y)/2)
                game.crt.composite_native(equipment,dest,(56,32))
            scene.room.render_background=background
            captures=[]
            for cy in (0,18):
                scene.camera.x,scene.camera.y=480,cy
                game.render()
                native=args.output_dir/f'camera_x480_y{cy}_native_960.png'
                review=args.output_dir/f'camera_x480_y{cy}_review_1920.png'
                pygame.image.save(game.crt.render_surface,str(native))
                pygame.image.save(pygame.transform.scale(game.crt.render_surface,(1920,1080)),str(review))
                captures.append({'camera':[480,cy],'native':native.name,'native_sha256':sha(native),
                                 'review':review.name,'review_sha256':sha(review),
                                 'cell_screen_native_origin':[648,416-2*cy], 'player_rect_world':list(scene.player.rect)})
            info={'source':str(SOURCE),'source_sha256':sha(SOURCE),'source_size':[1659,948],
                  'threshold_for_bounds_only':127,'strong_bbox_exclusive':list(strong_bbox),
                  'crop_box_exclusive':list(CROP),'crop_size':[crop.width,crop.height],
                  'excluded_source_nonzero_alpha_pixels':excluded_nonzero,'excluded_source_alpha_over_127_pixels':excluded_strong,
                  'resampling':'nearest neighbor crop to 73x36 (proportional rounding), no thresholding or alpha painting',
                  'cell':cell_path.name,'cell_sha256':sha(cell_path),'cell_size':list(CELL),'crop_in_cell':[*position,resized.width,resized.height],
                  'nonzero_alpha_bbox':list(alpha.getbbox()),'alpha_over_127_bbox':list(strong_cell.getbbox()),
                  'top_28_rows':'alpha zero','bottom_row':'alpha >127 present',
                  'native_world_anchor':list(NATIVE_WORLD_ANCHOR),'logical_world_anchor':[804,208],
                  'placement':'native equipment after far and architecture, before actual runtime tiles/objects/actors/weather/HUD',
                  'far_sha256':sha(FAR),'architecture_sha256':sha(ARCH),'matte_views':mats,'captures':captures,
                  'fixture':'dummy SDL, temporary save, direct field entry, 30 initial ticks; teleport to dish_perimeter then settle 30 ticks; camera forced x480 y0/18',
                  'limitations':'decorative study only; no runtime promotion, real input, moving camera, collision/cover fairness, native display or acceptance'}
            (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n')
            print(json.dumps(info,indent=2))
        finally:
            game.close()
            pygame.quit()


if __name__=='__main__':
    main()
