"""PURPOSE: Verify bounded, cancellable asynchronous music requests.
CALLED BY: pytest.
HOW TO MODIFY: Use events and a mocked mixer to control read ordering deterministically.
"""

from pathlib import Path
from threading import Event
from unittest.mock import MagicMock

import pygame
import pytest

from video_game.engine import config
from video_game.engine.audio import AudioManager, TRACK_BUNKER, TRACK_COMBAT


@pytest.fixture
def audio_fixture(monkeypatch, tmp_path):
    for name in (TRACK_BUNKER, TRACK_COMBAT):
        (tmp_path / name).write_bytes(name.encode())
    monkeypatch.setattr(AudioManager, "_init_mixer", lambda self: None)
    music = MagicMock()
    music.get_busy.return_value = False
    monkeypatch.setattr(pygame.mixer, "music", music)
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: (44100, -16, 2))
    sfx_stop = MagicMock()
    monkeypatch.setattr(pygame.mixer, "stop", sfx_stop)
    managers, gates, threads = [], [], []
    original_queue = AudioManager._queue_music
    original_read = Path.read_bytes

    def record_queue(manager, request):
        original_queue(manager, request)
        threads.append(manager._load_thread)

    monkeypatch.setattr(AudioManager, "_queue_music", record_queue)

    def make_audio():
        manager = AudioManager(tmp_path)
        manager.enabled = True
        managers.append(manager)
        return manager

    def block_read():
        entered, release = Event(), Event()
        gates.append(release)

        def read(path):
            if path.parent == tmp_path:
                entered.set()
                assert release.wait(3), "test did not release the file read"
            return original_read(path)

        monkeypatch.setattr(Path, "read_bytes", read)
        return entered, release

    def join_latest():
        thread = threads[-1]
        thread.join(3)
        assert not thread.is_alive(), "audio reader failed to exit"
        return thread

    yield make_audio, music, sfx_stop, block_read, threads, join_latest

    for gate in gates:
        gate.set()
    for manager in managers:
        manager.stop_all()
    for thread in set(threads):
        thread.join(3)
        assert not thread.is_alive(), "audio reader failed to exit"


def test_stop_invalidates_inflight_and_bounded_pending_requests(audio_fixture):
    make, music, sfx_stop, block, threads, join = audio_fixture
    audio = make()
    entered, release = block()
    audio.play_music(TRACK_BUNKER)
    thread = threads[-1]
    assert entered.wait(3)
    for index in range(12):
        audio.play_music(TRACK_COMBAT if index % 2 else TRACK_BUNKER)
        assert threads[-1] is thread
    audio.stop_all()
    assert audio.current_track is None and audio.target_track is None
    assert sfx_stop.call_count == 1
    release.set()
    join()
    audio.update(0)
    music.load.assert_not_called()
    music.play.assert_not_called()
    music.stop.assert_called_once()


def test_latest_request_wins_and_restart_after_stop(audio_fixture):
    make, music, _, block, threads, join = audio_fixture
    audio = make()
    entered, release = block()
    audio.play_music(TRACK_BUNKER)
    assert entered.wait(3)
    audio.play_music(TRACK_COMBAT, loop=False, fade_ms=275)
    release.set()
    join()
    music.load.assert_not_called()  # Worker never calls SDL.
    audio.update(0)
    assert music.load.call_args.args[0].getvalue() == TRACK_COMBAT.encode()
    assert music.load.call_args.args[1] == 'mp3'
    music.play.assert_called_once_with(0, fade_ms=275)
    audio.stop_all()
    music.play.reset_mock()
    audio.play_music(TRACK_BUNKER, fade_ms=40)
    join()
    audio.update(0)
    music.play.assert_called_once_with(-1, fade_ms=40)


def test_stop_then_restart_while_read_is_blocked(audio_fixture):
    make, music, _, block, threads, join = audio_fixture
    audio = make()
    entered, release = block()
    audio.play_music(TRACK_BUNKER)
    thread = threads[-1]
    assert entered.wait(3)
    audio.stop_all()
    audio.play_music(TRACK_COMBAT, loop=False, fade_ms=42)
    assert threads[-1] is thread
    release.set()
    join()
    audio.update(0)
    music.play.assert_called_once_with(0, fade_ms=42)
    assert music.stop.call_count == 1
    assert audio.current_track == TRACK_COMBAT


def test_stop_discards_completed_read_before_update(audio_fixture):
    make, music, _, _, _, join = audio_fixture
    audio = make()
    audio.play_music(TRACK_BUNKER)
    join()
    audio.stop_all()
    audio.update(0)
    music.load.assert_not_called()
    music.play.assert_not_called()


def test_scene_fade_uses_latest_target_loop_and_volume(audio_fixture):
    make, music, _, _, _, join = audio_fixture
    audio = make()
    music.get_busy.return_value = True
    audio.current_track = TRACK_BUNKER
    audio.play_music(TRACK_COMBAT, loop=False, fade_ms=500)
    assert audio.fade_state == "FADING_OUT"
    music.fadeout.assert_called_once_with(500)
    audio.set_master_volume(0.5)
    audio.set_music_volume(0.4)
    audio.toggle_mute()
    music.get_busy.return_value = False
    audio.update(0.6)
    join()
    audio.update(0)
    music.play.assert_called_once_with(0, fade_ms=500)
    assert music.set_volume.call_args.args == (0.0,)
    audio.toggle_mute()
    assert music.set_volume.call_args.args == pytest.approx((0.2,))


