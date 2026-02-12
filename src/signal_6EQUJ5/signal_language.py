"""
SIGNAL LANGUAGE — TERNARY HUFFMAN WORD CODEC
════════════════════════════════════════════════

Communication across 120 light-years is expensive.
Every symbol costs energy measured in stars.

So they built a language optimized for silence.
The most common words became the shortest signals.
The rarest thoughts became the longest.

Their dictionary is a map of what they considered
worth saying.

Encoding: ternary Huffman (prefix-free)
Symbols:  . (dot)  _ (line)  - (dash)
No separators needed. No ambiguity. No waste.

CLASSIFICATION: LEVEL 7 — RESTRICTED
"""

import heapq
import re


# ═══════════════════════════════════════════════════════
#   WORD FREQUENCY TABLE
#
#   Ranked by importance to the signal.
#   Common English weighted by frequency.
#   Game-critical terms weighted higher.
#
#   Frequency values are relative weights.
#   Higher = more common = shorter code.
# ═══════════════════════════════════════════════════════

# fmt: off
WORD_FREQUENCIES = {
    # --- Tier 0: structural (most common English words) ---
    "the":      10000, "be":       8500, "to":       8200,
    "of":       7800, "and":      7600, "a":        7400,
    "in":       7200, "that":     6800, "have":     6600,
    "i":        6400, "it":       6200, "for":      6000,
    "not":      5800, "on":       5600, "with":     5400,
    "he":       5200, "as":       5000, "you":      4800,
    "do":       4600, "at":       4400, "this":     4200,
    "but":      4000, "his":      3800, "by":       3600,
    "from":     3400, "they":     3200, "we":       3000,
    "her":      2900, "she":      2800, "or":       2700,
    "an":       2600, "will":     2500, "my":       2400,
    "one":      2300, "all":      2200, "would":    2100,
    "there":    2000, "their":    1950, "what":     1900,
    "so":       1850, "up":       1800, "out":      1750,
    "if":       1700, "about":    1650, "who":      1600,
    "get":      1550, "which":    1500, "go":       1450,
    "me":       1400, "when":     1350, "make":     1300,
    "can":      1250, "like":     1200, "no":       1150,
    "just":     1100, "him":      1050, "know":     1000,
    "take":     975, "come":     950, "could":    925,
    "than":     900, "look":     875, "them":     850,
    "its":      825, "only":     800, "think":    775,
    "also":     750, "after":    725, "use":      700,
    "how":      675, "our":      650, "work":     625,
    "any":      600, "these":    575, "us":       550,
    "into":     525, "then":     500, "time":     490,
    "very":     480, "your":     470, "say":      460,
    "see":      450, "way":      440, "more":     430,
    "now":      420, "find":     410, "here":     400,
    "thing":    390, "give":     380, "many":     370,
    "well":     360, "new":      350, "some":     340,
    "other":    330, "tell":     320, "ask":      310,
    "good":     300, "most":     290, "should":   280,
    "need":     270, "want":     260, "been":     250,
    "call":     240, "long":     230, "day":      220,
    "did":      210, "over":     200, "back":     195,
    "still":    190, "own":      185, "down":     180,
    "first":    175, "last":     170, "keep":     165,
    "same":     160, "much":     155, "because":  150,
    "does":     145, "turn":     140, "every":    135,
    "leave":    130, "may":      125, "between":  120,
    "never":    115, "before":   110, "must":     105,
    "through":  100, "where":    95, "begin":    90,
    "world":    88, "under":    86, "end":      84,
    "life":     82, "each":     80, "old":      78,
    "another":  76, "against":  74, "part":     72,
    "those":    70, "why":      68, "around":   66,
    "place":    64, "without":  62, "again":    60,
    "great":    58, "while":    56, "small":    54,
    "year":     52, "few":      50, "right":    48,
    "too":      46, "even":     44, "off":      42,
    "such":     40, "hand":     38, "high":     36,
    "night":    34, "both":     32, "point":    30,
    "far":      28, "man":      26, "woman":    24,
    "name":     22, "second":   20, "head":     18,
    "side":     16, "two":      15, "three":    14,

    # --- Tier 1: signal-critical terms (boosted weight) ---
    "signal":   5000, "frequency":4800, "listen":    4600,
    "waiting":  4400, "silence":  4200, "transmit":  4000,
    "receive":  3900, "decode":   3800, "message":   3700,
    "answer":   3600, "question": 3500, "channel":   3400,
    "hydrogen": 3300, "star":     3200, "contact":   3100,
    "origin":   3000, "pattern":  2950, "pulse":     2900,

    # --- Tier 2: game dialogue terms ---
    "civilization": 2850, "species":  2800, "universe":  2750,
    "language":  2700, "weapon":   2650, "gift":      2600,
    "truth":     2550, "fear":     2500, "hope":      2450,
    "war":       2400, "peace":    2350, "death":     2300,
    "extinction":2250, "survive":  2200, "build":     2150,
    "destroy":   2100, "heard":    2050, "hear":      2000,
    "chosen":    1975, "ready":    1950, "earth":     1925,
    "human":     1900, "planet":   1875, "light":     1850,
    "dark":      1825, "ancient":  1775,
    "marker":    1750, "gate":     1725, "key":       1700,
    "code":      1675, "builders": 1650, "watched":   1625,
    "centuries": 1600, "remember": 1575, "forget":    1550,
    "alive":     1525, "sacred":   1500, "knowledge": 1475,
    "power":     1450, "empty":    1400,
    "patient":   1375,

    # --- Tier 3: astronomy and science ---
    "telescope":  800, "receiver":   780, "bandwidth":  760,
    "spectrum":   740, "anomaly":    720, "noise":      700,
    "emission":   680, "radiation":  660, "orbit":      640,
    "gravity":    620, "mass":       600, "energy":     580,
    "photon":     560, "wavelength": 540, "amplitude":  520,
    "coordinate": 500, "declination":480, "ascension": 460,
    "galactic":   440, "interstellar":420, "transmission":400,

    # --- Tier 4: numbers (as words) ---
    "zero":    200, "seven":   180, "five":    160,
    "six":     150, "four":    140, "eight":   130,
    "nine":    120, "ten":     110, "hundred": 100,
    "thousand": 90, "million":  80, "billion":  70,

    # --- Tier 5: emotional/philosophical (game flavor) ---
    "alone":    350, "lost":     340,
    "broken":   320, "whole":    310, "forever":  300,
    "nothing":  290, "everything":280, "always":  270,
    "belong":   260, "choose":   250, "become":   240,
    "remain":   230, "return":   220, "born":     210,
    "beautiful":200, "terrible": 190, "impossible":180,
    "necessary":170, "enough":   160, "matter":   150,
    "exist":    140, "create":   130, "meaning":  120,
    "purpose":  110, "reason":   100, "worth":     90,
    "cost":      80, "price":     70, "measure":   60,

    # --- Tier 5b: verb forms ---
    "are":      4700, "is":      6300, "was":     4100,
    "were":     2050, "has":     2000, "had":     1800,
    "being":    1600, "am":      1500,
    "said":     700, "went":    600, "made":    500,
    "took":     400, "came":    350, "thought": 300,
    "knew":     250, "found":   200, "gave":    180,
    "told":     160, "asked":   140,

    # --- Tier 6: dialogue vocabulary ---
    # Every word that appears in the game's contact messages
    "acknowledged": 10, "across":    30, "activation": 40,
    "active":    35, "advantage": 20, "ago":       50,
    "aligned":   15, "almost":    55, "already":   50,
    "answered":  60, "answering": 55, "answers":   50,
    "archaeologists": 5, "arrived":  30, "art":      45,
    "asking":    40, "asks":      35, "atom":      40,
    "attach":    15, "began":     50, "beings":    45,
    "binary":    35, "brain":     30, "built":     65,
    "calendar":  10, "called":    60, "cannot":    55,
    "care":      40, "cares":     35, "carries":   30,
    "ceremonial": 10, "chance":   45, "change":    50,
    "channels":  30, "characters":25, "chemical":  30,
    "children":  40, "choice":    45, "chose":     40,
    "circles":   35, "cities":    30, "civilizations": 40,
    "close":     45, "closer":    40, "closest":   35,
    "closing":   35, "comes":     50, "common":    40,
    "communication": 55, "concepts": 30, "confined": 25,
    "contacted": 45, "coordinates": 40, "cured":   20,
    "curious":   30, "currently": 25, "danger":    45,
    "dead":      40, "decades":   30, "decibels":  25,
    "decoded":   35, "departure": 20, "design":    30,
    "determine": 25, "difference":30, "differently":25,
    "disadvantage": 15, "discovers": 25, "distance": 40,
    "east":      30, "either":    35, "element":   40,
    "encoded":   35, "encountered": 20, "engine":   30,
    "equivalent": 20, "eventually": 35, "ever":    50,
    "existence": 40, "expected":  35, "experience":30,
    "extraordinary": 25, "failure": 30, "fearing":  25,
    "fears":     30, "finally":   40, "fire":      45,
    "flaw":      20, "future":    55, "given":     45,
    "goodbye":   30, "governments": 25, "greatest": 35,
    "greet":     25, "grows":     30, "higher":    30,
    "hunger":    25, "ignored":   25, "imagine":   30,
    "implies":   20, "instead":   35, "instruction": 25,
    "invitation": 20, "inward":   25, "killing":   30,
    "knowing":   35, "lasted":    30, "learn":     45,
    "left":      50, "let":       45, "line":      40,
    "listened":  40, "listening": 45, "local":     30,
    "longer":    35, "loud":      25, "marked":    30,
    "markers":   35, "mathematics": 25, "matters":  30,
    "measured":  35, "memory":    35, "missed":    30,
    "mortality": 30, "music":     35, "mystery":   30,
    "names":     25, "needed":    35, "neither":   25,
    "next":      45, "none":      35, "north":     25,
    "noticed":   25, "observed":  30, "older":     25,
    "open":      40, "opens":     35, "others":    45,
    "outward":   25, "past":      40, "patience":  35,
    "persist":   30, "person":    30, "phenomenon":25,
    "physics":   30, "pillars":   35, "pointed":   25,
    "prayer":    25, "present":   35, "pretend":   25,
    "primitive": 30, "problem":   35, "produce":   25,
    "proof":     30, "questions": 35, "radio":     35,
    "random":    25, "rare":      30, "reach":     40,
    "reaches":   30, "readiness": 25, "really":    35,
    "received":  40, "recognized":25, "regretted": 15,
    "remains":   30, "reproducing": 15, "requires": 25,
    "retransmit": 20, "rise":     30, "science":   35,
    "seconds":   30, "secret":    35, "send":      50,
    "sent":      45, "set":       40, "seventy":   20,
    "shapes":    25, "shares":    25, "signals":   40,
    "similar":   25, "simplify":  15, "since":     35,
    "smaller":   25, "solved":    25, "someone":   35,
    "something": 40, "sometimes": 30, "speak":     35,
    "speaking":  30, "split":     20, "stand":     30,
    "stars":     40, "stone":     30, "stopped":   30,
    "stops":     25, "structural":20, "studied":   25,
    "survives":  30, "taught":    25, "telescopes":30,
    "temples":   25, "terminating": 20, "themselves":30,
    "thin":      25, "times":     30, "translate": 25,
    "transmitting": 30, "travel":  35, "try":      40,
    "unclear":   20, "understand":40, "understanding": 30,
    "understood":30, "universal": 30, "waited":    35,
    "walk":      30, "wanted":    35, "watch":     35,
    "weapons":   30, "whether":   30, "whoever":   25,
    "window":    35, "wonder":    30, "word":      35,
    "works":     30, "writing":   30, "written":   30,
    "wrong":     30, "years":     40, "yet":       40,
    "young":     25, "yours":     25, "yourselves":20,
    "done":      45, "t":         10,
}
# fmt: on


