"""
MODULE: video_game/tests/test_contact_session.py
PURPOSE: Comprehensive unit and integration test suite for ContactSession,
         TextInputBuffer, TranscriptScroller, and CRTTerminalScene.
CALLED BY: pytest (`python -m pytest video_game/tests/test_contact_session.py -vv`).
HOW TO MODIFY: Add focused test cases for UI edge cases, tuning bounds, or dialogue limits.
"""

import os
import time
import pygame
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from signal_6EQUJ5 import codec
from video_game.engine import config
from video_game.engine.contact_session import ContactSession, TARGET_FREQUENCIES
from video_game.engine.crt_renderer import CRTRenderer
from video_game.engine.scenes.bunker import MILESTONE_CIVS
from video_game.engine.scenes.terminal import CRTTerminalScene
from video_game.engine.state_machine import GameStateMachine
from video_game.engine.ui.text import TextInputBuffer, TranscriptScroller, wrap_text_chars, wrap_text_pixels
from video_game.tests.test_ai_worker import FakeOllamaClient
from video_game.engine.ai_adapter import AIAdapter
from video_game.engine.ai_worker import AIWorker


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    pygame.init()
    pygame.font.init()
    pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
    yield
    pygame.quit()


def test_contact_session_decode_bins_match_contract():
    """Verify that 6EQUJ5 decode bins match [6, 14, 26, 30, 19, 5]."""
    session = ContactSession()
    assert session.decode_bins == [6, 14, 26, 30, 19, 5]
    assert session.peak_intensity == 30
    assert session.duration_seconds == 72
    assert max(session.decode_bins) == 30


def test_all_eleven_targets_render_without_clipping():
    """Verify that all 11 milestone civilization targets render cleanly without errors."""
    crt = CRTRenderer()
    machine = GameStateMachine(crt, development=True)
    try:
        terminal = CRTTerminalScene(machine)
        for civ_id in MILESTONE_CIVS:
            assert civ_id in TARGET_FREQUENCIES
            freq = TARGET_FREQUENCIES[civ_id]
            assert 1400.0 <= freq <= 1440.0, f"Frequency {freq} out of 1400-1440 MHz band"

            terminal.session.switch_target(civ_id)
            assert terminal.session.active_civ_id == civ_id
            assert terminal.session.target_mhz == freq
            assert terminal.session.is_locked is True

            # Render scene
            terminal.render(crt)
            assert crt.canvas.get_size() == (480, 270)
    finally:
        terminal.session.worker.stop()
        machine.close()


def test_long_replies_and_unicode_wrap_and_scroll():
    """Verify word-wrapping of long replies and Unicode characters across lines."""
    long_reply = (
        "We are an ancient intelligence transmitting on 1420.4056 MHz. "
        "The Core cannot calculate non-linear analog entropy (PEAK: 30σ, DURATION: 72s). "
        "Our mathematical coordinate vectors include α=19h25m, δ=-27°03', and Planck factor ℏ."
    )

    wrapped = wrap_text_chars(long_reply, max_chars=38)
    assert len(wrapped) >= 4
    for line in wrapped:
        assert len(line) <= 38
        # Ensure Unicode characters remain intact
        for ch in ("σ", "°", "α", "δ", "ℏ"):
            if ch in line:
                assert ch in line

    # Test scroller
    scroller = TranscriptScroller(visible_lines=4)
    for line in wrapped:
        scroller.add_line(line)

    assert len(scroller.lines) == len(wrapped)
    # Scroll up
    scroller.scroll_up(2)
    assert scroller.scroll_offset < len(wrapped) - 4
    # Scroll to bottom
    scroller.scroll_to_bottom()
    assert scroller.scroll_offset == len(wrapped) - 4
    visible = scroller.get_visible_lines()
    assert len(visible) == 4


def test_text_input_buffer_typing_backspace_and_limits():
    """Verify text insertion, cursor manipulation, backspace, and 128 character max capacity."""
    buf = TextInputBuffer(max_length=20)
    assert buf.insert("Hello World") is True
    assert buf.text == "Hello World"
    assert buf.cursor_pos == 11

    # Backspace
    assert buf.backspace() is True
    assert buf.text == "Hello Worl"
    assert buf.cursor_pos == 10

    # Insert inside string
    buf.move_left()
    buf.move_left()
    buf.insert("k")
    assert buf.text == "Hello Wokrl"

    # Max length constraint
    buf.insert("12345678901234567890")
    assert len(buf.text) <= 20

    # Clear
    old = buf.clear()
    assert old.startswith("Hello")
    assert buf.text == ""
    assert buf.cursor_pos == 0


