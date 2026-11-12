"""PURPOSE: Register the annex candidate behind the actual two timeline layouts.
CALLED BY: From repo root with dummy SDL; supply a new --output-dir.
HOW TO MODIFY: Preserve full source framing, temporary saves and labeled fixture limits.
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import pygame
from PIL import Image

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine

SOURCE = Path("video_game/art/source/visual_upgrade/candidates/annex_shared_background_v01/source/annex_shared_background_generated_master.png")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    export = args.output_dir / "annex_shared_background_960x576.png"
    with Image.open(SOURCE) as src:
        if src.mode != "RGB" or src.size != (1620, 971):
            raise ValueError(f"Unexpected source {src.mode} {src.size}")
        source_size = src.size
        src.resize((960, 576), Image.Resampling.LANCZOS).save(export)

    pygame.init()
    pygame.display.set_mode((960, 540))
    try:
        with tempfile.TemporaryDirectory(prefix="6equj5-annex-registration-") as tmp:
            game = GameStateMachine(CRTRenderer(scale=1), save_store=SaveStore(tmp), settings_store=SettingsStore(tmp))
            try:
                game.start_new_game()
                game.change_state(config.STATE_FIELD_OPS)
                scene = game.current_scene
                samples = []
                for timeline in ("2029_CORE", "1977_ANALOG"):
                    scene.load_room("act_01/mandela_test.json", spawn_name="default")
                    if not scene.room.set_active_timeline(timeline):
                        raise ValueError(f"Missing timeline {timeline}")
                    scene.reality.world.active_timeline = timeline
                    for _ in range(30):
                        game.input.begin_frame()
                        game.update(1 / 60)
                    plate = pygame.image.load(str(export)).convert()

                    def background(_surface, camera):
                        source_y = round(2 * camera.y)
                        game.crt.composite_native(plate.subsurface(pygame.Rect(0, source_y, 960, 540)), (0, 0), (480, 270))

                    scene.room.render_background = background
                    for cy in (0, 18):
                        scene.camera.x, scene.camera.y = 0, cy
                        game.render()
                        native = args.output_dir / f"{timeline}_y{cy}_native_960.png"
                        review = args.output_dir / f"{timeline}_y{cy}_review_1920.png"
                        pygame.image.save(game.crt.render_surface, str(native))
                        pygame.image.save(pygame.transform.scale(game.crt.render_surface, (1920, 1080)), str(review))
                        samples.append({"timeline": timeline, "camera": [0, cy], "player_rect": list(scene.player.rect),
                                        "grounded": scene.player.is_grounded, "native": native.name,
                                        "native_sha256": sha(native), "review": review.name, "review_sha256": sha(review)})
                info = {"source": str(SOURCE), "source_size": list(source_size), "source_sha256": sha(SOURCE),
                        "export": export.name, "export_sha256": sha(export),
                        "transform": "Full 1620x971 image Lanczos-resized to 960x576; full canvas retained; approximately 0.1% aspect change, no masks, painting or cleanup.",
                        "composition": "Fixture-local room background callback draws source crop at y=2*camera.y, then actual MandelaWorld tiles, platforms, active objects, weather/transition and normal field actor/HUD.",
                        "fixture": "Dummy SDL, temporary saves, new game, direct annex spawn and directly selected timeline; 30 updates at 1/60 before camera positions; no input or normal-route claim.",
                        "limits": "Static isolated fixture only; no moving-platform endpoint, timeline swap, full interaction, CRT, native window, performance, playthrough or art-gate acceptance.",
                        "samples": samples}
                (args.output_dir / "context.json").write_text(json.dumps(info, indent=2) + "\n")
                print(json.dumps(samples, indent=2))
            finally:
                game.close()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
