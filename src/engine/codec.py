"""MODULE: video_game/engine/codec.py
PURPOSE: Decode Big Ear intensity characters for the authored game receiver.
CALLED BY: video_game/engine/contact_session.py.
HOW TO MODIFY: Preserve the historical intensity alphabet and twelve-second bins.

The decoding rules are retained from the historical signal package, but this
module has no dependency on the terminal application or a model service.
"""

INTENSITY_CHARS = " 123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
THE_SIGNAL = "6EQUJ5"
OBSERVATION_WINDOW_SECONDS = 72


def char_to_intensity(char):
    """Return the intensity for a character, or -1 for an unknown character."""
    return INTENSITY_CHARS.find(char.upper())


def decode(sequence):
    """Return the recorded intensity and descriptions for each signal bin."""
    results = []
    for index, char in enumerate(sequence.upper()):
        intensity = char_to_intensity(char)
        if intensity < 0:
            description = "UNKNOWN"
        elif intensity == 0:
            description = "baseline noise"
        elif intensity <= 3:
            description = "weak"
        elif intensity <= 6:
            description = "moderate"
        elif intensity <= 12:
            description = "notable"
        elif intensity <= 20:
            description = "strong"
        elif intensity <= 28:
            description = "very strong"
        else:
            description = "EXTRAORDINARY"
        results.append({
            'position': index,
            'char': char,
            'intensity': intensity,
            'description': description,
            'sigma': f"~{intensity}σ above noise" if intensity > 0 else "noise floor",
            'window': f"{index * 12}s - {(index + 1) * 12}s",
        })
    return results
