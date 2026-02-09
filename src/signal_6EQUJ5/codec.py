"""
SIGNAL ENCODING / DECODING MODULE
══════════════════════════════════

The Big Ear telescope recorded signal intensity using a
single alphanumeric character per 12-second integration window.

    Blank = 0-0.999...
    1     = 1.0-1.999...
    2     = 2.0-2.999...
    ...
    9     = 9.0-9.999...
    A     = 10.0-10.999...
    B     = 11.0-11.999...
    ...
    Z     = 35.0-35.999...

The sequence 6EQUJ5 thus represents intensities:

    6  →  6.0   (moderate)
    E  → 14.0   (strong)
    Q  → 26.0   (very strong)
    U  → 30.0   (PEAK — ~30x background noise)
    J  → 19.0   (strong, declining)
    5  →  5.0   (returning to baseline)

    — Jerry R. Ehman's logbook, August 1977
"""

# ═══════════════════════════════════════════════════════
#   Ehman's notation: each character maps to an integer
#   intensity level. Space = 0, digits = 1-9, letters
#   A-Z = 10-35. Simple. Elegant. Unmistakable.
# ═══════════════════════════════════════════════════════

# The full intensity alphabet, exactly as used by Big Ear
INTENSITY_CHARS = " 123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# The signal that started it all
THE_SIGNAL = "6EQUJ5"

# What Ehman wrote in the margin
THE_ANNOTATION = "Wow!"

# The frequency they were watching — 1420.405 MHz
# The emission line of neutral hydrogen
# The most common element in the universe
# If you wanted the whole galaxy to hear you, you'd use this
HYDROGEN_LINE_MHZ = 1420.4056

# Where it came from (approximately)
# Two candidate regions in Sagittarius, near Chi Sagittarii
RIGHT_ASCENSION = "19h 25m 31s"
DECLINATION = "-27° 03'"

# How long the telescope could see any single point
OBSERVATION_WINDOW_SECONDS = 72


def char_to_intensity(char):
    """
    Convert a Big Ear intensity character to its numeric value.

    Each 12-second integration period was recorded as a single
    character. Jerry kept the notation simple — you could read
    the intensity right off the printout.

    Parameters
    ----------
    char : str
        A single character from the Big Ear intensity alphabet.

    Returns
    -------
    int
        The intensity value (0-35).

    Examples
    --------
    >>> char_to_intensity('U')
    30
    >>> char_to_intensity('6')
    6
    """
    char = char.upper()
    if char == ' ':
        return 0
    idx = INTENSITY_CHARS.find(char)
    if idx == -1:
        return -1  # Unknown — noise? interference? something else?
    return idx


def intensity_to_char(intensity):
    """
    Convert a numeric intensity value back to its Big Ear character.

    Parameters
    ----------
    intensity : int
        Intensity value (0-35).

    Returns
    -------
    str
        The corresponding character.

    Examples
    --------
    >>> intensity_to_char(30)
    'U'
    >>> intensity_to_char(6)
    '6'
    """
    if 0 <= intensity < len(INTENSITY_CHARS):
        return INTENSITY_CHARS[intensity]
    return '?'


def decode(sequence):
    """
    Decode a Big Ear intensity sequence into its component values.

    Takes a string of intensity characters and returns each one
    mapped to its numeric intensity and a description of signal
    strength.

    Parameters
    ----------
    sequence : str
        A string of Big Ear intensity characters (e.g., '6EQUJ5').

    Returns
    -------
    list of dict
        Each entry contains 'char', 'intensity', and 'description'.

    Examples
    --------
    >>> results = decode('6EQUJ5')
    >>> results[3]['char']
    'U'
    >>> results[3]['intensity']
    30
    """
    results = []
    for i, char in enumerate(sequence.upper()):
        intensity = char_to_intensity(char)
        if intensity < 0:
            desc = "UNKNOWN"
        elif intensity == 0:
            desc = "baseline noise"
        elif intensity <= 3:
            desc = "weak"
        elif intensity <= 6:
            desc = "moderate"
        elif intensity <= 12:
            desc = "notable"
        elif intensity <= 20:
            desc = "strong"
        elif intensity <= 28:
            desc = "very strong"
        else:
            desc = "EXTRAORDINARY"

        results.append({
            'position': i,
            'char': char.upper(),
            'intensity': intensity,
            'description': desc,
            'sigma': f"~{intensity}σ above noise" if intensity > 0 else "noise floor",
            'window': f"{i * 12}s - {(i + 1) * 12}s",
        })

    return results


def encode(text):
    """
    Encode a text message into Big Ear intensity characters.

    Maps each ASCII character to an intensity value using modular
    arithmetic on its ordinal value, then converts to a Big Ear
    intensity character.

    This is NOT how the Big Ear actually worked — it recorded raw
    signal power. But if you wanted to hide a message in a signal
    that looked like telescope data... this is how you'd do it.

    Parameters
    ----------
    text : str
        The message to encode.

    Returns
    -------
    str
        The encoded intensity sequence.

    Examples
    --------
    >>> encode('Hi')
    '... (encoded result)'
    """
    encoded = []
    for char in text:
        # Map ASCII ordinal to 0-35 range
        intensity = ord(char) % 36
        encoded.append(intensity_to_char(intensity))
    return ''.join(encoded)


def encode_detailed(text):
    """
    Encode a message and return detailed mapping information.

    Parameters
    ----------
    text : str
        The message to encode.

    Returns
    -------
    list of dict
        Each entry contains 'original', 'intensity', and 'encoded_char'.
    """
    results = []
    for char in text:
        intensity = ord(char) % 36
        results.append({
            'original': char,
            'ordinal': ord(char),
            'intensity': intensity,
            'encoded_char': intensity_to_char(intensity),
        })
    return results


# ═══════════════════════════════════════════════════════
#   "I wrote 'Wow!' because I was impressed by the
#    signal. It was the strongest signal we had ever
#    seen."
#                          — Jerry R. Ehman, 1994
# ═══════════════════════════════════════════════════════


def _wow(frequency=None):
    """
    Was it them?

    This function is not documented anywhere.
    You found it because you read the source code.
    That's exactly what Ehman did.

    Parameters
    ----------
    frequency : float, optional
        The frequency to check, in Hz.
    """
    if frequency == 1420405000:
        return THE_ANNOTATION
    if frequency == HYDROGEN_LINE_MHZ:
        return THE_ANNOTATION
    return "..."
