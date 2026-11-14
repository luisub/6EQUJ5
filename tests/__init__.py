"""Shared test paths, valid before and after moving tests into src/."""
from pathlib import Path

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents
                 if (parent / "pyproject.toml").is_file())
