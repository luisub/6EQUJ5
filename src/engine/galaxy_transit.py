"""PURPOSE: Validate navigation and safely commit inter-world arrivals.
CALLED BY: Alien journey dispatch and the galaxy transit scene.
HOW TO MODIFY: Preserve pending saves and ordered receipts.
"""
from copy import deepcopy
from functools import lru_cache
import json
import math
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / 'data' / 'galaxy_navigation.json'


@lru_cache(maxsize=1)
def navigation_data():
    """Return validated route coordinates, or a safe empty map."""
    try:
        data = json.loads(PATH.read_text(encoding='utf-8'))
        locations = data['locations']
        if data.get('schema_version') != 1 or not isinstance(locations, list) or not locations:
            raise ValueError('invalid location list')
        seen = set()
        for item in locations:
            if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k] for k in ('id', 'name', 'label')):
                raise ValueError('invalid location')
            if item['id'] in seen:
                raise ValueError('duplicate location')
            seen.add(item['id'])
            for key in ('x', 'y'):
                v = item.get(key)
                if type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1:
                    raise ValueError('invalid location coordinate')
        from .alien_journey import journey_data
        if seen != {'earth', *(world['id'] for world in journey_data()['worlds'])}:
            raise ValueError('location roster mismatch')
        return data
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return {'schema_version': 1, 'locations': []}


def locations_by_id():
    return {item['id']: item for item in navigation_data()['locations']}


def display_name(loc_id):
    return locations_by_id().get(loc_id, {}).get('name', 'Unknown destination').title().replace("'S", "'s")


def route_ids():
    """The same ordered route for the opening briefing and every travel leg."""
    from .alien_journey import journey_data
    return ['earth', *(world['id'] for world in journey_data()['worlds']), 'earth']


def map_points(area):
    x, y, width, height = area
    return {key: (x + item['x'] * width, y + item['y'] * height)
            for key, item in locations_by_id().items()}


def leg_position(source, destination, area, progress):
    """A stable curved leg, shared by the briefing, route and moving ship."""
    # Construct the curve in normalized coordinates so the compact opening map
    # follows exactly the same path as the larger travel view.
    points = map_points((0, 0, 1, 1))
    start, end = points[source], points[destination]
    mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = max(0.001, math.hypot(dx, dy))
    direction = 1 if sum(map(ord, source + destination)) % 2 else -1
    bend = min(0.07, length * 0.18) * direction
    control = (mid[0] - dy / length * bend, mid[1] + dx / length * bend)
    t = max(0.0, min(1.0, progress))
    point = tuple((1 - t) ** 2 * start[i] + 2 * (1 - t) * t * control[i] + t * t * end[i]
                  for i in range(2))
    x, y, width, height = area
    return x + point[0] * width, y + point[1] * height


def leg_points(source, destination, area, progress=1.0):
    return [leg_position(source, destination, area, progress * i / 24) for i in range(25)]


def valid_pending(value, worlds, receipts, stage, world_id):
    """Accept only the next legitimate leg given the already-earned ledger."""
    if not isinstance(value, dict) or set(value) != {'source', 'destination'}:
        return False
    if stage == 'field' and not receipts:
        return value == {'source': 'earth', 'destination': worlds[0]['id']} and world_id == worlds[0]['id']
    if not receipts or not worlds:
        return False
    source = worlds[len(receipts) - 1]['id']
    if stage == 'field' and len(receipts) < len(worlds):
        destination = worlds[len(receipts)]['id']
        return world_id == destination and value == {'source': source, 'destination': destination}
    if stage == 'final' and len(receipts) == len(worlds):
        return world_id is None and value == {'source': source, 'destination': 'earth'}
    return False


def arrive(machine):
    """Clear a pending leg only after a durable save; leave it retryable on failure."""
    from .alien_journey import ledger, save_ledger, dispatch
    current = ledger(machine.campaign)
    if not current.get('pending_transit'):
        return False
    prior = deepcopy(current)
    current.pop('pending_transit', None)
    save_ledger(machine.campaign, current)
    if not machine.save_checkpoint():
        save_ledger(machine.campaign, prior)
        return False
    return dispatch(machine)
