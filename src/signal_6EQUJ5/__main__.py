"""
MAIN RECEIVER INTERFACE
═══════════════════════

Command-line interface for the 6EQUJ5 signal receiver.

Usage:
    python -m signal_6EQUJ5
    6equj5

    Then follow the prompts. The receiver is listening.
"""

import sys

from . import display
from . import codec
from . import contact


def handle_decode(args):
    """
    DECODE command — resolve an intensity sequence.

    Breaks each character into its numeric intensity value
    and prints a visual representation.
    """
    if not args:
        display.slow_print(display.green("  USAGE: DECODE <sequence>"))
        display.slow_print(display.dim_green("  Example: DECODE 6EQUJ5"))
        return

    sequence = args.strip().upper()
    results = codec.decode(sequence)

    print()
    display.slow_print(display.bright_green(f"  DECODING SEQUENCE: {sequence}"))
    display.print_separator()
    print()

    # Show each character's breakdown
    for r in results:
        char_display = display.bright_green(r['char'])
        intensity_display = display.green(f"{r['intensity']:>2}")
        desc_display = display.dim_green(r['description'])
        window_display = display.dim_green(r['window'])

        if r['description'] == "EXTRAORDINARY":
            char_display = display.red(r['char'])
            desc_display = display.red(r['description'])

        display.slow_print(
            f"  {char_display}  →  intensity {intensity_display}  "
            f"│  {desc_display:30s}  │  window: {window_display}",
            char_delay=0.01
        )

    print()

    # Draw the signal bars
    intensities = [r['intensity'] for r in results]
    labels = [r['char'] for r in results]
    display.draw_signal_bars(intensities, labels)

    # Easter egg: if they decoded THE signal
    if sequence == codec.THE_SIGNAL:
        import time
        time.sleep(0.5 * display.SPEED)
        display.slow_print(
            display.red("  ╔══════════════════════════════════════╗"),
            char_delay=0.02
        )
        display.slow_print(
            display.red('  ║          "Wow!"  — J. Ehman          ║'),
            char_delay=0.02
        )
        display.slow_print(
            display.red("  ╚══════════════════════════════════════╝"),
            char_delay=0.02
        )
        print()


def handle_encode(args):
    """
    ENCODE command — convert a text message to intensity characters.

    Maps each ASCII character to the Big Ear's intensity alphabet
    via modular arithmetic. Not historically accurate — but if you
    wanted to hide a message in telescope data...
    """
    if not args:
        display.slow_print(display.green("  USAGE: ENCODE <message>"))
        display.slow_print(display.dim_green("  Example: ENCODE HELLO WORLD"))
        return

    text = args.strip()
    results = codec.encode_detailed(text)
    encoded = codec.encode(text)

    print()
    display.slow_print(display.bright_green(f"  ENCODING: \"{text}\""))
    display.print_separator()
    print()

    for r in results:
        orig = display.dim_green(f"'{r['original']}'")
        ordinal = display.dim_green(f"ord={r['ordinal']:>3}")
        encoded_char = display.bright_green(r['encoded_char'])
        intensity = display.green(f"→ {r['intensity']:>2}")

        display.slow_print(
            f"  {orig}  ({ordinal})  mod 36  {intensity}  =  {encoded_char}",
            char_delay=0.008
        )

    print()
    display.slow_print(display.bright_green(f"  ENCODED SIGNAL: {encoded}"))
    print()

    # Draw bars for the encoded signal
    intensities = [r['intensity'] for r in results]
    labels = [r['encoded_char'] for r in results]
    if len(intensities) <= 30:  # Only draw bars if not too wide
        display.draw_signal_bars(intensities, labels)


def handle_signal():
    """
    SIGNAL command — replay the original Wow! signal detection.

    Animates the signal intensity rising, peaking, and falling,
    exactly as it appeared in the Big Ear printout on
    August 15, 1977.
    """
    import time

    print()
    display.slow_print(display.green("  ╔══════════════════════════════════════════════════╗"))
    display.slow_print(display.green("  ║  ██ CLASSIFIED SIGNAL RECORD — FASR-1977-001 ██  ║"))
    display.slow_print(display.green("  ║  Date: August 15, 1977 23:16 UTC                ║"))
    display.slow_print(display.green("  ║  Channel 2 — 1420.4056 MHz                      ║"))
    display.slow_print(display.green("  ║  Source: RA 19h25m31s / Dec -27°03'              ║"))
    display.slow_print(display.green("  ║  Constellation: Sagittarius                     ║"))
    display.slow_print(display.green("  ║  Classification: RESTRICTED — LEVEL 7           ║"))
    display.slow_print(display.green("  ╚══════════════════════════════════════════════════╝"))
    print()

    time.sleep(0.5 * display.SPEED)

    # The actual signal values
    results = codec.decode(codec.THE_SIGNAL)
    intensities = [r['intensity'] for r in results]
    labels = list(codec.THE_SIGNAL)

    # Animate: reveal bars one at a time
    if display.SPEED > 0:
        for i in range(1, len(intensities) + 1):
            print(display.CLEAR, end='')
            display.slow_print(
                display.green(f"  SIGNAL PLAYBACK — Window {i}/{len(intensities)}"
                              f"  [{(i)*12}s / {codec.OBSERVATION_WINDOW_SECONDS}s]"),
                char_delay=0.01
            )
            print()
            display.draw_signal_bars(
                intensities[:i],
                labels[:i]
            )
            time.sleep(0.8 * display.SPEED)

    # Final display with all bars
    print(display.CLEAR, end='')
    display.slow_print(
        display.bright_green("  SIGNAL COMPLETE — 72 second observation window"),
        char_delay=0.02
    )
    print()
    display.draw_signal_bars(intensities, labels)

    time.sleep(0.3 * display.SPEED)
    display.slow_print(display.dim_green(
        "  Signal rose for 36 seconds, peaked, then fell for 36 seconds."
    ))
    display.slow_print(display.dim_green(
        "  Consistent with a point source tracked by Earth's rotation."
    ))
    display.slow_print(display.dim_green(
        "  It never repeated."
    ))
    print()


