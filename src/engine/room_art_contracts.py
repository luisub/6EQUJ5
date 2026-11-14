"""MODULE: video_game/engine/room_art_contracts.py
PURPOSE: Define strict native art-family contracts for existing rooms and prototypes.
CALLED BY: Native room loader and the explicit room-family asset builder.
HOW TO MODIFY: Coordinate schema, ordered layers, prop anchors and backward compatibility.
"""
from types import MappingProxyType
from pathlib import Path

ROOM_ART_FAMILIES = ('ohio_approach_v2', 'ohio_salvage_v1', 'ohio_dish_v1', 'ohio_arena_v1',
                     'ohio_campus_v1')
OPAQUE_BACKDROP_FAMILIES = ('ohio_bunker_v1', 'mandela_annex_v1',
                            'dodleston_relay_v1', 'ehman_1977_v1')

_DIRECTORIES = MappingProxyType({
    'ohio_approach_v2': 'ohio/approach',
    'ohio_salvage_v1': 'ohio/salvage_yard',
    'ohio_dish_v1': 'ohio/dish',
    'ohio_arena_v1': 'ohio/arena',
    'ohio_campus_v1': 'ohio/campus',
    'ohio_bunker_v1': 'ohio/bunker',
    'mandela_annex_v1': 'mandela_annex',
    'dodleston_relay_v1': 'dodleston_relay',
    'ehman_1977_v1': 'ehman_1977',
})
SHARED_FAR_FAMILIES = frozenset({
    'ohio_approach_v2', 'ohio_salvage_v1', 'ohio_dish_v1', 'ohio_arena_v1',
})
SHARED_FAR_FILE = '../shared/far.png'
SHARED_FAR_PATH = Path('environments/ohio/shared/far.png')


def family_directory(family_id):
    """Resolve stable content IDs to the single canonical location directory."""
    try:
        return Path('environments') / _DIRECTORIES[family_id]
    except (KeyError, TypeError) as exc:
        raise ValueError(f'Unknown room-art family: {family_id}') from exc


def component_path(family_id, filename):
    """Resolve a local filename or the explicitly shared Ohio far plane."""
    directory = family_directory(family_id)
    if family_id in SHARED_FAR_FAMILIES and filename == SHARED_FAR_FILE:
        return SHARED_FAR_PATH
    if (not isinstance(filename, str) or not filename
            or Path(filename).name != filename or filename in {'.', '..'}):
        raise ValueError(f'Unsafe room-art filename: {filename}')
    return directory / filename

_BACKDROP_SPECS = MappingProxyType({
    'ohio_bunker_v1': ('bunker_hub', (480, 270)),
    'mandela_annex_v1': ('act_01_mandela_test', (480, 288)),
    'dodleston_relay_v1': ('act_04_dodleston_relay', (480, 288)),
    'ehman_1977_v1': ('flashback_ehman_1977', (480, 288)),
})

# The source descriptors are immutable; callers receive freshly constructed lists/dicts.
_SPECS = MappingProxyType({
    'ohio_approach_v2': ('act_01_approach', (960, 288), (
        ('equipment', 'equipment.png', (112, 64), (804, 208)),)),
    'ohio_salvage_v1': ('act_01_salvage_yard', (640, 288), (
        ('wagon', 'wagon.png', (168, 76), (196, 202)),)),
    'ohio_dish_v1': ('act_01_dish_catwalk', (640, 288), ()),
    'ohio_arena_v1': ('act_01_greenkeeper_arena', (640, 288), ()),
    'ohio_campus_v1': ('act_01_ohio_campus', (1280, 288), ()),
})


def _layer(identifier, filename, dimensions, parallax, rounding, alpha):
    return {'id': identifier, 'file': filename, 'dimensions': dimensions,
            'parallax': parallax, 'rounding': rounding, 'alpha': alpha,
            'repeat': False, 'origin': [0, 0]}


def _prop(identifier, filename, dimensions, origin):
    return {'id': identifier, 'file': filename, 'dimensions': list(dimensions),
            'origin_world': list(origin), 'alpha': 'straight',
            'placement': 'after_world_before_tiles', 'collision': 'none'}


def manifest_template(family_id):
    """Return a fresh serializable template; caller fills each record's sha256."""
    try:
        room_id, world, props = _SPECS[family_id]
    except (KeyError, TypeError) as exc:
        raise ValueError(f'Unknown room-art family: {family_id}') from exc
    width = world[0] * 2
    return {'schema_version': 2, 'room_id': room_id, 'density': 2,
            'viewport': [480, 270], 'world': list(world),
            'layers': [
                _layer('far', SHARED_FAR_FILE if family_id in SHARED_FAR_FAMILIES else 'far.png',
                       [1152, 544], [0.1, 0.05], 'native_nearest', 'opaque'),
                _layer('world', 'world.png', [width, 576], [1, 1], 'logical_nearest', 'straight')],
            'props': [_prop(*prop) for prop in props]}


def backdrop_manifest_template(family_id):
    """Return a fresh schema-3 template for a specifically allowlisted backdrop."""
    try:
        room_id, world = _BACKDROP_SPECS[family_id]
    except (KeyError, TypeError) as exc:
        raise ValueError(f'Unknown opaque backdrop family: {family_id}') from exc
    width, height = (dimension * 2 for dimension in world)
    return {'schema_version': 3, 'kind': 'opaque_backdrop', 'room_id': room_id,
            'density': 2, 'viewport': [480, 270], 'world': list(world),
            'backdrop': {'id': 'backdrop', 'file': 'background.png',
                         'dimensions': [width, height], 'alpha': 'opaque', 'origin': [0, 0],
                         'rounding': 'logical_nearest', 'repeat': False}}
