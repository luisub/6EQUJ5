"""
MODULE: video_game/engine/scenes/lab.py
PURPOSE: Interactive scientific validation workbench scene for formal claim/evidence puzzles and deployment decisions.
CALLED BY: video_game.engine.state_machine, video_game.engine.scenes.bunker.
HOW TO MODIFY: Add rendering controls, visual layout, and interactive inputs for validation workbenches.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import pygame

from video_game.engine import config
from video_game.engine.labs.biosecurity import BiosecurityValidationWorkbench
from video_game.engine.labs.formal import (
    FormalValidationWorkbench,
    STEP_SELECT,
    STEP_CLAIM,
    STEP_EVIDENCE,
    STEP_REPLICATION,
    STEP_DEPLOYMENT,
    STEP_COMPLETED,
)
from video_game.engine.labs.neuro import ConnectomeValidationWorkbench
from video_game.engine.labs.quantum import QuantumValidationWorkbench
from video_game.engine.protocols import ScienceArcManager
from video_game.engine.scenes.base import BaseScene
from video_game.engine.ui.text import ellipsize_pixels, wrap_text_pixels

STEP_EXPERIMENT = "EXPERIMENT"


class ScienceLabScene(BaseScene):
    """
    Formal scientific validation workbench scene across all four disciplines:
    Thermodynamic/Formal, Quantum Optics, Connectome, and Biosecurity.

    Provides a dual-CRT laboratory workstation where operators inspect
    signal fragments, simulate bounded physics/biology experiments, classify
    scientific claims, filter empirical evidence from counterexamples,
    verify conservation invariants, and commit risk-managed protocol
    deployment decisions that update the six campaign meters.
    """

    def __init__(self, machine: Any):
        super().__init__(machine)
        self.arc_manager = ScienceArcManager()
        self.scenarios = self.arc_manager.scenarios
        self.scenario_keys: List[str] = list(self.scenarios.keys())
        self.active_idx: int = 0
        self.workbench: Any = None
        self.cursor_timer: float = 0.0
        self.details_open = False
        self.details_offset = 0

        # Auto-select first scenario on boot
        if self.scenario_keys:
            self._select_active(0)

    @property
    def campaign(self) -> Optional[Any]:
        """Access campaign state from game state machine."""
        return getattr(self.machine, "campaign", None)

    def on_enter(self, previous_state_id: Optional[str] = None):
        """Refresh workbench state upon entering lab."""
        if self.scenario_keys and 0 <= self.active_idx < len(self.scenario_keys):
            self._select_active(self.active_idx)

    def _select_active(self, idx: int):
        """Switch active scenario and instantiate the proper workbench type."""
        if not self.scenario_keys:
            return
        self.active_idx = idx % len(self.scenario_keys)
        scen_id = self.scenario_keys[self.active_idx]
        scen = self.scenarios.get(scen_id, {})
        wb_type = scen.get("workbench_type", "formal")

        if wb_type == "quantum":
            self.workbench = QuantumValidationWorkbench(self.arc_manager.scenarios_data)
        elif wb_type == "neuro":
            self.workbench = ConnectomeValidationWorkbench(self.arc_manager.scenarios_data)
        elif wb_type == "biosecurity":
            self.workbench = BiosecurityValidationWorkbench(self.arc_manager.scenarios_data)
        else:
            self.workbench = FormalValidationWorkbench(self.arc_manager.scenarios_data)

        self.workbench.select_scenario(scen_id, self.campaign)

    def handle_event(self, event: pygame.event.Event):
        """Process keyboard interactions across validation pipeline steps."""
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_h:
            self.details_open = not self.details_open
            self.details_offset = 0
            return
        if self.details_open:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.details_open = False
            elif event.key in (pygame.K_DOWN, pygame.K_PAGEDOWN):
                self.details_offset = min(max(0, len(self.get_details_lines()) - 17), self.details_offset + 8)
            elif event.key in (pygame.K_UP, pygame.K_PAGEUP):
                self.details_offset = max(0, self.details_offset - 8)
            return

        # Global exit to bunker hub
        if event.key == pygame.K_ESCAPE:
            self.machine.change_state(config.STATE_BUNKER_HUB)
            return

        # Scenario navigation with arrow keys or Tab
        if event.key == pygame.K_UP:
            self._select_active(self.active_idx - 1)
            return
        elif event.key in (pygame.K_DOWN, pygame.K_TAB):
            self._select_active(self.active_idx + 1)
            return
        elif event.key in (pygame.K_5, pygame.K_KP5) and len(self.scenario_keys) >= 5:
            self._select_active(4)
            return
        elif event.key in (pygame.K_6, pygame.K_KP6) and len(self.scenario_keys) >= 6:
            self._select_active(5)
            return
        elif event.key in (pygame.K_7, pygame.K_KP7) and len(self.scenario_keys) >= 7:
            self._select_active(6)
            return
        elif event.key in (pygame.K_8, pygame.K_KP8) and len(self.scenario_keys) >= 8:
            self._select_active(7)
            return

        if not self.workbench:
            return

        step = self.workbench.current_step

        # Scenario selection step
        if step == STEP_SELECT:
            key_map = {
                pygame.K_1: 0, pygame.K_KP1: 0,
                pygame.K_2: 1, pygame.K_KP2: 1,
                pygame.K_3: 2, pygame.K_KP3: 2,
                pygame.K_4: 3, pygame.K_KP4: 3,
                pygame.K_5: 4, pygame.K_KP5: 4,
                pygame.K_6: 5, pygame.K_KP6: 5,
                pygame.K_7: 6, pygame.K_KP7: 6,
                pygame.K_8: 7, pygame.K_KP8: 7,
            }
            if event.key in key_map:
                target_idx = key_map[event.key]
                if target_idx < len(self.scenario_keys):
                    self._select_active(target_idx)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._select_active(self.active_idx)
            return

        # Step 0: Experiment Phase
        if step == STEP_EXPERIMENT:
            scen = self.workbench.active_scenario or {}
            wb_type = scen.get("workbench_type", "formal")

            if wb_type == "quantum":
                if event.key in (pygame.K_1, pygame.K_KP1):
                    self.workbench.wavelength_nm = 532.0
                    self.workbench.feedback_message = "Tuned laser wavelength to 532 nm (green line)"
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self.workbench.slit_width_um = 20.0
                    self.workbench.feedback_message = "Tuned slit width to 20 um"
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    self.workbench.slit_distance_um = 100.0
                    self.workbench.feedback_message = "Tuned slit distance to 100 um"
                elif event.key in (pygame.K_4, pygame.K_KP4):
                    self.workbench.shielding_factor = 0.90
                    self.workbench.feedback_message = "Engaged cryogenic vacuum shielding to 90%"
                elif event.key == pygame.K_SPACE:
                    self.workbench.run_experiment()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.workbench.advance_to_claim()

            elif wb_type == "neuro":
                target = scen.get("target_circuit", {})
                req_conns = target.get("required_connections", [])
                if event.key in (pygame.K_1, pygame.K_KP1) and len(req_conns) >= 1:
                    c = req_conns[0]
                    self.workbench.patch_cable(c[0], c[1], 1.2)
                elif event.key in (pygame.K_2, pygame.K_KP2) and len(req_conns) >= 2:
                    c = req_conns[1]
                    self.workbench.patch_cable(c[0], c[1], 1.0)
                elif event.key in (pygame.K_3, pygame.K_KP3) and len(req_conns) >= 3:
                    c = req_conns[2]
                    self.workbench.patch_cable(c[0], c[1], -1.5)
                elif event.key == pygame.K_SPACE:
                    self.workbench.run_circuit_trial()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.workbench.advance_to_claim()

            elif wb_type == "biosecurity":
                if event.key in (pygame.K_1, pygame.K_KP1):
                    self.workbench.set_allocation(37.0, 8000.0, 20.0, 1.0)
                    self.workbench.feedback_message = "Allocated optimal incubation parameters (37C, 8k RPM, 20uL)"
                elif event.key == pygame.K_SPACE:
                    self.workbench.run_protocol(steps=4)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.workbench.advance_to_claim()

            else:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                    if hasattr(self.workbench, "advance_to_claim"):
                        self.workbench.advance_to_claim()
                    else:
                        self.workbench.current_step = STEP_CLAIM
            return

        # Step 1: Claim tier classification
        if step == STEP_CLAIM:
            if event.key in (pygame.K_1, pygame.K_KP1):
                self.workbench.classify_claim("established")
            elif event.key in (pygame.K_2, pygame.K_KP2):
                self.workbench.classify_claim("plausible")
            elif event.key in (pygame.K_3, pygame.K_KP3):
                self.workbench.classify_claim("speculative")
            return

        # Step 2: Evidence and counterexample selection
        if step == STEP_EVIDENCE:
            evidence_pool = self.workbench.active_scenario.get("evidence_pool", []) if self.workbench.active_scenario else []
            if event.key in (pygame.K_1, pygame.K_KP1) and len(evidence_pool) >= 1:
                self.workbench.toggle_evidence(evidence_pool[0]["id"])
            elif event.key in (pygame.K_2, pygame.K_KP2) and len(evidence_pool) >= 2:
                self.workbench.toggle_evidence(evidence_pool[1]["id"])
            elif event.key in (pygame.K_3, pygame.K_KP3) and len(evidence_pool) >= 3:
                self.workbench.toggle_evidence(evidence_pool[2]["id"])
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.workbench.verify_evidence()
            return

        # Step 3: Replication invariant checks
        if step == STEP_REPLICATION:
            checks = self.workbench.active_scenario.get("replication_checks", []) if self.workbench.active_scenario else []
            if event.key in (pygame.K_1, pygame.K_KP1) and len(checks) >= 1:
                cid = checks[0]["id"]
                cur = self.workbench.replication_answers.get(cid)
                self.workbench.set_replication_check(cid, True if cur is not True else False)
            elif event.key in (pygame.K_2, pygame.K_KP2) and len(checks) >= 2:
                cid = checks[1]["id"]
                cur = self.workbench.replication_answers.get(cid)
                self.workbench.set_replication_check(cid, False if cur is not False else True)
            elif event.key in (pygame.K_3, pygame.K_KP3) and len(checks) >= 3:
                cid = checks[2]["id"]
                cur = self.workbench.replication_answers.get(cid)
                self.workbench.set_replication_check(cid, True if cur is not True else False)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.workbench.verify_replication()
            return

        # Step 4: Deployment decision
        if step == STEP_DEPLOYMENT:
            choices = self.workbench.active_scenario.get("deployment_choices", []) if self.workbench.active_scenario else []
            if event.key in (pygame.K_1, pygame.K_KP1) and len(choices) >= 1:
                self._commit_deployment(choices[0]["id"])
            elif event.key in (pygame.K_2, pygame.K_KP2) and len(choices) >= 2:
                self._commit_deployment(choices[1]["id"])
            return

        # Completed or retry
        if step == STEP_COMPLETED:
            if event.key == pygame.K_r:
                self._select_active(self.active_idx)

    def update(self, dt_seconds: float):
        """Update cursor blink timer."""
        self.cursor_timer += dt_seconds

    def _commit_deployment(self, decision_id):
        ok, message, record = self.workbench.choose_deployment(decision_id, self.campaign)
        if ok and self.campaign is not None:
            snapshot = self.campaign.state.world_states.get("bunker_hub", {})
            notices = snapshot.setdefault("science_consequences", {})
            notices.setdefault(record["scenario_id"], {"decision": decision_id,
                                                       "message": message, "delivered": False})
            self.campaign.store_world_state("bunker_hub", snapshot)
            self.machine.save_checkpoint()

    def get_details_lines(self):
        """Expose complete prompts and explanations without truncating essential text."""
        scenario = self.workbench.active_scenario or {}
        texts = [scenario.get('title', ''), scenario.get('claim', {}).get('statement', '')]
        texts.extend(o.get('label', '') for o in scenario.get('claim', {}).get('options', []))
        texts.extend(f"EVIDENCE {i+1}: {e['label']} — {e['detail']}" for i, e in enumerate(scenario.get('evidence_pool', [])))
        texts.extend(f"CHECK {i+1}: {c['prompt']}" for i, c in enumerate(scenario.get('replication_checks', [])))
        texts.extend(f"CHOICE {i+1}: {d['label']} — {d['description']} — METER: {d.get('meter_impact', '')}"
                     for i, d in enumerate(scenario.get('deployment_choices', [])))
        texts.append(getattr(self.workbench, 'feedback_message', ''))
        texts.extend(scenario.get('source_references', []))
        return [line for text in texts for line in wrap_text_pixels(text, self.machine.crt.font_sm, 442)]

    def render(self, crt: Any):
        """Render dual-monitor CRT validation workbench interface."""
        crt.clear((4, 10, 8))
        scen = self.workbench.active_scenario if self.workbench else None
        step = self.workbench.current_step if self.workbench else STEP_SELECT

        # ═══════════════════════════════════════════════════════
        # LEFT CRT: SCENARIOS, REFERENCES, & CAMPAIGN METERS
        # ═══════════════════════════════════════════════════════
        crt.draw_panel(
            (12, 20, 155, 224),
            bg_color=(6, 14, 12),
            border_color=config.COLOR_CRT_GREEN,
        )
        pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, (12, 20, 155, 12))

        # Dividers occupy gaps between text rows; drawing them first permits
        # one native text batch without changing their visible order.
        pygame.draw.line(crt.canvas, (16, 52, 34), (16, 122), (160, 122), width=1)
        pygame.draw.line(crt.canvas, (16, 52, 34), (16, 192), (160, 192), width=1)

        with crt.text_batch():
            crt.draw_text("LEFT CRT // ARC SELECTOR", 16, 21, color=config.COLOR_VOID_BLACK, has_shadow=False)
            y_left = 34
            crt.draw_text("VALIDATION STATIONS:", 18, y_left, color=config.COLOR_FIBO_GOLD, size="sm")

            # Scenario list (compact 8-station roster)
            for idx, s_key in enumerate(self.scenario_keys):
                s_data = self.scenarios[s_key]
                is_active = (idx == self.active_idx)
                is_done = self.workbench.is_completed(self.campaign) if (is_active and self.workbench) else False
                status_tag = "[VAL]" if is_done else "[RDY]"
                frag_tag = s_data.get("fragment_id", "FASR-001")
                col = config.COLOR_CRT_GREEN if is_active else config.COLOR_CORE_STEEL
                prefix = "▶" if is_active else " "
                # Display short label
                label = f"{prefix}[{idx + 1}] {status_tag} {frag_tag}"
                if "adv" in s_key:
                    label += "+"
                crt.draw_text(label, 16, y_left + 12 + idx * 9, color=col, size="sm")

            # Live Campaign Meters Display
            y_meters = 126
            crt.draw_text("CAMPAIGN METERS (ACT I):", 18, y_meters, color=config.COLOR_FIBO_GOLD, size="sm")
            c_meters = getattr(self.campaign.state, "meters", {}) if self.campaign else {}
            meter_keys = [
                ("scientific_certainty", "CERTAINTY"),
                ("alignment_confidence", "ALIGNMENT"),
                ("coordination_capacity", "COORD CAP"),
                ("public_trust", "PUB TRUST"),
                ("human_agency", "HUM AGENCY"),
                ("biosecurity_readiness", "BIOSEC RDY"),
            ]
            for m_idx, (m_id, m_label) in enumerate(meter_keys):
                val = c_meters.get(m_id, 35)
                # Mini progress bar: 6 blocks
                blocks_fill = max(0, min(6, int((val / 100.0) * 6)))
                bar_str = "■" * blocks_fill + "·" * (6 - blocks_fill)
                m_col = config.COLOR_CRT_GREEN if val >= 50 else config.COLOR_AMBER_1977
                crt.draw_text(f"{m_label[:9]}: {val:2d}% [{bar_str}]", 16, y_meters + 10 + m_idx * 9, color=m_col, size="sm")

            # Pipeline progress step indicator
            y_steps = 183
            steps_info = [
                (STEP_EXPERIMENT, "0. EXPERIMENT"),
                (STEP_CLAIM, "1. CLAIM TIER"),
                (STEP_EVIDENCE, "2. EVIDENCE"),
                (STEP_REPLICATION, "3. REPLICATION"),
                (STEP_DEPLOYMENT, "4. DEPLOYMENT"),
            ]
            for s_idx, (s_code, s_label) in enumerate(steps_info):
                if step == s_code:
                    s_col = config.COLOR_FIBO_GOLD
                    bullet = "▶ "
                elif step == STEP_COMPLETED:
                    s_col = config.COLOR_CRT_GREEN
                    bullet = "✔ "
                else:
                    s_col = config.COLOR_CORE_STEEL
                    bullet = "  "
                crt.draw_text(f"{bullet}{s_label}", 18, y_steps + 10 + s_idx * 9, color=s_col, size="sm")

        # ═══════════════════════════════════════════════════════
        # RIGHT CRT: INTERACTIVE WORKBENCH PUZZLE CANVAS
        # ═══════════════════════════════════════════════════════
        title_tag = scen.get("title", "VALIDATION BENCH") if scen else "BENCH"
        crt.draw_panel(
            (174, 20, 294, 224),
            bg_color=(6, 14, 12),
            border_color=config.COLOR_CRT_GREEN,
        )
        pygame.draw.rect(crt.canvas, config.COLOR_CRT_GREEN, (174, 20, 294, 12))

        with crt.text_batch():
            title = ellipsize_pixels(f"RIGHT CRT // {title_tag}", crt.font_sm, 286)
            crt.draw_text(title, 178, 21, color=config.COLOR_VOID_BLACK, has_shadow=False)
            y_right = 34
            if not scen or not self.workbench:
                crt.draw_text("NO SCENARIO LOADED", 184, y_right, color=config.COLOR_AMBER_1977, size="sm")
            else:
                wb_type = scen.get("workbench_type", "formal")

                # 0. Experiment Phase
                if step == STEP_EXPERIMENT:
                    crt.draw_text("STEP 0 // SIMULATION EXPERIMENT & TRIAL", 184, y_right, color=config.COLOR_FIBO_GOLD, size="sm")

                    if wb_type == "quantum":
                        wl = getattr(self.workbench, "wavelength_nm", 532.0)
                        sw = getattr(self.workbench, "slit_width_um", 20.0)
                        sd = getattr(self.workbench, "slit_distance_um", 100.0)
                        sh = getattr(self.workbench, "shielding_factor", 0.90)
                        res = getattr(self.workbench, "last_result", None)
                        vis = res.visibility if res else 0.0

                        crt.draw_text(f"LASER LINE:   {wl:.1f} nm   SLIT WIDTH: {sw:.1f} um", 184, y_right + 14, color=config.COLOR_CRT_DIM, size="sm")
                        crt.draw_text(f"SLIT DIST:    {sd:.1f} um   SHIELDING:  {sh:.1%}", 184, y_right + 25, color=config.COLOR_CRT_DIM, size="sm")
                        v_col = config.COLOR_CRT_GREEN if vis >= 0.70 else config.COLOR_AMBER_1977
                        crt.draw_text(f"INTERFERENCE VISIBILITY: V = {vis:.3f} (TARGET: >= 0.70)", 184, y_right + 38, color=v_col, size="sm")

                        # Draw ASCII diffraction fringe meter
                        fringe_bar = "|| |  |   |    |     |    |   |  | ||"
                        crt.draw_text(f"DIFFRACTION: [{fringe_bar}]", 184, y_right + 52, color=config.COLOR_ARC_CYAN, size="sm")
                        crt.draw_text("[1] 532nm  [2] 20um  [3] 100um  [4] 90% SHIELD", 184, y_right + 72, color=config.COLOR_CORE_STEEL, size="sm")
                        crt.draw_text("[SPACE] FIRE LASER TRIAL  [ENTER] ADVANCE", 184, y_right + 88, color=config.COLOR_FIBO_GOLD, size="sm")

                    elif wb_type == "neuro":
                        crt.draw_text("CONNECTOME CIRCUIT: SENSORY -> INTERNEURON -> MOTOR", 184, y_right + 14, color=config.COLOR_CRT_DIM, size="sm")
                        res = getattr(self.workbench, "last_result", None)
                        m_desync = res.motor_outputs.get("M_DESYNC_PULSE", 0.0) if res else 0.0
                        m_seiz = res.motor_outputs.get("M_RUNAWAY_SEIZURE", 0.0) if res else 0.0
                        delta_m = next(iter(res.causal_effects.values())) if (res and res.causal_effects) else 0.0

                        crt.draw_text(f"DESYNC REFLEX:  {m_desync:.2f} (TARGET: >= 0.70)", 184, y_right + 26, color=config.COLOR_CRT_GREEN if m_desync >= 0.70 else config.COLOR_CORE_STEEL, size="sm")
                        crt.draw_text(f"SEIZURE OVERFLOW: {m_seiz:.2f} (SAFE: <= 0.35)", 184, y_right + 38, color=config.COLOR_CRT_GREEN if m_seiz <= 0.35 else config.COLOR_EHMAN_RED, size="sm")
                        crt.draw_text(f"CAUSAL INTERVENTION DELTA: Delta M = {delta_m:+.2f} (>= 0.40)", 184, y_right + 50, color=config.COLOR_FIBO_GOLD, size="sm")

                        crt.draw_text("[1-3] PATCH CANDIDATE CABLES  [SPACE] RUN TRIAL", 184, y_right + 72, color=config.COLOR_CORE_STEEL, size="sm")
                        crt.draw_text("[ENTER] ADVANCE TO CLAIM", 184, y_right + 88, color=config.COLOR_FIBO_GOLD, size="sm")

                    elif wb_type == "biosecurity":
                        m = getattr(self.workbench, "model", None)
                        temp = m.controls.incubation_temp_c if m else 37.0
                        rpm = m.controls.centrifuge_rpm if m else 8000.0
                        reagents = m.reagents_remaining if m else 100.0
                        conf = m.observations[-1].confidence if (m and m.observations) else 0.0
                        titer = m.observations[-1].neutralization_titer if (m and m.observations) else 0.0

                        crt.draw_text(f"TEMP: {temp:.1f} C   RPM: {rpm:5.0f}   REAGENTS: {reagents:.1f} uL", 184, y_right + 14, color=config.COLOR_CRT_DIM, size="sm")
                        crt.draw_text(f"SPRT POSTERIOR CONFIDENCE: {conf:.1%} (TARGET: >= 85%)", 184, y_right + 28, color=config.COLOR_CRT_GREEN if conf >= 0.85 else config.COLOR_AMBER_1977, size="sm")
                        crt.draw_text(f"NEUTRALIZATION TITER:     {titer:.1%}", 184, y_right + 42, color=config.COLOR_ARC_CYAN, size="sm")

                        crt.draw_text("[1] SET OPTIMAL ALLOCATION (37C, 8k RPM, 20uL)", 184, y_right + 66, color=config.COLOR_CORE_STEEL, size="sm")
                        crt.draw_text("[SPACE] INCUBATE CYCLES  [ENTER] ADVANCE", 184, y_right + 84, color=config.COLOR_FIBO_GOLD, size="sm")

                    else:
                        crt.draw_text("EXPERIMENT NOT REQUIRED FOR THIS SCENARIO", 184, y_right + 24, color=config.COLOR_CRT_DIM, size="sm")
                        crt.draw_text("PRESS [SPACE] OR [ENTER] TO ADVANCE TO CLAIM", 184, y_right + 48, color=config.COLOR_FIBO_GOLD, size="sm")

                # 1. Pipeline Step Display: Claim Classification
                elif step == STEP_CLAIM:
                    crt.draw_text("STEP 1 // SCIENTIFIC CLAIM CLASSIFICATION", 184, y_right, color=config.COLOR_FIBO_GOLD, size="sm")
                    crt.draw_text("CLAIM PROPOSITION:", 184, y_right + 11, color=config.COLOR_CORE_STEEL, size="sm")
                    statement = scen.get("claim", {}).get("statement", "")
                    claim_lines = wrap_text_pixels(statement, crt.font_sm, 276)
                    preview = claim_lines[:4]
                    if len(claim_lines) > len(preview):
                        preview[-1] = ellipsize_pixels(preview[-1] + ' ...', crt.font_sm, 276)
                    cur_y = y_right + 22
                    for line in preview:
                        crt.draw_text(line, 184, cur_y, color=config.COLOR_CRT_GREEN, size="sm")
                        cur_y += 10

                    cur_y = max(cur_y + 3, y_right + 62)
                    crt.draw_text("SELECT CLAIM TIER ([1-3]):", 184, cur_y, color=config.COLOR_FIBO_GOLD, size="sm")
                    options = scen.get("claim", {}).get("options", [])
                    for opt_idx, opt in enumerate(options):
                        label = ellipsize_pixels(f"[{opt_idx + 1}] {opt['label']}", crt.font_sm, 276)
                        crt.draw_text(label, 184, cur_y + 11 + opt_idx * 11, color=config.COLOR_CRT_DIM, size="sm")

                # 2. Evidence Selection
                elif step == STEP_EVIDENCE:
                    crt.draw_text("STEP 2 // EMPIRICAL EVIDENCE OBSERVATION", 184, y_right, color=config.COLOR_FIBO_GOLD, size="sm")
                    crt.draw_text("FILTER VALID SIGNATURES (AVOID COUNTEREXAMPLES):", 184, y_right + 11, color=config.COLOR_CORE_STEEL, size="sm")

                    evidence_pool = scen.get("evidence_pool", [])
                    for e_idx, ev in enumerate(evidence_pool[:3]):
                        is_sel = ev["id"] in getattr(self.workbench, "selected_evidence", set())
                        box = "[X]" if is_sel else "[ ]"
                        e_col = config.COLOR_FIBO_GOLD if is_sel else config.COLOR_CORE_STEEL
                        label = ellipsize_pixels(f"[{e_idx + 1}] {box} {ev['label']}", crt.font_sm, 276)
                        detail = ellipsize_pixels(f"    {ev['detail']}", crt.font_sm, 276)
                        crt.draw_text(label, 184, y_right + 24 + e_idx * 24, color=e_col, size="sm")
                        crt.draw_text(detail, 184, y_right + 34 + e_idx * 24, color=config.COLOR_CRT_DIM, size="sm")

                    crt.draw_text("[1-3] TOGGLE SELECTION  [ENTER] VERIFY EVIDENCE", 184, y_right + 104, color=config.COLOR_FIBO_GOLD, size="sm")

                # 3. Replication Checks
                elif step == STEP_REPLICATION:
                    crt.draw_text("STEP 3 // REPLICATION INVARIANT CHECKS", 184, y_right, color=config.COLOR_FIBO_GOLD, size="sm")
                    crt.draw_text("EVALUATE CONSERVATION LAWS & INVARIANTS:", 184, y_right + 11, color=config.COLOR_CORE_STEEL, size="sm")

                    checks = scen.get("replication_checks", [])
                    for c_idx, chk in enumerate(checks[:3]):
                        cid = chk["id"]
                        val = getattr(self.workbench, "replication_answers", {}).get(cid)
                        val_str = "TRUE" if val is True else ("FALSE" if val is False else "UNCHECKED")
                        v_col = config.COLOR_CRT_GREEN if val is True else (config.COLOR_EHMAN_RED if val is False else config.COLOR_CORE_STEEL)
                        label = ellipsize_pixels(f"CHECK {c_idx + 1}: {chk['prompt']}", crt.font_sm, 276)
                        crt.draw_text(label, 184, y_right + 24 + c_idx * 26, color=config.COLOR_CRT_GREEN, size="sm")
                        crt.draw_text(f"[{c_idx + 1}] ANSWER: [{val_str}]", 184, y_right + 34 + c_idx * 26, color=v_col, size="sm")

                    crt.draw_text("[1-3] TOGGLE T/F  [ENTER] VERIFY REPLICATION", 184, y_right + 104, color=config.COLOR_FIBO_GOLD, size="sm")

                # 4. Deployment Decision
                elif step == STEP_DEPLOYMENT:
                    crt.draw_text("STEP 4 // PROTOCOL DEPLOYMENT DECISION", 184, y_right, color=config.COLOR_FIBO_GOLD, size="sm")
                    crt.draw_text("COMMIT PROTOCOL TO ACTIVE MASER OR QUARANTINE:", 184, y_right + 11, color=config.COLOR_CORE_STEEL, size="sm")

                    choices = scen.get("deployment_choices", [])
                    for d_idx, dc in enumerate(choices[:2]):
                        label = ellipsize_pixels(f"[{d_idx + 1}] {dc['label']}", crt.font_sm, 276)
                        detail = ellipsize_pixels(f"    {dc['description']}", crt.font_sm, 276)
                        impact = ellipsize_pixels(f"    METER: {dc.get('meter_impact', '')}", crt.font_sm, 276)
                        crt.draw_text(label, 184, y_right + 25 + d_idx * 32, color=config.COLOR_FIBO_GOLD, size="sm")
                        crt.draw_text(detail, 184, y_right + 36 + d_idx * 32, color=config.COLOR_CRT_DIM, size="sm")
                        crt.draw_text(impact, 184, y_right + 46 + d_idx * 32, color=config.COLOR_CORE_STEEL, size="sm")

                    crt.draw_text("[1-2] COMMIT DEPLOYMENT DECISION", 184, y_right + 104, color=config.COLOR_FIBO_GOLD, size="sm")

                # 5. Completed
                elif step == STEP_COMPLETED:
                    crt.draw_text("PROTOCOL FORMALLY VALIDATED & RECORDED", 184, y_right, color=config.COLOR_CRT_GREEN, size="sm")
                    record = self.workbench.get_completed_record(self.campaign) or getattr(self.workbench, "validation_record", {}) or {}
                    crt.draw_text(f"RECORD ID:   {record.get('id', scen.get('fragment_id', 'FASR-001'))}", 184, y_right + 16, color=config.COLOR_FIBO_GOLD, size="sm")
                    crt.draw_text(f"SCENARIO:    {record.get('scenario_id', scen.get('id', 'formal_fasr_001'))}", 184, y_right + 28, color=config.COLOR_CRT_DIM, size="sm")
                    crt.draw_text(f"CLAIM TIER:  {record.get('claim_tier', 'speculative').upper()}", 184, y_right + 40, color=config.COLOR_AMBER_1977, size="sm")
                    crt.draw_text(f"RESULT:      {record.get('result', 'validated').upper()} ({record.get('confidence', 90)}% CONF)", 184, y_right + 52, color=config.COLOR_CRT_GREEN, size="sm")
                    crt.draw_text(f"DECISION:    {record.get('deployment_decision', 'COMMITTED')}", 184, y_right + 64, color=config.COLOR_FIBO_GOLD, size="sm")
                    crt.draw_text("CAMPAIGN:    ALL 6 METERS SYNCHRONIZED ATOMICALLY", 184, y_right + 76, color=config.COLOR_CORE_STEEL, size="sm")

                    crt.draw_text("[R] RETRY  [ESC] RETURN TO BUNKER HUB", 184, y_right + 104, color=config.COLOR_CRT_GREEN, size="sm")

                # Feedback message bar
                fb_err = getattr(self.workbench, "feedback_is_error", False)
                fb_col = config.COLOR_EHMAN_RED if fb_err else config.COLOR_CRT_GREEN
                fb_text = getattr(self.workbench, "feedback_message", "")
                fb_text = ellipsize_pixels(fb_text, crt.font_sm, 276)
                crt.draw_text(fb_text, 184, 182, color=fb_col, size="sm")

        # Global Bottom HUD
        footer = ("[UP/DN] SCROLL [PGUP/PGDN] PAGE [H/ESC] CLOSE" if self.details_open else
                  "[UP/DN] SCENARIO [1-4] ACT [H] FULL TEXT [ENTER] NEXT [ESC] EXIT")
        self.machine.render_global_hud(
            crt,
            location_label="NSF / NIH DUAL-CRT SCIENCE LAB // VALIDATION MATRIX",
            footer_text=footer,
        )
        if self.details_open:
            crt.draw_panel((8, 18, 464, 226), title="FULL SCENARIO TEXT // UP/DOWN SCROLL // H CLOSE")
            detail_lines = self.get_details_lines()
            self.details_offset = max(0, min(self.details_offset, max(0, len(detail_lines) - 17)))
            with crt.text_batch():
                for i, line in enumerate(detail_lines[self.details_offset:self.details_offset+17]):
                    crt.draw_text(line, 16, 37 + i * 11)
                first = self.details_offset + 1 if detail_lines else 0
                last = min(len(detail_lines), self.details_offset + 17)
                crt.draw_text(f"LINES {first}-{last} OF {len(detail_lines)}", 16, 228, color=config.COLOR_CORE_STEEL)
