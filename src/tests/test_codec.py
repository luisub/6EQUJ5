"""PURPOSE: Verify the in-game signal decoder retains its intensity contract.
CALLED BY: pytest tests/test_codec.py.
HOW TO MODIFY: Preserve the historical character and signal-bin behavior.
"""
from video_game.engine import codec


def test_signal_bins_and_duration():
    bins = codec.decode(codec.THE_SIGNAL)
    assert [item['intensity'] for item in bins] == [6, 14, 26, 30, 19, 5]
    assert bins[3]['description'] == 'EXTRAORDINARY'
    assert bins[-1]['window'] == '60s - 72s'
    assert codec.OBSERVATION_WINDOW_SECONDS == 72


def test_character_decoding_keeps_zero_unknown_and_case():
    bins = codec.decode(' a?')
    assert [item['intensity'] for item in bins] == [0, 10, -1]
    assert [item['description'] for item in bins] == ['baseline noise', 'notable', 'UNKNOWN']
