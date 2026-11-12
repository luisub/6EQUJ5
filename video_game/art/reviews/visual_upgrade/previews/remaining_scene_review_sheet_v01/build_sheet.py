"""PURPOSE: Place four unchanged native scene captures on a labeled review sheet.
CALLED BY: Run from repository root with --output-dir NEW_DIR.
HOW TO MODIFY: Use actual configured-root fixtures, preserve full native cells and source hashes.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE=Path('video_game/art/reviews/visual_upgrade/previews')
SOURCES=[
    ('Bunker: terminal station',BASE/'bunker_installed_v02/terminal_native_960.png'),
    ('Annex: 2029, camera y18',BASE/'annex_installed_v01/2029_CORE_y18_native_960.png'),
    ('Relay: 2029',BASE/'relay_installed_v01/2029_native_960.png'),
    ('1977 observatory: entry',BASE/'ehman_installed_v01/entry_y18_native_960.png'),
]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',required=True,type=Path)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=False)
    width,height=1920,1176
    sheet=Image.new('RGB',(width,height),(18,23,30))
    draw=ImageDraw.Draw(sheet)
    try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
    except OSError:font=ImageFont.load_default()
    draw.text((8,7),'ACTUAL CONFIGURED-ROOT CAPTURES — STATIC DUMMY-DRIVER FIXTURES; NOT A GAMEPLAY RECORD',fill=(240,240,230),font=font)
    records=[]
    for index,(name,path) in enumerate(SOURCES):
        x=(index%2)*960;y=48+(index//2)*564
        with Image.open(path) as image:
            if image.size!=(960,540):raise ValueError(f'{path}: {image.size}')
            draw.text((x+8,y+3),name,fill=(235,226,190),font=font)
            sheet.paste(image.convert('RGB'),(x,y+24))
        records.append({'label':name,'source':str(path),'sha256':sha(path),'source_size':[960,540],'sheet_rect':[x,y+24,960,540]})
    result=a.output_dir/'remaining_scenes_native_sheet.png'
    sheet.save(result)
    info={'sheet':result.name,'sheet_sha256':sha(result),'sheet_size':[width,height],
          'composition':'Four unchanged 960x540 source pixels pasted 1:1 with external labels, no resampling or image editing.',
          'sources':records,'limits':'Actual configured asset-root captures with dummy SDL and scripted or injected prerequisites; static fixtures, not human gameplay, normal progression, real-window, performance or art-gate evidence. See each original directory context.json.'}
    (a.output_dir/'context.json').write_text(json.dumps(info,indent=2)+'\n')
    lines=['# Remaining scene native review sheet','','Four 960×540 captures from the actual configured asset root, placed at 1:1 with labels. Static dummy-driver fixtures; not a gameplay recording or complete review. See each original context for scripted inputs and injected prerequisites.','','[Review sheet](remaining_scenes_native_sheet.png)','','Originals:','']
    for name,path in SOURCES:
        relative=Path('../..')/path.relative_to(BASE)
        lines.append(f'- [{name}]({relative.as_posix()})')
    (a.output_dir/'README.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(info,indent=2))

if __name__=='__main__':main()
