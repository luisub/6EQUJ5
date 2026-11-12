"""PURPOSE: Package a generated Mateo master as a registered static review cell.
CALLED BY: python prepare_pose_v01.py --source MASTER --output-dir NEW_PATH.
HOW TO MODIFY: Preserve source, disclose crop/resampling and refuse existing outputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True); parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--resample', choices=('lanczos','nearest'), default='lanczos')
    parser.add_argument('--foot-shift', type=int, default=0)
    args=parser.parse_args(); original=Image.open(args.source).convert('RGBA'); a=original.getchannel('A')
    core=a.point(lambda v: 255 if v > 127 else 0).getbbox()
    if not core: parser.error('no alpha above 127')
    pad=24; box=(max(0,core[0]-pad),max(0,core[1]-pad),min(original.width,core[2]+pad),min(original.height,core[3]+pad))
    crop=original.crop(box); target_h=59; target_w=round(crop.width*target_h/crop.height)
    if target_w>48: parser.error('proportional pose does not fit cell')
    resampling = Image.Resampling.LANCZOS if args.resample == 'lanczos' else Image.Resampling.NEAREST
    sampled=crop.resize((target_w,target_h),resampling)
    cell=Image.new('RGBA',(48,64),(0,0,0,0)); origin=((48-target_w)//2,62-target_h + args.foot_shift)
    if origin[1] < 0 or origin[1] + target_h > 64: parser.error('pose exceeds 48x64 cell')
    cell.alpha_composite(sampled,origin)
    args.output_dir.mkdir(parents=True,exist_ok=False)
    result=args.output_dir/'mateo_olive_cell_48x64.png'; cell.save(result)
    for name,color in [('dark',(22,28,38,255)),('light',(224,224,215,255))]:
        bg=Image.new('RGBA',cell.size,color); bg.alpha_composite(cell); bg.convert('RGB').resize((384,512),Image.Resampling.NEAREST).save(args.output_dir/f'alpha_on_{name}_8x.png')
    histogram=a.histogram(); inside=crop.getchannel('A').histogram(); outside=sum(histogram[1:])-sum(inside[1:]); final=cell.getchannel('A'); hist=final.histogram()
    info={'source':str(args.source),'source_sha256':sha(args.source),'source_size':list(original.size),'source_alpha_nonzero_bbox':a.getbbox(),
          'source_alpha_over_127_bbox':core,'crop_box_exclusive':box,'crop_margin_source_pixels':pad,
          'nonzero_alpha_pixels_cropped_away':outside,'operation':f'crop by bbox of alpha >127 plus 24 source-pixel margin; retained alpha values preserved through {args.resample} proportional resampling and alpha-composite into transparent cell; no threshold or painting applied to retained pixels',
          'scaled_size':[target_w,target_h],'cell_origin':list(origin),'nominal_pivot':[24,62],'cell_size':[48,64],
          'cell_alpha_nonzero_bbox':final.getbbox(),'cell_alpha_over_127_bbox':final.point(lambda v:255 if v>127 else 0).getbbox(),
          'cell_alpha_counts':{'zero':hist[0],'partial':sum(hist[1:255]),'opaque':hist[255]},'cell_sha256':sha(result),
          'limitations':'static candidate only; partial alpha and crop require independent light/dark edge review, no cleanup, animation or runtime promotion'}
    (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n'); print(json.dumps(info,indent=2))


if __name__=='__main__': main()
