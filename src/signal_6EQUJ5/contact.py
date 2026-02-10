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

import sys
import time
import random

from . import display
from . import codec

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
#   Example: LISTEN 19h25m -27d03m
# ═══════════════════════════════════════════════════════

# Scan result types:
#   "contact"      → triggers the full conversation
#   "fragment"     → garbled/cryptic partial messages
#   "interference" → structured interference, hints at something
#   "noise"        → background noise, nothing interesting
#   "static"       → heavy static, blocks reception

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
        "result": "static",
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
        "result": "interference",
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
        "result": "noise",
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
        "result": "interference",
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
        "result": "noise",
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
        "result": "noise",
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
        "result": "fragment",
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
        "result": "interference",
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
        "result": "fragment",
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
        ]
    ),
    (
        {'why', 'purpose', 'reason'},
        [
            "TO KNOW WHEN YOU WERE READY TO LISTEN.",
            "BECAUSE EVERY CIVILIZATION REACHES A POINT WHERE IT MUST CHOOSE: TURN INWARD OR REACH OUTWARD. WE WANTED TO KNOW YOUR CHOICE.",
            "NOT EVERY SPECIES ASKS WHY. THAT YOU DID IS THE ANSWER.",
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
    Get a response based on keyword matching.

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
    SCAN command — continuous quadrant sweep of the hydrogen line band.

    Simulates methodically scanning through sky quadrants until
    the user interrupts with Ctrl+C.
    """
    print()
    display.slow_print(display.green(
        "  RECEIVER MODE: FULL SKY SURVEY"
    ), char_delay=0.02)
    display.slow_print(display.dim_green(
        "  Frequency lock: 1420.4056 MHz (hydrogen line)"
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

    sweep_count = 0

    try:
        while True:
            sweep_count += 1
            display.slow_print(display.green(
                f"  ═══ SWEEP {sweep_count:03d} ═══"
            ), char_delay=0.01)
            print()

            for q_id, ra_range, dec_lo, dec_hi in quadrants:
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
                    # Rolling hex data stream for each quadrant
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

                # Occasional anomaly flag (rare)
                is_anomaly = random.random() < 0.04

                if is_anomaly:
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
                f"Cycling to next pass..."
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
            f"  Sweeps completed: {sweep_count - 1}"
        ), char_delay=0.015)
        print()


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
        "  Usage: LISTEN <RA> <DEC>    Example: LISTEN 19h25m -27d03m"
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

        # LISTEN command hint
        listen_cmd = f"LISTEN {entry['ra']} {entry['dec']}"
        display.slow_print(
            f"             {display.dim_green('▸ ' + listen_cmd)}",
            char_delay=0.005
        )
        print()

    display.print_separator()
    display.slow_print(display.dim_green(
        "  10 targets in catalog. Use LISTEN <RA> <DEC> to scan."
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
        return "nothing"

    result = target['result']

    # Show target identification
    display.slow_print(display.dim_green(
        f"  Target identified: {target['name']} [{target['id']}]"
    ), char_delay=0.015)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    # Scanning animation
    display.slow_print(display.dim_green("  Scanning"), char_delay=0.02, end='')
    scan_dots = 8 if result == "contact" else 6
    if display.SPEED > 0:
        for _ in range(scan_dots):
            sys.stdout.write(display.dim_green("."))
            sys.stdout.flush()
            time.sleep(0.3 * display.SPEED)
    print()
    print()

    if result == "contact":
        _scan_contact(target)
    elif result == "fragment":
        _scan_fragment(target)
    elif result == "interference":
        _scan_interference(target)
    elif result == "static":
        _scan_static(target)
    elif result == "noise":
        _scan_noise(target)

    return result


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


def run_contact_session():
    """
    Run the interactive contact session.

    This is the conversation loop -- the user can RESPOND
    and receive responses from the signal source.
    """
    exchange_count = 0

    # Select a random initial transmission (with date)
    reception_date, initial_msg = random.choice(INITIAL_CONTACT)

    # Show reception metadata
    display.slow_print(display.dim_green(
        f"  RECEPTION TIMESTAMP: {reception_date}"
    ), char_delay=0.015)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    animate_incoming_signal(initial_msg)


    display.slow_print(display.dim_green(
        "  Type SEND to start communication."
    ), char_delay=0.015)
    print()

    return True  # Signal that contact mode is active


def handle_respond(user_message, exchange_count):
    """
    Handle a RESPOND command during active contact.

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
    if not user_message.strip():
        display.slow_print(display.dim_green(
            "  USAGE: SEND <your message>"
        ), char_delay=0.01)
        return True, exchange_count

    # Animate outgoing
    animate_outgoing_signal(user_message.strip())

    exchange_count += 1

    # Get response
    response = get_response(user_message, exchange_count)

    if response is None:
        # Final sequence — conversation ending
        for msg in FINAL_MESSAGES:
            animate_incoming_signal(msg)
            if display.SPEED > 0:
                time.sleep(0.5 * display.SPEED)

        print()
        display.slow_print(display.red(
            "  ██ SIGNAL LOST ██"
        ), char_delay=0.04)
        display.slow_print(display.dim_green(
            "  Contact window closed."
        ), char_delay=0.02)
        display.slow_print(display.dim_green(
            "  Session archived: FASR-CONTACT-001"
        ), char_delay=0.02)
        print()
        return False, exchange_count

    # Animate the response
    animate_incoming_signal(response)

    # Warn as we approach the limit
    remaining = MAX_EXCHANGES - exchange_count
    if remaining == 3:
        display.slow_print(display.dim_green(
            "  [SIGNAL DEGRADING — INTERFERENCE INCREASING]"
        ), char_delay=0.02)
        print()
    elif remaining == 1:
        display.slow_print(display.red(
            "  [WARNING: SIGNAL CRITICALLY WEAK]"
        ), char_delay=0.02)
        print()

    return True, exchange_count


# ═══════════════════════════════════════════════════════
#   SEND — interstellar message transmission
#
#   Distance to Chi Sagittarii: ~120 light-years
#   Speed of transmission: c (speed of light)
#   Estimated delivery: ~120 years from now
# ═══════════════════════════════════════════════════════

LIGHT_YEARS_TO_TARGET = 120
TARGET_DESIGNATION = "FASR-001 — Chi Sagittarii / 6EQUJ5 Signal Origin"
TRANSMISSION_FREQ = "1420.4056 MHz"


def handle_send():
    """
    SEND command — compose and transmit an interstellar message.

    Prompts user for a short message, then simulates:
    1. Message validation
    2. ASCII → binary conversion
    3. Signal compression
    4. Pulse encoding
    5. Power calibration
    6. Transmission with progress bar
    7. Delivery ETA based on light-speed travel to Chi Sagittarii
    """
    from datetime import datetime, timedelta

    print()
    display.slow_print(display.green(
        "  ╔══════════════════════════════════════════════════╗"
    ))
    display.slow_print(display.green(
        "  ║  INTERSTELLAR TRANSMISSION PROTOCOL             ║"
    ))
    display.slow_print(display.green(
        "  ║  Target: FASR-001 — 6EQUJ5 Signal Origin        ║"
    ))
    display.slow_print(display.green(
        "  ║  Frequency: 1420.4056 MHz (hydrogen line)       ║"
    ))
    display.slow_print(display.green(
        "  ╚══════════════════════════════════════════════════╝"
    ))
    print()

    display.slow_print(display.dim_green(
        "  Bandwidth is limited. Keep your message short."
    ), char_delay=0.015)
    display.slow_print(display.dim_green(
        "  Maximum: 64 characters. Every byte costs energy."
    ), char_delay=0.015)
    print()

    # Prompt for message
    display.slow_print(display.bright_green(
        "  COMPOSE YOUR MESSAGE:"
    ), char_delay=0.02)

    try:
        sys.stdout.write(display.green("  > "))
        sys.stdout.flush()
        message = input().strip()
    except (EOFError, KeyboardInterrupt):
        print()
        display.slow_print(display.dim_green(
            "  Transmission cancelled."
        ), char_delay=0.02)
        print()
        return

    if not message:
        display.slow_print(display.dim_green(
            "  No message provided. Transmission aborted."
        ), char_delay=0.02)
        print()
        return

    # Truncate if too long
    if len(message) > 64:
        message = message[:64]
        display.slow_print(display.dim_green(
            "  Message truncated to 64 characters."
        ), char_delay=0.015)

    print()

    # ── Phase 1: Message validation ──
    display.slow_print(display.dim_green(
        "  PHASE 1: MESSAGE VALIDATION"
    ), char_delay=0.02)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    char_count = len(message)
    word_count = len(message.split())
    display.slow_print(display.dim_green(
        f"  Characters: {char_count} | Words: {word_count} | "
        f"Encoding: UTF-8"
    ), char_delay=0.01)
    display.slow_print(display.green(
        "  ✓ Message validated"
    ), char_delay=0.01)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)
    print()

    # ── Phase 2: ASCII → Binary ──
    display.slow_print(display.dim_green(
        "  PHASE 2: ASCII → BINARY CONVERSION"
    ), char_delay=0.02)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    # Show binary for first few characters
    binary_bits = 0
    binary_preview = ""
    for i, ch in enumerate(message[:8]):
        bits = format(ord(ch), '08b')
        binary_bits += 8
        if i < 5:
            binary_preview += bits + " "

    binary_bits = char_count * 8
    display.slow_print(display.green(
        f"  {binary_preview.strip()}..."
    ), char_delay=0.008)
    display.slow_print(display.dim_green(
        f"  Raw payload: {binary_bits} bits ({char_count} bytes)"
    ), char_delay=0.01)
    display.slow_print(display.green(
        "  ✓ Binary conversion complete"
    ), char_delay=0.01)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)
    print()

    # ── Phase 3: Compression ──
    display.slow_print(display.dim_green(
        "  PHASE 3: SIGNAL COMPRESSION"
    ), char_delay=0.02)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    # Fake compression — show shrinking
    compressed_bits = int(binary_bits * 0.62)  # ~38% compression
    ratio = compressed_bits / binary_bits * 100

    if display.SPEED > 0:
        display.slow_print(display.dim_green(
            "  Applying Lempel-Ziv-Hydrogen encoding..."
        ), char_delay=0.015)
        time.sleep(0.3 * display.SPEED)

        # SCP-256 hash chain verification
        import hashlib
        seed = message.encode()
        for i in range(3):
            h = hashlib.sha256(seed + bytes([i])).hexdigest()
            sys.stdout.write(
                f"\r  {display.dim_green(f'BLOCK {i:02d}')}  "
                f"{display.green(h)}"
            )
            sys.stdout.flush()
            time.sleep(0.15 * display.SPEED)
            print()

        # Animated compression bar
        bar_width = 30
        for i in range(bar_width + 1):
            pct = int(i / bar_width * 100)
            filled = "█" * i + "░" * (bar_width - i)
            sys.stdout.write(
                f"\r  {display.green(filled)} {display.dim_green(f'{pct}%')}"
            )
            sys.stdout.flush()
            time.sleep(0.03 * display.SPEED)
        print()

    display.slow_print(display.dim_green(
        f"  Compressed: {binary_bits} → {compressed_bits} bits "
        f"({ratio:.0f}% of original)"
    ), char_delay=0.01)
    display.slow_print(display.green(
        "  ✓ Compression complete"
    ), char_delay=0.01)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)
    print()

    # ── Phase 4: Pulse encoding ──
    display.slow_print(display.dim_green(
        "  PHASE 4: PULSE ENCODING"
    ), char_delay=0.02)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    pulses = text_to_pulses(message)
    pulse_count = pulses.count('·') + pulses.count('−')

    # Show partial pulse string
    pulse_preview = pulses[:60]
    if len(pulses) > 60:
        pulse_preview += "..."
    display.slow_print(display.green(
        f"  {pulse_preview}"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        f"  Total pulses: {pulse_count} | "
        f"Frequency: {TRANSMISSION_FREQ}"
    ), char_delay=0.01)
    display.slow_print(display.green(
        "  ✓ Pulse encoding complete"
    ), char_delay=0.01)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)
    print()

    # ── Phase 5: Power calibration ──
    display.slow_print(display.dim_green(
        "  PHASE 5: TRANSMITTER POWER CALIBRATION"
    ), char_delay=0.02)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    display.slow_print(display.dim_green(
        f"  Target distance: {LIGHT_YEARS_TO_TARGET} light-years"
    ), char_delay=0.015)
    display.slow_print(display.dim_green(
        "  Required power: 2.4 GW (effective isotropic)"
    ), char_delay=0.015)
    display.slow_print(display.dim_green(
        "  Antenna gain: 73 dBi (Arecibo-class aperture)"
    ), char_delay=0.015)
    display.slow_print(display.dim_green(
        "  Signal-to-noise at target: ~30σ"
    ), char_delay=0.015)
    display.slow_print(display.green(
        "  ✓ Power calibration locked"
    ), char_delay=0.01)
    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)
    print()

    # ── Phase 6: Transmission ──
    display.slow_print(display.bright_green(
        "  PHASE 6: TRANSMITTING"
    ), char_delay=0.02)
    if display.SPEED > 0:
        time.sleep(0.3 * display.SPEED)

    display.slow_print(display.dim_green(
        f'  Payload: "{message.upper()}"'
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        f"  Target: {TARGET_DESIGNATION}"
    ), char_delay=0.01)
    print()

    # Transmission progress bar
    if display.SPEED > 0:
        bar_width = 40
        for i in range(bar_width + 1):
            pct = int(i / bar_width * 100)
            filled = "█" * i + "░" * (bar_width - i)
            sys.stdout.write(
                f"\r  {display.bright_green(filled)} "
                f"{display.green(f'{pct}%')}"
            )
            sys.stdout.flush()

            # Variable speed — slow start, fast middle, slow end
            if i < 5 or i > bar_width - 5:
                time.sleep(0.12 * display.SPEED)
            else:
                time.sleep(0.03 * display.SPEED)
        print()

    print()
    display.slow_print(display.green(
        "  ✓ TRANSMISSION COMPLETE"
    ), char_delay=0.02)

    if display.SPEED > 0:
        time.sleep(0.5 * display.SPEED)
    print()

    # ── Delivery estimate ──
    now = datetime.now()
    arrival = now + timedelta(days=LIGHT_YEARS_TO_TARGET * 365.25)
    arrival_year = now.year + LIGHT_YEARS_TO_TARGET

    display.slow_print(display.green(
        "  ╔══════════════════════════════════════════════════╗"
    ))
    display.slow_print(display.green(
        "  ║  TRANSMISSION RECEIPT                            ║"
    ))
    display.slow_print(display.green(
        "  ╚══════════════════════════════════════════════════╝"
    ))
    print()

    # Generate unique transmission ID from message + timestamp
    import hashlib
    tx_hash = hashlib.sha256(f"{message}{now}".encode()).hexdigest()
    tx_id = tx_hash[:16].upper()

    display.slow_print(display.bright_green(
        f"  TX-ID: {tx_id}"
    ), char_delay=0.01)
    print()

    display.slow_print(display.dim_green(
        f"  Sent:              {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        f"  Speed:             c (299,792,458 m/s)"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        f"  Distance:          {LIGHT_YEARS_TO_TARGET} light-years "
        f"(1.135 × 10¹⁵ km)"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        f"  Estimated arrival: Year {arrival_year}"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        f"  Travel time:       {LIGHT_YEARS_TO_TARGET} years, "
        f"0 days, 0 hours"
    ), char_delay=0.01)
    print()

    display.slow_print(display.dim_green(
        f"  Payload size:      {compressed_bits} bits (compressed)"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        f"  Frequency:         {TRANSMISSION_FREQ}"
    ), char_delay=0.01)
    display.slow_print(display.dim_green(
        f"  Target:            RA 19h25m / DEC -27°03'"
    ), char_delay=0.01)
    print()

    # Generate random arrival date and time within the year
    arrival_month = random.randint(1, 12)
    arrival_day = random.randint(1, 28)  # Safe for all months
    arrival_hour = random.randint(0, 23)
    arrival_minute = random.randint(0, 59)

    arrival_datetime = (
        f"{arrival_year}-{arrival_month:02d}-{arrival_day:02d} "
        f"at {arrival_hour:02d}:{arrival_minute:02d} UTC"
    )

    display.slow_print(display.bright_green(
        f"  Your message will arrive on {arrival_datetime}."
    ), char_delay=0.02)
    print()

