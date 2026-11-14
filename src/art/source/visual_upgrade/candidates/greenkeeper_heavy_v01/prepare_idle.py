from pathlib import Path
from PIL import Image
import hashlib, json
root=Path(__file__).resolve().parent
source=root/'source/idle_generated_master.png'
im=Image.open(source).convert('RGBA')
# Drop weak peripheral alpha specks, then fit original 4:3 source to native cell.
a=im.getchannel('A').point(lambda v: 0 if v < 16 else v)
im.putalpha(a)
im=im.resize((256,192), Image.Resampling.LANCZOS)
# Register bottom of alpha>=16 subject to final row, retaining canvas size.
a=im.getchannel('A'); bounds=a.point(lambda v: 255 if v>=16 else 0).getbbox(); shift=192-bounds[3]
out=Image.new('RGBA',(256,192)); out.alpha_composite(im,(0,shift))
export=root/'exports/idle_256x192.png'; out.save(export)
preview=Path(__file__).resolve().parents[4]/'reviews/visual_upgrade/previews/greenkeeper_heavy_idle_v01'
for name,color in [('dark',(17,26,35,255)),('light',(198,201,184,255))]:
    bg=Image.new('RGBA',out.size,color);bg.alpha_composite(out);bg.convert('RGB').save(preview/f'idle_{name}_native.png')
    bg.resize((512,384),Image.Resampling.NEAREST).convert('RGB').save(preview/f'idle_{name}_2x.png')
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
(root/'provenance.json').write_text(json.dumps({'tool':'image_gen.imagegen','reference':'video_game/assets/sprites/bosses/greenkeeper/idle_1.png','transparent_background':True,'master':str(source.name),'master_size':[1448,1086],'master_sha256':sha(source),'export':'exports/idle_256x192.png','export_sha256':sha(export),'transform':'alpha under 16 zeroed; RGBA Lanczos 1448x1086 to 256x192; translated downward to place alpha>=16 foot at row 191','translated_y':shift,'bounds_before':bounds,'bounds_after':out.getchannel('A').point(lambda v:255 if v>=16 else 0).getbbox(),'status':'idle candidate for review; not installed'},indent=2)+'\n')
print((root/'provenance.json').read_text())
