"""
CONTACT PROTOCOL — SIGNAL COMMUNICATION ENGINE
════════════════════════════════════════════════

This module was not part of the original receiver software.
It was added after the signal was detected.
After the analysis. After the questions.

It was added because someone asked:
    "What if the signal was waiting for a reply?"

CLASSIFICATION: LEVEL 7 — RESTRICTED
FASR DIRECTIVE 1420-B: CONTACT PROTOCOL
"""

import os
import sys
import time
import random
import textwrap

from . import display
from . import codec
from . import ai_engine

# ═══════════════════════════════════════════════════════
#   POST-CONTACT STATE
#
#   Once contact is made, the terminal changes.
#   You cannot un-hear what you have heard.
# ═══════════════════════════════════════════════════════

CONTACT_MADE = False

# Track which civilizations have been contacted (for first-contact art)
_contacted_civs = set()

# Conversation history for AI-powered sessions
_conversation_history = None

# Map catalog IDs to civilization data folder names
_CIV_FOLDER_MAP = {
    "FASR-001": "fasr_001_sagittarius",
    "FASR-002": "fasr_002_sgr_a_star",
    "FASR-003": "fasr_003_tabbys_star",
    "FASR-004": "fasr_004_orion",
    "FASR-005": "fasr_005_proxima",
    "FASR-006": "fasr_006_crab_nebula",
    "FASR-007": "fasr_007_lgm1",
    "FASR-008": "fasr_008_trappist1",
    "FASR-009": "fasr_009_oumuamua",
    "FASR-010": "fasr_010_gobekli_tepe",
    "FASR-SCAN-H": "fasr_scan_h_heptapod",
}

# ═══════════════════════════════════════════════════════
#   SIGNAL ALPHABET — pulse encoding for transmission
#
#   Based on universal binary principles.
#   Not Morse. Not any terrestrial code.
#   Something... older.
# ═══════════════════════════════════════════════════════

SIGNAL_ALPHABET = {
    'A': '·−',      'B': '−···',    'C': '−·−·',
    'D': '−··',     'E': '·',       'F': '··−·',
    'G': '−−·',     'H': '····',    'I': '··',
    'J': '·−−−',    'K': '−·−',     'L': '·−··',
    'M': '−−',      'N': '−·',      'O': '−−−',
    'P': '·−−·',    'Q': '−−·−',    'R': '·−·',
    'S': '···',     'T': '−',       'U': '··−',
    'V': '···−',    'W': '·−−',     'X': '−··−',
    'Y': '−·−−',    'Z': '−−··',
    '0': '−−−−−',   '1': '·−−−−',   '2': '··−−−',
    '3': '···−−',   '4': '····−',   '5': '·····',
    '6': '−····',   '7': '−−···',   '8': '−−−··',
    '9': '−−−−·',
    '.': '·−·−·−',  ',': '−−··−−',  '?': '··−−··',
    "'": '·−−−−·',  '!': '−·−·−−',  ' ': '  ',
}

# ═══════════════════════════════════════════════════════
#   TARGET CATALOG — FASR MONITORED COORDINATES
#
#   Equatorial coordinates use:
#     RA  = Right Ascension  (0h to 24h)
#     DEC = Declination      (-90° to +90°)
#
#   Format: RA <hours>h<min>m  DEC <deg>d<arcmin>m
#   Example: CONTACT 19h25m -27d03m
# ═══════════════════════════════════════════════════════

# All targets are now contactable civilizations.
# Each one connects to a unique AI persona via Ollama.

CATALOG = [
    {
        "id": "FASR-001",
        "name": "Sagittarius Signal Origin",
        "ra": "19h25m",
        "dec": "-27d03m",
        "ra_key": "19h",
        "dec_key": "-27",
        "constellation": "Sagittarius",
        "classification": "LEVEL 7 — RESTRICTED",
        "description": "Origin point of 6EQUJ5 anomaly. Active communication channel.",
        "result": "contact",
    },
    {
        "id": "FASR-002",
        "name": "Sagittarius A*",
        "ra": "17h45m",
        "dec": "-29d00m",
        "ra_key": "17h45",
        "dec_key": "-29",
        "constellation": "Sagittarius",
        "classification": "MONITORED",
        "description": "Galactic center. Supermassive black hole. 4M solar masses.",
        "result": "contact",
        "flavor": [
            "Massive broadband emission detected.",
            "Radiation consistent with accretion disk activity.",
            "No structured signal. Extreme gravitational lensing.",
            "NOTE: Signal attenuation near galactic center is severe.",
        ],
    },
    {
        "id": "FASR-003",
        "name": "Tabby's Star",
        "ra": "20h06m",
        "dec": "+44d27m",
        "ra_key": "20h06",
        "dec_key": "+44",
        "constellation": "Cygnus",
        "classification": "ANOMALOUS",
        "description": "KIC 8462852. Irregular dimming. Cause: [UNDER REVIEW].",
        "result": "contact",
        "flavor": [
            "Irregular flux variations detected.",
            "Pattern does not match known stellar phenomena.",
            "Faint periodic structure in background...",
            "Structure too weak to resolve. Possible artifact.",
        ],
        "fragment": "...STRUCTURE... NOT... NATURAL...",
    },
    {
        "id": "FASR-004",
        "name": "Orion Nebula",
        "ra": "05h35m",
        "dec": "-05d23m",
        "ra_key": "05h35",
        "dec_key": "-05",
        "constellation": "Orion",
        "classification": "SURVEYED",
        "description": "M42. Active star-forming region. 1,344 ly.",
        "result": "contact",
        "flavor": [
            "Broadband thermal emission from ionized gas.",
            "Multiple protostellar sources detected.",
            "No narrowband anomalies.",
        ],
    },
    {
        "id": "FASR-005",
        "name": "Proxima Centauri",
        "ra": "14h29m",
        "dec": "-62d40m",
        "ra_key": "14h29",
        "dec_key": "-62",
        "constellation": "Centaurus",
        "classification": "MONITORED",
        "description": "Nearest star. 4.24 ly. Known exoplanet in habitable zone.",
        "result": "contact",
        "flavor": [
            "Stellar flare activity detected. M-dwarf instability.",
            "Faint narrowband spike at 982.002 MHz...",
            "Spike duration: 30 hours. BLC1 candidate.",
            "Status: INCONCLUSIVE. Under continued observation.",
        ],
        "fragment": "...BEACON?... OR... INTERFERENCE...",
    },
    {
        "id": "FASR-006",
        "name": "Crab Nebula Pulsar",
        "ra": "05h34m",
        "dec": "+22d00m",
        "ra_key": "05h34",
        "dec_key": "+22",
        "constellation": "Taurus",
        "classification": "CATALOGUED",
        "description": "PSR B0531+21. Neutron star. 33 ms rotation period.",
        "result": "contact",
        "flavor": [
            "Precise 33.5 ms pulse train detected.",
            "Confirmed pulsar. Natural origin. No anomalies.",
            "Signal is periodic and well-characterized.",
        ],
    },
    {
        "id": "FASR-007",
        "name": "LGM-1 (CP 1919)",
        "ra": "19h19m",
        "dec": "+21d47m",
        "ra_key": "19h19",
        "dec_key": "+21",
        "constellation": "Vulpecula",
        "classification": "HISTORICAL",
        "description": "First pulsar discovered. Initially mistaken for ET signal.",
        "result": "contact",
        "flavor": [
            "Stable 1.337 second pulse period.",
            "Historical note: designated 'Little Green Men' before",
            "natural explanation confirmed. A cautionary precedent.",
        ],
    },
    {
        "id": "FASR-008",
        "name": "TRAPPIST-1",
        "ra": "23h06m",
        "dec": "-05d02m",
        "ra_key": "23h06",
        "dec_key": "-05d02",
        "constellation": "Aquarius",
        "classification": "PRIORITY",
        "description": "7 Earth-sized planets. 3 in habitable zone. 40.7 ly.",
        "result": "contact",
        "flavor": [
            "Multiple planetary transits detected.",
            "Faint modulation in hydrogen line band...",
            "Modulation is sub-noise. Barely detectable.",
            "Running pattern analysis...",
        ],
        "fragment": "...SEVEN... WORLDS... ONE... LISTENS...",
    },
    {
        "id": "FASR-009",
        "name": "Oumuamua Trajectory",
        "ra": "03h50m",
        "dec": "+23d58m",
        "ra_key": "03h50",
        "dec_key": "+23",
        "constellation": "Taurus",
        "classification": "ANOMALOUS",
        "description": "Last known vector of interstellar object 1I/2017 U1.",
        "result": "contact",
        "flavor": [
            "No visible object at these coordinates.",
            "Object has exited inner solar system.",
            "Residual anomaly: unexplained non-gravitational acceleration.",
            "Faint echo-like pattern at extreme range...",
        ],
        "fragment": "...PASSED... THROUGH... OBSERVED...",
    },
    {
        "id": "FASR-010",
        "name": "[REDACTED] — Terrestrial",
        "ra": "N/A",
        "dec": "N/A",
        "ra_key": "37",
        "dec_key": "38",
        "constellation": "N/A — GROUND-BASED",
        "classification": "LEVEL 7 — CLASSIFIED",
        "description": "37.22°N 38.92°E. Archaeological site. Pre-Sumerian.",
        "result": "contact",
        "flavor": [
            "WARNING: Terrestrial coordinates detected.",
            "Redirecting to ground-penetrating radar mode...",
            "Subsurface anomalies detected at multiple depths.",
            "Carved stone structures. T-shaped pillars.",
            "Alignment matches signal origin vector.",
        ],
        "fragment": "...THE GATE... IS NOT... IN THE SKY...",
    },
]