# ═══════════════════════════════════════════════════════
#   TERNARY HUFFMAN TREE BUILDER
#
#   Three symbols: . _ -
#   Prefix-free: no code is a prefix of another.
#   Optimal: minimum average code length.
#
#   Why ternary? Three states in a pulse:
#     .  short burst
#     _  sustained tone
#     -  silence (carrier gap)
# ═══════════════════════════════════════════════════════

SYMBOLS = ('.', '_', '-')


class _Node:
    """Node in the Huffman tree."""
    __slots__ = ('word', 'weight', 'children')

    def __init__(self, weight, word=None, children=None):
        self.weight = weight
        self.word = word
        self.children = children or []

    def __lt__(self, other):
        return self.weight < other.weight


def _build_tree(frequencies):
    """
    Build a ternary Huffman tree from word frequencies.

    For a ternary tree to be complete, we need
    (n - 1) % 2 == 0 leaf nodes. If not, pad with
    dummy nodes of weight 0.

    Parameters
    ----------
    frequencies : dict
        Mapping of word -> frequency weight.

    Returns
    -------
    _Node
        Root of the Huffman tree.
    """
    # Ensure valid ternary tree: (n - 1) must be divisible by 2
    items = list(frequencies.items())
    while (len(items) - 1) % 2 != 0:
        items.append((None, 0))  # dummy node

    # Build priority queue (min-heap)
    heap = [_Node(weight=w, word=word) for word, w in items]
    heapq.heapify(heap)

    # Merge nodes: take 3 smallest, create parent
    while len(heap) > 1:
        children = [heapq.heappop(heap) for _ in range(min(3, len(heap)))]
        combined_weight = sum(c.weight for c in children)
        parent = _Node(weight=combined_weight, children=children)
        heapq.heappush(heap, parent)

    return heap[0]


