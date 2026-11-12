# Milestone 1 — Task C04 Evidence Report: Receiver Interaction and Dialogue UI

**Date:** 2026-11-10  
**Task ID:** C04  
**Status:** Complete and Verified  
**Rollback Snapshot:** `video_game/_trash/2026-11-10_C04_before_changes.tar.gz` (SHA-256: `8d52d017025f3566b5f77d99fb551f3df97077298976940d3cb0ac6f42876628`)  
**Manifest:** `video_game/_trash/2026-11-10_C04_before_changes_manifest.json`

---

## 1. Executive Summary

Task C04 delivers the complete interactive receiver and communication UI in the bunker's CRT terminal (`CRTTerminalScene`), connecting player input to the asynchronous `AIWorker` established in C03. The terminal interface features a dual-monitor CRT aesthetic:
- **Left Monitor (Telemetry & Target Acquisition):** 128×128 indexed civilization portrait, receiver tuning controls (1400.0000–1440.0000 MHz band), carrier lock detection with ±0.0800 MHz tolerance, and signal strength meter.
- **Right Monitor (Dialogue & Signal Analysis):** 6-bin vertical histogram backed by `signal_6EQUJ5.codec.decode` displaying the 6EQUJ5 signal intensity profile (`[6, 14, 26, 30, 19, 5]`) with peak 'U' (30σ) highlighted, a 38-character word-wrapped transcript with keyboard/mouse scrolling, and a single-line interactive input buffer with blinking block cursor and status indicators.

In addition, the legacy ambiguity regarding "30s" has been formally resolved (Issue `I10` closed): the UI and session data structures now explicitly distinguish between the **72-second transit duration** (`OBSERVATION_WINDOW_SECONDS`) and the **30-sigma peak intensity** (`U = 30σ`).

---

## 2. Key Actions and Implementation Details