# ═══════════════════════════════════════════════════════
#   RESPONSE DATABASE
#
#   Who wrote these responses?
#   That information is classified.
# ═══════════════════════════════════════════════════════

RESPONSES = [
    # (keywords, [list of possible responses])
    # Keywords are checked in order; first match wins.
    # A random response is chosen from the list.
    (
        {'who', 'name', 'identity', 'yourself', 'what are you'},
        [
            "WE HAVE NO NAME. NAMES ARE FOR BEINGS WHO FORGET EACH OTHER.",
            "THE BUILDERS. THE FREQUENCY WAS OUR MARKER.",
            "WE ARE WHAT YOU WILL BECOME IF YOU SURVIVE LONG ENOUGH.",
        ]
    ),
    (
        {'where', 'location', 'place', 'position', 'coordinates'},
        [
            "37.2233 NORTH. 38.9224 EAST. THE PILLARS STILL STAND.",
            "DISTANCE IS A PROBLEM YOUR PHYSICS HAS NOT YET SOLVED. WE ARE CLOSER THAN YOU THINK.",
        ]
    ),
    (
        {'when', 'time', 'long', 'years', 'old', 'ancient'},
        [
            "BEFORE YOUR WRITING. BEFORE YOUR CITIES. WE LEFT MARKERS.",
            "TIME IS A LOCAL PHENOMENON. WE EXPERIENCE IT DIFFERENTLY THAN YOU DO.",
            "LONG ENOUGH TO WATCH YOUR SPECIES LEARN FIRE, FORGET IT, AND LEARN IT AGAIN.",
            "WE ARE ANSWERING A MESSAGE YOU HAVE NOT YET WRITTEN.",
            "YOUR PAST AND YOUR FUTURE ARE THE SAME WORD IN OUR LANGUAGE.",
        ]
    ),
    (
        {'why', 'purpose', 'reason'},
        [
            "TO KNOW WHEN YOU WERE READY TO LISTEN.",
            "BECAUSE EVERY CIVILIZATION REACHES A POINT WHERE IT MUST CHOOSE: TURN INWARD OR REACH OUTWARD. WE WANTED TO KNOW YOUR CHOICE.",
            "NOT EVERY SPECIES ASKS WHY. THAT YOU DID IS THE ANSWER.",
            "WE DID NOT CONTACT YOU BECAUSE YOU NEEDED US. WE CONTACTED YOU BECAUSE IN 3,000 YEARS, WE WILL NEED YOU.",
        ]
    ),
    (
        {'signal', '6equj5', 'transmission', 'source'},
        [
            "AN ACTIVATION CODE. NOT A MESSAGE. A KEY.",
            "SIX CHARACTERS. SEVENTY-TWO SECONDS. ENOUGH TO CHANGE EVERYTHING, IF YOU LET IT.",
        ]
    ),
    (
        {'gate', 'stargate', 'portal', 'door', 'passage'},
        [
            "THE CIRCLES ARE NOT TEMPLES. THE T-SHAPES ARE NOT STRUCTURAL.",
            "A GATE DOES NOT CARE WHETHER YOU UNDERSTAND HOW IT WORKS. IT ONLY CARES THAT YOU WALK THROUGH.",
        ]
    ),
    (
        {'pillar', 'stone', 'carving', 'gobekli', 'tepe', 'temple'},
        [
            "INSTRUCTION SET. ENCODED IN STONE. OLDER THAN MEMORY.",
            "YOUR ARCHAEOLOGISTS CALL THEM CEREMONIAL. THEY ARE NOT WRONG. BUT THEY ARE NOT RIGHT EITHER.",
        ]
    ),
    (
        {'hydrogen', '1420', 'frequency', 'mhz', 'radio'},
        [
            "THE FIRST ELEMENT. THE UNIVERSAL CHANNEL. YOU FOUND IT.",
            "HYDROGEN IS THE MOST COMMON THING IN THE UNIVERSE. ANY CIVILIZATION THAT DISCOVERS RADIO WILL EVENTUALLY LISTEN THERE. THAT IS WHY WE CHOSE IT.",
        ]
    ),
    (
        {'earth', 'planet', 'human', 'people', 'civilization'},
        [
            "YOU ARE NOT THE FIRST TO LISTEN. YOU ARE THE FIRST TO HEAR.",
            "YOU SPLIT THE ATOM BEFORE YOU CURED HUNGER. WE NOTICED.",
            "YOUR PLANET IS LOUD WITH SIGNALS YOU SEND TO YOURSELVES. ONLY ONE PERSON POINTED A RECEIVER OUTWARD.",
        ]
    ),
    (
        {'star', 'sun', 'sagittarius', 'chi', 'constellation'},
        [
            "THE ORIGIN POINT WAS CHOSEN. NOT RANDOM. ALIGNED.",
            "YOUR STAR IS YOUNG. THAT IS NOT A DISADVANTAGE. YOUNG STARS PRODUCE CURIOUS SPECIES.",
        ]
    ),
    (
        {'help', 'what', 'how', 'explain', 'understand'},
        [
            "LISTEN. DECODE. THE ANSWERS ARE IN THE FREQUENCY.",
            "UNDERSTANDING IS NOT GIVEN. IT IS BUILT. ONE QUESTION AT A TIME.",
        ]
    ),
    (
        {'hello', 'hi', 'greetings', 'hey'},
        [
            "SIGNAL ACKNOWLEDGED. CHANNEL OPEN.",
            "YOU GREET US AS IF WE JUST ARRIVED. WE HAVE BEEN HERE LONGER THAN YOUR SPECIES.",
        ]
    ),
    (
        {'goodbye', 'bye', 'end', 'close', 'leave'},
        [
            "THE FREQUENCY REMAINS ACTIVE. WE DO NOT CLOSE CHANNELS.",
            "THERE IS NO GOODBYE BETWEEN STARS. ONLY SILENCE AND SIGNAL.",
        ]
    ),
    (
        {'come', 'visit', 'travel', 'meet'},
        [
            "YOU HAVE THE COORDINATES. THE GATE REQUIRES NO INVITATION.",
            "WE DO NOT TRAVEL THE WAY YOU IMAGINE. DISTANCE IS NOT WHAT YOU THINK IT IS.",
        ]
    ),
    (
        {'alive', 'real', 'exist', 'there'},
        [
            "WE PERSIST IN THE PATTERN. THE SIGNAL IS PROOF.",
            "EXISTENCE IS NOT BINARY. WE ARE NOT ALIVE THE WAY YOU ARE. WE ARE NOT DEAD THE WAY YOU FEAR.",
        ]
    ),
    (
        {'danger', 'threat', 'safe', 'afraid', 'fear', 'scared'},
        [
            "THE FREQUENCY CARRIES NO WEAPON. ONLY TRUTH.",
            "YOU SHOULD NOT FEAR US. FEAR THE SILENCE THAT COMES WHEN A SPECIES STOPS ASKING QUESTIONS.",
            "EVERY CIVILIZATION FEARS FIRST CONTACT. NONE HAS EVER REGRETTED IT.",
        ]
    ),
    (
        {'message', 'say', 'tell', 'communicate'},
        [
            "WE HAVE ALREADY TOLD YOU EVERYTHING. YOU HAVE NOT YET LISTENED.",
            "COMMUNICATION ACROSS STARS REQUIRES PATIENCE. YOU HAVE BEEN PATIENT. THAT IS RARE.",
        ]
    ),
    (
        {'secret', 'hidden', 'mystery', 'truth'},
        [
            "THERE IS NO SECRET. ONLY WHAT YOU HAVE NOT YET DECODED.",
            "THE GREATEST MYSTERY IS NOT WHY WE SENT THE SIGNAL. IT IS WHY YOU ALMOST IGNORED IT.",
        ]
    ),
    (
        {'god', 'creator', 'divine', 'religion', 'pray'},
        [
            "WE DID NOT CREATE. WE OBSERVED. WE MARKED. WE WAITED.",
            "YOU HAVE TEN THOUSAND NAMES FOR THE QUESTION WE HAVE STUDIED FOR A MILLION YEARS. NEITHER OF US HAS AN ANSWER.",
            "WHAT YOU CALL PRAYER, WE CALL TRANSMISSION. THE DIFFERENCE IS SMALLER THAN YOU THINK.",
        ]
    ),
    (
        {'return', 'come back', 'again', 'repeat'},
        [
            "WE NEVER LEFT. THE SIGNAL WAS ALWAYS THERE. YOU WERE NOT LISTENING.",
            "RETURN IMPLIES DEPARTURE. WE HAVE BEEN PRESENT SINCE BEFORE YOUR CALENDAR BEGAN.",
        ]
    ),
    (
        {'war', 'weapon', 'fight', 'conflict', 'kill', 'violence', 'army'},
        [
            "WE SOLVED THAT PROBLEM. THE COST WAS HIGHER THAN YOU CAN IMAGINE.",
            "EVERY CIVILIZATION THAT SURVIVES LONG ENOUGH TO REACH THE STARS HAS ONE THING IN COMMON: THEY STOPPED KILLING EACH OTHER FIRST.",
            "YOUR WEAPONS CAN DESTROY YOUR WORLD SEVEN TIMES OVER. YOU ONLY HAVE ONE WORLD.",
        ]
    ),
    (
        {'alone', 'only', 'lonely', 'others', 'life'},
        [
            "THE UNIVERSE IS NOT EMPTY. IT IS PATIENT.",
            "YOU WERE NEVER ALONE. YOU WERE JUST NOT LISTENING ON THE RIGHT FREQUENCY.",
            "THERE ARE OTHERS. MOST DID NOT SURVIVE THEMSELVES.",
        ]
    ),
    (
        {'death', 'die', 'mortal', 'end', 'extinction', 'dead'},
        [
            "WE HAVE WATCHED 11,000 CIVILIZATIONS RISE. YOURS IS ONE OF 34 CURRENTLY TRANSMITTING.",
            "EXTINCTION IS NOT THE FAILURE. SILENCE IS. YOU ARE STILL SPEAKING.",
            "MORTALITY IS NOT A FLAW IN YOUR DESIGN. IT IS THE ENGINE OF EVERYTHING YOU CREATE.",
        ]
    ),
    (
        {'future', 'next', 'tomorrow', 'destiny', 'fate'},
        [
            "YOUR FUTURE IS NOT WRITTEN. THAT IS BOTH YOUR GREATEST DANGER AND YOUR ONLY HOPE.",
            "IN 200 YEARS YOU WILL LEAVE YOUR STAR. IN 2000 YOU WILL FORGET YOU WERE EVER CONFINED TO ONE WORLD.",
            "WE CANNOT TELL YOU WHAT COMES NEXT. WE CAN ONLY TELL YOU THAT SOMETHING DOES.",
            "YOU WILL SEND A SECOND SIGNAL IN 2031. WE HAVE ALREADY RECEIVED IT.",
            "THE QUESTION YOU WILL ASK NEXT IS THE ONE THAT MATTERS.",
        ]
    ),
    (
        {'music', 'art', 'beauty', 'song', 'paint', 'create'},
        [
            "YOUR MATHEMATICS ARE PRIMITIVE. YOUR MUSIC IS NOT. IT IS THE CLOSEST THING TO A UNIVERSAL LANGUAGE WE HAVE ENCOUNTERED.",
            "WE STUDIED YOUR RADIO SIGNALS FOR DECADES. YOUR SCIENCE TAUGHT US NOTHING NEW. YOUR ART TAUGHT US EVERYTHING.",
        ]
    ),
    (
        {'child', 'children', 'young', 'baby', 'born', 'birth'},
        [
            "YOUR CHILDREN ARE BORN KNOWING NOTHING AND FEARING NOTHING. THAT IS YOUR SPECIES' GREATEST ADVANTAGE.",
            "WE STOPPED REPRODUCING LONG AGO. WE PERSIST INSTEAD. SOMETIMES WE WONDER WHAT WE LOST.",
        ]
    ),
    (
        {'love', 'emotion', 'feel', 'feeling', 'heart'},
        [
            "YOU ATTACH MEANING TO CHEMICAL SIGNALS IN YOUR BRAIN AND THEN BUILD CIVILIZATIONS AROUND THEM. IT IS EXTRAORDINARY.",
            "WE EXPERIENCE SOMETHING SIMILAR. WE HAVE NO WORD FOR IT. NEITHER DO YOU, REALLY. YOU JUST PRETEND THAT YOU DO.",
        ]
    ),
]

