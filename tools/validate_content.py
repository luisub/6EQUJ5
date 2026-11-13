"""
MODULE: tools/validate_content.py
PURPOSE: Standalone CLI and verification tool to validate level data against DATA_CONTRACTS.md and campaign registries.
CALLED BY: pytest, CLI execution (`python -m tools.validate_content`).
HOW TO MODIFY: Add checks for new room components, enemy spawns, or interactable props; maintain zero wildcard imports.
"""

import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from video_game.engine.campaign import load_campaign_data
from video_game.engine.world import Room

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "data"
LEVELS_DIR = DATA_DIR / "levels"


def validate_level_file(path: Path, campaign_data: Optional[Dict[str, Any]] = None) -> List[str]:
    """Validate a single level JSON file and return list of actionable errors."""
    if not path.exists():
        return [f"File not found: {path}"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"JSON syntax error in {path.name}: {exc}"]

    room = Room(data)
    errors = room.validate(campaign_data=campaign_data)
    return errors


def validate_all_levels(
    levels_dir: Optional[Path] = None,
    campaign_data: Optional[Dict[str, Any]] = None
) -> Dict[str, List[str]]:
    """Scan and validate all level JSON files under data/levels/."""
    target_dir = levels_dir or LEVELS_DIR
    c_data = campaign_data or load_campaign_data()

    results: Dict[str, List[str]] = {}
    if not target_dir.exists():
        return {"all": [f"Levels directory not found: {target_dir}"]}

    level_files = sorted(target_dir.rglob("*.json"))
    if not level_files:
        return {"all": [f"No level files found in {target_dir}"]}

    for lf in level_files:
        rel_key = str(lf.relative_to(target_dir))
        errs = validate_level_file(lf, campaign_data=c_data)
        results[rel_key] = errs

    return results


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point for content validation."""
    c_data = load_campaign_data()
    all_results = validate_all_levels(campaign_data=c_data)

    total_errors = 0
    print("=" * 60)
    print("6EQUJ5 LEVEL CONTENT VALIDATION")
    print("=" * 60)

    for level_name, errors in all_results.items():
        if not errors:
            print(f"[OK] {level_name}")
        else:
            print(f"[FAIL] {level_name}:")
            for err in errors:
                print(f"  - {err}")
                total_errors += 1

    print("=" * 60)
    if total_errors == 0:
        print(f"SUCCESS: All {len(all_results)} levels validated cleanly.")
        return 0
    else:
        print(f"FAILURE: Found {total_errors} errors across {len(all_results)} levels.")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

