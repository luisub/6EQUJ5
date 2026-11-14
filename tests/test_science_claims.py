"""PURPOSE: Verify audited references reach earned and persisted lab records.
CALLED BY: pytest tests/test_science_claims.py.
HOW TO MODIFY: Exercise normal-input earning and preserve historical save records.
"""

from video_game.engine import config
import json
from pathlib import Path

from video_game.engine.campaign import Campaign
from video_game.engine.save_game import SaveStore
from video_game.tools.mechanics_route import run_route


def test_earned_references_and_older_save_compatibility(tmp_path, monkeypatch):
    """Normal lab input commits current refs; older recorded refs still load unchanged."""
    sources = {
        'quantum_fasr_002': 'Englert_1996_Fringe_Visibility_Which_Way_Information',
        'connectome_adv_fasr_004': 'Amit_Gutfreund_Sompolinsky_1987_Statistical_Mechanics_Near_Saturation',
    }
    earned = {}
    original_apply = Campaign.apply_event

    def observe_apply(self, event):
        applied = original_apply(self, event)
        if applied:
            records = self.state.validation_records
            for record in records:
                if record['scenario_id'] in sources:
                    earned[record['scenario_id']] = record
            if len(earned) == len(sources):
                earned['snapshot'] = self.to_dict()
        return applied

    monkeypatch.setattr(Campaign, 'apply_event', observe_apply)
    run_route(tmp_path / 'captures')
    for scenario_id, reference in sources.items():
        assert reference in earned[scenario_id]['source_references']

    # A pre-correction save retains its original references rather than being rewritten.
    old_state = earned['snapshot']
    for record in old_state['validation_records']:
        reference = sources.get(record['scenario_id'])
        if reference:
            record['source_references'].remove(reference)
    old_campaign = Campaign(state=old_state)
    store = SaveStore(tmp_path / 'older_save')
    assert store.save(old_campaign)
    loaded = store.load()
    assert loaded.status == 'ok'
    assert loaded.campaign.to_dict() == old_state

    # Both deploy and withhold event templates carry the audited references.
    data_dir = config.DATA_DIR
    catalog = json.loads((data_dir / 'lab_scenarios.json').read_text())['scenarios']
    events = json.loads((data_dir / 'campaign.json').read_text())['events']
    for scenario_id, reference in sources.items():
        for choice in catalog[scenario_id]['deployment_choices']:
            record = events[choice['event_type']]['grants']['validation_records'][0]
            assert reference in record['source_references']