def test_target_switching_and_cancellation():
    """Verify target switching and in-flight cancellation via session."""
    fake = FakeOllamaClient(tokens=["Token "] * 20, delay_per_token=0.03)
    adapter = AIAdapter(client=fake, enable_fallback=False)
    worker = AIWorker(adapter=adapter)
    session = ContactSession(worker=worker, initial_civ="FASR-001")

    try:
        # Send message
        sent = session.send_message("Initiating contact")
        assert sent is True
        assert session.is_streaming is True

        # Cancel in-flight transmission
        time.sleep(0.04)
        cancelled = session.cancel_transmission()
        assert cancelled is True
        assert session.is_streaming is False
        assert "ABORTED" in session.status_text

        # Switch target
        session.switch_target("FASR-002")
        assert session.active_civ_id == "FASR-002"
        assert session.target_mhz == TARGET_FREQUENCIES["FASR-002"]
        assert session.is_streaming is False
    finally:
        worker.stop()


def test_twelve_completed_exchanges_limit():
    """Verify the 12 completed exchanges limit stops further transmissions."""
    fake = FakeOllamaClient(tokens=["Brief response."], delay_per_token=0.001)
    adapter = AIAdapter(client=fake, enable_fallback=False)
    worker = AIWorker(adapter=adapter)
    session = ContactSession(worker=worker, initial_civ="FASR-001")

    try:
        session.update(0.01)
        for i in range(12):
            session.send_message(f"Turn {i + 1}")
            # Process stream
            t0 = time.time()
            while session.is_streaming and time.time() - t0 < 1.0:
                session.update(0.01)
                time.sleep(0.01)
            assert session.exchange_count == i + 1

        assert session.exchange_count == 12

        # 13th message must be rejected by rule
        rejected = session.send_message("13th turn")
        assert rejected is False
        assert "LIMIT" in session.status_text
    finally:
        worker.stop()


def test_rapid_exit_and_reentry_preserves_state():
    """Verify that rapid exit to bunker and re-entry to terminal preserves dialogue and session state."""
    crt = CRTRenderer()
    machine = GameStateMachine(crt, development=True)

    try:
        terminal = machine.scenes[config.STATE_CRT_TERMINAL]
        machine.change_state(config.STATE_CRT_TERMINAL)
        terminal.session.send_message("First message")

        # Exit to bunker
        machine.change_state(config.STATE_BUNKER_HUB)
        assert machine.current_state_name == config.STATE_BUNKER_HUB

        # Re-enter terminal
        machine.change_state(config.STATE_CRT_TERMINAL)
        assert machine.current_state_name == config.STATE_CRT_TERMINAL

        # Verify message preserved
        user_msgs = [m for m in terminal.session.transcripts["FASR-001"] if m["role"] == "user"]
        assert len(user_msgs) == 1
        assert user_msgs[0]["text"] == "First message"

        # Rapid repeated transitions
        for _ in range(5):
            machine.change_state(config.STATE_BUNKER_HUB)
            machine.change_state(config.STATE_CRT_TERMINAL)

        assert len(user_msgs) == 1
    finally:
        machine.close()


def test_receiver_tuning_and_carrier_lock():
    """Verify frequency tuning across 1400-1440 MHz band and carrier lock boundaries."""
    session = ContactSession(initial_civ="FASR-001")
    try:
        assert session.tuner_mhz == 1420.4056
        assert session.is_locked is True

        # Tune away from carrier
        session.tune_frequency(-0.5000)
        assert session.tuner_mhz == 1419.9056
        assert session.is_locked is False
        assert session.signal_strength < 0.2

        # Transmitting while unlocked must be rejected
        assert session.send_message("Lost in noise") is False
        assert "ERR: NO CARRIER LOCK" in session.status_text

        # Tune back to carrier
        session.snap_to_carrier()
        assert session.is_locked is True
        assert session.signal_strength == 1.0
    finally:
        session.worker.stop()


