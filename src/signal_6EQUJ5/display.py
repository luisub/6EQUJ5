"""
DISPLAY SUBSYSTEM — RECEIVER TERMINAL OUTPUT
═════════════════════════════════════════════

All output formatted for standard VT100-compatible
terminal. Green phosphor. 80 columns. No more, no less.

The Big Ear's output was a continuous paper printout.
Each column was a different frequency channel.
Each row was a 12-second integration.
The numbers and letters marched down the page,
column after column, day after day.

Until one column lit up.
"""

import sys
import time
import os
import shutil

# ═══════════════════════════════════════════════════════
#   ANSI escape codes — the language of terminals
#   since the 1970s. Still works. Still beautiful.
# ═══════════════════════════════════════════════════════

GREEN = "\033[32m"
BRIGHT_GREEN = "\033[92m"
DIM_GREEN = "\033[2;32m"
RED = "\033[31m"
BRIGHT_RED = "\033[91m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
DIM = "\033[2m"
BLINK = "\033[5m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"

# Block characters for signal bars
FULL_BLOCK = "█"
UPPER_HALF = "▀"
LOWER_HALF = "▄"
LIGHT_SHADE = "░"
MEDIUM_SHADE = "▒"
DARK_SHADE = "▓"

# Are we in a real terminal?
IS_TTY = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

# Speed multiplier — set to 0 to skip animations (for testing)
SPEED = 0.2 if IS_TTY else 0.0


def green(text):
    """Wrap text in green ANSI escape codes."""
    return f"{GREEN}{text}{RESET}"


def bright_green(text):
    """Bright phosphor — when something matters."""
    return f"{BRIGHT_GREEN}{text}{RESET}"


def dim_green(text):
    """Faded phosphor — like old CRT burn-in."""
    return f"{DIM_GREEN}{text}{RESET}"


def red(text):
    """Red — for the annotation. For the circle. For the margin."""
    return f"{BRIGHT_RED}{text}{RESET}"


def bold(text):
    """Bold — when the signal is strong."""
    return f"{BOLD}{text}{RESET}"


def dim(text):
    """Dim — background noise."""
    return f"{DIM}{text}{RESET}"


def slow_print(text, char_delay=0.02, line_delay=0.0, end='\n'):
    """
    Print text character by character, like a teletype.

    The Big Ear didn't have a screen — it printed to paper.
    Continuously. For years. Ehman reviewed the printouts
    by hand, days after the data was recorded.

    Parameters
    ----------
    text : str
        The text to print.
    char_delay : float
        Seconds between characters.
    line_delay : float
        Additional delay at end of line.
    end : str
        End character (default newline).
    """
    delay = char_delay * SPEED
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        if delay > 0:
            time.sleep(delay)
            if char == '\n' and line_delay > 0:
                time.sleep(line_delay * SPEED)
    sys.stdout.write(end)
    sys.stdout.flush()


def print_header():
    """Print the receiver header — system identification."""
    width = min(shutil.get_terminal_size().columns, 80)
    border = "═" * width
    print(green(border))
    title = "FEDERATION OF ANOMALOUS SIGNAL RESEARCH"
    subtitle = "TERMINAL ACCESS — RESTRICTED"
    print(green(f"  {title}"))
    print(green(f"  {subtitle}"))
    print(green(border))
    print()


