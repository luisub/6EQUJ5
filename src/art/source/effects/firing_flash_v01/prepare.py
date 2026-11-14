"""PURPOSE: Inspect transparent muzzle-flash source at intended native dimensions.
CALLED BY: Run from repo root with --output-dir NEW_DIR.
HOW TO MODIFY: Preserve source hash, full-canvas nearest sampling and unmodified alpha.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

SOURCE = Path(__file__).resolve().parent / 'source/firing_flash_generated_master.png'
EXPECTED='e572751bb235e9dc92a80cbbb3ceb9428dffacedea9e1f7ff74bb6b861441b8f'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def stats(alpha):
    h=alpha.histogram()
    return {'zero':h[0],'partial':sum(h[1:255]),'opaque':h[255],
            'bbox_nonzero_exclusive':alpha.getbbox(),
            'bbox_gt127_exclusive':alpha.point(lambda a:255 if a>127 else 0).getbbox()}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True,type=Path);args=p.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    if sha(SOURCE)!=EXPECTED:raise ValueError('Source SHA mismatch')
    with Image.open(SOURCE) as src:
        if src.mode!='RGBA' or src.size!=(1774,887):raise ValueError('Unexpected source dimensions or mode')
        srcstats=stats(src.getchannel('A'))
        cell=src.resize((64,32),Image.Resampling.NEAREST)
    export=args.output_dir/'firing_flash_64x32.png';cell.save(export)
    for facing in ('right','left'):
        pose=cell if facing=='right' else cell.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        px=12 if facing=='right' else 51
        for label,bg in (('light',(224,224,214,255)),('dark',(18,24,32,255))):
            comp=Image.new('RGBA',(64,32),bg);comp.alpha_composite(pose)
            zoom=comp.resize((640,320),Image.Resampling.NEAREST).convert('RGB')
            zoom.save(args.output_dir/f'{facing}_{label}_10x.png')
            draw=ImageDraw.Draw(zoom);x=px*10+5;y=16*10+5
            draw.line((x-8,y,x+8,y),fill=(255,70,70),width=2);draw.line((x,y-8,x,y+8),fill=(255,70,70),width=2)
            zoom.save(args.output_dir/f'{facing}_{label}_pivot_10x.png')
    info={'source':str(SOURCE),'source_size':[1774,887],'source_mode':'RGBA','source_sha256':sha(SOURCE),'source_alpha':srcstats,
          'export':export.name,'export_sha256':sha(export),'export_size':[64,32],'export_alpha':stats(cell.getchannel('A')),
          'transform':'Full 1774x887 canvas nearest sampled to 64x32, exact 2:1 aspect; no crop, thresholds, masks, alpha edits or painting.',
          'right_pivot':[12,16],'left_mirrored_pivot':[51,16],
          'limits':'Static source/alpha inspection only; no actual-room timing, light response, runtime installation or production acceptance.'}
    (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info,indent=2))

if __name__=='__main__':main()