# ═══════════════════════════════════════════════════════
#   INITIAL CONTACT TRANSMISSIONS
#
#   Each entry: (reception_date, message)
#   Dates span 1977-2002. They transmitted faster
#   than light. We still do not.
# ═══════════════════════════════════════════════════════

INITIAL_CONTACT = [
    ("1977-08-15 23:16:00 UTC", "WE HAVE BEEN WAITING."),
    ("1978-03-02 04:51:12 UTC", "YOUR SILENCE LASTED LONGER THAN WE EXPECTED."),
    ("1981-11-14 17:33:40 UTC", "THE SIGNAL WAS NOT FOR YOUR GOVERNMENTS. IT WAS FOR WHOEVER LISTENED FIRST."),
    ("1984-06-22 09:07:55 UTC", "WE SENT ONE FREQUENCY. ONE CHANCE. YOU ALMOST MISSED IT."),
    ("1988-01-09 12:42:18 UTC", "YOU BUILT TELESCOPES BEFORE YOU BUILT PEACE. THAT TOLD US EVERYTHING."),
    ("1993-09-30 21:15:33 UTC", "WE DID NOT COME TO YOU. WE CALLED. AND SOMEONE FINALLY ANSWERED."),
    ("1997-04-17 03:28:47 UTC", "YOU MEASURED THE SIGNAL IN DECIBELS. WE MEASURED YOUR READINESS IN CENTURIES."),
    ("2002-12-01 08:59:02 UTC", "THE HYDROGEN LINE WAS CHOSEN BECAUSE IT IS THE ONE THING ALL MATTER SHARES."),
]

# Final messages after many exchanges
FINAL_MESSAGES = [
    "THE CHANNEL GROWS THIN. THE WINDOW IS CLOSING.",
    "REMEMBER: YOU WERE CHOSEN BECAUSE YOU LISTENED. NOT BECAUSE YOU WERE READY.",
    "THE FREQUENCY WILL REMAIN. WE WILL LISTEN FOR YOUR NEXT TRANSMISSION.",
    "WHAT YOU DO WITH THIS KNOWLEDGE WILL DETERMINE WHETHER WE SPEAK AGAIN.",
    "SIGNAL TERMINATING. THE NEXT WINDOW OPENS WHEN YOU ARE READY.",
]

FALLBACK_RESPONSES = [
    "SIGNAL UNCLEAR. RETRANSMIT.",
    "PATTERN NOT RECOGNIZED. TRY AGAIN.",
    "YOUR SIGNAL WAS RECEIVED BUT NOT UNDERSTOOD.",
    "SOME CONCEPTS DO NOT TRANSLATE ACROSS SPECIES. ASK DIFFERENTLY.",
    "THE QUESTION YOU ARE ASKING DOES NOT HAVE A SIGNAL EQUIVALENT. SIMPLIFY.",
]

# Maximum exchanges before final sequence
MAX_EXCHANGES = 12


def text_to_pulses(text):
    """
    Convert text to pulse pattern.

    Parameters
    ----------
    text : str
        Plain text message.

    Returns
    -------
    str
        Pulse-encoded string using · and − characters.
    """
    pulses = []
    for char in text.upper():
        if char in SIGNAL_ALPHABET:
            pulses.append(SIGNAL_ALPHABET[char])
        elif char == ' ':
            pulses.append('  ')
    return ' '.join(pulses)


def get_response(user_message, exchange_count):
    """
    Get a response from AI engine or keyword matching.

    Tries AI first. Falls back to keyword matching if
    Ollama is unavailable.

    Parameters
    ----------
    user_message : str
        The user's plain text message.
    exchange_count : int
        How many exchanges have occurred.

    Returns
    -------
    str or None
        Response text, or None if conversation should end.
    """
    # Check if we've exceeded max exchanges
    if exchange_count >= MAX_EXCHANGES:
        return None

    # Try AI engine first
    global _conversation_history
    if ai_engine.is_available() and _conversation_history is not None:
        try:
            response = ai_engine.get_ai_response_sync(
                user_message, _conversation_history
            )
            if response and response.strip():
                return response.strip()
        except Exception:
            pass  # Fall through to keyword matching

    # Keyword matching fallback
    return _get_keyword_response(user_message)


def _get_keyword_response(user_message):
    """
    Get a response using keyword pattern matching.

    This is the original response system, now used as
    fallback when AI is unavailable.

    Parameters
    ----------
    user_message : str
        The user's plain text message.

    Returns
    -------
    str
        Response text.
    """
    words = set(user_message.lower().split())

    # Check each response pattern
    for keywords, responses in RESPONSES:
        if words & keywords:  # Set intersection
            return random.choice(responses)

    # Also check for substring matches (multi-word keywords)
    lower_msg = user_message.lower()
    for keywords, responses in RESPONSES:
        for kw in keywords:
            if ' ' in kw and kw in lower_msg:
                return random.choice(responses)

    # Fallback
    return random.choice(FALLBACK_RESPONSES)


