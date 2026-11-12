"""PURPOSE: Package a larger source-sampled character for a static registered study.
CALLED BY: python prepare_pose_large_v01.py --source MASTER --output-dir NEW_PATH.
HOW TO MODIFY: Preserve the master, disclose the crop and alpha, and refuse overwrites.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--sample-height',type=int,default=74)
    args=parser.parse_args()
    original=Image.open(args.source).convert('RGBA')
    alpha=original.getchannel('A')
    core=alpha.point(lambda value: 255 if value > 127 else 0).getbbox()
    if not core: parser.error('source has no substantial alpha')
    pad=24
    crop_box=(max(0,core[0]-pad),max(0,core[1]-pad),min(original.width,core[2]+pad),min(original.height,core[3]+pad))
    crop=original.crop(crop_box)
    height=args.sample_height
    if height < 1 or height > 80: parser.error('sample height must fit the cell')
    width=round(crop.width * height / crop.height)
    sampled=crop.resize((width,height),Image.Resampling.NEAREST)
    sampled_core=sampled.getchannel('A').point(lambda value: 255 if value > 127 else 0).getbbox()
    if not sampled_core: parser.error('sampled cell has no substantial alpha')
    origin=((60-width)//2,79-sampled_core[3])
    if origin[1] < 0 or origin[1]+height > 80: parser.error('registered subject exceeds cell')
    cell=Image.new('RGBA',(60,80),(0,0,0,0)); cell.alpha_composite(sampled,origin)
    args.output_dir.mkdir(parents=True,exist_ok=False)
    result=args.output_dir/'mateo_large_60x80.png'; cell.save(result)
    for name,color in [('dark',(22,28,38,255)),('light',(224,224,215,255))]:
        bg=Image.new('RGBA',cell.size,color); bg.alpha_composite(cell)
        bg.convert('RGB').resize((360,480),Image.Resampling.NEAREST).save(args.output_dir/f'alpha_{name}_6x.png')
    cell_a=cell.getchannel('A'); histogram=cell_a.histogram()
    removed=sum(alpha.histogram()[1:])-sum(crop.getchannel('A').histogram()[1:])
    info={'source':str(args.source),'source_sha256':sha(args.source),'source_size':list(original.size),
          'source_alpha_over_127_bbox_exclusive':core,'crop_box_exclusive':crop_box,'cropped_faint_nonzero_pixels':removed,
          'transform':'direct crop from original master, alpha>127 bounds plus 24 source pixels, nearest proportional downsampling; no threshold applied to retained alpha or hand painting',
          'sampled_size':[width,height],'sampled_origin_in_cell':list(origin),'cell_size':[60,80],
          'nominal_pivot':[30,78], 'cell_origin_native':[82,366], 'screen_foot':[112,444],
          'alpha_nonzero_bbox_exclusive':cell_a.getbbox(),
          'alpha_over_127_bbox_exclusive':cell_a.point(lambda value:255 if value > 127 else 0).getbbox(),
          'alpha_counts':{'zero':histogram[0],'partial':sum(histogram[1:255]),'opaque':histogram[255],'at_least_240':sum(histogram[240:])},
          'cell_sha256':sha(result),
          'limits':'Static preview only. Existing 16x32 world collider and gameplay attachments are not enlarged; mixed grid, aliasing and alpha need art review.'}
    (args.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n'); print(json.dumps(info,indent=2))


if __name__=='__main__': main()
