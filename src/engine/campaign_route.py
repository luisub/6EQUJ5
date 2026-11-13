"""PURPOSE: Load authored later-campaign routes and bunker-safe recovery coordinates.
CALLED BY: FieldOpsScene, BossScene, BunkerHubScene and ObjectiveTracker.
HOW TO MODIFY: Preserve save compatibility, validate content paths and keep loading cached.
"""
from functools import lru_cache
import re
from copy import deepcopy
import json
from pathlib import Path
from .alien_journey import room_meta as alien_room_meta

ROUTE_PATH = Path(__file__).resolve().parent.parent / 'data' / 'campaign_route.json'


@lru_cache(maxsize=1)
def route_data():
    try:
        data = json.loads(ROUTE_PATH.read_text(encoding='utf-8'))
        if data.get('schema_version') != 1 or not isinstance(data.get('acts'), dict) or not isinstance(data.get('rooms'), dict):
            return {'acts': {}, 'rooms': {}}
        for room_id, room in data['rooms'].items():
            if not isinstance(room_id, str) or not isinstance(room, dict):
                raise ValueError('invalid route room')
            path = room.get('path')
            if (not isinstance(path, str) or not re.fullmatch(r'act_0[2-5]/[a-z0-9_]+\.json', path)
                    or path.removesuffix('.json').replace('/', '_') != room_id
                    or room.get('act_id') != path.split('/')[0]):
                raise ValueError('invalid route path')
        for act_id, act in data['acts'].items():
            if act_id not in ('act_02', 'act_03', 'act_04', 'act_05') or not isinstance(act, dict):
                raise ValueError('invalid route act')
            for field in ('entry_room', 'boss_room'):
                path = act.get(field)
                if not isinstance(path, str) or path.removesuffix('.json').replace('/', '_') not in data['rooms']:
                    raise ValueError('unknown route act room')
        return data
    except (OSError, ValueError, TypeError, KeyError):
        return {'acts': {}, 'rooms': {}}


def room_meta(room_id):
    return route_data()['rooms'].get(room_id, {}) or alien_room_meta(room_id)


def act_meta(act_id):
    return route_data()['acts'].get(act_id, {})


def unlocked_act(campaign):
    flags = campaign.state.room_flags
    result = None
    for act_id in ('act_02', 'act_03', 'act_04', 'act_05'):
        act = act_meta(act_id)
        if act and flags.get(act.get('unlock_flag'), False):
            result = act_id
        else:
            break
    return result


def saved_route(campaign):
    hub = campaign.state.world_states.get('bunker_hub', {})
    route = hub.get('campaign_route', {}) if isinstance(hub, dict) else {}
    if not isinstance(route, dict) or not isinstance(route.get('room_id'), str):
        return {}
    checkpoint = route.get('checkpoint')
    if checkpoint is not None and not isinstance(checkpoint, str):
        return {}
    return route


def store_route(campaign, room_id, checkpoint=None):
    snapshot = deepcopy(campaign.state.world_states.get('bunker_hub', {}))
    snapshot['campaign_route'] = {'room_id': room_id, 'checkpoint': checkpoint}
    campaign.store_world_state('bunker_hub', snapshot)


def departure(campaign):
    """Resume a known checkpoint in the highest earned act, else its entrance."""
    act_id = unlocked_act(campaign)
    if not act_id:
        return None
    act = act_meta(act_id)
    saved = saved_route(campaign)
    meta = room_meta(saved.get('room_id'))
    if meta.get('act_id') == act_id and meta.get('path'):
        return meta['path'], saved.get('checkpoint'), act_id
    return act['entry_room'], act.get('entry_spawn', 'default'), act_id


def act_for_boss_room(room_id):
    for act_id, act in route_data()['acts'].items():
        if act.get('boss_room', '').removesuffix('.json').replace('/', '_') == room_id:
            return act_id, act
    return None, None