def handle_listen(args):
    """
    LISTEN command — scan frequencies or target specific coordinates.

    Without arguments: original frequency sweep.
    With coordinates: target a specific location.
    Only the Wow! signal origin coordinates trigger contact.
    """
    import time

    if not args:
        # No coordinates — prompt user
        print()
        display.slow_print(display.dim_green(
            "  LISTEN requires a target."
        ), char_delay=0.01)
        display.slow_print(display.dim_green(
            "  Usage: LISTEN <RA> <DEC>  or  LISTEN <CATALOG-ID>"
        ), char_delay=0.01)
        display.slow_print(display.dim_green(
            "  Type CATALOG to view available targets."
        ), char_delay=0.01)
        print()
        return "none"
    else:
        # Coordinate targeting
        result = contact.scan_coordinates(args)
        if result == "contact":
            # Signal found — initiate contact
            contact.run_contact_session()
        return result


def handle_help():
    """
    HELP command — terse, period-appropriate documentation.
    """
    print()
    help_text = [
        ("CATALOG",          "View FASR monitored targets"),
        ("SCAN",             "Scan hydrogen line band"),
        ("LISTEN <RA> <DEC>","Target specific coordinates"),
        ("SEND",             "Transmit a message to the stars"),
        ("CLEAR",            "Clear terminal"),
        ("EXIT",             "Shut down receiver"),
    ]

    display.slow_print(display.green("  AVAILABLE COMMANDS:"), char_delay=0.01)
    print()
    for cmd, desc in help_text:
        display.slow_print(
            f"    {display.bright_green(cmd.ljust(20))} {display.dim_green(desc)}",
            char_delay=0.005
        )
    print()


def handle_history():
    """
    HISTORY command — a brief timeline of events.
    """
    print()
    display.slow_print(display.green("  CHRONOLOGY OF EVENTS"), char_delay=0.02)
    display.print_separator()
    print()

    events = [
        ("1956",       "[REDACTED] begins radio astronomy program"),
        ("1963",       "Big Ear telescope construction completed"),
        ("1965",       "Big Ear begins sky survey"),
        ("1973",       "FASR SETI division activated — longest-running program"),
        ("1977.08.15", "23:16 UTC — Signal detected on Channel 2"),
        ("1977.08.18", "Analyst J.R.E. reviews printout — files report FASR-1977-001"),
        ("1987-1989",  "Operative R. Gray searches 100+ hours — no repeat"),
        ("1995",       "Big Ear site decommissioned — cover story: golf course"),
        ("1999",       "Gray accesses VLA — no detection"),
        ("2012",       "35th anniversary — Arecibo transmits reply toward origin"),
        ("2016",       "Paris proposes comet hypothesis — FASR assessment: UNLIKELY"),
        ("2017",       "40th anniversary — comet hypothesis debated publicly"),
        ("2022",       "Caballero identifies Sun-like star candidate in source region"),
        ("2023",       "Méndez proposes hydrogen cloud hypothesis — UNDER REVIEW"),
        ("[REDACTED]", "Archaeological survey initiated at 37.22°N 38.92°E"),
        ("NOW",        "Signal unexplained. Receiver active. FASR listening."),
    ]

    for date, event in events:
        display.slow_print(
            f"  {display.bright_green(date.ljust(12))} {display.dim_green(event)}",
            char_delay=0.008
        )

    print()


