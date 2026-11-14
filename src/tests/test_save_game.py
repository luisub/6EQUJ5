"""
MODULE: tests/test_save_game.py
PURPOSE: Verify checkpoint persistence, migration, interruption and recovery.
CALLED BY: pytest (`python -m pytest tests -q`).
HOW TO MODIFY: Exercise real entry points and preserve user files in failures;
  all tests use isolated temporary save directories.
"""

from . import REPO_ROOT

import json
import os
from pathlib import Path
import subprocess
import sys

import pygame
import pytest

from video_game.engine import config, save_game
from video_game.engine.campaign import Campaign, seeded_development_campaign
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveError, SaveStore
from video_game.engine.state_machine import GameStateMachine

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def store(tmp_path):
    return SaveStore(tmp_path / "saves")


def key(machine, code):
    machine.handle_event(pygame.event.Event(pygame.KEYDOWN, key=code))


def shift(campaign, event_id="shift_1"):
    campaign.apply_event({"event_id": event_id, "type": "timeline_shift", "payload": {"timeline_mode": "1977_ANALOG"}})


def test_platform_directory_override(monkeypatch, tmp_path):
    monkeypatch.setenv(save_game.SAVE_DIRECTORY_ENV, str(tmp_path / "overridden"))
    assert save_game.user_data_dir() == tmp_path / "overridden"
    assert SaveStore().directory == tmp_path / "overridden"
    assert not (tmp_path / "overridden").exists()


def test_earned_progress_round_trip_and_previous_backup(store):
    campaign = seeded_development_campaign()
    original = campaign.to_dict()
    assert store.save(campaign) is True
    assert store.load().campaign.to_dict() == original
    shift(campaign)
    assert store.save(campaign) is True
    assert store.load().campaign.to_dict() == campaign.to_dict()
    assert store.load_backup().campaign.to_dict() == original
    before_backup = store.backup_path.read_bytes()
    assert store.save(campaign) is False
    assert store.backup_path.read_bytes() == before_backup


@pytest.mark.parametrize("version", [1, 2])
def test_each_supported_fixture_loads_and_old_migrates_without_rewriting(store, version):
    store.directory.mkdir(parents=True)
    original = (FIXTURES / f"save_v{version}.json").read_bytes()
    store.path.write_bytes(original)
    result = store.load()
    assert result.status == "ok" and result.migrated is (version == 1)
    assert result.campaign.state.extracted_fragments == ["FASR-001"]
    assert result.campaign.state.validation_records[0]["result"] == "fixture"
    assert result.campaign.timeline_mode == "1977_ANALOG"
    assert store.path.read_bytes() == original
    if version == 1:
        assert store.save(result.campaign) is True
        assert json.loads(store.path.read_text())["schema_version"] == 2
        assert store.backup_path.read_bytes() == original


@pytest.mark.parametrize("raw,status", [
    (b"{", "corrupt"),
    (b'{}', "corrupt"),
    (b'{"schema_version": 0}', "old_version"),
    (b'{"schema_version": 99}', "future_version"),
    (b'{"schema_version": 1, "campaign": {}}', "migration_failed"),
])
def test_invalid_and_unsupported_saves_are_distinguished_and_preserved(store, raw, status):
    assert store.load().status == "missing"
    store.directory.mkdir(parents=True)
    store.path.write_bytes(raw)
    assert store.load().status == status
    with pytest.raises(SaveError, match="preserved"):
        store.save(Campaign(save_id="new_game"))
    assert store.path.read_bytes() == raw


def test_future_nested_campaign_and_checkpoint_mismatch_are_not_loaded(store):
    document = json.loads((FIXTURES / "save_v2.json").read_text())
    store.directory.mkdir(parents=True)
    document["campaign"]["schema_version"] = 99
    store.path.write_text(json.dumps(document))
    assert store.load().status == "future_version"
    document["campaign"]["schema_version"] = 1
    document["checkpoint"]["room_id"] = "unknown"
    store.path.write_text(json.dumps(document))
    assert store.load().status == "corrupt"


def test_failed_primary_replace_keeps_prior_save_and_backup(store, monkeypatch):
    campaign = seeded_development_campaign()
    store.save(campaign)
    original = store.path.read_bytes()
    shift(campaign)
    replace = save_game.os.replace

    def fail_primary(source, destination):
        if Path(destination) == store.path:
            raise OSError("simulated primary replacement failure")
        return replace(source, destination)

    monkeypatch.setattr(save_game.os, "replace", fail_primary)
    with pytest.raises(SaveError, match="simulated"):
        store.save(campaign)
    assert store.path.read_bytes() == original
    assert store.load().status == store.load_backup().status == "ok"
    assert not list(store.directory.glob("*.tmp"))