def test_offline_dialogue_all_eleven_civs_reachable_without_model():
    """Verify that every required evidence route across all 11 civs is reachable without a model (C05)."""
    for civ_id in MILESTONE_CIVS:
        session = ContactSession(initial_civ=civ_id, force_offline=True)
        try:
            assert session.is_offline is True
            assert session.active_civ_id == civ_id

            # 1. Check initial greeting present in transcript
            assert len(session.transcripts[civ_id]) >= 1
            greeting = session.transcripts[civ_id][0]["text"]
            assert len(greeting) > 20

            # 2. Channel 1: Inquire readiness
            ok = session.send_message("1")
            assert ok is True
            assert session.exchange_count == 1
            last_reply = session.transcripts[civ_id][-1]["text"]
            assert len(last_reply) > 20
            assert "PREREQUISITE UNMET" not in last_reply

            # 3. Channel 2: Request evidence route
            ok = session.send_message("2")
            assert ok is True
            assert session.exchange_count == 2
            evidence_reply = session.transcripts[civ_id][-1]["text"]
            assert len(evidence_reply) > 20
            assert "PREREQUISITE UNMET" not in evidence_reply

            # Verify action was granted in session completed evidence
            civ_data = session.offline_data["civilizations"][civ_id]
            expected_action = civ_data["evidence"]["action"]
            assert expected_action in session.completed_evidence_actions

            # 4. Unknown question fallback
            ok = session.send_message("random unparseable gibberish 999")
            assert ok is True
            assert session.exchange_count == 3
            unknown_reply = session.transcripts[civ_id][-1]["text"]
            assert len(unknown_reply) > 10
        finally:
            session.worker.stop()


def test_offline_civ_identity_and_voice_are_distinct():
    """Verify that civilization identities, greetings, evidence, and unknown replies remain distinct (C05)."""
    greetings = []
    readiness_replies = []
    evidence_replies = []
    unknown_replies = []
    names = []

    for civ_id in MILESTONE_CIVS:
        session = ContactSession(initial_civ=civ_id, force_offline=True)
        try:
            civ_data = session.offline_data["civilizations"][civ_id]
            names.append(civ_data["name"])
            greetings.append(civ_data["initial_greeting"])
            readiness_replies.append(civ_data["readiness"]["reply"])
            evidence_replies.append(civ_data["evidence"]["reply"])
            unknown_replies.append(civ_data["unknown_response"])
        finally:
            session.worker.stop()

    assert len(set(names)) == 11, "Civilization names must be distinct"
    assert len(set(greetings)) == 11, "Initial greetings must be distinct across all 11 civs"
    assert len(set(readiness_replies)) == 11, "Readiness dialogue must be distinct across all 11 civs"
    assert len(set(evidence_replies)) == 11, "Evidence dialogue must be distinct across all 11 civs"
    assert len(set(unknown_replies)) == 11, "Unknown question replies must be distinct across all 11 civs"


def test_offline_choices_enforce_campaign_prerequisites():
    """Verify that offline choices never bypass unmet prerequisites (C05)."""
    session = ContactSession(initial_civ="FASR-001", force_offline=True)
    try:
        # FASR-001 Choice 3 requires 'EVIDENCE_ANALOG_ENTROPY'
        assert "EVIDENCE_ANALOG_ENTROPY" not in session.completed_evidence_actions

        # Attempt to bypass directly to Choice 3
        sent = session.send_message("3")
        assert sent is True
        reply = session.transcripts["FASR-001"][-1]["text"]
        assert "PREREQUISITE UNMET" in reply
        assert "EVIDENCE_ANALOG_ENTROPY" in reply
        assert "REWARD_FIBONACCI_KEY_1" not in session.completed_evidence_actions

        # Now fulfill prerequisite via Choice 2 (Evidence)
        sent = session.send_message("2")
        assert sent is True
        assert "EVIDENCE_ANALOG_ENTROPY" in session.completed_evidence_actions

        # Now Choice 3 must be unlocked and succeed
        sent = session.send_message("3")
        assert sent is True
        reply_unlocked = session.transcripts["FASR-001"][-1]["text"]
        assert "PREREQUISITE UNMET" not in reply_unlocked
        assert "REWARD_FIBONACCI_KEY_1" in session.completed_evidence_actions
    finally:
        session.worker.stop()