def handle_about():
    """
    ABOUT command — what is this?
    """
    print()
    display.print_telescope()
    display.slow_print(display.green("  6EQUJ5"), char_delay=0.05)
    display.slow_print(display.dim_green(
        "  FASR INCIDENT REPORT — FILE NO. FASR-1977-001"
    ), char_delay=0.01)
    print()
    display.slow_print(display.dim_green(
        "  On August 15, 1977, the Big Ear receiver array"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        "  intercepted a 72-second narrowband transmission"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        "  at 1420.4056 MHz — the hydrogen line frequency."
    ), char_delay=0.01)
    print()
    display.slow_print(display.dim_green(
        "  Peak amplitude: ~30x background noise floor."
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        "  Origin vector: Sagittarius. Near Chi Sagittarii."
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        "  Status: UNREPEATED. SOURCE UNIDENTIFIED."
    ), char_delay=0.01)
    print()
    display.slow_print(display.dim_green(
        "  FASR Analyst J.R. Ehman flagged the anomaly in the"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        "  printout record. His annotation has become the"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        "  file's unofficial designation:"
    ), char_delay=0.01)
    print()
    display.slow_print(display.red("  Wow!"), char_delay=0.1)
    print()
    display.slow_print(display.dim_green(
        "  FASR continues to monitor the origin coordinates."
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        "  Parallel investigation: 37.22°N 38.92°E — status: ONGOING."
    ), char_delay=0.01)
    print()


def main():
    """
    Main entry point — boot the receiver and enter command loop.
    """
    # Contact state
    contact_active = False
    exchange_count = 0

    try:
        display.boot_sequence()
        display.print_telescope()

        display.slow_print(display.green("  RECEIVER READY"), char_delay=0.03)
        display.slow_print(display.dim_green(
            "  Frequency locked: 1420.4056 MHz"
        ), char_delay=0.01)
        display.slow_print(display.dim_green(
            "  Type HELP for available commands."
        ), char_delay=0.01)
        print()

        while True:
            try:
                display.print_prompt()
                raw = input().strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not raw:
                continue

            parts = raw.split(None, 1)
            command = parts[0].upper()
            args = parts[1] if len(parts) > 1 else ""

            if command in ('EXIT', 'QUIT', 'Q'):
                print()
                display.slow_print(display.dim_green(
                    "  Shutting down receiver..."
                ), char_delay=0.02)
                display.slow_print(display.dim_green(
                    "  The signal is still out there."
                ), char_delay=0.02)
                print()
                break
            elif command == 'DECODE':
                handle_decode(args)
            elif command == 'ENCODE':
                handle_encode(args)
            elif command == 'SIGNAL':
                handle_signal()
            elif command == 'LISTEN':
                result = handle_listen(args)
                if result == 'contact':
                    contact_active = True
                    exchange_count = 0
            elif command == 'SCAN':
                contact.handle_scan()
            elif command == 'CATALOG':
                contact.handle_catalog()
            elif command == 'SEND':
                if contact_active and args:
                    # In contact mode, SEND <msg> acts as respond
                    still_active, exchange_count = contact.handle_respond(
                        args, exchange_count
                    )
                    contact_active = still_active
                else:
                    contact.handle_send()
            elif command == 'RESPOND':
                # Hidden alias — still works
                if contact_active:
                    still_active, exchange_count = contact.handle_respond(
                        args, exchange_count
                    )
                    contact_active = still_active
                else:
                    contact.handle_send()
            elif command == 'CLOSE':
                if contact_active:
                    contact_active = False
                    exchange_count = 0
                    print()
                    display.slow_print(display.dim_green(
                        "  Contact session terminated."
                    ), char_delay=0.02)
                    display.slow_print(display.dim_green(
                        "  Session archived: FASR-CONTACT-001"
                    ), char_delay=0.02)
                    print()
                else:
                    display.slow_print(display.dim_green(
                        "  No active contact session."
                    ), char_delay=0.01)
                    print()
            elif command == 'HELP':
                handle_help()
            elif command == 'HISTORY':
                handle_history()
            elif command == 'ABOUT':
                handle_about()
            elif command == 'CLEAR':
                print(display.CLEAR, end='')
            elif command == 'WOW':
                # Easter egg
                print()
                display.slow_print(display.red("  Wow!"), char_delay=0.15)
                print()
            elif command == '1420':
                # Easter egg — the frequency
                print()
                display.slow_print(display.bright_green(
                    "  You know the frequency."
                ), char_delay=0.03)
                display.slow_print(display.bright_green(
                    "  The hydrogen line. 21 cm. 1420.4056 MHz."
                ), char_delay=0.03)
                display.slow_print(display.bright_green(
                    "  The most natural channel for interstellar communication."
                ), char_delay=0.03)
                display.slow_print(display.bright_green(
                    "  They would know we'd be listening here."
                ), char_delay=0.03)
                print()
            elif command == 'EHMAN':
                # Easter egg — the analyst
                try:
                    from . import ehman
                    ehman.annotate()
                except ImportError:
                    display.slow_print(display.dim_green("  ..."), char_delay=0.1)
            else:
                display.slow_print(display.dim_green(
                    f"  UNKNOWN COMMAND: {command}"
                ), char_delay=0.01)
                display.slow_print(display.dim_green(
                    "  Type HELP for available commands."
                ), char_delay=0.01)
                print()

    except KeyboardInterrupt:
        print()
        display.slow_print(display.dim_green(
            "  Receiver interrupted. The signal is still out there."
        ), char_delay=0.02)
        print()
        sys.exit(0)


if __name__ == '__main__':
    main()