def boot_sequence():
    """
    Simulate the receiver boot-up sequence.

    This never actually happened — the Big Ear was analog.
    But it feels right.
    """
    print(CLEAR, end='')

    width = min(shutil.get_terminal_size().columns, 80)
    thin = "─" * width

    # ── Phase 1: Neofetch-style splash ──
    # Icon on the left, system info on the right

    # Load the icon art
    icon_path = os.path.join(os.path.dirname(__file__), "data", "icon.txt")
    try:
        with open(icon_path, "r") as f:
            icon_lines = [line.rstrip() for line in f.readlines()]
    except FileNotFoundError:
        icon_lines = []

    # Remove trailing empty lines
    while icon_lines and not icon_lines[-1].strip():
        icon_lines.pop()

    icon_w = 40   # fixed icon width
    spacer = 3    # gap between icon and info

    # Info lines: (label, value) or None for blank, or str for section header
    info = [
        None,
        ("", "6 E Q U J 5"),
        ("", "─" * 30),
        ("Designation", "FASR-6EQUJ5-1977.815"),
        ("Frequency", "1420.4056 MHz (Hydrogen Line)"),
        ("Bandwidth", "10 kHz"),
        ("Integration", "12 sec / sample"),
        ("Duration", "72 seconds"),
        ("Intensity", "6 → 14 → 26 → 30 → 19 → 5"),
        ("Origin", "Chi Sagittarii (RA 19h25m)"),
        None,
        ("Organization", "FASR"),
        ("Classification", "LEVEL 7 -- RESTRICTED"),
        ("Terminal", "v1977.815"),
        ("Status", "ACTIVE"),
        None,
        ("", "FEDERATION OF ANOMALOUS SIGNAL RESEARCH"),
        ("", "DEEP SIGNAL RECEIVER // TERMINAL"),
    ]

    # Pad to match icon height
    total = max(len(icon_lines), len(info))
    while len(icon_lines) < total:
        icon_lines.append("")
    while len(info) < total:
        info.append(None)

    # Render each row: icon (left) + spacer + info (right)
    for i in range(total):
        # Left side: icon line padded to icon_w
        left = icon_lines[i] if i < len(icon_lines) else ""
        left_padded = left + " " * (icon_w - len(left))

        # Right side: info
        entry = info[i]
        if entry is None:
            right = ""
        elif entry[0] == "":
            # Header or separator — no label
            right = entry[1]
        else:
            label, value = entry
            right = label + ": " + value

        line = "  " + left_padded + " " * spacer + right

        # Colorize
        if entry is not None and entry[0] == "" and "─" not in entry[1]:
            # Title lines (6EQUJ5, FASR name) — bright green
            slow_print(bright_green(line), char_delay=0.008)
        elif entry is not None and "CLASSIFICATION" in str(entry):
            # Classification — red label
            label, value = entry
            colored = "  " + green(left_padded) + " " * spacer
            colored += red(label + ": " + value)
            slow_print(colored, char_delay=0.012)
        elif entry is not None and entry[0] != "":
            # Regular info — green label, dim value
            label, value = entry
            colored = "  " + green(left_padded) + " " * spacer
            colored += bright_green(label) + dim_green(": " + value)
            slow_print(colored, char_delay=0.010)
        else:
            slow_print(green(line), char_delay=0.005)

        if SPEED > 0:
            time.sleep(0.04 * SPEED)

    print()
    if SPEED > 0:
        time.sleep(0.6 * SPEED)

    slow_print(dim_green("  NOTICE: Unauthorized access to this terminal"), char_delay=0.015)
    slow_print(dim_green("  is a violation of FASR Directive 1420-A."), char_delay=0.015)
    slow_print(dim_green("  All sessions are monitored and logged."), char_delay=0.015)
    print()
    if SPEED > 0:
        time.sleep(0.4 * SPEED)

    # Phase 2: System boot
    lines = [
        ("INITIALIZING RECEIVER SUBSYSTEMS...", 0.04),
        ("", 0),
        ("  [OK] Antenna array ............ ONLINE", 0.02),
        ("  [OK] Ground plane ............. CALIBRATED", 0.02),
        ("  [OK] Feed horns ............... ALIGNED", 0.02),
        ("  [OK] Receiver chain ........... NOMINAL", 0.02),
        ("  [OK] Signal filter ............ ARMED", 0.02),
        ("  [OK] Integration: 12 sec/sample", 0.02),
        ("  [OK] Bandwidth: 10 kHz", 0.02),
        ("  [OK] Frequency: 1420.4056 MHz", 0.02),
        ("  [OK] Channel 2 ................ ACTIVE", 0.02),
        ("", 0),
        ("  CLEARANCE VERIFIED. SESSION ACTIVE.", 0.03),
        ("", 0),
    ]

    print(green(thin))
    for text, delay in lines:
        if text:
            slow_print(green(f"  {text}"), char_delay=delay)
        else:
            print()
        if SPEED > 0:
            time.sleep(0.15 * SPEED)
    print(green(thin))
    print()


