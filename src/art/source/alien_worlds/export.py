"""Export reviewed world masters without changing their artwork.

Run from the repository root with .venv/bin/python
src/art/source/alien_worlds/export.py <civilization directory>.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageOps


def export(directory: Path):
    record = json.loads((directory / 'provenance.json').read_text())
    for kind, dimensions in [('background', (1920, 540)), ('guardian', (256, 192))]:
        master = directory / f'{kind}_master.png'
        target = directory / ('background.png' if kind == 'background' else 'body.png')
        with Image.open(master) as image:
            if kind == 'background':
                result = ImageOps.fit(image.convert('RGB'), dimensions,
                                      method=Image.Resampling.LANCZOS, centering=(0.5, 0.8))
            else:
                image = image.convert('RGBA')
                # Ignore near-transparent generation residue when anchoring feet.
                bounds = image.getchannel('A').point(lambda value: 255 if value >= 64 else 0).getbbox()
                if not bounds:
                    raise ValueError('Guardian master is empty')
                sprite = image.crop(bounds)
                sprite.thumbnail((248, 184), Image.Resampling.LANCZOS)
                result = Image.new('RGBA', dimensions, (0, 0, 0, 0))
                result.alpha_composite(sprite, ((256 - sprite.width) // 2, 192 - sprite.height))
            result.save(target, optimize=True)
        record[kind]['master_sha256'] = hashlib.sha256(master.read_bytes()).hexdigest()
        record[kind]['export_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        record[kind]['dimensions'] = list(dimensions)
    (directory / 'provenance.json').write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    export(parser.parse_args().directory)
