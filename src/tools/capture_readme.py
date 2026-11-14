"""Capture README media from the actual renderer, using isolated save fixtures.

Run: python -m video_game.tools.capture_readme --output <new-directory>
This is a presentation capture, not a full playthrough or gameplay acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from PIL import Image

from video_game.engine import config
from video_game.engine.alien_journey import journey_data, save_ledger
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.save_game import SaveStore
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine


def capture(output):
    output.mkdir(parents=True, exist_ok=False)
    random.seed(1977)
    records = []
    pygame.init()
    pygame.display.set_mode((960, 540))
    with tempfile.TemporaryDirectory(prefix="6equj5-readme-") as temporary:
        previous = os.environ.get("SIX_GAME_SAVE_DIR")
        os.environ["SIX_GAME_SAVE_DIR"] = temporary
        game = GameStateMachine(CRTRenderer(scale=1),
                                save_store=SaveStore(Path(temporary) / "save"),
                                settings_store=SettingsStore(Path(temporary) / "settings"))
        game.change_settings(scale=1, crt_effects=False)

        def key(code, down=True):
            game.handle_event(pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP, key=code))

        def tap(code):
            key(code)
            key(code, False)

        def step(count=1):
            for _ in range(count):
                game.update(1 / 60)
                game.input.begin_frame()

        def fresh():
            assert game.start_new_game(replace_existing=True)[0]
            step(12)

        def frame():
            game.render()
            return game.crt.render_surface.copy()

        def still(name, setup):
            surface = frame()
            pygame.image.save(surface, output / f"{name}.png")
            records.append({"file": f"{name}.png", "setup": setup,
                            "scene": game.current_state_name, "size": list(surface.get_size())})

        def gif(name, frames, setup, duration=100):
            # Shared palette and delta frames keep the actual captured animation small.
            # No composited scenery, UI removal or invented gameplay is introduced.
            palette = frames[len(frames) // 2].quantize(colors=128, dither=Image.Dither.NONE)
            indexed = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
            indexed[0].save(output / f"{name}.gif", save_all=True, append_images=indexed[1:],
                            duration=duration, loop=0, optimize=True, disposal=1)
            records.append({"file": f"{name}.gif", "setup": setup, "frames": len(frames),
                            "frame_duration_ms": duration, "size": list(frames[0].size),
                            "encoding": "128-color shared palette; nearest-neighbor 768 x 432 export"})

        def gif_frame():
            surface = pygame.transform.scale(frame(), (768, 432))
            return Image.frombytes("RGB", surface.get_size(), pygame.image.tobytes(surface, "RGB"))

        def world(index, stage):
            fresh()
            worlds = journey_data()["worlds"]
            game.campaign.apply_event({"event_id": "readme_portal", "type": "defeat_portal_warden"})
            for n, prior in enumerate(worlds[:index]):
                game.campaign.apply_event({"event_id": f"readme_guardian_{n}", "type": prior["defeat_event"]})
            current = worlds[index]
            save_ledger(game.campaign, {"version": 1, "world_id": current["id"], "stage": stage,
                                       "checkpoint": None, "receipts": [w["civ_id"] for w in worlds[:index]]})
            return current

        try:
            fresh()
            still("observatory", "Fresh game in the bunker; opening already dismissed.")
            game.change_state(config.STATE_CRT_TERMINAL)
            step(12)
            still("receiver", "Direct scene entry; initial authored FASR-001 receiver message.")

            fresh()
            tap(pygame.K_RETURN)
            scene = game.current_scene
            game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(900, 424)))
            step(4)
            key(pygame.K_d)
            for _ in range(100):
                step()
                if scene.player.arsenal.temporary_id:
                    break
            key(pygame.K_d, False)
            assert scene.player.arsenal.temporary_id == "arc_lance"
            frames = []
            for i in range(180):
                step()
                if i % 6 == 0:
                    frames.append(gif_frame())
                if i == 24:
                    still("arc-lance", "Arc Lance collected by mapped D movement; mapped mouse fire.")
            game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(900, 424)))
            gif("arc-lance", frames, "Normal bunker exit, mapped movement to pickup and mouse fire; three seconds.")

            rooms = [
                ("ohio", "act_01/ohio_campus.json", "default"),
                ("neo-denver", "act_02/blackout_street.json", "default"),
                ("area-51", "act_03/s4_hangar.json", "default"),
                ("vla-rift", "act_04/rail_yard.json", "default"),
                ("gobekli-tepe", "act_05/pillar_approach.json", "default"),
                ("buried-archive", "act_05/buried_archive.json", "default"),
            ]
            for name, room, spawn in rooms:
                fresh()
                if name == 'neo-denver':
                    game.campaign.apply_event({'event_id': 'readme_denver_prior_act',
                                               'type': 'defeat_greenkeeper'})
                game.change_state(config.STATE_FIELD_OPS, room=room, spawn=spawn,
                                  campaign_route=not room.startswith("act_01/"))
                if name == 'neo-denver':
                    scene = game.current_scene
                    scene.player.x, scene.player.y = 96, 208
                    scene.player.rect.topleft = (96, 208)
                    scene.camera.snap_to(104, 224)
                    game.crt.glitch_timer_ms = 0
                    still(name, 'Direct Denver scene/position setup with prior-act fixture; Fitzsimons and mountain backdrop.')
                    still('neo-denver-mountains', 'Denver entry at x=96 with the ridge and hillside A visible; direct position and prior-act fixtures.')
                    scene.player.x = 480
                    scene.player.rect.topleft = (480, 208)
                    scene.camera.snap_to(488, 224)
                    still('neo-denver-fitzsimons', 'Denver campus at x=480 with the Fitzsimons entrance centered; direct position and prior-act fixtures.')
                    scene.player.x = 96
                    scene.player.rect.topleft = (96, 208)
                    scene.camera.snap_to(104, 224)
                    frames = []
                    key(pygame.K_RIGHT)
                    for index in range(540):
                        scene.enemy_manager.clear()
                        step()
                        if index % 12 == 0:
                            frames.append(gif_frame())
                    key(pygame.K_RIGHT, False)
                    assert scene.room.room_id == 'act_02_relay_rooftops'
                    gif('neo-denver-walk', frames,
                        'Held Right through the Denver/relay boundary; prior-act and starting-position fixtures; enemies cleared for scenery inspection.',
                        duration=200)
                    continue
                key(pygame.K_d)
                step(40)
                key(pygame.K_d, False)
                step(150)
                still(name, f"Direct development scene entry to {room}, then mapped movement; no progression claim.")

            current = world(1, "field")
            game.change_state(config.STATE_FIELD_OPS, room=current["field_room"], spawn="default",
                              journey_world=current["id"], campaign_route=True)
            key(pygame.K_d)
            step(40)
            key(pygame.K_d, False)
            step(150)
            still("crystal-network", "Direct field entry with staged prior guardian and receipt, then mapped movement.")

            current = world(2, "field")
            game.change_state(config.STATE_FIELD_OPS, room=current["field_room"], spawn="default",
                              journey_world=current["id"], campaign_route=True)
            scene = game.current_scene
            scene.player.x, scene.player.y = scene.room.width_px / 2, 208
            scene.player.rect.topleft = (round(scene.player.x), 208)
            scene.camera.snap_to(scene.player.x + 8, 224)
            game.crt.glitch_timer_ms = 0
            still("proxima-twilight", "Proxima field midpoint; prior victories, receipts and player position are scenery fixtures.")

            current = world(2, "guardian")
            game.change_state(config.STATE_BOSS_BOUNTY, room=current["arena_room"],
                              boss_id=current["boss_id"], journey_world=current["id"], spawn="default")
            step(12)
            still("flare-bastion", "Proxima guardian with staged journey ledger; 0.2 seconds of runtime.")
            for index, name in [(0, "signal-jailer"), (1, "heat-auditor")]:
                current = world(index, "guardian")
                game.change_state(config.STATE_BOSS_BOUNTY, room=current["arena_room"],
                                  boss_id=current["boss_id"], journey_world=current["id"], spawn="default")
                step(96)
                still(name, "Guardian scene with staged journey ledger; 1.6 seconds of actual runtime.")

            fresh()
            game.campaign.apply_event({"event_id": "readme_travel", "type": "defeat_portal_warden"})
            tap(pygame.K_RETURN)
            assert game.current_state_name == config.STATE_GALAXY_TRANSIT
            frames = []
            for i in range(246):
                step()
                if i % 6 == 0:
                    frames.append(gif_frame())
                if i == 90:
                    still("galaxy-map", "First Earth-to-FASR-001 transit with staged portal unlock; schematic map.")
            gif("signal-transit", frames, "Actual first-world map, vortex and arrival; staged portal unlock.")
            for record in records:
                path = output / record["file"]
                record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                record["bytes"] = path.stat().st_size
            (output / "capture.json").write_text(json.dumps({
                "purpose": "README presentation; not gameplay acceptance or a full playthrough",
                "video_driver": pygame.display.get_driver(), "audio_driver": "dummy",
                "crt_effects": False, "isolated_temporary_saves": True, "seed": 1977,
                "screenshots": "Unretouched render surfaces at 960 x 540",
                "captures": records,
            }, indent=2) + "\n")
        finally:
            game.close()
            pygame.quit()
            if previous is None:
                os.environ.pop("SIX_GAME_SAVE_DIR", None)
            else:
                os.environ["SIX_GAME_SAVE_DIR"] = previous
    print(f"Captured {len(records)} assets in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    capture(parser.parse_args().output)