def load_telescope_art():
    """
    Load the telescope ASCII art from the bundled data file.

    Returns
    -------
    str
        The ASCII art, or a fallback if file not found.
    """
    # Try package data location
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    art_path = os.path.join(data_dir, 'telescope.txt')

    if os.path.exists(art_path):
        with open(art_path, 'r', encoding='utf-8') as f:
            return f.read()

    # Fallback — minimal art
    return r"""
        /\
       /  \
      / () \
     /______\
        ||
        ||
    ════════════
    """


def print_telescope():
    """Display the telescope ASCII art in green phosphor."""
    art = load_telescope_art()
    for line in art.splitlines():
        print(dim_green(line))
    print()


def draw_signal_bars(intensities, labels=None, highlight_peak=True):
    """
    Draw vertical signal intensity bars in the terminal.

    Each bar represents one 12-second integration window.
    The peak should jump out at you — just like it jumped
    out at Ehman.

    Parameters
    ----------
    intensities : list of int
        Intensity values (0-35).
    labels : list of str, optional
        Character labels for each bar.
    highlight_peak : bool
        If True, the peak bar is drawn in bright green.
    """
    if not intensities:
        return

    max_height = 20  # Terminal rows for the tallest bar
    max_val = max(intensities) if max(intensities) > 0 else 1
    peak_idx = intensities.index(max(intensities))

    # Draw bars top-down
    for row in range(max_height, 0, -1):
        line_chars = []
        for i, val in enumerate(intensities):
            threshold = (val / max_val) * max_height
            if row <= threshold:
                if highlight_peak and i == peak_idx:
                    line_chars.append(bright_green(f" {FULL_BLOCK}{FULL_BLOCK} "))
                else:
                    line_chars.append(green(f" {DARK_SHADE}{DARK_SHADE} "))
            else:
                line_chars.append("    ")
        print("  " + "".join(line_chars))

    # Baseline
    baseline = "  " + "────" * len(intensities)
    print(green(baseline))

    # Labels
    if labels:
        label_line = "  "
        for lbl in labels:
            label_line += f" {bright_green(lbl)}  "
        print(label_line)

    # Intensity values
    val_line = "  "
    for val in intensities:
        val_str = str(val).rjust(2)
        val_line += f" {dim_green(val_str)} "
    print(val_line)
    print()


def scan_animation(duration=3.0):
    """
    Simulate scanning through radio frequencies.

    Sweeps across the band, printing noise... then finds something.
    """
    import random

    if SPEED == 0:
        print(green("  SCANNING... SIGNAL DETECTED."))
        return

    width = min(shutil.get_terminal_size().columns, 60)
    start_freq = 1420.000
    end_freq = 1420.800
    steps = int(duration / 0.05)
    freq_step = (end_freq - start_freq) / steps

    print(green("  SCANNING BAND: 1420.000 — 1420.800 MHz"))
    print()

    for i in range(steps):
        freq = start_freq + (freq_step * i)
        # Noise floor with a spike at the hydrogen line
        distance_from_signal = abs(freq - 1420.4056)
        if distance_from_signal < 0.01:
            noise = random.randint(25, 30)
            bar = bright_green(FULL_BLOCK * min(noise, width - 25))
        elif distance_from_signal < 0.05:
            noise = random.randint(8, 15)
            bar = green(DARK_SHADE * min(noise, width - 25))
        else:
            noise = random.randint(1, 4)
            bar = dim_green(LIGHT_SHADE * noise)

        freq_str = f"{freq:10.4f} MHz"
        sys.stdout.write(f"\r  {green(freq_str)} │{bar}" + " " * (width - len(bar) - 20))
        sys.stdout.flush()
        time.sleep(0.05 * SPEED)

    # Snap to the signal frequency
    sys.stdout.write(f"\r  {bright_green('1420.4056 MHz')} │{bright_green(FULL_BLOCK * (width - 25))}")
    sys.stdout.flush()
    print()
    print()
    time.sleep(0.5 * SPEED)
    slow_print(bright_green("  *** ANOMALOUS SIGNAL DETECTED ***"), char_delay=0.04)
    print()


