"""
═══════════════════════════════════════════════════════════
  MODULE DESIGNATION: [REDACTED]
  CLEARANCE: LEVEL 7 — RESTRICTED
  STATUS: ARCHIVED — DO NOT DISTRIBUTE
═══════════════════════════════════════════════════════════

  You found this because you read the source code.
  Just as the analyst found the signal because
  he read the printout.

  The following is a reconstructed account based on
  recovered field notes, classified under FASR
  Directive 1420-A, Section 12: "Anomalous Event
  Documentation."

  On the third day after the event, an analyst —
  designation J.R.E. — was conducting routine review
  of receiver output. Paper printouts. Columns of
  single-character intensity values. Pages of
  cosmic background noise. The kind of work that
  numbs the mind and sharpens the eye.

  Somewhere in the middle of the stack, in a single
  column, six characters broke the pattern:

                    6 E Q U J 5

  The analyst circled them. He wrote one word
  in the margin with red ink.

  That word became the file's designation.
  The paper was sealed and archived.

  The analyst spent the remainder of his career
  searching for a recurrence.
  He found nothing.

  The signal has not repeated.
  The paper is still sealed.
  The question remains open.
═══════════════════════════════════════════════════════════
"""


def annotate():
    """
    Reproduce the analyst's annotation — the most significant
    margin note in the history of signal intelligence.

    This is a reconstruction of the original printout
    (approximately). Each character represents one
    12-second integration window on a single channel.
    """
    from . import display

    print()

    # Simulated printout columns — the signal is in column 2
    # The surrounding data is typical background noise
    printout = [
        "  Ch1  Ch2  Ch3  Ch4  Ch5",
        "  ───  ───  ───  ───  ───",
        "   2    1    1    3    1 ",
        "   1    1    2    1    2 ",
        "   3    2    1    1    1 ",
        "   1    1    1    2    1 ",
        "   2    {6}    1    1    3 ",
        "   1    {E}    2    1    1 ",
        "   1    {Q}    1    3    2 ",
        "   2    {U}    1    1    1 ",
        "   1    {J}    2    1    1 ",
        "   1    {5}    1    2    1 ",
        "   2    1    1    1    2 ",
        "   1    2    3    1    1 ",
        "   1    1    1    1    1 ",
    ]

    for line in printout:
        # Highlight the signal characters
        formatted = line
        for char in "6EQUJ5":
            placeholder = "{" + char + "}"
            if placeholder in formatted:
                formatted = formatted.replace(
                    placeholder,
                    display.red(display.bold(char))
                )
        display.slow_print(display.green(f"  {formatted}"), char_delay=0.008)

    print()

    # The annotation
    display.slow_print(
        display.red("           ╭─────╮"),
        char_delay=0.03
    )
    display.slow_print(
        display.red("           │Wow! │"),
        char_delay=0.03
    )
    display.slow_print(
        display.red("           ╰─────╯"),
        char_delay=0.03
    )
    print()

    display.slow_print(display.dim_green(
        "  — Annotation by FASR Analyst [DESIGNATION: J.R.E.]"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        "    Date: [REDACTED] + 3 days post-event"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        "    Facility: Federation of Anomalous Signal Research"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        "    Status: ARCHIVED — FASR-1977-001"
    ), char_delay=0.01)
    print()


def timeline():
    """
    Extended field notes — the account of the event,
    reconstructed from classified material.

    This function is not documented. You have to find it.
    """
    from . import display

    entries = [
        "FIELD REPORT — FASR-1977-001 SUPPLEMENTAL",
        "CLASSIFICATION: RESTRICTED",
        "",
        "The receiver array was a Kraus-type fixed instrument,",
        "spanning an area equivalent to three football fields.",
        "It could not be aimed. It waited. The sky rotated overhead.",
        "",
        "Any source would drift through the beam in exactly",
        "72 seconds. Rising for 36 seconds as it entered,",
        "peaking at the center, then fading for 36 seconds",
        "as it exited. The signature of a point source.",
        "",
        "This is precisely what the 6EQUJ5 sequence shows.",
        "",
        "The signal was narrowband — less than 10 kHz wide.",
        "Natural radio sources are broadband. This was not natural.",
        "The frequency: 1420.4056 MHz. The hydrogen line.",
        "The most logical channel for deliberate transmission.",
        "",
        "The vector pointed toward the constellation Sagittarius.",
        "Near a star catalogued as Chi Sagittarii.",
        "Approximately 120 light-years distant.",
        "",
        "Or perhaps from much farther.",
        "Or perhaps from something passing through.",
        "Or perhaps from something that was already here.",
        "",
        "Recent analysis of archaeological site at",
        '37°13\'23"N 38°55\'21"E has revealed alignments',
        "consistent with the signal's origin vector.",
        "",
        "The implications of this correlation are",
        "currently under review by FASR Directorate.",
        "",
        "This file remains open.",
    ]

    print()
    for line in entries:
        if line:
            display.slow_print(display.dim_green(f"  {line}"), char_delay=0.01)
        else:
            print()
    print()


# ═══════════════════════════════════════════════════════
#   ANALYST'S FINAL NOTE (recovered from personal effects):
#
#   "I do not believe it was of artificial origin.
#    But I cannot state with certainty that it was not."
#
#                         — [DESIGNATION: J.R.E.]
#                            [DATE: REDACTED]
# ═══════════════════════════════════════════════════════
