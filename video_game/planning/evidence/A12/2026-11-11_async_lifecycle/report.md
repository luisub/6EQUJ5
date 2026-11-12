# A12 asynchronous music lifecycle repair — 2026-11-11

I38 reproduced an unbounded thread and stale-playback race: with the former music lock held, 12 alternating requests created 12 loader threads and all could play after `stop_all`. The repair keeps one replaceable pending request per manager, invalidates generations across managers, and reads music bytes in a short-lived worker. A later `AudioManager.update` loads a retained `BytesIO` stream into the mixer and starts playback on the caller thread. The worker never calls pygame or SDL. Stop invalidates pending and ready data, stops the owned music and sound effects without waiting for a blocked file read, and later requests can restart. The newest manager owns the shared mixer stream; closing an older manager does not stop the newer stream. Cross-fade duration, loop arguments and live volume/mute are preserved. Tests use controlled `threading.Event` gates and join each reader.

Changed `video_game/engine/audio.py`; added `video_game/tests/test_audio_lifecycle.py`. The untracked original is hash-verified at `video_game/_trash/2026-11-11_A12_async_lifecycle/video_game/engine/audio.py`; its [recovery manifest](../../../../_trash/2026-11-11_A12_async_lifecycle/manifest.json) records SHA-256 and restoration instructions. This is a local recovery copy, not an independent backup.

## Checks

Environment: Python 3.12.16 from `/opt/anaconda3/envs/6equj5_game/bin/python`, pygame-ce 2.5.8, SDL 2.32.10, dummy video and audio; no real window or speakers.

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_audio_lifecycle.py video_game/tests/test_combat.py video_game/tests/test_checkpoint_audit.py -q
```

61 passed in 0.72 seconds. The lifecycle tests cover blocked reads, 12 alternating requests using one worker, stop during a read and after a ready result, restart, newest request, two-manager ownership/reclaim, fade/loop arguments, volume/mute and unavailable/missing audio. They release the gates and join all spawned reader threads.

The following direct dummy-mixer check loaded each actual MP3 from bytes, played it, asserted busy/retained stream, stopped it, and quit. Measured single `update` samples were 0.067 ms for `Static_Bloom.mp3` and 0.029 ms for `Echoes_of_the_Static_Void.mp3`; these are not graphical performance or audible-quality measurements.

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python - <<'PY'
import time
import pygame
from video_game.engine.audio import AudioManager, TRACK_BUNKER, TRACK_COMBAT
pygame.init()
audio = AudioManager()
assert audio.enabled and pygame.mixer.get_init()
for track in (TRACK_BUNKER, TRACK_COMBAT):
    audio.stop_all()
    audio.play_music(track, loop=False, fade_ms=25)
    worker = audio._load_thread
    if worker is not None:
        worker.join(5)
        assert not worker.is_alive()
    start = time.perf_counter()
    audio.update(0.0)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(track, 'in-memory update ms:', round(elapsed_ms, 3), 'busy:', pygame.mixer.music.get_busy())
    assert pygame.mixer.music.get_busy()
    assert audio._music_stream is not None
    audio.stop_all()
    assert not pygame.mixer.music.get_busy()
pygame.quit()
PY
```

A separate actual SDL check deliberately blocked the file reader, called `stop_all()` and `pygame.quit()` before releasing it, then joined it and called `update`: completed without an SDL abort, with `current_track` still `None`. Exact command:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python - <<'PY'
from pathlib import Path
from threading import Event
import pygame
from video_game.engine.audio import AudioManager, TRACK_BUNKER
pygame.init()
audio = AudioManager()
assert audio.enabled
original = Path.read_bytes
entered, release = Event(), Event()
def blocked(path):
    if path.name == TRACK_BUNKER:
        entered.set()
        if not release.wait(5):
            raise RuntimeError('read gate timeout')
    return original(path)
Path.read_bytes = blocked
try:
    audio.play_music(TRACK_BUNKER)
    worker = audio._load_thread
    assert worker is not None and entered.wait(5)
    audio.stop_all()
    pygame.quit()
    release.set()
    worker.join(5)
    assert not worker.is_alive()
    assert pygame.mixer.get_init() is None
    audio.update(0)
    assert audio.current_track is None
finally:
    release.set()
    Path.read_bytes = original
    pygame.quit()
PY
```

The first attempted design performed native `music.load` in workers; two concurrent unrelated test runs aborted during `pygame.quit`. It was replaced before final testing by byte-only workers. MP3 initialization/decoding from memory now occurs on the update thread and could still cause a frame stall; the two short dummy samples do not bound this cost on other systems. Audible transitions, physical devices, and representative native graphical performance remain unverified. A12 remains in progress; no gate or art review is claimed. No model was downloaded, no player saves were used, and the controlled worker threads were joined. Root is coordinating the final full suite and package check.

## Fade completion follow-up

The parent observed the full checkpoint's field profile at 53.8 FPS and an isolated repeat at 54.9 FPS. Instrumentation showed SDL `fadeout(1000)` returned in 0.001 ms, but a later `music.load(BytesIO(...))` took 1044.615 ms. The uncapped profile advances a fixed simulated 1/60-second `dt` faster than SDL's real-time fade, so its fade timer expired before SDL finished the fade and the next load waited for it. These figures are diagnostic dummy-driver observations, not graphical performance acceptance.

On a simulated fade deadline, if SDL still reports music busy, `update` now stops the stream before queuing the next track. It verifies the manager still owns the current request before stopping, so a superseded manager cannot stop a newer owner's music. In real-time play the fade continues until its existing deadline; this terminates any remaining SDL fade at that deadline. Two controlled regression tests assert stop-before-load ordering and protect a newer owner. Pre-follow-up audio, test and report copies are SHA-verified in `video_game/_trash/2026-11-11_A12_fade_completion/manifest.json`.

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_audio_lifecycle.py video_game/tests/test_combat.py video_game/tests/test_checkpoint_audit.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy /opt/anaconda3/envs/6equj5_game/bin/python -m pytest video_game/tests/test_profile.py::test_scene_frame_budgets -q
```

Results: 63 passed in 0.79 seconds; isolated scene frame-budget check passed in 3.29 seconds. No thresholds were changed. Native visual performance and audible fade quality remain unverified.