def print_dual_panel(left_art, right_art, left_label="", right_label=""):
    """
    Print two ASCII art panels side-by-side in a green frame.

    Used during initial contact to display constellation and species
    art together — a visual first impression.

    Parameters
    ----------
    left_art : str
        ASCII art for the left panel (constellation).
    right_art : str
        ASCII art for the right panel (species/face).
    left_label : str
        Label below the left panel.
    right_label : str
        Label below the right panel.
    """
    left_lines = left_art.split('\n')
    right_lines = right_art.split('\n')

    # Determine panel width from the art (max line length)
    left_width = max((len(line) for line in left_lines), default=45)
    right_width = max((len(line) for line in right_lines), default=45)

    # Ensure consistent width
    left_width = max(left_width, 45)
    right_width = max(right_width, 45)

    # Pad to same height
    max_height = max(len(left_lines), len(right_lines))
    while len(left_lines) < max_height:
        left_lines.append("")
    while len(right_lines) < max_height:
        right_lines.append("")

    sep = " │ "
    total_width = left_width + len(sep) + right_width

    # Top border
    print(dim_green("  ╔" + "═" * total_width + "╗"))

    # Panels
    for l_line, r_line in zip(left_lines, right_lines):
        l_padded = l_line.ljust(left_width)
        r_padded = r_line.ljust(right_width)
        sys.stdout.write(dim_green("  ║"))
        sys.stdout.write(green(l_padded))
        sys.stdout.write(dim_green(sep))
        sys.stdout.write(green(r_padded))
        sys.stdout.write(dim_green("║"))
        sys.stdout.write("\n")
        sys.stdout.flush()
        if SPEED > 0:
            time.sleep(0.01 * SPEED)

    # Labels row
    if left_label or right_label:
        l_label = left_label.center(left_width)
        r_label = right_label.center(right_width)
        print(dim_green("  ╠" + "═" * total_width + "╣"))
        sys.stdout.write(dim_green("  ║"))
        sys.stdout.write(bright_green(l_label))
        sys.stdout.write(dim_green(sep))
        sys.stdout.write(bright_green(r_label))
        sys.stdout.write(dim_green("║"))
        sys.stdout.write("\n")

    # Bottom border
    print(dim_green("  ╚" + "═" * total_width + "╝"))
    print()

import textwrap


# ═══════════════════════════════════════════════════════
#   ANSI cursor control — for panel-based layouts
# ═══════════════════════════════════════════════════════

def _cursor_to(row, col):
    """Move cursor to (row, col), 1-indexed."""
    sys.stdout.write(f"\033[{row};{col}H")

def _clear_line():
    """Clear from cursor to end of line."""
    sys.stdout.write("\033[K")

def _save_cursor():
    sys.stdout.write("\033[s")

def _restore_cursor():
    sys.stdout.write("\033[u")

def _hide_cursor():
    sys.stdout.write("\033[?25l")

def _show_cursor():
    sys.stdout.write("\033[?25h")


# Minimum terminal width for dual-panel mode
MIN_PANEL_WIDTH = 150