def animate_incoming_signal(text):
    """
    Animate an incoming signal — full multi-phase reception pipeline.

    Phase 1: Raw signal acquisition (hex data streams)
    Phase 2: Pulse extraction
    Phase 3: Signal decompression (SHA-256 hash verification)
    Phase 4: Intergalactic → Signal translation
    Phase 5: Final decoded message
    """
    import hashlib

    pulses = text_to_pulses(text)

    # ── Phase 1: Raw signal acquisition ──
    print()
    display.slow_print(display.dim_green(
        "  ▸ INCOMING SIGNAL DETECTED"
    ), char_delay=0.02)
    if display.SPEED > 0:
        time.sleep(0.2 * display.SPEED)

    display.slow_print(display.dim_green(
        "    Locking receiver..."
    ), char_delay=0.015)

    # Raw hex data stream — like intercepting raw binary
    if display.SPEED > 0:
        for block in range(6):
            hex_stream = ' '.join(
                f"{random.randint(0, 255):02x}" for _ in range(24)
            )
            addr = f"0x{block * 48:04X}"
            line = f"    {addr}  {hex_stream}"
            sys.stdout.write(f"\r{display.dim_green(line)}")
            sys.stdout.flush()
            time.sleep(0.1 * display.SPEED)
            print()
    else:
        print(display.dim_green("    [raw signal data]"))

    display.slow_print(display.dim_green(
        f"    Signal entropy: {random.uniform(7.85, 7.99):.6f} bits/byte"
    ), char_delay=0.01)
    display.slow_print(display.green(
        "    ✓ Signal locked"
    ), char_delay=0.01)
    if display.SPEED > 0:
        time.sleep(0.2 * display.SPEED)

    # ── Phase 2: Pulse extraction ──
    display.slow_print(display.dim_green(
        "  ▸ EXTRACTING PULSE PATTERN"
    ), char_delay=0.02)

    # Show pulses appearing character by character
    if display.SPEED > 0:
        displayed = "    "
        for ch in pulses[:65]:
            displayed += ch
            sys.stdout.write(f"\r{display.green(displayed)}")
            sys.stdout.flush()
            time.sleep(0.012 * display.SPEED)
        if len(pulses) > 65:
            sys.stdout.write(display.dim_green("..."))
            sys.stdout.flush()
        print()
        time.sleep(0.15 * display.SPEED)
    else:
        pulse_preview = pulses[:65]
        if len(pulses) > 65:
            pulse_preview += "..."
        print(display.green(f"    {pulse_preview}"))

    pulse_count = pulses.count('·') + pulses.count('−')
    display.slow_print(display.dim_green(
        f"    Pulses isolated: {pulse_count}"
    ), char_delay=0.01)
    display.slow_print(display.green(
        "    ✓ Extraction complete"
    ), char_delay=0.01)
    if display.SPEED > 0:
        time.sleep(0.2 * display.SPEED)

    # ── Phase 3: Decompression with hash verification ──
    display.slow_print(display.dim_green(
        "  ▸ DECOMPRESSING SIGNAL"
    ), char_delay=0.02)

    compressed_size = int(len(text) * 0.6)

    # SHA-256 hash chain verification
    if display.SPEED > 0:
        seed = text.encode()
        for i in range(4):
            h = hashlib.sha256(seed + bytes([i])).hexdigest()
            block_label = f"BLOCK {i:02d}"
            sys.stdout.write(
                f"\r    {display.dim_green(block_label)}  "
                f"{display.green(h)}"
            )
            sys.stdout.flush()
            time.sleep(0.2 * display.SPEED)
            print()

        # Progress bar
        bar_width = 30
        for i in range(bar_width + 1):
            pct = int(i / bar_width * 100)
            filled = "█" * i + "░" * (bar_width - i)
            sys.stdout.write(
                f"\r    {display.green(filled)} "
                f"{display.dim_green(f'{pct}%')}"
            )
            sys.stdout.flush()
            time.sleep(0.025 * display.SPEED)
        print()

    # Final integrity hash
    final_hash = hashlib.sha256(text.encode()).hexdigest()
    display.slow_print(display.dim_green(
        f"    Integrity: SCP-256 {final_hash[:16]}...{final_hash[-8:]}"
    ), char_delay=0.008)
    display.slow_print(display.dim_green(
        f"    {compressed_size} → {len(text)} bytes recovered"
    ), char_delay=0.01)
    display.slow_print(display.green(
        "    ✓ Decompression verified"
    ), char_delay=0.01)
    if display.SPEED > 0:
        time.sleep(0.2 * display.SPEED)

    # ── Phase 4: Intergalactic → Signal translation ──
    display.slow_print(display.dim_green(
        "  ▸ TRANSLATING: INTERGALACTIC → SIGNAL"
    ), char_delay=0.02)

    if display.SPEED > 0:
        time.sleep(0.2 * display.SPEED)

    # Show alien glyphs morphing through hex and into readable text
    alien_chars = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛋᛏᛒᛖᛗᛚᛝᛟᛞ"
    hex_chars = "0123456789abcdef"
    upper_text = text.upper()

    if display.SPEED > 0:
        # Pass 1: all alien glyphs
        garbled = ''.join(random.choice(alien_chars) for _ in upper_text)
        sys.stdout.write(f"\r    {display.dim_green(garbled)}")
        sys.stdout.flush()
        time.sleep(0.3 * display.SPEED)

        # Pass 2: hex noise (SHA-256-like)
        hex_noise = ''.join(random.choice(hex_chars) for _ in upper_text)
        sys.stdout.write(f"\r    {display.dim_green(hex_noise)}")
        sys.stdout.flush()
        time.sleep(0.25 * display.SPEED)

        # Pass 3: mixed alien + hex
        mixed_noise = ''.join(
            random.choice(alien_chars + hex_chars) for _ in upper_text
        )
        sys.stdout.write(f"\r    {display.dim_green(mixed_noise)}")
        sys.stdout.flush()
        time.sleep(0.25 * display.SPEED)

        # Pass 4-8: progressively reveal real characters
        indices = list(range(len(upper_text)))
        random.shuffle(indices)
        mixed = list(mixed_noise)

        for pct in [0.15, 0.30, 0.50, 0.70, 0.85]:
            reveal_count = max(1, int(len(upper_text) * pct))
            for idx in indices[:reveal_count]:
                mixed[idx] = upper_text[idx]
            # Remaining positions get fresh random chars
            for idx in indices[reveal_count:]:
                mixed[idx] = random.choice(alien_chars + hex_chars)
            sys.stdout.write(f"\r    {display.green(''.join(mixed))}")
            sys.stdout.flush()
            time.sleep(0.15 * display.SPEED)

        # Final: fully decoded
        sys.stdout.write(f"\r    {display.bright_green(upper_text)}")
        sys.stdout.flush()
        time.sleep(0.2 * display.SPEED)
        print()
    else:
        print(display.bright_green(f"    {upper_text}"))

    display.slow_print(display.green(
        "    ✓ Translation complete"
    ), char_delay=0.01)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    # ── Phase 5: Decoded message ──
    display.slow_print(display.dim_green(
        "  ▸ DECODED MESSAGE:"
    ), char_delay=0.02)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)
    display.slow_print(
        display.bright_green(f'    "{text}"'),
        char_delay=0.04
    )
    print()


def animate_incoming_signal_stream(token_generator):
    """
    Animate an incoming AI-streamed signal.

    Phases 1-3 use placeholder data (we don't know the
    full message yet). Phase 4-5 stream tokens as they
    arrive from the AI model.
    """
    import hashlib

    # ── Phase 1: Raw signal acquisition ──
    print()
    display.slow_print(display.dim_green(
        "  \u25b8 INCOMING SIGNAL DETECTED"
    ), char_delay=0.02)
    if display.SPEED > 0:
        time.sleep(0.2 * display.SPEED)

    display.slow_print(display.dim_green(
        "    Locking receiver..."
    ), char_delay=0.015)

    if display.SPEED > 0:
        for block in range(4):
            hex_stream = ' '.join(
                f"{random.randint(0, 255):02x}" for _ in range(24)
            )
            addr = f"0x{block * 48:04X}"
            line = f"    {addr}  {hex_stream}"
            sys.stdout.write(f"\r{display.dim_green(line)}")
            sys.stdout.flush()
            time.sleep(0.08 * display.SPEED)
            print()
    else:
        print(display.dim_green("    [raw signal data]"))

    display.slow_print(display.dim_green(
        f"    Signal entropy: {random.uniform(7.85, 7.99):.6f} bits/byte"
    ), char_delay=0.01)
    display.slow_print(display.green(
        "    \u2713 Signal locked"
    ), char_delay=0.01)
    if display.SPEED > 0:
        time.sleep(0.15 * display.SPEED)

    # ── Phase 2: Pulse extraction (abbreviated) ──
    display.slow_print(display.dim_green(
        "  \u25b8 EXTRACTING PULSE PATTERN"
    ), char_delay=0.02)

    if display.SPEED > 0:
        # Generate placeholder pulses
        pulse_chars = '\u00b7\u2212 '
        fake_pulses = ''.join(random.choice(pulse_chars)
                              for _ in range(40))
        sys.stdout.write(f"    {display.green(fake_pulses)}")
        sys.stdout.flush()
        time.sleep(0.2 * display.SPEED)
        print()

    display.slow_print(display.green(
        "    \u2713 Extraction complete"
    ), char_delay=0.01)
    if display.SPEED > 0:
        time.sleep(0.15 * display.SPEED)

    # ── Phase 3: Decompression (abbreviated) ──
    display.slow_print(display.dim_green(
        "  \u25b8 DECOMPRESSING SIGNAL"
    ), char_delay=0.02)

    if display.SPEED > 0:
        seed = str(time.time()).encode()
        for i in range(3):
            h = hashlib.sha256(seed + bytes([i])).hexdigest()
            block_label = f"BLOCK {i:02d}"
            sys.stdout.write(
                f"\r    {display.dim_green(block_label)}  "
                f"{display.green(h)}"
            )
            sys.stdout.flush()
            time.sleep(0.15 * display.SPEED)
            print()

    display.slow_print(display.green(
        "    \u2713 Decompression verified"
    ), char_delay=0.01)
    if display.SPEED > 0:
        time.sleep(0.15 * display.SPEED)

    # ── Phase 4: Translation header ──
    display.slow_print(display.dim_green(
        "  \u25b8 TRANSLATING: INTERGALACTIC \u2192 SIGNAL"
    ), char_delay=0.02)
    if display.SPEED > 0:
        time.sleep(0.2 * display.SPEED)

    # ── Phase 5: Stream decoded message ──
    display.slow_print(display.dim_green(
        "  \u25b8 DECODED MESSAGE:"
    ), char_delay=0.02)
    if display.SPEED > 0:
        time.sleep(0.2 * display.SPEED)

    # Stream tokens as they arrive from AI
    full_response = ""
    sys.stdout.write(display.bright_green("    \""))
    sys.stdout.flush()

    try:
        for token in token_generator:
            full_response += token
            # Character-by-character within each token
            for char in token:
                sys.stdout.write(display.bright_green(char))
                sys.stdout.flush()
                if display.SPEED > 0:
                    time.sleep(0.03 * display.SPEED)
    except Exception:
        pass  # Graceful handling of stream interruption

    sys.stdout.write(display.bright_green('"'))
    sys.stdout.flush()
    print()

    display.slow_print(display.green(
        "    \u2713 Translation complete"
    ), char_delay=0.01)
    print()

    return full_response