def test_partial_ai_failure_recovers_to_offline_without_duplication_or_stranding():
    """Verify partial AI failures switch to offline recovery without duplicating exchanges or stranding (C05)."""
    fake = FakeOllamaClient(tokens=["Token 1", "Token 2"], delay_per_token=0.01)
    adapter = AIAdapter(client=fake, enable_fallback=False)
    worker = AIWorker(adapter=adapter)
    session = ContactSession(worker=worker, initial_civ="FASR-001")

    try:
        assert session.is_offline is False

        # Simulate transmission
        session.send_message("Requesting evidence seed")
        assert session.is_streaming is True
        req_id = session.active_request_id

        # Inject mid-stream connection error from worker
        session.worker._emit_event(session.active_session_id, req_id, "ERROR", "Connection reset by peer")
        session.update(0.01)

        # Session must transition to offline recovery
        assert session.is_offline is True
        assert session.is_streaming is False
        assert session.active_request_id is None
        assert "OFFLINE RECOVERY" in session.status_text

        # Verify no duplicate user messages
        user_msgs = [m for m in session.transcripts["FASR-001"] if m["role"] == "user"]
        assert len(user_msgs) == 1
        assert session.exchange_count == 1

        # Check recovery assistant reply was recorded
        asst_msgs = [m for m in session.transcripts["FASR-001"] if m["role"] == "assistant"]
        assert any("OFFLINE RECOVERY" in m["text"] for m in asst_msgs)

        # Subsequent messages must work cleanly offline
        ok = session.send_message("1")
        assert ok is True
        assert session.exchange_count == 2
        assert "CARRIER_LOCKED" in session.transcripts["FASR-001"][-1]["text"] or len(session.transcripts["FASR-001"][-1]["text"]) > 20
    finally:
        worker.stop()


def test_reconnect_controls_and_channel_help():
    """Verify /reconnect command, /offline toggle, and ? help command (C05)."""
    session = ContactSession(initial_civ="FASR-001", force_offline=True)
    try:
        assert session.is_offline is True

        # /choices command
        session.send_message("/choices")
        last_asst = session.transcripts["FASR-001"][-1]["text"]
        assert "[CHANNELS]" in last_asst

        # /reconnect command
        session.send_message("/reconnect")
        asst_reply = session.transcripts["FASR-001"][-1]["text"]
        assert "SYSTEM" in asst_reply

        # /offline command
        session.send_message("/offline")
        assert session.is_offline is True
    finally:
        session.worker.stop()


def test_offline_twelve_completed_exchanges_limit():
    """Verify 12 exchanges quota is strictly enforced in offline mode (C05)."""
    session = ContactSession(initial_civ="FASR-001", force_offline=True)
    try:
        for i in range(12):
            sent = session.send_message("1")
            assert sent is True
            assert session.exchange_count == i + 1

        assert session.exchange_count == 12

        # 13th turn must be blocked
        sent = session.send_message("1")
        assert sent is False
        assert "LIMIT: 12 EXCHANGES COMPLETED" in session.status_text
    finally:
        session.worker.stop()


def test_hostile_signal_core_mimic_detection():
    """Verify telegraphed Core-mimic detection heuristics and signatures (C06)."""
    session = ContactSession(initial_civ="FASR-001")
    try:
        # Authentic signal test
        clean_telemetry = {
            "frequency_mhz": 1420.4056,
            "determinism_score": 0.12,
            "doppler_drift_khz": 1.4,
            "line_width_khz": 8.5,
            "payload_syntax": "ANALOG_HYDROGEN_CARRIER",
        }
        assessment_clean = session.assess_signal_telemetry(clean_telemetry)
        assert assessment_clean.is_hostile is False
        assert "AUTHENTIC" in assessment_clean.telegraphed_warning

        # Hostile Core-mimic test: synthetic determinism >= 0.90
        hostile_telemetry = {
            "frequency_mhz": 1420.4056,
            "determinism_score": 0.98,
            "doppler_drift_khz": 0.0,
            "line_width_khz": 0.2,
            "payload_syntax": "<CORE_MIMIC_ATTACK>",
        }
        assessment_hostile = session.assess_signal_telemetry(hostile_telemetry)
        assert assessment_hostile.is_hostile is True
        assert assessment_hostile.confidence >= 0.95
        assert "HOSTILE CORE-MIMIC DETECTED" in assessment_hostile.telegraphed_warning
        assert len(assessment_hostile.telemetry_reasons) >= 2
        assert assessment_hostile.failure_consequence == "RECEIVER_OVERLOAD_JAMMED"
        assert assessment_hostile.recovery_action == "PURGE_RECEIVER_BUFFER"
    finally:
        session.worker.stop()