def _generate_codebook(node, prefix="", codebook=None):
    """
    Traverse the tree to generate prefix-free codes.

    Parameters
    ----------
    node : _Node
        Current node in the tree.
    prefix : str
        Code accumulated so far.
    codebook : dict or None
        Accumulated codebook.

    Returns
    -------
    dict
        Mapping of word -> code string.
    """
    if codebook is None:
        codebook = {}

    if node.word is not None:
        # Leaf node (skip dummy nodes with word=None)
        codebook[node.word] = prefix or '.'  # root-only edge case
        return codebook

    for i, child in enumerate(node.children):
        _generate_codebook(child, prefix + SYMBOLS[i], codebook)

    return codebook


# Build the codebook once at import time
_tree = _build_tree(WORD_FREQUENCIES)
CODEBOOK = _generate_codebook(_tree)

# Build reverse lookup: code -> word
REVERSE_CODEBOOK = {code: word for word, code in CODEBOOK.items()}


# ═══════════════════════════════════════════════════════
#   ENCODE / DECODE API
#
#   encode("we have been waiting")
#   → compact ternary string
#
#   decode(signal)
#   → "we have been waiting"
# ═══════════════════════════════════════════════════════


def encode(text):
    """
    Encode English text into signal language.

    Words not in the codebook are spelled out using
    character-level ternary encoding with an escape
    prefix.

    Parameters
    ----------
    text : str
        English text to encode.

    Returns
    -------
    str
        Signal-encoded string using . _ - characters.
    """
    words = re.findall(r"[a-zA-Z]+", text.lower())
    codes = []

    for word in words:
        if word in CODEBOOK:
            codes.append(CODEBOOK[word])
        else:
            # Unknown word: encode each character individually
            for char in word:
                if char in CODEBOOK:
                    codes.append(CODEBOOK[char])
                else:
                    codes.append(_char_to_ternary(char))

    return ''.join(codes)


