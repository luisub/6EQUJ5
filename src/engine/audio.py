"""
# PURPOSE: Audio manager managing background music cross-fades, SFX playback, volume control, and headless fallbacks.
# CALLED BY: GameStateMachine, scenes (bunker, terminal, lab, field, boss), and pause settings overlay.
# HOW TO MODIFY: Register new sound effects or adjust music fade durations; maintain zero wildcard imports.
"""

from io import BytesIO
import json
from pathlib import Path
import re
import threading
from typing import Any, Dict, Optional
import pygame

from video_game.engine import config

AUDIO_DIR = config.AUDIO_ASSETS_DIR

TRACK_BUNKER = "Static_Bloom.mp3"
TRACK_COMBAT = "Echoes_of_the_Static_Void.mp3"
TRACK_RESTORED = "terrestrial_memory.ogg"


class AudioManager:
    """
    Central audio controller managing background music cross-fades,
    procedural sound effect channels, volume attenuation, and headless/dummy driver safety.
    """

    # pygame exposes one process-wide music stream, even with multiple managers.
    _request_lock = threading.Lock()
    _request_generation = 0
    _music_owner = None

    def __init__(self, audio_dir: Optional[Path] = None):
        self.audio_dir: Path = Path(audio_dir) if audio_dir is not None else AUDIO_DIR
        self.enabled: bool = False
        self.is_muted: bool = False
        self.master_volume: float = 1.0
        self.music_volume: float = 0.75
        self.sfx_volume: float = 0.85

        self.sfx_bank: Dict[str, pygame.mixer.Sound] = {}
        self.current_track: Optional[str] = None
        self.target_track: Optional[str] = None
        self.fade_duration_s: float = 1.0
        self.fade_timer_s: float = 0.0
        self.fade_state: str = "IDLE"  # "IDLE", "FADING_OUT", "FADING_IN"
        self._load_thread: Optional[threading.Thread] = None
        self._pending_music = None
        self._ready_music = None
        self._music_stream = None
        self._music_generation = 0
        self._target_loop = True
        self._target_fade_ms = 1000
        self.world_tracks = self._load_world_tracks()

        self._init_mixer()

    def _load_world_tracks(self):
        """Read packaged world assignments once, with the Earth score as fallback."""
        path = self._audio_path('manifest.json')
        if path is None:
            return {}
        try:
            tracks = json.loads(path.read_text(encoding='utf-8'))['music_tracks']
            return {entry['world_id']: filename for filename, entry in tracks.items()
                    if isinstance(entry, dict)
                    and isinstance(entry.get('world_id'), str)
                    and re.fullmatch(r'alien_(?:\d{3}|scan_h)', entry['world_id'])
                    and self._audio_path(filename) is not None}
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return {}

    def _audio_path(self, filename):
        """Resolve one file inside the audio bank without following redirects."""
        if not isinstance(filename, str):
            return None
        relative = Path(filename)
        if relative.is_absolute() or relative.name != filename or filename in ('', '.', '..'):
            return None
        root = self.audio_dir.absolute()
        path = root / relative
        if root.is_symlink() or path.is_symlink():
            return None
        if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
            return None
        return path

    def _init_mixer(self):
        """Safely initialize pygame.mixer with headless fallback."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
            self.enabled = True
            self._load_sfx_bank()
        except Exception:
            # Headless or missing audio driver environment (SDL_AUDIODRIVER=dummy)
            self.enabled = False

    def _load_sfx_bank(self):
        """Pre-load WAV sound effects from assets/audio/ into memory."""
        if not self.enabled:
            return

        sound_names = [
            "maser_tap.wav",
            "maser_charge.wav",
            "impact_spark.wav",
            "alarm_lock.wav",
            "station_chime.wav",
            "printer_chatter.wav",
            "player_jump.wav",
            "player_land.wav",
            "player_slide.wav",
            "player_hurt.wav",
            "enemy_telegraph.wav",
            "boss_mortar_launch.wav",
        ]

        for s_name in sound_names:
            s_path = self._audio_path(s_name)
            if s_path is not None:
                try:
                    snd = pygame.mixer.Sound(str(s_path))
                    # Prevent clipping by setting sensible baseline volume
                    snd.set_volume(self._calc_sfx_gain(1.0))
                    self.sfx_bank[s_name] = snd
                    # Also register without .wav extension for convenience
                    base_key = s_name.replace(".wav", "")
                    self.sfx_bank[base_key] = snd
                except Exception:
                    pass

    def _calc_sfx_gain(self, volume: float) -> float:
        """Compute final attenuated volume factor."""
        if self.is_muted or not self.enabled:
            return 0.0
        return max(0.0, min(1.0, volume * self.sfx_volume * self.master_volume))

    def _calc_music_gain(self) -> float:
        """Compute final attenuated music volume factor."""
        if self.is_muted or not self.enabled:
            return 0.0
        return max(0.0, min(1.0, self.music_volume * self.master_volume))

    def play_sfx(self, name: str, volume: float = 1.0) -> bool:
        """
        Play a sound effect from the loaded bank.
        Returns True if successfully played, False if muted/disabled/missing.
        """
        if not self.enabled or self.is_muted:
            return False

        key = name.replace(".wav", "")
        snd = self.sfx_bank.get(key) or self.sfx_bank.get(name)
        if snd is None:
            return False

        gain = self._calc_sfx_gain(volume)
        if gain <= 0.0:
            return False

        try:
            snd.set_volume(gain)
            snd.play()
            return True
        except Exception:
            return False

    def _next_music_generation(self):
        """Invalidate older requests across managers; caller holds _request_lock."""
        AudioManager._request_generation += 1
        AudioManager._music_owner = self
        self._music_generation = AudioManager._request_generation
        self._pending_music = None
        self._ready_music = None
        return self._music_generation

    def _queue_music(self, request):
        """Replace the pending operation and start at most one worker per manager.

        Caller holds _request_lock. The worker exits when no work remains.
        """
        self._pending_music = request
        if self._load_thread is None:
            self._load_thread = threading.Thread(target=self._music_worker, name="AudioLoad", daemon=True)
            self._load_thread.start()

    def _music_worker(self):
        while True:
            with AudioManager._request_lock:
                request = self._pending_music
                self._pending_music = None
                if request is None:
                    self._load_thread = None
                    return
            generation, path, loop, fade_ms = request
            path = self._audio_path(path.name)
            if path is None:
                continue
            try:
                data = path.read_bytes()
            except OSError:
                continue
            with AudioManager._request_lock:
                if (generation == self._music_generation == AudioManager._request_generation
                        and AudioManager._music_owner is self):
                    self._ready_music = (generation, data, path.suffix.lstrip("."), loop, fade_ms)

    def play_music(self, track_filename: str, loop: bool = True, fade_ms: int = 1000):
        """
        Stream background music track with smooth cross-fade.
        Safe against already-playing duplicate requests.
        """
        track_path = self._audio_path(track_filename)
        if track_path is None:
            return
        if not self.enabled:
            self.current_track = track_filename
            return

        try:
            busy = pygame.mixer.music.get_busy()
            with AudioManager._request_lock:
                if (AudioManager._music_owner is self and self.current_track == track_filename
                        and busy and self.fade_state == "IDLE"):
                    return
                generation = self._next_music_generation()
                if busy:
                    self.target_track = track_filename
                    self._target_loop = loop
                    self._target_fade_ms = fade_ms
                    self.fade_duration_s = max(0.1, fade_ms / 1000.0)
                    self.fade_timer_s = self.fade_duration_s
                    self.fade_state = "FADING_OUT"
                else:
                    self.current_track = track_filename
                    self.target_track = None
                    self.fade_state = "IDLE"
                    self._queue_music((generation, track_path, loop, fade_ms))
            if busy:
                # Cross-fade out existing track first
                pygame.mixer.music.fadeout(int(self.fade_duration_s * 1000))
        except Exception:
            pass

    def transition_scene_music(self, state_name: str, fade_ms: int = 1000, *, world_id=None):
        """Keep a world's score through its field, guardian and earned contact."""
        bunker_states = (
            config.STATE_TITLE_BOOT,
            config.STATE_BUNKER_HUB,
            config.STATE_CRT_TERMINAL,
            config.STATE_SCIENCE_LAB,
        )
        combat_states = (
            config.STATE_FIELD_OPS,
            config.STATE_BOSS_BOUNTY,
            config.STATE_ALIEN_CONTACT,
        )

        target = None
        if state_name in bunker_states:
            target = TRACK_BUNKER
        elif state_name == config.STATE_RESTORED_EARTH:
            target = TRACK_RESTORED if self._audio_path(TRACK_RESTORED) else TRACK_BUNKER
        elif state_name in combat_states:
            target = self.world_tracks.get(world_id, TRACK_COMBAT)
            if self._audio_path(target) is None:
                target = TRACK_COMBAT

        # A quick field → boss transition must not restart the outgoing fade.
        if (target == self.target_track and self.fade_state == 'FADING_OUT'
                and AudioManager._music_owner is self):
            return

        if target and (target != self.current_track or self.fade_state != "IDLE"
                       or AudioManager._music_owner is not self):
            self.play_music(target, loop=True, fade_ms=fade_ms)

    def set_master_volume(self, val: float):
        """Set master volume in range [0.0, 1.0]."""
        self.master_volume = max(0.0, min(1.0, float(val)))
        if self.enabled:
            try:
                pygame.mixer.music.set_volume(self._calc_music_gain())
            except Exception:
                pass

    def set_music_volume(self, val: float):
        """Set music volume in range [0.0, 1.0]."""
        self.music_volume = max(0.0, min(1.0, float(val)))
        if self.enabled:
            try:
                pygame.mixer.music.set_volume(self._calc_music_gain())
            except Exception:
                pass

    def set_sfx_volume(self, val: float):
        """Set SFX volume in range [0.0, 1.0]."""
        self.sfx_volume = max(0.0, min(1.0, float(val)))

    def toggle_mute(self) -> bool:
        """Toggle mute state on or off."""
        self.is_muted = not self.is_muted
        if self.enabled:
            try:
                pygame.mixer.music.set_volume(self._calc_music_gain())
            except Exception:
                pass
        return self.is_muted

    def update(self, dt: float):
        """Step cross-fade transitions and channel lifecycles."""
        if not self.enabled:
            return

        # Workers only read bytes; all native mixer operations stay on the caller's
        # thread, so pygame.quit cannot race a background SDL music load.
        with AudioManager._request_lock:
            ready = self._ready_music
            self._ready_music = None
            if (ready is not None and ready[0] == self._music_generation == AudioManager._request_generation
                    and AudioManager._music_owner is self):
                _, data, namehint, loop, fade_ms = ready
                try:
                    if pygame.mixer.get_init():
                        stream = BytesIO(data)
                        pygame.mixer.music.load(stream, namehint)
                        self._music_stream = stream
                        pygame.mixer.music.set_volume(self._calc_music_gain())
                        pygame.mixer.music.play(-1 if loop else 0, fade_ms=fade_ms)
                except Exception:
                    pass

        if self.fade_state == "IDLE":
            return

        if self.fade_state == "FADING_OUT":
            self.fade_timer_s -= dt
            busy = pygame.mixer.music.get_busy()
            if self.fade_timer_s <= 0.0 or not busy:
                # Queue the target's bytes; a later update starts the fade-in.
                with AudioManager._request_lock:
                    owns_request = (AudioManager._music_owner is self and
                                    self._music_generation == AudioManager._request_generation)
                    if self.target_track and owns_request:
                        # Simulation time can advance faster than SDL's real-time fade.
                        # Finish that fade before the next load, which otherwise waits
                        # for the remaining fade inside SDL_mixer.
                        if busy:
                            pygame.mixer.music.stop()
                        target_path = self._audio_path(self.target_track)
                        if target_path is not None:
                            self.current_track = self.target_track
                            self._queue_music((self._music_generation, target_path,
                                               self._target_loop, self._target_fade_ms))
                    self.target_track = None
                    self.fade_state = "IDLE"

    def stop_all(self):
        """Invalidate pending music immediately, without waiting for a blocked read."""
        with AudioManager._request_lock:
            owns_music = AudioManager._music_owner is self
            if owns_music:
                self._next_music_generation()
                AudioManager._music_owner = None
            else:
                self._pending_music = None
                self._ready_music = None
            self.current_track = None
            self.target_track = None
            self.fade_state = "IDLE"
        if self.enabled and pygame.mixer.get_init():
            try:
                if owns_music:
                    pygame.mixer.music.stop()
                    self._music_stream = None
                pygame.mixer.stop()
            except Exception:
                pass