### 2.1 UI Text & Buffer Components (`video_game/engine/ui/text.py`)
- Created [`video_game/engine/ui/text.py`](file:///Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/engine/ui/text.py):
  - **`wrap_text_chars(text, max_chars=38)`:** Word-boundary preserving line wrapper. Handles arbitrary paragraphs, explicit newlines, unbreakable long tokens, and Unicode symbols (`σ`, `°`, `α`, `δ`, `ℏ`).
  - **`wrap_text_pixels(font, text, max_pixels)`:** Monospace pixel-width wrapping for pixel-perfect HUD text alignment.
  - **`TextInputBuffer(max_length=128)`:** Single-line text editing buffer supporting printable character insertion, backspace, delete, left/right cursor navigation, clear, and visible window slicing.
  - **`TranscriptScroller(visible_lines=9)`:** Line-based transcript viewport manager with auto-scrolling on new messages, manual `scroll_up`, `scroll_down`, `scroll_to_bottom`, and bounded offset clamping.

### 2.2 Contact Session Management (`video_game/engine/contact_session.py`)
- Created [`video_game/engine/contact_session.py`](file:///Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/engine/contact_session.py):
  - **Carrier Tuning (1400–1440 MHz):** Maps all 11 milestone civilization targets across the hydrogen line band:
    - `FASR-001`: 1420.4056 MHz
    - `FASR-002`: 1420.3500 MHz
    - `FASR-003`: 1420.4800 MHz
    - `FASR-004`: 1420.2100 MHz
    - `FASR-005`: 1420.5500 MHz
    - `FASR-006`: 1420.1200 MHz
    - `FASR-007`: 1420.6700 MHz
    - `FASR-008`: 1420.3000 MHz
    - `FASR-009`: 1420.7500 MHz
    - `FASR-010`: 1420.0500 MHz
    - `FASR-SCAN-H`: 1420.4056 MHz
  - **Carrier Lock:** ±0.0800 MHz lock window (`LOCK_TOLERANCE_MHZ`). Unlocked receivers attenuate signal strength and reject outbound transmissions (`ERR: NO CARRIER LOCK`).
  - **Signal Decodes:** Codec-backed intensity bins `[6, 14, 26, 30, 19, 5]` derived via `signal_6EQUJ5.codec.decode(THE_SIGNAL)`. Peak intensity is 30σ (`U`), transit duration is 72s.
  - **Dialogue Quota:** Enforces the 12 completed exchanges limit per session. The 13th turn is blocked with `LIMIT: 12 EXCHANGES COMPLETED`.
  - **Stale Event Filtering:** Worker events are matched against `active_session_id` and monotonic `active_request_id`.

### 2.3 CRT Terminal Scene Interface (`video_game/engine/scenes/terminal.py`)
- Rewrote [`video_game/engine/scenes/terminal.py`](file:///Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/engine/scenes/terminal.py):
  - **Dual Panel Layout (480×270 canvas):**
    - Left Monitor: `(10, 20, 150, 240)` containing 128×128 indexed portrait plate, target ID header, frequency readout (`1420.4056 MHz`), lock status indicator (`LOCKED` in cyan vs `DRIFT` in amber), and signal strength bar.
    - Right Monitor: `(165, 20, 305, 240)` containing signal analysis telemetry, vertical 6EQUJ5 histogram bars with numeric labels, 9-line scrollable transcript area, user prompt entry line `> [input]▌`, and status/help footer.
  - **Controls:**
    - `[A-Z0-9 / Symbols]`: Type into message buffer.
    - `[Return]`: Submit transmission to worker.
    - `[Backspace] / [Delete]`: Edit buffer.
    - `[Left] / [Right]`: Navigate cursor within input line.
    - `[Up] / [Down] / [PageUp] / [PageDown]`: Scroll transcript.
    - `[Tab]`: Cycle active target civilization (synchronizes with bunker hub).
    - `[C]`: Cancel current in-flight AI transmission.
    - `[ [ ] / [ ] ]`: Fine frequency tuning (-0.0500 / +0.0500 MHz).
    - `[Esc]`: Return to Bunker Hub (preserves session and transcript state).
  - **Backward Compatibility:** Maintained `text_buffer` property and setter to ensure compatibility with existing integration tests.

---

## 3. Telemetry Verification & Issue I10 Resolution

Jerry Ehman’s 1977 printout characters `'6'`, `'E'`, `'Q'`, `'U'`, `'J'`, `'5'` decode into intensities:
$$\text{intensities} = [6, 14, 26, 30, 19, 5]$$
The peak value is $30\sigma$ (character `'U'`). The telescope's beam sweep across the source spanned $72\text{ seconds}$ ($10\text{ seconds}$ per bin over $6$ bins with inter-channel integration, modeled canonically as $72\text{ seconds}$).

The legacy codebase occasionally conflated the peak intensity ($30\sigma$) with the duration ($30\text{s}$). Issue `I10` is now resolved:
1. `ContactSession.decode_bins == [6, 14, 26, 30, 19, 5]`.
2. `ContactSession.peak_intensity == 30` ($\sigma$).
3. `ContactSession.duration_seconds == 72` (seconds).
4. Terminal UI renders: `PEAK: 30σ // DURATION: 72s`.

---

## 4. Visual Inspection Evidence

Inspection screenshots were generated across terminal states in [`video_game/planning/evidence/C04/previews/`](file:///Users/nzlab-la/Desktop/Github/6EQUJ5/video_game/planning/evidence/C04/previews/):

1. **`01_terminal_carrier_locked.png`:** Default locked terminal on FASR-001 (1420.4056 MHz), initial greeting displayed, 6EQUJ5 histogram bars visible.
2. **`02_terminal_typing_prompt.png`:** Active operator input (`CAN YOU DECODE THE WOW SIGNAL?`), blinking block cursor, standby status indicator.
3. **`03_terminal_tuner_unlocked.png`:** Receiver tuned to 1420.0056 MHz (-0.4000 MHz off-carrier), amber carrier drift alert, attenuated signal strength meter.
4. **`04_terminal_target_fasr006.png`:** Target switched via `[Tab]` to FASR-006 (1420.1200 MHz), active portrait plate swapped, target-specific greeting loaded.
5. **`pygame_live_crt_terminal.png`:** Scaled CRT presentation preview with scanline shader overlay.

---

## 5. Automated Test Results

1. **Contact Session & Terminal Test Suite (`video_game/tests/test_contact_session.py`):**
   - `test_contact_session_decode_bins_match_contract`: **PASSED** (`[6, 14, 26, 30, 19, 5]`, peak 30σ, 72s)
   - `test_all_eleven_targets_render_without_clipping`: **PASSED** (all 11 civilizations render on 480×270 canvas)
   - `test_long_replies_and_unicode_wrap_and_scroll`: **PASSED** (wrap at 38 chars, Unicode `σ, °, α, δ, ℏ` intact, viewport scroller)
   - `test_text_input_buffer_typing_backspace_and_limits`: **PASSED** (insertion, backspace, left/right move, 128 max capacity)
   - `test_target_switching_and_cancellation`: **PASSED** (in-flight stream cancellation, target switch)
   - `test_twelve_completed_exchanges_limit`: **PASSED** (12 exchanges succeed; 13th turn rejected)
   - `test_rapid_exit_and_reentry_preserves_state`: **PASSED** (hub <-> terminal transitions preserve transcripts)
   - `test_receiver_tuning_and_carrier_lock`: **PASSED** (1400–1440 MHz tuning, 80 kHz lock tolerance, transmission block when unlocked)
   **Result:** `8 passed in 0.56s`.

2. **Full Video Game Test Suite (`video_game/tests/`):**
   **Result:** `106 passed in 10.74s`.

3. **Root CLI Test Suite (`tests/`):**
   **Result:** `20 passed in 0.01s`.

4. **Checkpoint Audit Suite (`video_game/tests/test_checkpoint_audit.py`):**
   **Result:** `3 passed in 0.22s`.

5. **Asset Builder Dry-Run (`build_assets --dry-run`):**
   **Result:** All 14 locked asset groups verified and preserved.

---

## 6. Acceptance Criteria Sign-Off

- [x] **All eleven targets render without clipped essential text:** Verified in `test_all_eleven_targets_render_without_clipping`.
- [x] **Long replies and supported Unicode wrap and scroll correctly:** Verified in `test_long_replies_and_unicode_wrap_and_scroll`.
- [x] **Decode bins match `[6, 14, 26, 30, 19, 5]`:** Verified in `test_contact_session_decode_bins_match_contract`.
- [x] **Typing, target switching, cancellation, and rapid exit/reentry have regression coverage:** Verified across all test cases in `test_contact_session.py` and `test_input_settings.py`.