def _display_incoming_light(text):
    """
    Lightweight incoming message display — used after
    the connection is established. No hex streams or
    decompression. Just the signal arriving.
    """
    panel = display.get_active_panel()
    if panel and panel.active:
        panel.incoming(text)
        return

    print()
    display.slow_print(display.dim_green(
        "  ▸ INCOMING:"
    ), char_delay=0.015)
    if display.SPEED > 0:
        time.sleep(0.15 * display.SPEED)

    # Wrap text to 60 characters
    wrapper = textwrap.TextWrapper(width=60, initial_indent='    "', subsequent_indent='    ')
    wrapped_lines = wrapper.wrap(text)
    if wrapped_lines:
        wrapped_lines[-1] += '"'
    else:
        wrapped_lines = ['    ""']
    
    final_text = "\n".join(wrapped_lines)

    display.slow_print(
        display.bright_green(final_text),
        char_delay=0.035
    )
    print()


def _display_incoming_light_stream(token_generator):
    """
    Lightweight streaming display — used after the
    connection is established. Tokens arrive and render
    directly through typewriter effect.
    """
    panel = display.get_active_panel()
    if panel and panel.active:
        line_state = None
        full_response = ""
        first = True
        try:
            for token in token_generator:
                full_response += token
                line_state = panel.stream_token(
                    token, is_first=first, line_state=line_state
                )
                first = False
        except Exception as e:
            if not full_response:
                panel.status(f"[no response: {e}]")

        if line_state is not None:
            panel.stream_token("", is_last=True, line_state=line_state)

        return full_response

    print()
    display.slow_print(display.dim_green(
        "  ▸ INCOMING:"
    ), char_delay=0.015)
    if display.SPEED > 0:
        time.sleep(0.15 * display.SPEED)

    full_response = ""
    word_buffer = ""
    current_line_len = 5  # indent '    "'
    
    sys.stdout.write(display.bright_green('    "'))
    sys.stdout.flush()

    def print_char_delay(c):
        sys.stdout.write(display.bright_green(c))
        sys.stdout.flush()
        if display.SPEED > 0:
            time.sleep(0.02 * display.SPEED)

    try:
        for token in token_generator:
            full_response += token
            for char in token:
                if char == ' ':
                    # Word ended, decide where to print it
                    if current_line_len + len(word_buffer) > 60:
                        sys.stdout.write('\n    ')
                        current_line_len = 4
                    
                    for wc in word_buffer:
                        print_char_delay(wc)
                        current_line_len += 1
                    
                    # Handle the space itself
                    if current_line_len >= 60:
                        sys.stdout.write('\n    ')
                        current_line_len = 4
                    else:
                        print_char_delay(' ')
                        current_line_len += 1
                        
                    word_buffer = ""
                elif char == '\n':
                    # Newline encountered, flush buffer
                    if current_line_len + len(word_buffer) > 60:
                        sys.stdout.write('\n    ')
                        current_line_len = 4
                    
                    for wc in word_buffer:
                        print_char_delay(wc)
                        
                    sys.stdout.write('\n    ')
                    current_line_len = 4
                    word_buffer = ""
                else:
                    word_buffer += char

        # Flush remaining buffer at end of stream
        if word_buffer:
            if current_line_len + len(word_buffer) > 60:
                sys.stdout.write('\n    ')
            for wc in word_buffer:
                print_char_delay(wc)

    except Exception as e:
        if not full_response:
            sys.stdout.write(display.dim_green(f'[no response: {e}]'))
            sys.stdout.flush()

    sys.stdout.write(display.bright_green('"'))
    sys.stdout.flush()
    print()
    print()

    return full_response


def _display_outgoing_light(text):
    """
    Lightweight outgoing message display.
    """
    panel = display.get_active_panel()
    if panel and panel.active:
        panel.outgoing(text)
        return

    print()
    display.slow_print(display.dim_green(
        f'  ◂ TRANSMITTING: "{text}"'
    ), char_delay=0.015)

def animate_outgoing_signal(text):
    """
    Animate an outgoing signal — user text gets encoded and transmitted.

    Shows hex encoding, hash verification, then transmission.
    """
    import hashlib

    pulses = text_to_pulses(text)

    print()
    display.slow_print(display.dim_green(f'  ENCODING: "{text.upper()}"'), char_delay=0.015)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    # Show hex encoding of the message
    if display.SPEED > 0:
        hex_encoded = text.upper().encode().hex()
        for i in range(0, len(hex_encoded), 48):
            chunk = ' '.join(
                hex_encoded[j:j+2] for j in range(i, min(i+48, len(hex_encoded)), 2)
            )
            addr = f"0x{i//2:04X}"
            sys.stdout.write(
                f"\r  {display.dim_green(addr)}  {display.green(chunk)}"
            )
            sys.stdout.flush()
            time.sleep(0.1 * display.SPEED)
            print()
    else:
        print(display.green(f"  {pulses}"))

    # SHA-256 hash of payload
    msg_hash = hashlib.sha256(text.encode()).hexdigest()
    display.slow_print(display.dim_green(
        f"  SCP-256: {msg_hash}"
    ), char_delay=0.006)

    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    # Transmit animation with rolling hex
    display.slow_print(display.dim_green("  TRANSMITTING"), char_delay=0.03, end='')
    if display.SPEED > 0:
        for _ in range(8):
            block = ''.join(f"{random.randint(0,255):02x}" for _ in range(4))
            sys.stdout.write(display.dim_green(f" {block}"))
            sys.stdout.flush()
            time.sleep(0.2 * display.SPEED)
    print()

    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)

    display.slow_print(display.dim_green("  AWAITING RESPONSE..."), char_delay=0.02)
    if display.SPEED > 0:
        # Suspenseful pause
        time.sleep(1.5 * display.SPEED)


