"""PURPOSE: Produce a measured static candidate and diagnostic target overlays.
CALLED BY: From repo root with --output-dir NEW_DIR.
HOW TO MODIFY: Preserve source provenance, proportional transform and unmodified alpha.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

SOURCE=Path('video_game/art/source/visual_upgrade/candidates/mateo_olive_recoil_v02/source/mateo_olive_recoil_generated_master.png')
EXPECTED='281cb71983ab01048ac3b3e01380a61873677969b6e0a79f6faf642f6a92ed91'
CROP=(52,145,997,1405)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',required=True,type=Path)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=False)
    if sha(SOURCE)!=EXPECTED:raise ValueError('Source hash mismatch')
    with Image.open(SOURCE) as src:
        if src.mode!='RGBA' or src.size!=(1086,1448):raise ValueError('Unexpected master')
        alpha=src.getchannel('A')
        source_nonzero=alpha.getbbox()
        strong=alpha.point(lambda v:255 if v>127 else 0)
        source_strong=strong.getbbox()
        original_nonzero=sum(alpha.histogram()[1:])
        original_strong=sum(alpha.histogram()[128:])
        crop=src.crop(CROP)
        hist=crop.getchannel('A').histogram()
        retained_nonzero=sum(hist[1:]);retained_strong=sum(hist[128:])
        cell=crop.resize((60,80),Image.Resampling.NEAREST)
        path=a.output_dir/'mateo_olive_recoil_60x80.png'
        cell.save(path)
    alpha=cell.getchannel('A')
    hist=alpha.histogram()
    cell_strong=alpha.point(lambda v:255 if v>127 else 0).getbbox()
    for facing in ('right','left'):
        pose=cell if facing=='right' else cell.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        targets={'foot':(30,78),'hand':(46,36),'muzzle':(58,33)} if facing=='right' else {'foot':(29,78),'hand':(13,36),'muzzle':(1,33)}
        for background,color in [('light',(220,220,210,255)),('dark',(20,25,31,255))]:
            image=Image.new('RGBA',(60,80),color)
            image.alpha_composite(pose)
            image.resize((600,800),Image.Resampling.NEAREST).convert('RGB').save(a.output_dir/f'{facing}_{background}_10x.png')
            marked=image.resize((600,800),Image.Resampling.NEAREST).convert('RGB')
            draw=ImageDraw.Draw(marked)
            for name,(x,y) in targets.items():
                rgb={'foot':(255,240,0),'hand':(0,255,255),'muzzle':(255,60,60)}[name]
                xx,yy=x*10+5,y*10+5
                draw.line((xx-8,yy,xx+8,yy),fill=rgb,width=2)
                draw.line((xx,yy-8,xx,yy+8),fill=rgb,width=2)
            marked.save(a.output_dir/f'{facing}_{background}_targets_10x.png')
    info={'source':str(SOURCE),'source_sha256':sha(SOURCE),'source_size':[1086,1448],
          'source_nonzero_alpha_bbox_exclusive':source_nonzero,'source_alpha_gt127_bbox_exclusive':source_strong,
          'crop_box_exclusive':CROP,'crop_size':[945,1260],
          'transform':'Proportional direct source crop 945x1260 to 60x80 by nearest sampling, ratio 4/63; transparent source alpha retained, no distortion, mask, painting or creative edit.',
          'source_pixels_excluded':{'nonzero_alpha':original_nonzero-retained_nonzero,'alpha_gt127':original_strong-retained_strong},
          'cell':path.name,'cell_sha256':sha(path),'cell_alpha_nonzero_bbox_exclusive':alpha.getbbox(),'cell_alpha_gt127_bbox_exclusive':cell_strong,
          'cell_alpha_counts':{'zero':hist[0],'partial':sum(hist[1:255]),'opaque':hist[255]},
          'right_target_points_cell':{'foot':[30,78],'hand':[46,36],'muzzle':[58,33]},
          'left_target_points_cell':{'foot':[29,78],'hand':[13,36],'muzzle':[1,33]},
          'target_overlay_legend':'yellow=nominal foot; cyan=existing recoil hand; red=existing recoil muzzle; overlays diagnostic only',
          'limits':'Single static pose, manual visual measurements pending; no animation, gameplay, human, performance or art-gate acceptance.'}
    (a.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info,indent=2))

if __name__=='__main__':main()
