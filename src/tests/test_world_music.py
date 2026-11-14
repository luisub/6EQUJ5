"""World scores follow scene context, remain packaged, and decode as real loops."""
import hashlib
import json

import numpy as np
import pygame
import pytest

from video_game.engine import config
from video_game.engine.alien_journey import journey_data, save_ledger
from video_game.engine.audio import AudioManager, TRACK_BUNKER, TRACK_COMBAT
from .test_campaign_world_route import game


def test_every_world_score_decodes_and_matches_its_manifest(monkeypatch):
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
    try:
        audio = AudioManager()
        worlds = journey_data()['worlds']
        assert set(audio.world_tracks) == {world['id'] for world in worlds}
        assert len(set(audio.world_tracks.values())) == len(worlds)
        manifest = json.loads((config.AUDIO_ASSETS_DIR / 'manifest.json').read_text())['music_tracks']
        hashes = set()
        for filename in audio.world_tracks.values():
            path = config.AUDIO_ASSETS_DIR / filename
            entry = manifest[filename]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == entry['sha256'] and digest not in hashes
            hashes.add(digest)
            sound = pygame.mixer.Sound(str(path))
            assert sound.get_length() == pytest.approx(entry['duration_seconds'], abs=.01)
            assert 60 < sound.get_length() < 120
            samples = pygame.sndarray.array(sound).astype(np.float32) / 32768
            assert samples.shape[1] == 2
            assert .1 < np.abs(samples).max() < .9
            assert np.max(np.abs(samples[0] - samples[-1])) < .02
            assert np.sqrt(np.mean(samples ** 2)) > .05
    finally:
        pygame.mixer.quit()


def test_world_score_follows_field_guardian_contact_and_return_home(game):
    game.audio.stop_all()
    game.audio.enabled = False  # Routing test; decoding is covered separately.
    worlds = journey_data()['worlds']
    game.campaign.apply_event({'event_id': 'music_portal', 'type': 'defeat_portal_warden'})
    receipts = []
    previous = None
    for world in worlds:
        progress = {'version': 1, 'world_id': world['id'], 'stage': 'field',
                    'checkpoint': None, 'receipts': list(receipts)}
        save_ledger(game.campaign, progress)
        game.change_state(config.STATE_FIELD_OPS, room=world['field_room'],
                          journey_world=world['id'], campaign_route=True)
        expected = game.audio.world_tracks[world['id']]
        assert game.audio.current_track == expected and expected != previous
        progress['stage'] = 'guardian'
        save_ledger(game.campaign, progress)
        game.change_state(config.STATE_BOSS_BOUNTY, room=world['arena_room'],
                          boss_id=world['boss_id'], journey_world=world['id'])
        assert game.audio.current_track == expected
        game.campaign.apply_event({'event_id': 'music_' + world['id'], 'type': world['defeat_event']})
        progress['stage'] = 'contact'
        save_ledger(game.campaign, progress)
        game.change_state(config.STATE_ALIEN_CONTACT, world_id=world['id'])
        assert game.current_state_name == config.STATE_ALIEN_CONTACT
        assert game.audio.current_track == expected
        receipts.append(world['civ_id'])
        previous = expected
    assert game.start_new_game(replace_existing=True)[0]
    assert game.audio.current_track == TRACK_BUNKER
    game.change_state(config.STATE_FIELD_OPS, room='act_01/ohio_campus.json')
    assert game.audio.current_track == TRACK_COMBAT