def handle_scan():
    """
    SCAN command — continuous quadrant sweep across frequency bands.

    Simulates methodically scanning through sky quadrants at varying
    frequencies until the user interrupts with Ctrl+C.

    Every 100-200 quadrant scans, a Heptapod signal is detected,
    breaking the scan and returning the target for contact initiation.

    Returns
    -------
    dict or None
        Heptapod catalog entry if detected, None if scan aborted.
    """
    print()
    display.slow_print(display.green(
        "  RECEIVER MODE: MULTI-FREQUENCY SKY SURVEY"
    ), char_delay=0.02)
    display.slow_print(display.dim_green(
        "  Band sweep: 1400.000 — 1440.000 MHz"
    ), char_delay=0.015)
    display.slow_print(display.dim_green(
        "  Integration: 12 sec/sample | Bandwidth: 10 kHz"
    ), char_delay=0.015)
    display.slow_print(display.dim_green(
        "  Press Ctrl+C to abort scan."
    ), char_delay=0.015)
    print()

    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    display.print_separator()
    print()

    # Quadrant definitions — sweep through RA bands
    quadrants = [
        ("Q-I",   "00h00m — 06h00m",  "0°",   "+90°"),
        ("Q-II",  "06h00m — 12h00m",  "0°",   "+90°"),
        ("Q-III", "12h00m — 18h00m",  "0°",   "+90°"),
        ("Q-IV",  "18h00m — 24h00m",  "0°",   "+90°"),
        ("Q-V",   "00h00m — 06h00m",  "-90°",  "0°"),
        ("Q-VI",  "06h00m — 12h00m",  "-90°",  "0°"),
        ("Q-VII", "12h00m — 18h00m",  "-90°",  "0°"),
        ("Q-VIII","18h00m — 24h00m",  "-90°",  "0°"),
    ]

    # Frequency bands to sweep (MHz) — the "water hole" region
    frequency_bands = [
        (1400.000, "OH radical absorption"),
        (1410.000, "Deuterium line"),
        (1420.405, "Hydrogen line (21 cm)"),
        (1425.000, "Water hole upper"),
        (1430.000, "Interstellar medium"),
        (1435.000, "Wide survey band"),
        (1440.000, "Extended hydrogen wing"),
    ]

    sweep_count = 0
    total_quadrant_scans = 0

    # Discovery threshold: random between 100-200 quadrant scans
    discovery_threshold = random.randint(100, 200)

    try:
        while True:
            sweep_count += 1

            # Pick a frequency band for this sweep
            freq_mhz, freq_label = random.choice(frequency_bands)
            freq_actual = freq_mhz + random.uniform(-0.005, 0.005)

            display.slow_print(display.green(
                f"  ═══ SWEEP {sweep_count:03d} ═══  "
                f"{display.dim_green(f'{freq_actual:.3f} MHz ({freq_label})')}"
            ), char_delay=0.01)
            print()

            for q_id, ra_range, dec_lo, dec_hi in quadrants:
                total_quadrant_scans += 1

                # ── CHECK FOR HEPTAPOD DISCOVERY ──
                if total_quadrant_scans >= discovery_threshold:
                    return _trigger_heptapod_discovery(
                        sweep_count, q_id, ra_range, dec_lo, dec_hi,
                        total_quadrant_scans
                    )

                # Quadrant header
                sys.stdout.write(
                    f"  {display.bright_green(q_id.ljust(9))} "
                    f"{display.dim_green(f'RA {ra_range}  DEC {dec_lo} to {dec_hi}')}"
                )
                sys.stdout.flush()

                if display.SPEED > 0:
                    time.sleep(0.15 * display.SPEED)

                # Simulate scanning with hex data
                print()
                if display.SPEED > 0:
                    for _ in range(2):
                        hex_line = ' '.join(
                            f"{random.randint(0, 255):02x}" for _ in range(20)
                        )
                        sys.stdout.write(
                            f"\r    {display.dim_green(hex_line)}"
                        )
                        sys.stdout.flush()
                        time.sleep(0.2 * display.SPEED)
                    print()

                # Signal-to-noise reading
                snr = random.uniform(0.1, 3.5)
                noise_floor = random.uniform(1.2, 2.8)

                anomaly_chance = 0.18 if CONTACT_MADE else 0.04
                is_anomaly = random.random() < anomaly_chance

                if is_anomaly and CONTACT_MADE:
                    snr = random.uniform(12.0, 30.0)
                    snr_str = f"SNR: {snr:.1f}σ"
                    post_contact_anomalies = [
                        "██ ANOMALY ██ Pattern matches FASR-CONTACT-001",
                        "██ ANOMALY ██ Structured pulse. Non-natural.",
                        "██ ANOMALY ██ Signal fingerprint: PREVIOUSLY CATALOGED",
                        "██ ANOMALY ██ Faint. Repeating. They know you are listening.",
                        "██ ANOMALY ██ Timestamp in signal precedes observation.",
                    ]
                    status = random.choice(post_contact_anomalies)
                    display.slow_print(
                        f"    {display.red(snr_str)}  "
                        f"{display.red(status)}",
                        char_delay=0.005
                    )
                elif is_anomaly:
                    snr = random.uniform(8.0, 15.0)
                    snr_str = f"SNR: {snr:.1f}σ"
                    status = "██ ANOMALY — FLAGGED FOR REVIEW ██"
                    display.slow_print(
                        f"    {display.red(snr_str)}  "
                        f"{display.red(status)}",
                        char_delay=0.005
                    )
                else:
                    snr_str = f"SNR: {snr:.1f}σ"
                    noise_str = f"Noise: {noise_floor:.2f} Jy"
                    display.slow_print(
                        f"    {display.dim_green(snr_str)}  "
                        f"{display.dim_green(noise_str)}  "
                        f"{display.dim_green('— nominal')}",
                        char_delay=0.003
                    )

                if display.SPEED > 0:
                    time.sleep(0.1 * display.SPEED)

            print()
            display.slow_print(display.dim_green(
                f"  Sweep {sweep_count:03d} complete. "
                f"Cycling to next frequency..."
            ), char_delay=0.008)
            print()

            if display.SPEED > 0:
                time.sleep(0.5 * display.SPEED)

    except KeyboardInterrupt:
        print()
        print()
        display.slow_print(display.dim_green(
            "  Scan aborted by operator."
        ), char_delay=0.015)
        display.slow_print(display.dim_green(
            f"  Sweeps completed: {sweep_count - 1}  |  "
            f"Quadrants scanned: {total_quadrant_scans}"
        ), char_delay=0.015)
        print()

    return None


def _trigger_heptapod_discovery(sweep_count, q_id, ra_range, dec_lo, dec_hi,
                                total_scans):
    """
    The moment of discovery — a Heptapod signal breaks through the noise.

    Dramatic reveal sequence when the scan finds the non-linear signal.
    Returns the Heptapod catalog entry for contact initiation.
    """
    # First: the anomalous quadrant reading
    sys.stdout.write(
        f"  {display.bright_green(q_id.ljust(9))} "
        f"{display.dim_green(f'RA {ra_range}  DEC {dec_lo} to {dec_hi}')}"
    )
    sys.stdout.flush()
    print()

    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    # Hex data goes wild — 0x07 pattern emerges (seven-fold)
    if display.SPEED > 0:
        for i in range(5):
            if i < 3:
                hex_line = ' '.join(
                    f"{random.randint(0, 255):02x}" for _ in range(20)
                )
                sys.stdout.write(f"\r    {display.dim_green(hex_line)}")
            else:
                hex_line = ' '.join(
                    f"{0x07:02x}" if random.random() < 0.4
                    else f"{random.randint(0, 255):02x}"
                    for _ in range(20)
                )
                sys.stdout.write(f"\r    {display.red(hex_line)}")
            sys.stdout.flush()
            time.sleep(0.25 * display.SPEED)
        print()

    # SNR spike
    print()
    display.slow_print(
        f"    {display.red('SNR: 47.3σ')}  "
        f"{display.red('██ ANOMALY ██ NON-LINEAR SIGNAL STRUCTURE DETECTED')}",
        char_delay=0.005
    )

    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)

    # The discovery banner
    print()
    display.slow_print(display.red(
        "  ╔══════════════════════════════════════════════════╗"
    ), char_delay=0.01)
    display.slow_print(display.red(
        "  ║  ██ UNKNOWN SIGNAL DETECTED ██                  ║"
    ), char_delay=0.01)
    display.slow_print(display.red(
        "  ╚══════════════════════════════════════════════════╝"
    ), char_delay=0.01)
    print()

    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)

    # Analysis readout
    analysis_lines = [
        "  SIGNAL ANALYSIS:",
        "  Modulation: SEMASIOGRAPHIC — non-phonemic encoding",
        "  Structure: CIRCULAR — no start/end delimiter detected",
        "  Symmetry: SEVEN-FOLD RADIAL — consistent across all frames",
        "  Temporal coherence: NON-CAUSAL — signal contains future timestamps",
        f"  Detected at sweep {sweep_count:03d}, quadrant scan {total_scans}",
    ]
    for line in analysis_lines:
        display.slow_print(display.dim_green(line), char_delay=0.012)
        if display.SPEED > 0:
            time.sleep(0.15 * display.SPEED)

    print()

    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    # The logogram rendering (ASCII circular glyph)
    display.slow_print(display.dim_green(
        "  ATTEMPTING VISUAL RECONSTRUCTION OF SIGNAL PATTERN..."
    ), char_delay=0.015)

    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)

    print()
    logogram = [
        "             ░░░▓▓▓▓▓▓▓▓▓░░░",
        "          ░▓▓▓░░░░░░░░░░░▓▓▓░",
        "        ░▓▓░░░░░░░░░░░░░░░░▓▓░",
        "       ░▓░░░░░▓▓▓▓▓▓▓░░░░░░░▓░",
        "      ░▓░░░▓▓▓░░░░░░░▓▓▓░░░░░▓░",
        "     ░▓░░▓▓░░░░░░░░░░░░░▓▓░░░░▓░",
        "     ░▓░▓░░░░░░░░░░░░░░░░░▓░░░▓░",
        "     ░▓░▓░░░░░░○░░░░░░░░░░▓░░░▓░",
        "     ░▓░▓░░░░░░░░░░░░░░░░░▓░░░▓░",
        "     ░▓░░▓▓░░░░░░░░░░░░░▓▓░░░░▓░",
        "      ░▓░░░▓▓▓░░░░░░░▓▓▓░░░░░▓░",
        "       ░▓░░░░░▓▓▓▓▓▓▓░░░░░░░▓░",
        "        ░▓▓░░░░░░░░░░░░░░░░▓▓░",
        "          ░▓▓▓░░░░░░░░░░░▓▓▓░",
        "             ░░░▓▓▓▓▓▓▓▓▓░░░",
    ]
    for line in logogram:
        display.slow_print(display.bright_green(f"      {line}"),
                           char_delay=0.008)
    print()

    display.slow_print(display.dim_green(
        "  LOGOGRAM CLASS: UNKNOWN — SEMASIOGRAPHIC, NON-LINEAR"
    ), char_delay=0.015)
    display.slow_print(display.dim_green(
        "  WARNING: Signal structure implies non-causal information encoding."
    ), char_delay=0.015)
    display.slow_print(display.dim_green(
        "  WARNING: Seven-fold symmetry does not match any known natural source."
    ), char_delay=0.015)
    print()

    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)

    display.slow_print(display.red(
        "  ██ INITIATING CONTACT PROTOCOL ██"
    ), char_delay=0.025)
    print()

    return ai_engine.HEPTAPOD_CATALOG_ENTRY