def decode(signal):
    """
    Decode signal language back to English text.

    Walks the Huffman tree character by character.
    Prefix-free codes mean no ambiguity.

    Parameters
    ----------
    signal : str
        Signal string using . _ - characters.

    Returns
    -------
    str
        Decoded English text, words separated by spaces.
    """
    words = []
    current = ""

    for char in signal:
        if char not in set(SYMBOLS):
            continue  # skip non-signal characters
        current += char
        if current in REVERSE_CODEBOOK:
            words.append(REVERSE_CODEBOOK[current])
            current = ""

    # If there's remaining unmatched signal, include as-is
    if current:
        words.append(f"[{current}]")

    return ' '.join(words)


def _char_to_ternary(char):
    """
    Encode a single character as a ternary number.

    Uses a fixed-width 6-trit encoding (3^6 = 729 > 128 ASCII).

    Parameters
    ----------
    char : str
        Single character.

    Returns
    -------
    str
        6-character ternary string using . _ -
    """
    n = ord(char)
    trits = []
    for _ in range(6):
        trits.append(SYMBOLS[n % 3])
        n //= 3
    return ''.join(reversed(trits))


# ═══════════════════════════════════════════════════════
#   CODEBOOK INSPECTION UTILITIES
# ═══════════════════════════════════════════════════════


def get_shortest_codes(n=20):
    """
    Return the n shortest codes in the codebook.

    These are the words the signal considers most
    important: the ones worth compressing the most.

    Parameters
    ----------
    n : int
        Number of entries to return.

    Returns
    -------
    list of (word, code, length) tuples
        Sorted by code length, then alphabetically.
    """
    entries = [
        (word, code, len(code))
        for word, code in CODEBOOK.items()
    ]
    entries.sort(key=lambda x: (x[2], x[0]))
    return entries[:n]


def get_codebook_stats():
    """
    Return statistics about the codebook.

    Returns
    -------
    dict
        Statistics including total words, min/max/avg code length.
    """
    lengths = [len(code) for code in CODEBOOK.values()]
    return {
        "total_words": len(CODEBOOK),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "avg_length": sum(lengths) / len(lengths),
        "symbols": SYMBOLS,
    }
