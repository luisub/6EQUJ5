"""
MODULE: video_game/engine/save_game.py
PURPOSE: Store validated campaign checkpoints with atomic writes and recovery.
CALLED BY: The game state machine and title scene.
HOW TO MODIFY: Add explicit migrations for supported versions and preserve both
  damaged files and the last valid backup during any recovery or replacement.
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
import tempfile
from uuid import uuid4

from .campaign import Campaign


SAVE_VERSION = 2
SAVE_DIRECTORY_ENV = "SIX_GAME_SAVE_DIR"


class SaveError(RuntimeError):
    """A save operation failed without intentionally discarding prior data."""


@dataclass(frozen=True)
class LoadResult:
    status: str
    message: str
    campaign: Campaign | None = None
    migrated: bool = False


def user_data_dir():
    """Resolve a user-data directory; tests can override it explicitly."""
    override = os.environ.get(SAVE_DIRECTORY_ENV)
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "6EQUJ5"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")) / "6EQUJ5"
    return Path(os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")) / "6EQUJ5"


def _decode(raw):
    """Validate an envelope and migrate the supported version-1 shape in memory."""
    try:
        document = json.loads(raw)
    except (ValueError, UnicodeDecodeError, RecursionError) as exc:
        return LoadResult("corrupt", f"Save is not valid JSON: {exc}")
    if not isinstance(document, dict) or type(document.get("schema_version")) is not int:
        return LoadResult("corrupt", "Save has no valid version")
    version = document["schema_version"]
    if version > SAVE_VERSION:
        return LoadResult("future_version", f"Save version {version} is newer than supported version {SAVE_VERSION}")
    if version < 1:
        return LoadResult("old_version", f"Save version {version} is not supported")
    migrated = version == 1
    if migrated:
        if set(document) != {"schema_version", "campaign"} or not isinstance(document.get("campaign"), dict):
            return LoadResult("migration_failed", "Version 1 save is missing its campaign")
        campaign = document["campaign"]
        try:
            checkpoint = {"room_id": campaign["current_room"], "checkpoint_id": campaign["checkpoint_id"]}
        except KeyError:
            return LoadResult("migration_failed", "Version 1 save is missing checkpoint fields")
        document = {"schema_version": SAVE_VERSION, "campaign": campaign, "checkpoint": checkpoint}
    try:
        if set(document) != {"schema_version", "campaign", "checkpoint"}:
            raise ValueError("unexpected or missing save fields")
        if isinstance(document["campaign"], dict):
            campaign_version = document["campaign"].get("schema_version")
            if type(campaign_version) is int and campaign_version > 1:
                return LoadResult("future_version", f"Campaign version {campaign_version} is newer than supported version 1")
            if type(campaign_version) is int and campaign_version < 1:
                return LoadResult("old_version", f"Campaign version {campaign_version} is not supported")
        campaign = Campaign(document["campaign"])
        state = campaign.state
        if document["checkpoint"] != {"room_id": state.current_room, "checkpoint_id": state.checkpoint_id}:
            raise ValueError("checkpoint does not match campaign state")
    except (KeyError, TypeError, ValueError) as exc:
        return LoadResult("migration_failed" if migrated else "corrupt", f"Invalid campaign or checkpoint: {exc}")
    return LoadResult("ok", "Save loaded", campaign, migrated)


class SaveStore:
    """One save slot and a separately retained last valid backup."""

    def __init__(self, directory=None):
        self.directory = Path(directory) if directory is not None else user_data_dir()
        self.path = self.directory / "campaign.json"
        self.backup_path = self.directory / "campaign.backup.json"

    def has_existing_data(self):
        return self.path.exists() or self.backup_path.exists()

    def _load_path(self, path):
        try:
            raw = path.read_bytes()
        except FileNotFoundError:
            return LoadResult("missing", f"No save found at {path}")
        except OSError as exc:
            return LoadResult("io_error", f"Cannot read save {path}: {exc}")
        return _decode(raw)

    def load(self):
        return self._load_path(self.path)

    def load_backup(self):
        return self._load_path(self.backup_path)

    def _atomic_write(self, destination, raw):
        """Write and validate a sibling before the atomic replacement."""
        temporary = None
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=self.directory)
            temporary = Path(name)
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            staged = temporary.read_bytes()
            if staged != raw or _decode(staged).status != "ok":
                raise SaveError("Staged save did not pass verification")
            os.replace(temporary, destination)
            temporary = None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _preserve_file(self, path):
        """Retain a verbatim copy before replacing an unreadable save file."""
        if not path.exists():
            return None
        raw = path.read_bytes()
        preserved = self.directory / f"{path.stem}.preserved-{uuid4().hex}.json"
        with preserved.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if preserved.read_bytes() != raw:
            raise SaveError(f"Preserved save failed verification: {preserved}")
        return preserved

    def save(self, campaign, *, replace_invalid=False):
        """Save a validated campaign, retaining the previous valid generation."""
        try:
            state = campaign.to_dict()
            checked = Campaign(state)
            checkpoint = {"room_id": checked.state.current_room, "checkpoint_id": checked.state.checkpoint_id}
            document = {"schema_version": SAVE_VERSION, "campaign": checked.to_dict(), "checkpoint": checkpoint}
            raw = (json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
            if _decode(raw).status != "ok":
                raise SaveError("New save failed validation")
            prior = self.load()
            if prior.status == "ok":
                backup = self.load_backup()
                if backup.status == "io_error":
                    raise SaveError(f"Existing backup was preserved: {backup.message}")
                unchanged = prior.campaign.to_dict() == checked.to_dict() and not prior.migrated
                if unchanged and backup.status == "ok":
                    return False
                if backup.status not in ("ok", "missing"):
                    self._preserve_file(self.backup_path)
                self._atomic_write(self.backup_path, self.path.read_bytes())
                if unchanged:
                    return False
            elif prior.status != "missing":
                if prior.status == "io_error" or not replace_invalid:
                    raise SaveError(f"Existing save was preserved ({prior.status}): {prior.message}")
                self._preserve_file(self.path)
            self._atomic_write(self.path, raw)
            return True
        except SaveError:
            raise
        except (OSError, TypeError, ValueError) as exc:
            raise SaveError(f"Could not save campaign: {exc}") from exc

    def recover_backup(self):
        """Explicitly restore a validated backup, preserving any current file."""
        result = self.load_backup()
        if result.status != "ok":
            return result
        try:
            raw = self.backup_path.read_bytes()
            if self.path.exists():
                self._preserve_file(self.path)
            self._atomic_write(self.path, raw)
        except (OSError, SaveError) as exc:
            return LoadResult("io_error", f"Backup was not restored: {exc}")
        return result