def test_partial_staged_write_is_rejected_without_changing_previous_save(store, monkeypatch):
    campaign = seeded_development_campaign()
    store.save(campaign)
    original = store.path.read_bytes()
    shift(campaign)
    fdopen = save_game.os.fdopen

    class PartialWriter:
        def __init__(self, stream):
            self.stream = stream
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.stream.close()
        def write(self, raw):
            return self.stream.write(raw[:len(raw) // 2])
        def flush(self):
            return self.stream.flush()
        def fileno(self):
            return self.stream.fileno()

    monkeypatch.setattr(save_game.os, "fdopen", lambda fd, mode: PartialWriter(fdopen(fd, mode)))
    with pytest.raises(SaveError, match="verification"):
        store.save(campaign)
    assert store.path.read_bytes() == original and store.load().status == "ok"
    assert not list(store.directory.glob("*.tmp"))


def test_explicit_backup_recovery_preserves_corrupt_original(store):
    campaign = seeded_development_campaign()
    store.save(campaign)
    original = store.path.read_bytes()
    shift(campaign)
    store.save(campaign)
    backup = store.backup_path.read_bytes()
    assert backup == original
    store.path.write_bytes(b"{damaged")
    assert store.load().status == "corrupt"
    result = store.recover_backup()
    assert result.status == "ok" and result.campaign.to_dict() == seeded_development_campaign().to_dict()
    assert store.path.read_bytes() == backup == store.backup_path.read_bytes()
    preserved = list(store.directory.glob("campaign.preserved-*.json"))
    assert len(preserved) == 1 and preserved[0].read_bytes() == b"{damaged"


def test_unreadable_backup_is_preserved_before_a_new_backup(store):
    campaign = seeded_development_campaign()
    store.save(campaign)
    original = store.path.read_bytes()
    future_backup = b'{"schema_version": 999}'
    store.backup_path.write_bytes(future_backup)
    shift(campaign)
    store.save(campaign)
    assert store.backup_path.read_bytes() == original
    assert next(store.directory.glob("campaign.backup.preserved-*.json")).read_bytes() == future_backup


def test_unchanged_save_repairs_damaged_backup_without_losing_it(store):
    campaign = seeded_development_campaign()
    store.save(campaign)
    original = store.path.read_bytes()
    damaged = b"{broken backup"
    store.backup_path.write_bytes(damaged)
    assert store.save(campaign) is False
    assert store.path.read_bytes() == store.backup_path.read_bytes() == original
    assert next(store.directory.glob("campaign.backup.preserved-*.json")).read_bytes() == damaged


def test_recovery_failure_keeps_both_generations(store, monkeypatch):
    campaign = seeded_development_campaign()
    store.save(campaign)
    shift(campaign)
    store.save(campaign)
    store.path.write_bytes(b"{damaged")
    backup = store.backup_path.read_bytes()
    replace = save_game.os.replace

    def fail_primary(source, destination):
        if Path(destination) == store.path:
            raise OSError("cannot restore")
        return replace(source, destination)

    monkeypatch.setattr(save_game.os, "replace", fail_primary)
    assert store.recover_backup().status == "io_error"
    assert store.path.read_bytes() == b"{damaged" and store.backup_path.read_bytes() == backup


def test_restart_in_new_process_restores_checkpoint(store):
    campaign = seeded_development_campaign()
    shift(campaign)
    store.save(campaign)
    script = '''
import json, sys
from video_game.engine.save_game import SaveStore
result = SaveStore(sys.argv[1]).load()
assert result.status == "ok"
print(json.dumps(result.campaign.to_dict(), sort_keys=True))
'''
    result = subprocess.run([sys.executable, "-c", script, str(store.directory)], cwd=REPO_ROOT,
                            capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == campaign.to_dict()


def test_normal_game_entry_starts_fresh_after_process_restart(store):
    campaign = seeded_development_campaign()
    shift(campaign)
    store.save(campaign)
    script = '''
import json
from unittest.mock import patch
import pygame
import video_game.main as main
from video_game.engine.state_machine import GameStateMachine
class ObservedMachine(GameStateMachine):
    def close(self):
        print("RESTORED=" + json.dumps(self.campaign.to_dict(), sort_keys=True))
        super().close()
with patch.object(main, "GameStateMachine", ObservedMachine), patch.object(pygame.event, "get", return_value=[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]):
    assert main.run_game(max_frames=1) == 1
'''
    environment = dict(os.environ, SIX_GAME_SAVE_DIR=str(store.directory), SDL_VIDEODRIVER="dummy",
                       SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
    result = subprocess.run([sys.executable, "-c", script], cwd=REPO_ROOT, env=environment,
                            capture_output=True, text=True, check=True)
    line = next(line for line in result.stdout.splitlines() if line.startswith("RESTORED="))
    fresh = json.loads(line.removeprefix("RESTORED="))
    assert fresh["save_id"] != campaign.state.save_id
    assert fresh["extracted_fragments"] == []
    assert fresh["timeline_mode"] == "2029_CORE"


def test_new_run_continue_api_and_safe_autosave(store, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    machine = GameStateMachine(CRTRenderer(), save_store=store, development=True)
    assert machine.continue_game().status == "missing"
    assert machine.continue_game(recover=True).status == "missing"
    assert machine.current_state_name == config.STATE_TITLE_BOOT
    key(machine, pygame.K_n)
    assert machine.current_state_name == config.STATE_BUNKER_HUB
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_n))
    key(machine, pygame.K_DOWN)  # Skip the title-start opening before development controls.
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_DOWN))
    save_id = machine.campaign.state.save_id
    assert store.load().campaign.state.save_id == save_id
    key(machine, pygame.K_q)
    assert store.load().campaign.timeline_mode == "1977_ANALOG"
    machine.close()
    machine = GameStateMachine(CRTRenderer(), save_store=store)
    assert machine.continue_game().status == "ok"
    assert machine.current_state_name == config.STATE_BUNKER_HUB
    assert machine.campaign.state.save_id == save_id and machine.campaign.timeline_mode == "1977_ANALOG"
    machine.close()
    pygame.quit()


def test_recovery_api_and_immediate_new_run(store, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    campaign = seeded_development_campaign()
    store.save(campaign)
    shift(campaign)
    store.save(campaign)
    store.path.write_bytes(b"{broken")
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    machine = GameStateMachine(CRTRenderer(), save_store=store)
    assert machine.continue_game().status == "corrupt"
    assert machine.continue_game(recover=True).status == "ok"
    assert machine.current_state_name == config.STATE_BUNKER_HUB
    assert machine.campaign.state.extracted_fragments == ["FASR-001"]
    assert next(store.directory.glob("campaign.preserved-*.json")).read_bytes() == b"{broken"
    machine.close()
    prior = store.path.read_bytes()
    machine = GameStateMachine(CRTRenderer(), save_store=store)
    key(machine, pygame.K_n)
    assert machine.current_state_name == config.STATE_BUNKER_HUB
    assert machine.campaign.state.extracted_fragments == []
    assert store.backup_path.read_bytes() == prior
    machine.close()
    pygame.quit()


def test_bunker_save_failure_blocks_departure_until_retry(store, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    machine = GameStateMachine(CRTRenderer(), save_store=store, development=True)
    key(machine, pygame.K_n)
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_n))
    key(machine, pygame.K_DOWN)  # Skip the opening before exercising save failure.
    machine.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_DOWN))
    prior = store.path.read_bytes()
    save = store.save

    def fail_save(*args, **kwargs):
        raise SaveError("simulated full disk")

    monkeypatch.setattr(store, "save", fail_save)
    key(machine, pygame.K_q)
    assert machine.save_notice.startswith("SAVE FAILED")
    key(machine, pygame.K_e)
    assert machine.current_state_name == config.STATE_BUNKER_HUB
    assert store.path.read_bytes() == prior
    monkeypatch.setattr(store, "save", save)
    key(machine, pygame.K_F5)
    assert machine.save_notice == "CHECKPOINT SAVED"
    assert store.load().campaign.timeline_mode == "1977_ANALOG"
    key(machine, pygame.K_e)
    assert machine.current_state_name == config.STATE_CRT_TERMINAL
    machine.close()
    pygame.quit()


def test_new_game_preserves_unreadable_version_file(store, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    store.directory.mkdir(parents=True)
    original = b'{"schema_version": 999}'
    store.path.write_bytes(original)
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    machine = GameStateMachine(CRTRenderer(), save_store=store)
    assert machine.continue_game().status == "future_version"
    key(machine, pygame.K_n)
    assert machine.current_state_name == config.STATE_BUNKER_HUB
    assert next(store.directory.glob("campaign.preserved-*.json")).read_bytes() == original
    assert store.load().status == "ok"
    machine.close()
    pygame.quit()


def test_recovery_api_reports_damaged_backup_without_changing_files(store, monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    store.directory.mkdir(parents=True)
    store.path.write_bytes(b"{broken primary")
    store.backup_path.write_bytes(b"{broken backup")
    pygame.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    machine = GameStateMachine(CRTRenderer(), save_store=store)
    assert machine.continue_game(recover=True).status == "corrupt"
    assert store.path.read_bytes() == b"{broken primary"
    assert store.backup_path.read_bytes() == b"{broken backup"
    machine.close()
    pygame.quit()