class ContactPanel:
    """
    Persistent dual-panel display for contact sessions.

    Left panel:  alien face art (fixed, never scrolls)
    Right panel: dialogue messages (scrolls when full)

    Uses ANSI cursor positioning to keep the face visible
    while dialogue lines are added to the right column.
    The input prompt sits below the frame.

    If the terminal is too narrow (< MIN_PANEL_WIDTH),
    the panel is not drawn and all output falls through
    to standard scrolling mode.
    """

    def __init__(self, face_art, civ_name="UNKNOWN", constellation="",
                 catalog_id=""):
        self.civ_name = civ_name
        self.constellation = constellation
        self.catalog_id = catalog_id

        # Parse face art lines
        self.face_lines = face_art.split('\n') if face_art else []
        while self.face_lines and not self.face_lines[-1].strip():
            self.face_lines.pop()

        # Panel geometry
        term_cols = shutil.get_terminal_size().columns
        self.active = term_cols >= MIN_PANEL_WIDTH and IS_TTY

        if not self.active:
            self.left_w = 0
            self.right_w = 0
            self.panel_h = 0
            self.right_lines = []
            self.right_colors = []
            self.right_cursor = 0
            self.frame_top = 1
            self.prompt_row = 1
            self.right_col_start = 1
            return

        # Left panel: face art width (at least 47 for padding)
        self.left_w = max(
            max((len(l) for l in self.face_lines), default=45),
            47
        )
        # Right panel: fills remaining space
        # Layout: "  ║" (4) + left_w + " │ " (3) + right_w + "║" (1)
        # total visible = 4 + left_w + 3 + right_w + 1
        self.right_w = term_cols - 4 - self.left_w - 3 - 1
        self.right_w = max(self.right_w, 40)  # minimum usable

        # Panel height = face art height, minimum 31 lines
        self.panel_h = max(len(self.face_lines), 31)

        # Pad face lines to panel height
        while len(self.face_lines) < self.panel_h:
            self.face_lines.append("")

        # Right panel content buffer (lines currently displayed)
        self.right_lines = [""] * self.panel_h
        # Color function for each right-panel line (for scroll redraws)
        self.right_colors = [None] * self.panel_h

        # Cursor tracking: which row of the right panel to write next
        self.right_cursor = 0

        # Screen row where the frame starts (set after draw)
        self.frame_top = 1

    def draw(self):
        """
        Draw the initial frame with face art and empty right panel.
        """
        if not self.active:
            return

        _hide_cursor()

        # Clear screen and position at top
        sys.stdout.write(CLEAR)
        sys.stdout.flush()

        self.frame_top = 1  # start at row 1

        sep = " │ "
        total_inner = self.left_w + len(sep) + self.right_w

        # Top border
        _cursor_to(self.frame_top, 1)
        sys.stdout.write(dim_green(
            "  ╔" + "═" * total_inner + "╗"
        ))

        # Panel rows
        for i in range(self.panel_h):
            row = self.frame_top + 1 + i
            _cursor_to(row, 1)

            face_line = self.face_lines[i] if i < len(self.face_lines) else ""
            l_padded = face_line.ljust(self.left_w)

            sys.stdout.write(dim_green("  ║"))
            sys.stdout.write(green(l_padded))
            sys.stdout.write(dim_green(sep))
            # Right panel — empty for now
            sys.stdout.write(" " * self.right_w)
            sys.stdout.write(dim_green("║"))

        # Label row
        label_row = self.frame_top + 1 + self.panel_h
        _cursor_to(label_row, 1)
        sys.stdout.write(dim_green(
            "  ╠" + "═" * total_inner + "╣"
        ))

        info_row = label_row + 1
        _cursor_to(info_row, 1)

        # Build label: civ name on left, catalog_id + "CLOSE to end" on right
        left_label = f" {self.civ_name}"
        if self.constellation:
            left_label += f" — {self.constellation}"
        left_label = left_label.ljust(self.left_w)

        right_label = f"[{self.catalog_id}]  Type CLOSE to end."
        right_label = right_label.ljust(self.right_w)

        sys.stdout.write(dim_green("  ║"))
        sys.stdout.write(bright_green(left_label))
        sys.stdout.write(dim_green(sep))
        sys.stdout.write(dim_green(right_label))
        sys.stdout.write(dim_green("║"))

        # Bottom border
        bottom_row = info_row + 1
        _cursor_to(bottom_row, 1)
        sys.stdout.write(dim_green(
            "  ╚" + "═" * total_inner + "╝"
        ))

        # Input prompt row
        self.prompt_row = bottom_row + 1
        _cursor_to(self.prompt_row, 1)
        sys.stdout.flush()

        _show_cursor()

        # Right panel starts at column: 4 (indent + border) + left_w + 3 (sep)
        self.right_col_start = 4 + self.left_w + 3 + 1  # +1 for 1-indexed

    def _right_panel_row(self, panel_line_idx):
        """Screen row for a given right-panel line index."""
        return self.frame_top + 1 + panel_line_idx

    def _write_right_line(self, panel_line_idx, text):
        """Write a single line into the right panel at the given index."""
        _save_cursor()
        _hide_cursor()

        row = self._right_panel_row(panel_line_idx)
        _cursor_to(row, self.right_col_start)

        # Truncate to right_w, pad with spaces
        display_text = text[:self.right_w].ljust(self.right_w)
        sys.stdout.write(display_text)

        _restore_cursor()
        _show_cursor()
        sys.stdout.flush()

    def _scroll_right_panel(self):
        """Scroll all right-panel lines up by one, freeing the last line."""
        # Shift buffers
        self.right_lines.pop(0)
        self.right_lines.append("")
        self.right_colors.pop(0)
        self.right_colors.append(None)

        # Redraw all right-panel lines with their stored colors
        _save_cursor()
        _hide_cursor()

        for i in range(self.panel_h):
            row = self._right_panel_row(i)
            _cursor_to(row, self.right_col_start)
            raw = self.right_lines[i][:self.right_w]
            padded = raw.ljust(self.right_w)
            cfn = self.right_colors[i]
            if cfn:
                sys.stdout.write(cfn(padded))
            else:
                sys.stdout.write(padded)

        _restore_cursor()
        _show_cursor()
        sys.stdout.flush()

        self.right_cursor = self.panel_h - 1

    def _ensure_room(self):
        """Make sure there's at least one free line in the right panel."""
        if self.right_cursor >= self.panel_h:
            self._scroll_right_panel()

    def add_line(self, text, color_fn=None, char_delay=0.0):
        """
        Add a single line to the right panel.

        Parameters
        ----------
        text : str
            Raw text (will be truncated to panel width).
        color_fn : callable, optional
            Color function (e.g. bright_green). Applied for display only.
        char_delay : float
            If > 0, typewriter effect per character.
        """
        if not self.active:
            # Fallback: just print normally
            colored = color_fn(text) if color_fn else text
            slow_print(colored, char_delay=char_delay)
            return

        self._ensure_room()

        # Store raw text and color function in buffer
        display_text = text[:self.right_w]
        self.right_lines[self.right_cursor] = display_text
        self.right_colors[self.right_cursor] = color_fn

        # Render with optional typewriter
        if char_delay > 0 and SPEED > 0:
            _save_cursor()
            _hide_cursor()
            row = self._right_panel_row(self.right_cursor)
            _cursor_to(row, self.right_col_start)

            padded = display_text.ljust(self.right_w)
            for j, ch in enumerate(padded):
                colored_ch = color_fn(ch) if color_fn else ch
                sys.stdout.write(colored_ch)
                sys.stdout.flush()
                if j < len(display_text):
                    time.sleep(char_delay * SPEED)

            _restore_cursor()
            _show_cursor()
            sys.stdout.flush()
        else:
            colored = color_fn(display_text) if color_fn else display_text
            self._write_right_line(self.right_cursor,
                                   colored)

        self.right_cursor += 1

    def add_blank(self):
        """Add a blank line to the right panel."""
        self.add_line("")

    def add_wrapped(self, text, color_fn=None, char_delay=0.0,
                    indent=2, prefix=""):
        """
        Add text to the right panel with word wrapping.

        Parameters
        ----------
        text : str
            Text to wrap and add.
        color_fn : callable
            Color function.
        char_delay : float
            Typewriter delay.
        indent : int
            Left indent in spaces.
        prefix : str
            First-line prefix (e.g. '▸ INCOMING:').
        """
        if not self.active:
            # Fallback
            colored = color_fn(text) if color_fn else text
            slow_print(colored, char_delay=char_delay)
            return

        usable_w = self.right_w - indent
        if usable_w < 20:
            usable_w = self.right_w

        pad = " " * indent

        if prefix:
            self.add_line(f"{pad}{prefix}", color_fn, char_delay)

        wrapper = textwrap.TextWrapper(width=usable_w)
        for line in wrapper.wrap(text):
            self.add_line(f"{pad}{line}", color_fn, char_delay)

    def incoming(self, text, char_delay=0.035):
        """Display an incoming message in the right panel."""
        self.add_line("  ▸ INCOMING:", dim_green, char_delay=0.015)

        usable_w = max(self.right_w - 6, 60)
        wrapper = textwrap.TextWrapper(
            width=usable_w,
            initial_indent='    "',
            subsequent_indent='     '
        )
        lines = wrapper.wrap(text)
        if lines:
            lines[-1] += '"'
        else:
            lines = ['    ""']

        for line in lines:
            self.add_line(line, bright_green, char_delay=char_delay)
        self.add_blank()

    def outgoing(self, text):
        """Display an outgoing message in the right panel."""
        self.add_line(
            f'  ◂ TRANSMITTING: "{text}"',
            dim_green,
            char_delay=0.015
        )

    def status(self, text, char_delay=0.015):
        """Display a status line in the right panel."""
        self.add_line(f"  {text}", dim_green, char_delay=char_delay)

    def move_to_prompt(self):
        """Position cursor at the input prompt inside the right panel."""
        if not self.active:
            return
        self._ensure_room()
        row = self._right_panel_row(self.right_cursor)
        _cursor_to(row, self.right_col_start)
        # Clear only the right panel area on this row
        sys.stdout.write(" " * self.right_w)
        _cursor_to(row, self.right_col_start)
        sys.stdout.flush()

    def print_prompt(self):
        """Print the contact input prompt inside the right panel."""
        if not self.active:
            sys.stdout.write(green("  ◂ "))
            sys.stdout.flush()
            return
        self.move_to_prompt()
        sys.stdout.write(green("  ◂ "))
        sys.stdout.flush()

    def consume_input(self, raw_text):
        """
        After input() returns, clean up the prompt line in the right
        panel and record the raw text properly. The echoed text from
        input() may have moved the cursor; this resets it.
        """
        if not self.active:
            return
        # Overwrite the prompt line with blank (the outgoing display
        # will re-render it properly via panel.outgoing())
        row = self._right_panel_row(self.right_cursor)
        _cursor_to(row, self.right_col_start)
        sys.stdout.write(" " * self.right_w)
        sys.stdout.flush()

    def close(self):
        """
        Clean up after a contact session — move cursor below frame
        and restore normal scrolling output.
        """
        if not self.active:
            return
        # Move to prompt row + 1 so normal output resumes below
        _cursor_to(self.prompt_row + 1, 1)
        _show_cursor()
        sys.stdout.flush()

    def stream_token(self, token, is_first=False, is_last=False,
                     line_state=None):
        """
        Stream a single token into the right panel for live AI responses.

        Parameters
        ----------
        token : str
            The incoming token text.
        is_first : bool
            If True, print the '▸ INCOMING:' header and open quote.
        is_last : bool
            If True, print the closing quote.
        line_state : dict
            Mutable dict tracking streaming state:
            {'line_buf': str, 'col': int, 'started': bool}

        Returns
        -------
        dict
            Updated line_state.
        """
        if line_state is None:
            line_state = {'line_buf': '', 'col': 0, 'started': False}

        if not self.active:
            # Fallback: write directly
            if is_first:
                print()
                slow_print(dim_green("  ▸ INCOMING:"), char_delay=0.015)
                sys.stdout.write(bright_green('    "'))
                sys.stdout.flush()
            for ch in token:
                sys.stdout.write(bright_green(ch))
                sys.stdout.flush()
                if SPEED > 0:
                    time.sleep(0.02 * SPEED)
            if is_last:
                sys.stdout.write(bright_green('"'))
                sys.stdout.flush()
                print()
                print()
            return line_state

        usable_w = self.right_w - 6  # matches indent '     ' (5 chars + margin)

        if is_first:
            self.add_line("  ▸ INCOMING:", dim_green, char_delay=0.015)
            self._ensure_room()
            line_state['started'] = True
            line_state['line_buf'] = '    "'
            line_state['col'] = 5

            # Write the opening quote
            _save_cursor()
            _hide_cursor()
            row = self._right_panel_row(self.right_cursor)
            _cursor_to(row, self.right_col_start)
            sys.stdout.write(bright_green('    "'))
            _restore_cursor()
            _show_cursor()
            sys.stdout.flush()

        # Process token character by character
        for ch in token:
            if ch == '\n':
                # Flush current line and move to next
                self.right_lines[self.right_cursor] = line_state['line_buf']
                self.right_colors[self.right_cursor] = bright_green
                self.right_cursor += 1
                self._ensure_room()
                line_state['line_buf'] = '     '
                line_state['col'] = 5
                # Position cursor at new line
                _save_cursor()
                _hide_cursor()
                row = self._right_panel_row(self.right_cursor)
                _cursor_to(row, self.right_col_start)
                sys.stdout.write(bright_green('     '))
                _restore_cursor()
                _show_cursor()
                sys.stdout.flush()
                continue

            # Check if word wrapping needed
            if line_state['col'] >= usable_w and ch == ' ':
                # Wrap to next line
                self.right_lines[self.right_cursor] = line_state['line_buf']
                self.right_colors[self.right_cursor] = bright_green
                self.right_cursor += 1
                self._ensure_room()
                line_state['line_buf'] = '     '
                line_state['col'] = 5
                _save_cursor()
                _hide_cursor()
                row = self._right_panel_row(self.right_cursor)
                _cursor_to(row, self.right_col_start)
                sys.stdout.write(bright_green('     '))
                _restore_cursor()
                _show_cursor()
                sys.stdout.flush()
                continue

            # Write character
            line_state['line_buf'] += ch
            line_state['col'] += 1

            _save_cursor()
            _hide_cursor()
            row = self._right_panel_row(self.right_cursor)
            col = self.right_col_start + line_state['col'] - 1
            _cursor_to(row, col)
            sys.stdout.write(bright_green(ch))
            _restore_cursor()
            _show_cursor()
            sys.stdout.flush()

            if SPEED > 0:
                time.sleep(0.02 * SPEED)

        if is_last:
            # Write closing quote
            line_state['line_buf'] += '"'
            line_state['col'] += 1
            _save_cursor()
            _hide_cursor()
            row = self._right_panel_row(self.right_cursor)
            col = self.right_col_start + line_state['col'] - 1
            _cursor_to(row, col)
            sys.stdout.write(bright_green('"'))
            _restore_cursor()
            _show_cursor()
            sys.stdout.flush()

            self.right_lines[self.right_cursor] = line_state['line_buf']
            self.right_colors[self.right_cursor] = bright_green
            self.right_cursor += 1
            self.add_blank()

        return line_state


# The currently active panel (None when not in a contact session)
_active_panel = None


def get_active_panel():
    """Return the currently active ContactPanel, or None."""
    return _active_panel


def set_active_panel(panel):
    """Set the active ContactPanel (or None to clear)."""
    global _active_panel
    _active_panel = panel


def print_separator():
    """Print a thin separator line."""
    width = min(shutil.get_terminal_size().columns, 80)
    print(dim_green("─" * width))


def print_prompt():
    """Print the command prompt."""
    from . import contact
    if contact.CONTACT_MADE:
        sys.stdout.write(green("RECEIVER") + dim_green(" // ") + dim_green("SIGNAL ACQUIRED") + dim_green(" > "))
    else:
        sys.stdout.write(green("RECEIVER") + dim_green(" > "))
    sys.stdout.flush()