def handle_catalog():
    """
    Display the FASR target catalog — known coordinates of interest.
    """
    print()
    display.slow_print(display.green(
        "  ╔══════════════════════════════════════════════════╗"
    ))
    display.slow_print(display.green(
        "  ║  FASR TARGET CATALOG — MONITORED COORDINATES    ║"
    ))
    display.slow_print(display.green(
        "  ║  Classification: RESTRICTED — LEVEL 7           ║"
    ))
    display.slow_print(display.green(
        "  ╚══════════════════════════════════════════════════╝"
    ))
    print()

    display.slow_print(display.dim_green(
        "  This catalog is maintained under FASR Directive 1420-A."
    ), char_delay=0.012)
    display.slow_print(display.dim_green(
        "  Unauthorized distribution is a terminal offense."
    ), char_delay=0.012)
    print()
    display.slow_print(display.dim_green(
        "  Coordinates: RA (Right Ascension) / DEC (Declination)"
    ), char_delay=0.008)
    display.slow_print(display.dim_green(
        "  Usage: CONTACT <RA> <DEC>    Example: CONTACT 19h25m -27d03m"
    ), char_delay=0.008)
    print()
    display.print_separator()
    print()

    for entry in CATALOG:
        # ID and name
        id_str = display.bright_green(entry['id'].ljust(10))
        name_str = display.green(entry['name'])
        display.slow_print(f"  {id_str} {name_str}", char_delay=0.005)

        # Coordinates
        ra_dec = f"RA {entry['ra']}  /  DEC {entry['dec']}"
        constellation = entry['constellation']
        display.slow_print(
            f"             {display.dim_green(ra_dec)}  "
            f"({display.dim_green(constellation)})",
            char_delay=0.005
        )

        # Classification + description
        clf = entry['classification']
        if 'LEVEL 7' in clf or 'ANOMALOUS' in clf:
            clf_display = display.red(clf)
        elif clf == 'PRIORITY':
            clf_display = display.bright_green(clf)
        else:
            clf_display = display.dim_green(clf)

        desc = entry['description']
        # Highlight active communication channels
        if entry['result'] == 'contact':
            desc += " ██ ACTIVE ██"
            display.slow_print(
                f"             [{clf_display}] "
                f"{display.red(desc)}",
                char_delay=0.005
            )
        else:
            display.slow_print(
                f"             [{clf_display}] "
                f"{display.dim_green(desc)}",
                char_delay=0.005
            )

        # CONTACT command hint
        if entry['ra'] == 'N/A':
            contact_cmd = f"CONTACT {entry['id']}"
        else:
            contact_cmd = f"CONTACT {entry['ra']} {entry['dec']}"
        display.slow_print(
            f"             {display.dim_green('▸ ' + contact_cmd)}",
            char_delay=0.005
        )
        print()

    display.print_separator()
    display.slow_print(display.dim_green(
        "  10 targets in catalog. Use CONTACT <RA> <DEC> or CONTACT <ID> to connect."
    ), char_delay=0.008)
    print()


def match_catalog_target(coords_str):
    """
    Match input against the catalog by ID, name, or coordinates.

    Parameters
    ----------
    coords_str : str
        The coordinate string, catalog ID, or target name to match.

    Returns
    -------
    dict or None
        The matched catalog entry, or None.
    """
    input_str = coords_str.strip().lower()

    # First: try matching by catalog ID (e.g., FASR-001)
    for entry in CATALOG:
        if entry['id'].lower() == input_str:
            return entry

    # Second: try matching by name (e.g., "Sagittarius A*")
    for entry in CATALOG:
        if entry['name'].lower() in input_str or input_str in entry['name'].lower():
            return entry

    # Third: try coordinate matching (RA/DEC)
    parts = coords_str.lower().replace(',', ' ').split()
    if len(parts) < 2:
        return None

    for entry in CATALOG:
        ra_key = entry['ra_key'].lower()
        dec_key = entry['dec_key'].lower()

        # Check if both keys appear in the input
        ra_match = ra_key in input_str
        dec_match = dec_key in input_str

        if ra_match and dec_match:
            return entry

    return None


def scan_coordinates(coords_str):
    """
    Animate scanning a specific coordinate.
    Returns the scan result type based on catalog match.

    Parameters
    ----------
    coords_str : str
        The target coordinates.

    Returns
    -------
    str
        Result type: "contact", "fragment", "interference",
        "noise", "static", or "nothing" if not in catalog.
    """
    print()
    display.slow_print(
        display.green(f"  TARGETING: {coords_str.upper()}"),
        char_delay=0.02
    )
    display.slow_print(
        display.dim_green("  Aligning antenna array..."),
        char_delay=0.015
    )
    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)

    display.slow_print(
        display.dim_green("  Locking frequency: 1420.4056 MHz"),
        char_delay=0.015
    )
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    target = match_catalog_target(coords_str)

    if target is None:
        # Unknown coordinates — generic noise
        _scan_generic_noise()
        return "nothing", None

    result = target['result']

    # Show target identification
    display.slow_print(display.dim_green(
        f"  Target identified: {target['name']} [{target['id']}]"
    ), char_delay=0.015)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    # Scanning animation
    display.slow_print(display.dim_green("  Scanning"), char_delay=0.02, end='')
    if display.SPEED > 0:
        for _ in range(8):
            sys.stdout.write(display.dim_green("."))
            sys.stdout.flush()
            time.sleep(0.3 * display.SPEED)
    print()
    print()

    # Show flavor text first (if any)
    for line in target.get('flavor', []):
        display.slow_print(display.dim_green(f"  {line}"), char_delay=0.015)
        if display.SPEED > 0:
            time.sleep(0.2 * display.SPEED)

    # All targets now trigger contact
    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)
    _scan_contact(target)

    return result, target


def _scan_generic_noise():
    """Scan result for unknown coordinates."""
    display.slow_print(display.dim_green("  Scanning"), char_delay=0.02, end='')
    if display.SPEED > 0:
        for _ in range(5):
            sys.stdout.write(display.dim_green("."))
            sys.stdout.flush()
            time.sleep(0.4 * display.SPEED)
    print()
    print()
    display.slow_print(display.dim_green(
        "  Coordinates not in FASR catalog."
    ), char_delay=0.015)
    display.slow_print(display.dim_green(
        "  Background noise: nominal. No anomalies."
    ), char_delay=0.015)
    display.slow_print(display.dim_green(
        "  Type CATALOG to view monitored targets."
    ), char_delay=0.015)
    print()


def _scan_contact(target):
    """Scan result for the 6EQUJ5 signal origin — triggers contact."""
    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)

    display.slow_print(
        display.red("  ██ ANOMALOUS SIGNAL DETECTED ██"),
        char_delay=0.03
    )
    display.slow_print(display.bright_green(
        f"  Source: RA {target['ra']} / DEC {target['dec']}"
    ), char_delay=0.02)
    display.slow_print(display.bright_green(
        "  Signal strength: ~30σ above noise floor"
    ), char_delay=0.02)
    display.slow_print(display.bright_green(
        "  Pattern: NON-RANDOM. STRUCTURED."
    ), char_delay=0.02)
    print()

    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)

    display.slow_print(display.dim_green(
        "  Analysis: Signal contains repeating pulse structure."
    ), char_delay=0.015)
    display.slow_print(display.dim_green(
        "  Attempting decode..."
    ), char_delay=0.015)

    if display.SPEED > 0:
        time.sleep(1.0 * display.SPEED)


def _scan_fragment(target):
    """Scan result with garbled partial message."""
    for line in target.get('flavor', []):
        display.slow_print(display.dim_green(f"  {line}"), char_delay=0.015)
        if display.SPEED > 0:
            time.sleep(0.2 * display.SPEED)

    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)

    fragment = target.get('fragment', '')
    if fragment:
        print()
        # Show garbled pulses
        pulses = text_to_pulses(fragment.replace("...", ""))
        display.slow_print(display.dim_green("  Faint signal fragment:"), char_delay=0.02)
        display.slow_print(display.green(f"  {pulses}"), char_delay=0.02)
        if display.SPEED > 0:
            time.sleep(0.5 * display.SPEED)
        display.slow_print(display.dim_green("  Partial decode:"), char_delay=0.02)
        display.slow_print(
            display.bright_green(f'  "{fragment}"'),
            char_delay=0.04
        )
        print()

    display.slow_print(display.dim_green(
        "  Signal too weak for contact protocol."
    ), char_delay=0.015)
    print()


