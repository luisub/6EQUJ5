"""
MODULE: video_game/engine/campaign.py
PURPOSE: Own validated campaign state and apply idempotent data-defined events.
CALLED BY: config.default_campaign_state and the game state machine.
HOW TO MODIFY: Define stable IDs and rewards in campaign.json; validate a staged
  state before commit and keep development fixtures separate from new games.
"""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, fields
import json
from pathlib import Path
import re
from typing import NotRequired, TypedDict
from uuid import uuid4


CAMPAIGN_FILE = Path(__file__).resolve().parent.parent / "data" / "campaign.json"
IDENTIFIER = re.compile(r"^[A-Za-z0-9_.:-]+$")
PROGRESSION_FIELDS = {
    "contacted_civs": "civ_ids",
    "extracted_fragments": "fragment_ids",
    "unlocked_weapons": "weapon_ids",
    "unlocked_abilities": "ability_ids",
}


class CampaignEvent(TypedDict):
    """A uniquely identified, content-defined campaign event."""

    event_id: str
    type: str
    payload: NotRequired[dict]


@dataclass(frozen=True)
class CampaignState:
    """A detached snapshot; mutations of nested values never change the owner."""

    schema_version: int
    save_id: str
    current_act: str
    current_room: str
    checkpoint_id: str
    timeline_mode: str
    room_flags: dict
    inventory: dict
    contacted_civs: list
    extracted_fragments: list
    validation_records: list
    unlocked_weapons: list
    unlocked_abilities: list
    active_weapon: str
    meters: dict
    choices: dict
    applied_event_ids: list
    completed_event_types: list
    world_states: dict

    def to_dict(self):
        return {field.name: deepcopy(getattr(self, field.name)) for field in fields(self)}


