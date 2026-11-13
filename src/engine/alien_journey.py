"""PURPOSE: Validate the alien journey and persist earned post-battle information.
CALLED BY: Field, boss, bunker and alien contact scenes.
HOW TO MODIFY: Keep receipts independent from earlier fragment/contact progression.
"""
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import re

PATH = Path(__file__).resolve().parent.parent / 'data' / 'alien_journey.json'


@lru_cache(maxsize=1)
def journey_data():
    """Load a bounded authored route once; reject unknown or escaping paths."""
    try:
        data = json.loads(PATH.read_text(encoding='utf-8'))
        worlds, rooms, finale = data['worlds'], data['rooms'], data['final_earth']
        if (data.get('schema_version') != 1 or not isinstance(worlds, list) or len(worlds) != 11
                or not isinstance(rooms, dict) or not isinstance(finale, dict)):
            raise ValueError('invalid journey shape')
        ids, civs = set(), set()
        for item in worlds:
            if not isinstance(item, dict):
                raise ValueError('invalid world')
            world_id, civ_id = item['id'], item['civ_id']
            if (not re.fullmatch(r'alien_(?:\d{3}|scan_h)', world_id)
                    or not re.fullmatch(r'FASR-(?:\d{3}|SCAN-H)', civ_id)
                    or world_id in ids or civ_id in civs):
                raise ValueError('invalid world or civilization identifier')
            ids.add(world_id); civs.add(civ_id)
            pages = item['contact_pages']
            if (not isinstance(pages, list) or not 1 <= len(pages) <= 4 or
                    any(not isinstance(p, dict) or not isinstance(p.get('title'), str)
                        or not isinstance(p.get('text'), str) for p in pages)):
                raise ValueError('invalid contact pages')
        for i, item in enumerate(worlds):
            expected = worlds[i + 1]['id'] if i + 1 < len(worlds) else None
            if item.get('next_world') != expected:
                raise ValueError('nonlinear journey')
        for room_id, room in rooms.items():
            path = room.get('path') if isinstance(room, dict) else None
            if (not isinstance(path, str) or not re.fullmatch(r'(?:alien_worlds|earth_finale)/[a-z0-9_]+\.json', path)
                    or room_id not in (Path(path).stem, 'earth_finale_' + Path(path).stem)):
                raise ValueError('invalid journey room path')
        for item in worlds:
            for field in ('field_room', 'arena_room'):
                if Path(item[field]).stem not in rooms or rooms[Path(item[field]).stem]['path'] != item[field]:
                    raise ValueError('unknown world room')
        final_path = finale['arena_room']
        if not any(meta['path'] == final_path for meta in rooms.values()):
            raise ValueError('unknown final room')
        return data
    except (OSError, TypeError, ValueError, KeyError, AttributeError):
        return {'worlds': [], 'rooms': {}, 'final_earth': {}}


def world_by_id(world_id):
    return next((w for w in journey_data()['worlds'] if w['id'] == world_id), None)


def room_meta(room_id):
    return journey_data()['rooms'].get(room_id, {})


def world_for_room(room_id):
    for world in journey_data()['worlds']:
        if room_id in (Path(world['field_room']).stem, Path(world['arena_room']).stem):
            return world
    return None


def earth_portal_ready(campaign):
    flags = campaign.state.room_flags
    return bool(flags.get('portal_warden_defeated') or flags.get('core_prime_defeated'))


def ledger(campaign):
    hub = campaign.state.world_states.get('bunker_hub', {})
    value = hub.get('alien_journey', {}) if isinstance(hub, dict) else {}
    if not isinstance(value, dict) or value.get('version') != 1:
        return {}
    world_id, stage, receipts = value.get('world_id'), value.get('stage'), value.get('receipts')
    worlds = journey_data()['worlds']
    if (stage not in ('field', 'guardian', 'contact', 'final', 'complete') or not isinstance(receipts, list)
            or any(not isinstance(x, str) for x in receipts)
            or receipts != [w['civ_id'] for w in worlds[:len(receipts)]]
            or len(receipts) > len(worlds)):
        return {}
    if any(not campaign.state.room_flags.get(w['defeat_flag'], False) for w in worlds[:len(receipts)]):
        return {}
    if stage in ('field', 'guardian', 'contact'):
        if len(receipts) >= len(worlds) or worlds[len(receipts)]['id'] != world_id:
            return {}
    elif len(receipts) != len(worlds) or world_id is not None:
        return {}
    checkpoint = value.get('checkpoint')
    if checkpoint is not None and not isinstance(checkpoint, str):
        return {}
    if 'pending_transit' in value:
        from .galaxy_transit import valid_pending
        if not earth_portal_ready(campaign) or not valid_pending(value['pending_transit'], worlds, receipts, stage, world_id):
            return {}
    return deepcopy(value)