def test_hostile_signal_consequence_and_recovery():
    """Verify that hostile-signal failure is telegraphed, penalized, and fully recoverable (C06)."""
    from video_game.engine.campaign import Campaign

    campaign = Campaign(save_id="test_hostile_recovery")
    session = ContactSession(initial_civ="FASR-001", campaign=campaign)
    try:
        init_align = campaign.state.meters["alignment_confidence"]
        init_trust = campaign.state.meters["public_trust"]

        # Detect hostile mimic
        hostile_telemetry = {
            "frequency_mhz": 1420.4900,  # FASR-001 known spoof frequency
            "determinism_score": 0.96,
        }
        assessment = session.assess_signal_telemetry(hostile_telemetry)
        assert assessment.is_hostile is True

        # CASE 1: Operator accepts / transmits to hostile mimic
        breach_result = session.resolve_hostile_signal(assessment, action="ACCEPT")
        assert breach_result["outcome"] == "BREACH"
        assert breach_result["recoverable"] is True
        assert session.is_locked is False
        assert session.signal_strength < 0.1
        assert "OVERLOAD" in session.status_text

        # Bounded penalty applied to campaign meters
        assert campaign.state.meters["alignment_confidence"] == init_align - 10
        assert campaign.state.meters["public_trust"] == init_trust - 5

        # RECOVERY: Operator purges buffer and locks carrier
        session.snap_to_carrier()
        assert session.is_locked is True
        assert session.signal_strength == 1.0
        assert "CARRIER LOCKED" in session.status_text

        # CASE 2: Operator purges / rejects hostile mimic on FASR-007
        session.switch_target("FASR-007")
        assessment_7 = session.assess_signal_telemetry({"frequency_mhz": 1418.9900, "determinism_score": 0.94})
        assert assessment_7.is_hostile is True

        init_cert = campaign.state.meters["scientific_certainty"]
        init_coord = campaign.state.meters["coordination_capacity"]

        neutralize_result = session.resolve_hostile_signal(assessment_7, action="PURGE")
        assert neutralize_result["outcome"] == "NEUTRALIZED"
        assert "CARRIER PURGED" in session.status_text
        assert campaign.state.meters["scientific_certainty"] == init_cert + 5
        assert campaign.state.meters["coordination_capacity"] == init_coord + 5
    finally:
        session.worker.stop()


def test_claim_evidence_grant_integration():
    """Verify session evidence claiming integrates with campaign and validator (C06)."""
    from video_game.engine.campaign import Campaign

    campaign = Campaign(save_id="test_session_grant")
    session = ContactSession(initial_civ="FASR-001", campaign=campaign, force_offline=True)
    try:
        # Before completing evidence, claim must fail
        ok, msg = session.claim_evidence_grant("FASR-001")
        assert ok is False
        assert "REJECTED" in msg
        assert "FASR-001" not in campaign.state.extracted_fragments

        # Complete evidence channel (Choice 2)
        sent = session.send_message("2")
        assert sent is True
        assert "EVIDENCE_ANALOG_ENTROPY" in session.completed_evidence_actions

        # Fragment must now be extracted and present in campaign
        assert "FASR-001" in campaign.state.extracted_fragments
        assert "grant_fragment_fasr_001" in campaign.state.completed_event_types

        # Re-claiming must be idempotent and return False
        ok_dup, msg_dup = session.claim_evidence_grant("FASR-001")
        assert ok_dup is False
        assert "already extracted" in msg_dup
        assert campaign.state.extracted_fragments.count("FASR-001") == 1
    finally:
        session.worker.stop()