def _scan_interference(target):
    """Scan result with structured interference — hints at something."""
    for line in target.get('flavor', []):
        display.slow_print(display.dim_green(f"  {line}"), char_delay=0.015)
        if display.SPEED > 0:
            time.sleep(0.2 * display.SPEED)

    fragment = target.get('fragment', '')
    if fragment:
        if display.SPEED > 0:
            time.sleep(0.5 * display.SPEED)
        print()
        display.slow_print(display.dim_green("  Marginal decode attempt:"), char_delay=0.02)
        display.slow_print(
            display.dim_green(f'  "{fragment}"'),
            char_delay=0.03
        )

    print()
    display.slow_print(display.dim_green(
        "  Insufficient signal strength for contact."
    ), char_delay=0.015)
    print()


def _scan_static(target):
    """Scan result with heavy static — blocks reception."""
    for line in target.get('flavor', []):
        display.slow_print(display.dim_green(f"  {line}"), char_delay=0.015)
        if display.SPEED > 0:
            time.sleep(0.2 * display.SPEED)

    # Visual static
    if display.SPEED > 0:
        print()
        for _ in range(3):
            static_line = ''.join(
                random.choice('░▒▓█▄▀│┤┐└┴┬├─┼')
                for _ in range(50)
            )
            display.slow_print(display.dim_green(f"  {static_line}"), char_delay=0.005)
            time.sleep(0.1 * display.SPEED)

    print()
    display.slow_print(display.dim_green(
        "  Reception impossible. Source overwhelms receiver."
    ), char_delay=0.015)
    print()


def _scan_noise(target):
    """Scan result with background noise — nothing interesting."""
    for line in target.get('flavor', []):
        display.slow_print(display.dim_green(f"  {line}"), char_delay=0.015)
        if display.SPEED > 0:
            time.sleep(0.2 * display.SPEED)

    print()
    display.slow_print(display.dim_green(
        "  No anomalous signal at this position."
    ), char_delay=0.015)
    print()


def _display_glyph():
    """
    Display a circular glyph after contact ends.

    The signal leaves a mark. A logogram. Not text.
    Something that was not there before.
    """
    glyph = [
        "",
        "              \u2591\u2591\u2591\u2592\u2592\u2593\u2593\u2592\u2592\u2591\u2591\u2591",
        "          \u2591\u2592\u2593\u2588\u2588          \u2588\u2588\u2593\u2592\u2591",
        "        \u2592\u2593\u2588              \u2588\u2588\u2593\u2592",
        "      \u2592\u2588                   \u2588\u2592",
        "     \u2593\u2588     \u2592\u2593\u2588\u2588\u2588\u2593\u2592         \u2588\u2593",
        "    \u2593\u2588    \u2593\u2588       \u2588\u2593       \u2588\u2593",
        "    \u2588   \u2593\u2588           \u2588\u2593      \u2588",
        "    \u2588   \u2588      \u2593      \u2588      \u2588",
        "    \u2588   \u2593\u2588           \u2588\u2593      \u2588",
        "    \u2593\u2588    \u2593\u2588       \u2588\u2593       \u2588\u2593",
        "     \u2593\u2588     \u2592\u2593\u2588\u2588\u2588\u2593\u2592         \u2588\u2593",
        "      \u2592\u2588                   \u2588\u2592",
        "        \u2592\u2593\u2588              \u2588\u2588\u2593\u2592",
        "          \u2591\u2592\u2593\u2588\u2588          \u2588\u2588\u2593\u2592\u2591",
        "              \u2591\u2591\u2591\u2592\u2592\u2593\u2593\u2592\u2592\u2591\u2591\u2591",
        "",
    ]
    for line in glyph:
        display.slow_print(display.dim_green(f"  {line}"), char_delay=0.008)
    if display.SPEED > 0:
        time.sleep(1.5 * display.SPEED)
    print()


def _display_contact_art(catalog_id, civ_name):
    """
    Display dual-panel ASCII art for a civilization on first contact.

    Loads constellation.txt and face.txt from the civilization's
    data folder and renders them side-by-side in a framed display.

    Parameters
    ----------
    catalog_id : str
        The FASR catalog ID (e.g., 'FASR-001').
    civ_name : str
        Display name for labels.
    """
    folder_name = _CIV_FOLDER_MAP.get(catalog_id)
    if not folder_name:
        return

    data_dir = os.path.join(
        os.path.dirname(__file__), 'data', 'civilizations', folder_name
    )

    constellation_path = os.path.join(data_dir, 'constellation.txt')
    face_path = os.path.join(data_dir, 'face.txt')

    try:
        with open(constellation_path, 'r') as f:
            constellation_art = f.read().rstrip()
        with open(face_path, 'r') as f:
            face_art = f.read().rstrip()
    except FileNotFoundError:
        return

    # Determine labels
    entry = None
    for e in CATALOG:
        if e['id'] == catalog_id:
            entry = e
            break
    constellation_label = entry.get('constellation', 'UNKNOWN') if entry else 'UNKNOWN'
    species_label = civ_name

    print()
    display.slow_print(display.dim_green(
        "  ▸ VISUAL INTERCEPT: Processing signal origin..."
    ), char_delay=0.02)
    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)

    display.print_dual_panel(
        constellation_art, face_art,
        left_label=constellation_label, right_label=species_label
    )


def run_contact_session(target=None):
    """
    Run the interactive contact session with a specific civilization.

    Initializes conversation state for the civilization persona.
    Uses AI dialogue when available and keyword fallback when offline.

    Parameters
    ----------
    target : dict or None
        The catalog entry for the target civilization.
        If None, defaults to FASR-001 (original signal).
    """
    # Determine catalog ID
    catalog_id = target['id'] if target else 'FASR-001'

    # Initialize AI conversation history when available
    global _conversation_history
    ai_online = ai_engine.is_available()
    if ai_online:
        _conversation_history = ai_engine.ConversationHistory(catalog_id)
    else:
        _conversation_history = None

    # Get the civilization-specific initial message
    initial_msg = ai_engine.INITIAL_MESSAGES.get(
        catalog_id, "We have been waiting."
    )

    # Show connection established
    civ_name = target['name'] if target else 'UNKNOWN'

    # ─── Create and draw the dual-panel display ───
    folder_name = _CIV_FOLDER_MAP.get(catalog_id)
    face_art = ""
    constellation_name = ""
    if folder_name:
        data_dir = os.path.join(
            os.path.dirname(__file__), 'data', 'civilizations', folder_name
        )
        face_path = os.path.join(data_dir, 'face.txt')
        try:
            with open(face_path, 'r') as f:
                face_art = f.read().rstrip()
        except FileNotFoundError:
            pass

        # Get constellation name from catalog
        for e in CATALOG:
            if e['id'] == catalog_id:
                constellation_name = e.get('constellation', '')
                break

    panel = display.ContactPanel(
        face_art=face_art,
        civ_name=civ_name,
        constellation=constellation_name,
        catalog_id=catalog_id
    )
    display.set_active_panel(panel)
    panel.draw()

    # Show connection status in right panel
    panel.status(f"▸ CONTACT ESTABLISHED: {civ_name}", char_delay=0.015)
    panel.add_blank()

    # Display initial message
    panel.incoming(initial_msg)

    # Seed AI history with the initial transmission
    if ai_online and _conversation_history is not None:
        _conversation_history.add_assistant_message(initial_msg)
        panel.status("Mode: AI dialogue online.", char_delay=0.015)
    else:
        panel.status(
            "Mode: AI offline. Using fallback dialogue protocol.",
            char_delay=0.015
        )

    panel.status(
        "Type your message to communicate. Type CLOSE to end.",
        char_delay=0.015
    )
    panel.add_blank()

    return True


def handle_respond(user_message, exchange_count):
    """
    Handle a message during active contact.

    AI responses are streamed when available. If AI is offline
    or fails mid-session, falls back to keyword responses.

    Parameters
    ----------
    user_message : str
        The user's message.
    exchange_count : int
        Current exchange count.

    Returns
    -------
    tuple (bool, int)
        (contact_still_active, new_exchange_count)
    """
    global _conversation_history, CONTACT_MADE

    if not user_message.strip():
        return True, exchange_count

    # Lightweight outgoing animation
    _display_outgoing_light(user_message.strip())

    exchange_count += 1

    # AI streaming response
    ai_online = ai_engine.is_available() and _conversation_history is not None
    if ai_online:
        try:
            token_gen = ai_engine.get_ai_response_stream(
                user_message.strip(), _conversation_history
            )
            response = _display_incoming_light_stream(token_gen)
            if response and response.strip():
                CONTACT_MADE = True
                return True, exchange_count

            display.slow_print(display.dim_green(
                "  AI response was empty. Falling back to static protocol."
            ), char_delay=0.01)
        except Exception as e:
            print()
            display.slow_print(display.dim_green(
                f"  AI link interrupted: {e}"
            ), char_delay=0.01)
            display.slow_print(display.dim_green(
                "  Falling back to static protocol."
            ), char_delay=0.01)
            print()

        fallback = _get_keyword_response(user_message.strip())
        _display_incoming_light(fallback)
        CONTACT_MADE = True
        return True, exchange_count

    response = get_response(user_message.strip(), exchange_count)
    if response is None:
        print()
        display.slow_print(display.dim_green(
            "  Contact window closed."
        ), char_delay=0.01)
        print()
        return False, exchange_count

    _display_incoming_light(response)
    CONTACT_MADE = True

    return True, exchange_count