def save_ledger(campaign, value):
    hub = deepcopy(campaign.state.world_states.get('bunker_hub', {}))
    hub['alien_journey'] = deepcopy(value)
    campaign.store_world_state('bunker_hub', hub)


def start_ledger(campaign):
    current = ledger(campaign)
    worlds = journey_data()['worlds']
    hub = campaign.state.world_states.get('bunker_hub', {})
    # Never replace a present but invalid journey snapshot with a new one.
    if current or (isinstance(hub, dict) and 'alien_journey' in hub) or not worlds or not earth_portal_ready(campaign):
        return current
    return {'version': 1, 'world_id': worlds[0]['id'], 'stage': 'field',
            'checkpoint': worlds[0].get('entry_spawn', 'default'), 'receipts': [],
            'pending_transit': {'source': 'earth', 'destination': worlds[0]['id']}}


def record_receipt(campaign, world):
    """Apply authored contact and fragment once, then add the ordered receipt."""
    current = ledger(campaign)
    if current.get('stage') != 'contact' or current.get('world_id') != world['id']:
        return False
    if not campaign.state.room_flags.get(world['defeat_flag'], False):
        return False
    civ = world['civ_id']
    safe_id = civ.lower().replace('-', '_')
    if civ not in campaign.state.contacted_civs:
        campaign.apply_event({'event_id': f'journey_contact_{safe_id}', 'type': 'record_contact',
                              'payload': {'civilization_id': civ}})
    if civ not in campaign.state.extracted_fragments:
        campaign.apply_event({'event_id': f'journey_fragment_{safe_id}',
                              'type': f'grant_fragment_{safe_id}'})
    current['receipts'].append(civ)
    next_id = world.get('next_world')
    current['world_id'] = next_id
    current['stage'] = 'field' if next_id else 'final'
    current['checkpoint'] = world_by_id(next_id).get('entry_spawn', 'default') if next_id else None
    current['pending_transit'] = {'source': world['id'], 'destination': next_id or 'earth'}
    save_ledger(campaign, current)
    return True


def dispatch(machine):
    """Resume the current stage from the bunker or a completed story sequence."""
    from . import config
    current = ledger(machine.campaign)
    if not current:
        return False
    if current.get('pending_transit'):
        machine.change_state(config.STATE_GALAXY_TRANSIT)
        return True
    stage = current['stage']
    if stage == 'contact':
        machine.change_state(config.STATE_ALIEN_CONTACT, world_id=current['world_id'])
        return True
    if stage in ('field', 'guardian'):
        world = world_by_id(current['world_id'])
        if not world:
            return False
        if stage == 'guardian':
            machine.change_state(config.STATE_BOSS_BOUNTY, room=world['arena_room'],
                                 spawn='default', boss_id=world['boss_id'], journey_world=world['id'])
        else:
            machine.change_state(config.STATE_FIELD_OPS, room=world['field_room'],
                                 spawn=current.get('checkpoint') or world.get('entry_spawn', 'default'),
                                 campaign_route=True, journey_world=world['id'])
        return True
    if stage == 'final' and len(current['receipts']) == len(journey_data()['worlds']) == 11:
        final = journey_data()['final_earth']
        machine.change_state(config.STATE_BOSS_BOUNTY, room=final['arena_room'],
                             spawn=final.get('entry_spawn', 'default'),
                             boss_id=final['boss_id'], journey_final=True)
        return True
    return False