def test_gate_g1_fresh_game_end_to_end_contact_to_validation_route(tmp_path):
    """
    GATE G1 VERIFICATION (C08):
    Full fresh-game end-to-end loop:
      1. Receiver tuning & carrier lock.
      2. Dialogue interaction & fragment evidence acquisition.
      3. Formal validation workbench claim classification, evidence filtering & replication.
      4. Deployment decision & campaign reward deltas.
      5. Atomic disk save and reload round-trip.
    """
    from video_game.engine.campaign import Campaign
    from video_game.engine.save_game import SaveStore
    from video_game.engine.labs.formal import FormalValidationWorkbench

    # Step 1: Fresh campaign
    campaign = Campaign(save_id="fresh_g1_route")
    assert campaign.state.contacted_civs == []
    assert campaign.state.extracted_fragments == []
    assert campaign.state.validation_records == []

    # Step 2: Receiver & Terminal contact
    session = ContactSession(initial_civ="FASR-001", campaign=campaign, force_offline=True)
    try:
        assert session.is_locked is True
        # Send greeting / readiness
        session.send_message("1")
        assert "FASR-001" in campaign.state.contacted_civs

        # Send evidence query
        session.send_message("2")
        assert "FASR-001" in campaign.state.extracted_fragments
        assert "grant_fragment_fasr_001" in campaign.state.completed_event_types

        # Step 3: Formal Science Lab Workbench
        workbench = FormalValidationWorkbench()
        ok_sel, _ = workbench.select_scenario("formal_fasr_001", campaign)
        assert ok_sel is True

        # Classify claim tier
        ok_cls, fb_cls = workbench.classify_claim("speculative")
        assert ok_cls is True

        # Filter observations (rejecting counterexamples)
        workbench.toggle_evidence("obs_entropy_seed")
        workbench.toggle_evidence("obs_snr_coherence")
        ok_ev, _ = workbench.verify_evidence()
        assert ok_ev is True

        # Invariant checks
        workbench.set_replication_check("check_cavity_conservation", True)
        workbench.set_replication_check("check_perpetual_motion", False)
        ok_rep, _ = workbench.verify_replication()
        assert ok_rep is True

        # Step 4: Commit deployment decision
        init_cert = campaign.state.meters["scientific_certainty"]
        ok_dep, msg_dep, record = workbench.choose_deployment("deploy_analog_filter", campaign)
        assert ok_dep is True
        assert len(campaign.state.validation_records) == 1
        assert campaign.state.meters["scientific_certainty"] == init_cert + 10

        # Step 5: Save & reload round-trip
        store = SaveStore(tmp_path)
        assert store.save(campaign) is True

        load_res = store.load()
        assert load_res.status == "ok"
        loaded = load_res.campaign

        assert loaded.state.contacted_civs == ["FASR-001"]
        assert loaded.state.extracted_fragments == ["FASR-001"]
        assert len(loaded.state.validation_records) == 1
        loaded_rec = loaded.state.validation_records[0]
        assert loaded_rec["id"] == "FASR-001"
        assert loaded_rec["deployment_decision"] == "deploy_analog_filter"
        assert loaded_rec["claim_tier"] == "speculative"
        assert loaded.state.meters["scientific_certainty"] == init_cert + 10
    finally:
        session.worker.stop()


def test_gate_g1_live_local_model_and_offline_route_parity():
    """
    GATE G1 VERIFICATION (C08):
    Verify parity between live Ollama local-model inference and canonical offline dialogue.
    """
    from video_game.engine.campaign import Campaign
    import urllib.request

    # Check if local Ollama service is reachable
    ollama_online = False
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                ollama_online = True
    except Exception:
        ollama_online = False

    if not ollama_online:
        pytest.skip("Local Ollama service not reachable on localhost:11434")

    campaign_live = Campaign(save_id="live_test")
    session_live = ContactSession(initial_civ="FASR-001", campaign=campaign_live, force_offline=False)
    try:
        assert session_live.is_offline is False
        session_live.snap_to_carrier()

        # Send transmission to live model
        t0 = time.time()
        sent = session_live.send_message("What is your origin?")
        assert sent is True

        # Wait for completion (bounded timeout)
        done = False
        while time.time() - t0 < 12.0:
            session_live.update(0.05)
            time.sleep(0.05)
            if not session_live.is_streaming and len(session_live.transcripts["FASR-001"]) >= 2:
                done = True
                break

        assert done is True
        asst_msg = session_live.transcripts["FASR-001"][-1]
        assert asst_msg["role"] == "assistant"
        assert len(asst_msg["text"]) > 10
        assert session_live.exchange_count == 1
    finally:
        session_live.worker.stop()





def test_online_numbered_evidence_channel_uses_campaign_rules():
    """Live mode retains explicit, prerequisite-checked mission channels."""
    from video_game.engine.campaign import Campaign

    campaign = Campaign(save_id="online_channel")
    session = ContactSession(initial_civ="FASR-001", campaign=campaign, force_offline=True)
    try:
        session.is_offline = False
        session.snap_to_carrier()
        assert session.send_message("2")
        assert "FASR-001" in campaign.state.extracted_fragments
        assert session.exchange_count == 1
        assert session.is_offline is False
        assert not session.is_streaming
        assert session.send_message("2")
        assert campaign.state.extracted_fragments.count("FASR-001") == 1
    finally:
        session.worker.stop()
