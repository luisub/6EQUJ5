"""
MODULE: video_game/engine/settings.py
PURPOSE: Load and atomically persist validated user-facing game settings.
CALLED BY: The game entry point and pause overlay.
HOW TO MODIFY: Validate each field and retain safe defaults for invalid data;
  audio playback and controller configuration belong to later milestones.
"""

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import tempfile

from .save_game import user_data_dir


MIN_SCALE = 1
MAX_SCALE = 2


@dataclass(frozen=True)
class Settings:
    volume: int = 70
    crt_effects: bool = True
    scale: int = 2


def _validated(data):
    default = Settings()
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] not in (1, 2):
        return default
    volume = data.get("volume")
    scale = data.get("scale")
    if data['schema_version'] == 1:
        scale = {1: 1, 2: 1, 3: 2, 4: 2}.get(scale) if type(scale) is int else None
    effects = data.get("crt_effects")
    return Settings(
        volume=volume if type(volume) is int and 0 <= volume <= 100 else default.volume,
        crt_effects=effects if type(effects) is bool else default.crt_effects,
        scale=scale if type(scale) is int and MIN_SCALE <= scale <= MAX_SCALE else default.scale,
    )


class SettingsError(RuntimeError):
    """Settings could not be safely persisted."""


class SettingsStore:
    """Read settings without rewriting invalid files; write through a sibling."""

    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else user_data_dir()
        self.path = self.directory / "settings.json"
        self.warning = ""

    def load(self):
        self.warning = ""
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return Settings()
        except (OSError, ValueError, UnicodeDecodeError, RecursionError):
            self.warning = "SETTINGS INVALID - USING DEFAULTS"
            return Settings()
        result = _validated(data)
        if isinstance(data, dict) and data.get('schema_version') == 1:
            legacy_scale = data.get('scale')
            expected = {"schema_version": 1, "volume": result.volume, "crt_effects": result.crt_effects, "scale": legacy_scale}
            if type(legacy_scale) is not int or legacy_scale not in (1, 2, 3, 4) or data != expected:
                self.warning = "SOME SETTINGS RESET TO DEFAULTS"
        elif data != {"schema_version": 2, **asdict(result)}:
            self.warning = "SOME SETTINGS RESET TO DEFAULTS"
        return result

    def save(self, settings):
        if not isinstance(settings, Settings):
            raise SettingsError("Invalid settings object")
        data = {"schema_version": 2, **asdict(settings)}
        if _validated(data) != settings:
            raise SettingsError("Invalid settings value")
        temporary = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix=".settings.", suffix=".tmp", dir=self.directory)
            temporary = Path(name)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(data, stream, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            staged = json.loads(temporary.read_text(encoding="utf-8"))
            if staged != data:
                raise SettingsError("Settings write failed verification")
            os.replace(temporary, self.path)
            temporary = None
        except (OSError, ValueError) as exc:
            raise SettingsError(f"Could not save settings: {exc}") from exc
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
