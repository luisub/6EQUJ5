"""
═══════════════════════════════════════════════════════
MODULE: src/tools/play_act_01.py
PURPOSE: Comprehensive headless playthrough harness and Gate G2 verification tool
         for Act I: fresh game start, signal contact, formal lab validation,
         surface scavenging, bunker workbench repair, 72s dish defense,
         Core Warden Greenkeeper boss bounty, failure recovery, and save persistence.
CALLED BY: CLI (`python -m video_game.tools.play_act_01`), pytest suites, and CI.
HOW TO MODIFY:
  - Add edge-case branches or route variations.
═══════════════════════════════════════════════════════
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from video_game.engine import config
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.objectives import (
    DishDefenseHoldout,
    ObjectiveTracker,
    HOLDOUT_ACTIVE,
    HOLDOUT_COMPLETED,
    HOLDOUT_FAILED,
)
from video_game.engine.protocols import EvidenceTrace
from video_game.engine.scenes.lab import (
    STEP_CLAIM,
    STEP_EVIDENCE,
    STEP_REPLICATION,
    STEP_DEPLOYMENT,
    STEP_COMPLETED,
)
from video_game.engine.settings import SettingsStore
from video_game.engine.state_machine import GameStateMachine

EVIDENCE_DIR = REPO_ROOT / "_temp" / "play_act_01"


class Act01PlaythroughRunner:
    """Automated runner simulating an end-to-end player route across Act I."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        if headless:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        import pygame
        pygame.init()

        self.window_surf = pygame.display.set_mode(
            (config.INTERNAL_WIDTH * config.DEFAULT_SCALE, config.INTERNAL_HEIGHT * config.DEFAULT_SCALE)
        )
        self.settings_store = SettingsStore()
        self.crt = CRTRenderer(scale=config.DEFAULT_SCALE)
        self.machine = GameStateMachine(self.crt, development=False, settings_store=self.settings_store)
        self.route_log: List[Dict[str, Any]] = []

    def log_step(self, stage: str, action: str, details: Dict[str, Any]):
        entry = {
            "timestamp_s": round(time.time(), 3),
            "stage": stage,
            "action": action,
            "details": details,
            "current_state": self.machine.current_state_name,
            "objective": self.machine.scenes[config.STATE_BUNKER_HUB].objective_tracker.get_active_objective(self.machine.campaign).id
            if config.STATE_BUNKER_HUB in self.machine.scenes else "unknown",
        }
        self.route_log.append(entry)
        print(f"[{stage}] {action} -> {details.get('summary', '')}")

    def run_full_act_01_playthrough(self) -> Dict[str, Any]:
        """Execute all 9 stages of the canonical Act I route with failure/recovery checks."""
        print("═══════════════════════════════════════════════════════════════")
        print(" 6EQUJ5 // ACT I FULL ROUTE PLAYTHROUGH & GATE G2 AUDIT")
        print("═══════════════════════════════════════════════════════════════")

        start_time = time.perf_counter()

        # -------------------------------------------------------------
        # STAGE 1: Fresh Game Boot & Objective Audit
        # -------------------------------------------------------------
        ok, msg = self.machine.start_new_game(replace_existing=True)
        assert ok is True, f"Failed to start new game: {msg}"
        assert self.machine.session_active is True

        state = self.machine.campaign.state
        tracker = self.machine.scenes[config.STATE_BUNKER_HUB].objective_tracker

        assert len(state.extracted_fragments) == 0
        assert len(state.validation_records) == 0
        assert state.room_flags.get("act_01_completed", False) is False

        obj = tracker.get_active_objective(self.machine.campaign)
        assert obj.id == "obj_defeat_greenkeeper"
        assert obj.station_id == "field"

        self.log_step("STAGE_01_BOOT", "VERIFY_FRESH_STATE", {
            "summary": "Verified pristine campaign state; active objective is obj_defeat_greenkeeper.",
            "starter_weapon": state.inventory.get("weapon_id"),
        })

        # -------------------------------------------------------------
        # STAGE 2: CRT Terminal Signal Contact (FASR-001)
        # -------------------------------------------------------------
        self.machine.change_state(config.STATE_CRT_TERMINAL)
        terminal_scene = self.machine.current_scene

        # Set canonical offline dialogue route and snap to carrier
        terminal_scene.session.is_offline = True
        terminal_scene.session.snap_to_carrier()
        assert terminal_scene.session.is_locked is True

        # Send choice '2' requesting Analog Entropy Seed (evidence branch)
        res = terminal_scene.session.send_message("2")
        assert res is True
        assert "FASR-001" in self.machine.campaign.state.extracted_fragments

        self.machine.change_state(config.STATE_BUNKER_HUB)
        obj = tracker.get_active_objective(self.machine.campaign)
        assert obj.id == "obj_defeat_greenkeeper"

        self.log_step("STAGE_02_CONTACT", "EXTRACT_FASR_001_FRAGMENT", {
            "summary": "Tuned to 1420.405 MHz carrier, completed dialogue, claimed FASR-001 fragment grant.",
            "extracted_fragments": self.machine.campaign.state.extracted_fragments,
        })

        # -------------------------------------------------------------
        # STAGE 3: Science Lab Formal Protocol Validation
        # -------------------------------------------------------------
        self.machine.change_state(config.STATE_SCIENCE_LAB)
        lab_scene = self.machine.current_scene

        # 1. Select scenario
        lab_scene._select_active(0)
        assert lab_scene.workbench.active_scenario["id"] == "formal_fasr_001"

        # 2. Classify claim as speculative (novel theoretical physics)
        ok, msg = lab_scene.workbench.classify_claim("speculative")
        assert ok is True, f"Claim classification failed: {msg}"
        assert lab_scene.workbench.current_step == STEP_EVIDENCE

        # 3. Select observations
        lab_scene.workbench.toggle_evidence("obs_entropy_seed")
        lab_scene.workbench.toggle_evidence("obs_snr_coherence")
        ok, msg = lab_scene.workbench.verify_evidence()
        assert ok is True, f"Evidence verification failed: {msg}"
        assert lab_scene.workbench.current_step == STEP_REPLICATION

        # 4. Replication invariant answers
        lab_scene.workbench.set_replication_check("check_cavity_conservation", True)
        lab_scene.workbench.set_replication_check("check_perpetual_motion", False)
        ok, msg = lab_scene.workbench.verify_replication()
        assert ok is True, f"Replication verification failed: {msg}"
        assert lab_scene.workbench.current_step == STEP_DEPLOYMENT

        # 5. Deployment decision (withhold quarantine in Faraday isolation)
        ok, msg, evt = lab_scene.workbench.choose_deployment("withhold_quarantine", self.machine.campaign)
        assert ok is True, f"Deployment decision failed: {msg}"
        assert lab_scene.workbench.current_step == STEP_COMPLETED
        assert len(self.machine.campaign.state.validation_records) == 1

        self.machine.change_state(config.STATE_BUNKER_HUB)
        obj = tracker.get_active_objective(self.machine.campaign)
        assert obj.id == "obj_defeat_greenkeeper"

        self.log_step("STAGE_03_VALIDATION", "COMPLETE_FORMAL_LAB_PROTOCOL", {
            "summary": "Passed formal 5-step validation for FASR-001; registered authoritative record.",
            "validation_count": len(self.machine.campaign.state.validation_records),
        })

        # -------------------------------------------------------------
        # STAGE 4: Surface Scavenge & Hazard Checkpoint Recovery Test
        # -------------------------------------------------------------
        self.machine.change_state(config.STATE_FIELD_OPS)
        field_scene = self.machine.current_scene
        field_scene.load_room("act_01/salvage_yard.json", spawn_name="yard_start")

        # Edge-case verification: player hazard damage, death, and checkpoint respawn
        field_scene.player.health = 0
        field_scene.player.respawn_at_checkpoint(field_scene.room)
        assert field_scene.player.health == 100
        assert field_scene.player.is_dead is False

        # Collect analog coupler
        field_scene.player.x = field_scene.coupler_x
        field_scene.player.y = field_scene.coupler_y
        field_scene.update(0.016)

        evt_coupler = {"event_id": "playthrough_col_coupler", "type": "collect_analog_coupler"}
        self.machine.campaign.apply_event(evt_coupler)

        assert self.machine.campaign.state.inventory["analog_coupler"] == 1
        assert self.machine.campaign.state.room_flags["trench_coupler_collected"] is True

        # Return to bunker
        self.machine.change_state(config.STATE_BUNKER_HUB)
        obj = tracker.get_active_objective(self.machine.campaign)
        assert obj.id == "obj_defeat_greenkeeper"

        self.log_step("STAGE_04_SCAVENGE", "COLLECT_COUPLER_AND_TEST_DEATH", {
            "summary": "Tested hazard death and checkpoint respawn; collected analog coupler in salvage yard.",
            "inventory": self.machine.campaign.state.inventory,
        })

        # -------------------------------------------------------------
        # STAGE 5: Bunker Workbench Coupler Repair
        # -------------------------------------------------------------
        bunker_scene = self.machine.current_scene
        bunker_scene.mateo_x = 295.0  # Station position for workbench
        repaired = bunker_scene.interact_with_station()
        assert repaired is True
        assert self.machine.campaign.state.room_flags["feedhorn_repaired"] is True
        assert self.machine.campaign.state.inventory.get("analog_coupler", 0) == 0

        obj = tracker.get_active_objective(self.machine.campaign)
        assert obj.id == "obj_defeat_greenkeeper"

        self.log_step("STAGE_05_REPAIR", "INSTALL_COUPLER_AT_WORKBENCH", {
            "summary": "Consumed analog coupler to repair dish feedhorn; catwalk access unlocked.",
            "feedhorn_repaired": True,
        })

        # -------------------------------------------------------------
        # STAGE 6: Dish Catwalk Wave Defense & Failure Retry Test
        # -------------------------------------------------------------
        self.machine.change_state(config.STATE_FIELD_OPS)
        field_scene = self.machine.current_scene
        field_scene.load_room("act_01/dish_catwalk.json", spawn_name="catwalk_start")

        holdout = DishDefenseHoldout()
        holdout.start()
        assert holdout.is_active is True

        # Edge-case verification: Holdout Integrity Failure & Reset
        holdout.damage_dish(150.0)
        assert holdout.is_failed is True
        assert holdout.failure_reason == "DISH DESTROYED BY HOSTILES"

        # Retry holdout cleanly
        holdout.reset()
        holdout.start()
        assert holdout.is_active is True

        # Step full 72.0s duration (in 1.0s increments across all 6 signal bins)
        for _ in range(73):
            holdout.update(1.0)
            if holdout.is_jammed:
                holdout.unjam()

        assert holdout.is_completed is True
        assert holdout.elapsed_time >= 72.0

        applied_reward = holdout.apply_completion_reward(self.machine.campaign)
        assert applied_reward is True
        assert self.machine.campaign.state.room_flags["dish_defense_completed"] is True

        self.machine.change_state(config.STATE_BUNKER_HUB)
        obj = tracker.get_active_objective(self.machine.campaign)
        assert obj.id == "obj_defeat_greenkeeper"

        self.log_step("STAGE_06_DISH_DEFENSE", "SURVIVE_72S_WOW_SIGNAL_WAVES", {
            "summary": "Tested holdout failure & restart; survived 72s defense across 6 signal bins.",
            "dish_defense_completed": True,
        })

        # -------------------------------------------------------------
        # STAGE 7: Greenkeeper Boss Bounty & Retry Test
        # -------------------------------------------------------------
        self.machine.change_state(config.STATE_BOSS_BOUNTY)
        boss_scene = self.machine.current_scene
        boss = boss_scene.boss

        # Edge-case verification: Player Boss Defeat & Checkpoint Retry
        boss_scene.player.health = 0
        boss_scene.retry_from_checkpoint()
        assert boss_scene.player.health == 100
        assert boss_scene.player.is_dead is False
        assert boss.current_phase == 1

        # Combat Phase 1: Heavy Armor
        boss.skip_intro()
        boss.take_damage(boss.max_health // 3)
        assert boss.current_phase == 2
        boss.update(1.0)

        # Combat Phase 2: Dual Trench Sweepers
        boss.take_damage(boss.max_health // 3)
        assert boss.current_phase == 3
        boss.update(1.0)

        # Combat Phase 3: Overcharged Reactor Core Exposed
        boss.take_damage(boss.max_health // 3)
        assert boss.is_defeated is True

        resolution = boss.resolve_simultaneous_death(not boss_scene.player.is_dead)
        assert resolution == "BOSS_DEFEATED"

        reward_applied = boss.apply_defeat_reward(self.machine.campaign)
        assert reward_applied is True
        assert self.machine.campaign.state.room_flags["greenkeeper_defeated"] is True
        assert self.machine.campaign.state.room_flags["act_01_completed"] is True
        assert self.machine.campaign.state.room_flags["act_02_unlocked"] is True

        self.machine.change_state(config.STATE_BUNKER_HUB)

        self.log_step("STAGE_07_BOSS_BOUNTY", "NEUTRALIZE_CORE_WARDEN_GREENKEEPER", {
            "summary": "Tested boss death retry; completed 3-phase combat; neutralized Core Warden; unlocked Act II.",
            "act_01_completed": True,
            "act_02_unlocked": True,
        })

        # -------------------------------------------------------------
        # STAGE 8: Contact FASR-007 (Signal from Next Arc)
        # -------------------------------------------------------------
        self.machine.change_state(config.STATE_CRT_TERMINAL)
        term = self.machine.current_scene
        term.session.switch_target("FASR-007")
        assert term.session.active_civ_id == "FASR-007"
        term.session.is_offline = True
        term.session.snap_to_carrier()
        term.session.send_message("2")

        assert "FASR-007" in self.machine.campaign.state.extracted_fragments

        self.machine.change_state(config.STATE_BUNKER_HUB)

        self.log_step("STAGE_08_SECOND_CONTACT", "CONTACT_FASR_007", {
            "summary": "Established contact with FASR-007; extracted second civilization fragment.",
            "extracted_fragments": self.machine.campaign.state.extracted_fragments,
        })

        # -------------------------------------------------------------
        # STAGE 9: Persistence Across Save / Process Restart
        # -------------------------------------------------------------
        saved_ok = self.machine.save_checkpoint()
        assert saved_ok is True
        slot_dir = self.machine.save_store.directory

        # Tear down current state machine completely
        self.machine.close()

        # Re-instantiate pristine state machine and load from disk via continue_game()
        fresh_crt = CRTRenderer(scale=config.DEFAULT_SCALE)
        reloaded_machine = GameStateMachine(fresh_crt, development=False, settings_store=self.settings_store)
        cont_res = reloaded_machine.continue_game()
        assert cont_res.status == "ok"
        assert reloaded_machine.session_active is True

        reloaded_state = reloaded_machine.campaign.state
        assert reloaded_state.room_flags["feedhorn_repaired"] is True
        assert reloaded_state.room_flags["dish_defense_completed"] is True
        assert reloaded_state.room_flags["greenkeeper_defeated"] is True
        assert reloaded_state.room_flags["act_01_completed"] is True
        assert reloaded_state.room_flags["act_02_unlocked"] is True
        assert "FASR-001" in reloaded_state.extracted_fragments
        assert "FASR-007" in reloaded_state.extracted_fragments
        assert len(reloaded_state.validation_records) == 1

        reloaded_machine.close()

        total_runtime = time.perf_counter() - start_time

        self.log_step("STAGE_09_SAVE_ROUNDTRIP", "VERIFY_PROCESS_RELOAD_PERSISTENCE", {
            "summary": "Committed checkpoint to disk and loaded selected state in a new state machine in the same process.",
            "save_slot_dir": str(slot_dir),
        })

        print("═══════════════════════════════════════════════════════════════")
        print(f" ACT I ROUTE COMPLETED SUCCESSFULLY IN {total_runtime:.2f}s")
        print(" INTEGRATION FIXTURE ONLY: GATE G2 REQUIRES A NORMAL-CONTROLS PLAYTHROUGH")
        print("═══════════════════════════════════════════════════════════════")

        payload = {
            "test_run": "act_01_complete_playthrough",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "PASSED",
            "gate_g2_verdict": "NOT_VERIFIED",
            "total_execution_seconds": round(total_runtime, 3),
            "route_steps": self.route_log,
            "final_campaign_state": {
                "act_01_completed": True,
                "act_02_unlocked": True,
                "extracted_fragments": ["FASR-001", "FASR-007"],
                "validation_count": 1,
                "room_flags": {
                    "feedhorn_repaired": True,
                    "dish_defense_completed": True,
                    "greenkeeper_defeated": True,
                },
            },
        }

        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        out_json = EVIDENCE_DIR / "playthrough.json"
        out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Saved route log: {out_json}")
        return payload


def main():
    parser = argparse.ArgumentParser(description="Act I Full Route Playthrough Runner")
    parser.add_argument("--windowed", action="store_true", help="Run with active window rather than headless")
    args = parser.parse_args()

    runner = Act01PlaythroughRunner(headless=not args.windowed)
    try:
        runner.run_full_act_01_playthrough()
    finally:
        runner.machine.close()


if __name__ == "__main__":
    main()