def load_campaign_data(path=CAMPAIGN_FILE):
    """Load a fresh copy of the content definitions, with no Pygame dependency."""
    with Path(path).open(encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported campaign data schema")
    return data


def _identifier(value, label):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid {label}: {value!r}")


def _unique_ids(values, allowed, label):
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise ValueError(f"{label} must be a list of IDs")
    if len(values) != len(set(values)) or not set(values).issubset(allowed):
        raise ValueError(f"Invalid or repeated {label}")


def _validation_record(record, data):
    required = {"id", "scenario_id", "scenario_version", "claim_id", "observations", "result",
                "confidence", "claim_tier", "source_references", "deployment_decision"}
    if (not isinstance(record, dict) or set(record) != required
            or not isinstance(record["id"], str) or record["id"] not in data["validation_ids"]):
        raise ValueError("Invalid validation record")
    for key in ("scenario_id", "claim_id"):
        _identifier(record[key], key)
    if type(record["scenario_version"]) is not int or record["scenario_version"] < 1:
        raise ValueError("Invalid scenario version")
    scenario = data["validation_scenarios"].get(record["scenario_id"])
    if (not isinstance(scenario, dict) or record["scenario_version"] not in scenario.get("versions", [])
            or record["claim_id"] not in scenario.get("claim_ids", [])):
        raise ValueError("Unknown validation scenario, version or claim")
    if not isinstance(record["observations"], list) or not all(isinstance(v, str) for v in record["observations"]):
        raise ValueError("Invalid validation observations")
    if not isinstance(record["source_references"], list) or not all(isinstance(v, str) for v in record["source_references"]):
        raise ValueError("Invalid validation sources")
    if type(record["confidence"]) is not int or not 0 <= record["confidence"] <= 100:
        raise ValueError("Invalid validation confidence")
    if record["claim_tier"] not in ("established", "plausible", "speculative"):
        raise ValueError("Invalid claim tier")
    for key in ("result", "deployment_decision"):
        _identifier(record[key], key)


def validate_state(state, data):
    """Reject inconsistent, unknown or non-JSON state without modifying it."""
    if not isinstance(state, dict) or set(state) != {field.name for field in fields(CampaignState)}:
        raise ValueError("Campaign state fields do not match schema")
    if type(state["schema_version"]) is not int or state["schema_version"] != 1:
        raise ValueError("Unsupported campaign state schema")
    _identifier(state["save_id"], "save ID")
    act = state["current_act"]
    room = state["current_room"]
    if (not isinstance(act, str) or not isinstance(room, str) or act not in data["acts"]
            or room not in data["rooms"] or data["rooms"][room]["act_id"] != act):
        raise ValueError("Invalid act or room ID")
    if state["checkpoint_id"] not in data["rooms"][room]["checkpoints"]:
        raise ValueError("Invalid checkpoint ID")
    if state["timeline_mode"] not in data["timeline_ids"]:
        raise ValueError("Invalid timeline ID")
    flags = state["room_flags"]
    if not isinstance(flags, dict) or not set(flags).issubset(data["flag_ids"]) or any(type(v) is not bool for v in flags.values()):
        raise ValueError("Invalid room flags")
    inventory = state["inventory"]
    if not isinstance(inventory, dict) or not set(inventory).issubset(data["item_ids"]) or any(type(v) is not int or v < 0 for v in inventory.values()):
        raise ValueError("Invalid inventory")
    for field, registry in PROGRESSION_FIELDS.items():
        _unique_ids(state[field], set(data[registry]), field)
    for fragment in state["extracted_fragments"]:
        if data["fragment_sources"].get(fragment) not in state["contacted_civs"]:
            raise ValueError(f"Fragment lacks required contact: {fragment}")
    if state["active_weapon"] not in state["unlocked_weapons"]:
        raise ValueError("Active weapon must be unlocked")
    records = state["validation_records"]
    if not isinstance(records, list):
        raise ValueError("Validation records must be a list")
    for record in records:
        _validation_record(record, data)
    if len({(record["id"], record["scenario_id"]) for record in records}) != len(records):
        raise ValueError("Duplicate validation record")
    for record in records:
        if data["validation_sources"].get(record["id"]) not in state["extracted_fragments"]:
            raise ValueError(f"Validation lacks required fragment: {record['id']}")
    meters = state["meters"]
    if not isinstance(meters, dict) or set(meters) != set(data["meters"]) or any(type(v) is not int or not 0 <= v <= 100 for v in meters.values()):
        raise ValueError("Invalid campaign meters")
    choices = state["choices"]
    worlds = state["world_states"]
    if not isinstance(worlds, dict) or not set(worlds).issubset(data["rooms"]):
        raise ValueError("Invalid world-state rooms")
    if any(not isinstance(value, dict) for value in worlds.values()):
        raise ValueError("World states must be objects")
    if not isinstance(choices, dict) or not set(choices).issubset(data["choice_ids"]):
        raise ValueError("Choices must contain registered IDs")
    for key, value in choices.items():
        _identifier(key, "choice ID")
        if value is not None and not isinstance(value, (str, bool, int)):
            raise ValueError(f"Invalid choice value for {key}")
    if not isinstance(state["applied_event_ids"], list):
        raise ValueError("Event IDs must be a list")
    for event_id in state["applied_event_ids"]:
        _identifier(event_id, "event ID")
    if len(state["applied_event_ids"]) != len(set(state["applied_event_ids"])):
        raise ValueError("Invalid or repeated event IDs")
    _unique_ids(state["completed_event_types"], set(data["events"]), "completed event types")
    try:
        json.dumps(state, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("Campaign state is not JSON compatible") from exc


class Campaign(Mapping):
    """Single state owner; item access is a detached legacy-compatible view."""

    def __init__(self, state=None, *, data=None, save_id=None):
        self._data = deepcopy(data if data is not None else load_campaign_data())
        if not isinstance(self._data, dict) or self._data.get("schema_version") != 1:
            raise ValueError("Unsupported campaign data schema")
        if state is None:
            initial = deepcopy(self._data["new_game"])
            state = {"schema_version": 1, "save_id": uuid4().hex if save_id is None else save_id,
                     **initial, "contacted_civs": [], "extracted_fragments": [],
                     "validation_records": [], "unlocked_abilities": [],
                     "meters": {key: value["initial"] for key, value in self._data["meters"].items()},
                     "choices": {}, "applied_event_ids": [], "completed_event_types": []}
        elif save_id is not None:
            raise ValueError("save_id cannot override existing state")
        state = deepcopy(state)
        state.setdefault("world_states", {})  # Additive migration for existing v1/v2 saves.
        validate_state(state, self._data)
        self._state = state

    @property
    def state(self):
        return CampaignState(**deepcopy(self._state))

    @property
    def timeline_mode(self):
        return self._state["timeline_mode"]

    @property
    def current_act_label(self):
        return self._data["acts"][self._state["current_act"]]["name"]

    def to_dict(self):
        return deepcopy(self._state)

    def store_world_state(self, room_id, snapshot):
        """Validate and commit detached, JSON-compatible room mechanics state."""
        staged = deepcopy(self._state)
        staged["world_states"][room_id] = deepcopy(snapshot)
        validate_state(staged, self._data)
        self._state = staged

    def __getitem__(self, key):
        if key == "current_act":
            return self._data["acts"][self._state[key]]["legacy_index"]
        if key == "act_names":
            return {value["legacy_index"]: value["name"] for value in self._data["acts"].values()}
        if key == "validated_protocols":
            return [record["id"] for record in self._state["validation_records"]]
        if key == "meters":
            return {self._data["meters"][name]["label"]: value for name, value in self._state["meters"].items()}
        return deepcopy(self._state[key])

    def __iter__(self):
        return iter((*self._state, "act_names", "validated_protocols"))

    def __len__(self):
        return len(self._state) + 2

    def apply_event(self, event: CampaignEvent) -> bool:
        """Apply one defined event atomically; return False for an idempotent replay."""
        if not isinstance(event, dict) or set(event) - {"event_id", "type", "payload"}:
            raise ValueError("Invalid event shape")
        event_id = event.get("event_id")
        event_type = event.get("type")
        _identifier(event_id, "event ID")
        if not isinstance(event_type, str) or event_type not in self._data["events"]:
            raise ValueError(f"Unknown campaign event type: {event_type!r}")
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            raise ValueError("Event payload must be an object")
        if event_id in self._state["applied_event_ids"]:
            return False
        definition = self._data["events"][event_type]
        if not isinstance(definition, dict):
            raise ValueError(f"Invalid campaign event definition for {event_type}")
        staged = deepcopy(self._state)
        if definition.get("kind") == "contact":
            if set(payload) != {"civilization_id"} or payload["civilization_id"] not in self._data["civ_ids"]:
                raise ValueError("Invalid contact civilization")
            if payload["civilization_id"] not in staged["contacted_civs"]:
                staged["contacted_civs"].append(payload["civilization_id"])
        elif definition.get("kind") == "timeline_shift":
            if set(payload) != {"timeline_mode"} or payload["timeline_mode"] not in self._data["timeline_ids"]:
                raise ValueError("Invalid timeline shift payload")
            staged["timeline_mode"] = payload["timeline_mode"]
        elif definition.get("kind") == "grant":
            if payload:
                raise ValueError("Grant event payload must be empty")
            if event_type in staged["completed_event_types"]:
                return False
            self._apply_grant(staged, definition)
            staged["completed_event_types"].append(event_type)
        else:
            raise ValueError(f"Unsupported campaign event kind for {event_type}")
        staged["applied_event_ids"].append(event_id)
        validate_state(staged, self._data)
        self._state = staged
        return True

    def _apply_grant(self, staged, definition):
        requirements = definition.get("requires", {})
        grants = definition.get("grants", {})
        allowed = set(PROGRESSION_FIELDS) | {"validation_records", "inventory", "room_flags"}
        if not isinstance(requirements, dict) or not set(requirements).issubset(allowed):
            raise ValueError("Invalid event prerequisites")
        if not isinstance(grants, dict) or not set(grants).issubset(allowed):
            raise ValueError("Invalid event grants")
        for field, required in requirements.items():
            if field == "inventory":
                if not isinstance(required, dict) or not set(required).issubset(self._data["item_ids"]):
                    raise ValueError("Inventory prerequisites must be dict of item IDs to counts")
                for item_id, count in required.items():
                    if staged["inventory"].get(item_id, 0) < count:
                        raise ValueError(f"Unmet prerequisites for inventory item {item_id}")
            elif field == "room_flags":
                if not isinstance(required, dict) or not set(required).issubset(self._data["flag_ids"]):
                    raise ValueError("Room flag prerequisites must be dict of flag IDs to bool")
                for flag_id, val in required.items():
                    if staged["room_flags"].get(flag_id) != val:
                        raise ValueError(f"Unmet prerequisites for room flag {flag_id}")
            else:
                if not isinstance(required, list) or any(not isinstance(value, str) for value in required):
                    raise ValueError("Prerequisites must be lists")
                existing = {record["id"] for record in staged[field]} if field == "validation_records" else set(staged[field])
                if not set(required).issubset(existing):
                    raise ValueError(f"Unmet prerequisites for {field}")
        for field, values in grants.items():
            if field == "inventory":
                if not isinstance(values, dict) or not set(values).issubset(self._data["item_ids"]):
                    raise ValueError("Inventory grants must be dict of item IDs to counts")
                for item_id, delta in values.items():
                    staged["inventory"][item_id] = max(0, staged["inventory"].get(item_id, 0) + delta)
            elif field == "room_flags":
                if not isinstance(values, dict) or not set(values).issubset(self._data["flag_ids"]):
                    raise ValueError("Room flag grants must be dict of flag IDs to bool")
                for flag_id, val in values.items():
                    staged["room_flags"][flag_id] = val
            elif field == "validation_records":
                if not isinstance(values, list):
                    raise ValueError("Grants must be lists")
                existing = {(record["id"], record["scenario_id"]) for record in staged[field]}
                for value in values:
                    _validation_record(value, self._data)
                    if (value["id"], value["scenario_id"]) not in existing:
                        staged[field].append(deepcopy(value))
                        existing.add((value["id"], value["scenario_id"]))
            else:
                if not isinstance(values, list):
                    raise ValueError("Grants must be lists")
                for value in values:
                    if value not in staged[field]:
                        staged[field].append(value)
        consume = definition.get("consume", {})
        if isinstance(consume, dict) and "inventory" in consume:
            for item_id, qty in consume["inventory"].items():
                staged["inventory"][item_id] = max(0, staged["inventory"].get(item_id, 0) - qty)
        deltas = definition.get("meter_deltas", {})
        if (not isinstance(deltas, dict) or not set(deltas).issubset(staged["meters"])
                or any(type(v) is not int or not -100 <= v <= 100 for v in deltas.values())):
            raise ValueError("Invalid meter deltas")
        for name, delta in deltas.items():
            staged["meters"][name] = min(100, max(0, staged["meters"][name] + delta))


def seeded_development_campaign():
    """Construct a deliberately seeded preview fixture; never use for new games."""
    campaign = Campaign(save_id="development_fixture")
    state = campaign.to_dict()
    state["contacted_civs"] = ["FASR-001"]
    state["extracted_fragments"] = ["FASR-001"]
    state["validation_records"] = [{"id": "FASR-001", "scenario_id": "development_fixture", "scenario_version": 1,
                                    "claim_id": "development_fixture", "observations": [], "result": "fixture",
                                    "confidence": 0, "claim_tier": "speculative", "source_references": [],
                                    "deployment_decision": "not_deployed"}]
    return Campaign(state)