def test_fade_deadline_stops_busy_mixer_before_next_load(audio_fixture):
    make, music, _, _, _, join = audio_fixture
    audio = make()
    order = []
    music.stop.side_effect = lambda: order.append("stop")
    music.load.side_effect = lambda *_: order.append("load")
    music.get_busy.return_value = True
    audio.play_music(TRACK_COMBAT, fade_ms=500)
    audio.update(0.5)
    assert order == ["stop"]
    join()
    audio.update(0)
    assert order == ["stop", "load"]
    music.play.assert_called_once_with(-1, fade_ms=500)


def test_obsolete_fade_does_not_stop_new_owner(audio_fixture):
    make, music, _, _, _, join = audio_fixture
    first, second = make(), make()
    music.get_busy.return_value = True
    first.play_music(TRACK_BUNKER, fade_ms=500)
    music.get_busy.return_value = False
    second.play_music(TRACK_COMBAT)
    join()
    second.update(0)
    music.get_busy.return_value = True
    first.update(0.5)
    music.stop.assert_not_called()
    assert first.fade_state == "IDLE" and first.target_track is None


def test_new_manager_supersedes_old_global_stream(audio_fixture):
    make, music, _, block, threads, join = audio_fixture
    first, second = make(), make()
    entered, release = block()
    first.play_music(TRACK_BUNKER)
    first_thread = threads[-1]
    assert entered.wait(3)
    second.play_music(TRACK_COMBAT, fade_ms=77)
    release.set()
    join()
    first_thread.join(3)
    assert not first_thread.is_alive()
    first.update(0)
    second.update(0)
    music.play.assert_called_once_with(-1, fade_ms=77)
    assert music.load.call_args.args[0].getvalue() == TRACK_COMBAT.encode()
    first.stop_all()
    music.stop.assert_not_called()  # An obsolete manager does not stop the new owner.


def test_previous_owner_can_reclaim_same_track(audio_fixture):
    make, music, _, _, _, join = audio_fixture
    first, second = make(), make()
    first.play_music(TRACK_BUNKER)
    join()
    first.update(0)
    second.play_music(TRACK_COMBAT)
    join()
    second.update(0)
    music.get_busy.return_value = True
    first.transition_scene_music(config.STATE_BUNKER_HUB, fade_ms=300)
    assert first.target_track == TRACK_BUNKER
    music.fadeout.assert_called_once_with(300)
    music.get_busy.return_value = False
    first.update(0.4)
    join()
    first.update(0)
    assert music.load.call_args.args[0].getvalue() == TRACK_BUNKER.encode()


def test_missing_driver_and_missing_file_do_not_start_workers(audio_fixture):
    make, music, _, _, _, _ = audio_fixture
    audio = make()
    audio.play_music('missing.mp3')
    assert audio._load_thread is None
    audio.enabled = False
    audio.play_music(TRACK_BUNKER)
    assert audio.current_track == TRACK_BUNKER
    audio.stop_all()
    assert audio.current_track is None and audio._load_thread is None
    music.load.assert_not_called()
    music.play.assert_not_called()


def test_mixer_initialization_failure_is_safe(monkeypatch, tmp_path):
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: None)
    monkeypatch.setattr(pygame.mixer, "init", MagicMock(side_effect=pygame.error("no device")))
    audio = AudioManager(tmp_path)
    assert not audio.enabled
    audio.play_music(TRACK_BUNKER)
    audio.update(0.1)
    audio.stop_all()
    assert audio.current_track is None and audio._load_thread is None


@pytest.mark.parametrize('escape', ['parent', 'absolute', 'symlink'])
def test_music_rejects_paths_outside_audio_without_reads(audio_fixture, tmp_path, monkeypatch, escape):
    make, music, _, _, threads, _ = audio_fixture
    outside = tmp_path.parent / (tmp_path.name + '-outside.mp3')
    outside.write_bytes(b'outside audio')
    if escape == 'parent':
        name = '../' + outside.name
    elif escape == 'absolute':
        name = str(outside)
    else:
        (tmp_path / 'linked.mp3').symlink_to(outside)
        name = 'linked.mp3'
    audio = make()
    monkeypatch.setattr(Path, 'read_bytes', lambda *_: pytest.fail('rejected music was read'))
    audio.play_music(name)
    audio.update(0)
    assert not threads and audio.current_track is None and audio.target_track is None
    assert not music.mock_calls


def test_fade_target_revalidates_before_worker_read(audio_fixture, tmp_path, monkeypatch):
    make, music, _, _, threads, _ = audio_fixture
    audio = make()
    music.get_busy.return_value = True
    audio.play_music(TRACK_COMBAT, fade_ms=100)
    outside = tmp_path.parent / (tmp_path.name + '-outside.mp3')
    outside.write_bytes(b'outside audio')
    (tmp_path / TRACK_COMBAT).unlink()
    (tmp_path / TRACK_COMBAT).symlink_to(outside)
    monkeypatch.setattr(Path, 'read_bytes', lambda *_: pytest.fail('redirected music was read'))
    music.get_busy.return_value = False
    audio.update(0.2)
    assert not threads
    music.load.assert_not_called()
    music.play.assert_not_called()


def test_sfx_symlink_is_skipped_and_contained_file_loads(monkeypatch, tmp_path):
    monkeypatch.setattr(AudioManager, '_init_mixer', lambda self: None)
    outside = tmp_path.parent / (tmp_path.name + '-outside.wav')
    outside.write_bytes(b'outside audio')
    (tmp_path / 'maser_tap.wav').symlink_to(outside)
    valid = tmp_path / 'player_jump.wav'
    valid.write_bytes(b'contained fixture')
    sound = MagicMock()
    monkeypatch.setattr(pygame.mixer, 'Sound', sound)
    audio = AudioManager(tmp_path)
    audio.enabled = True
    audio._load_sfx_bank()
    sound.assert_called_once_with(str(valid))
    assert 'player_jump' in audio.sfx_bank and 'maser_tap' not in audio.sfx_bank
