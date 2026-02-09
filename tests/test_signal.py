"""
TEST SUITE — THE WOW! SIGNAL
═════════════════════════════

Read the test names top to bottom.
They tell a story.
"""

from signal_6EQUJ5 import codec


# ═══════════════════════════════════════════════════════
#   Act I — The Telescope
# ═══════════════════════════════════════════════════════


class TestTheTelescope:
    """The Big Ear was listening. It had been listening since 1973."""

    def test_the_telescope_was_listening(self):
        """It listened on the hydrogen line — 1420.4056 MHz."""
        assert codec.HYDROGEN_LINE_MHZ == 1420.4056

    def test_the_observation_window_was_72_seconds(self):
        """Any source drifted through the beam in exactly 72 seconds."""
        assert codec.OBSERVATION_WINDOW_SECONDS == 72

    def test_each_sample_was_12_seconds(self):
        """Each character represented 12 seconds of integration."""
        # 6 characters × 12 seconds = 72 seconds
        assert len(codec.THE_SIGNAL) * 12 == codec.OBSERVATION_WINDOW_SECONDS

    def test_the_intensity_alphabet_has_36_levels(self):
        """Space through Z — 36 possible intensity values."""
        assert len(codec.INTENSITY_CHARS) == 36


# ═══════════════════════════════════════════════════════
#   Act II — The Signal
# ═══════════════════════════════════════════════════════


class TestTheSignal:
    """On August 15, 1977, something appeared in the data."""

    def test_the_signal_was_6equj5(self):
        """Six characters. That's all we have."""
        assert codec.THE_SIGNAL == "6EQUJ5"

    def test_it_started_moderate(self):
        """Intensity 6 — noticeable, but not alarming."""
        assert codec.char_to_intensity('6') == 6

    def test_it_grew_strong(self):
        """E = 14. Something was building."""
        assert codec.char_to_intensity('E') == 14

    def test_it_grew_very_strong(self):
        """Q = 26. Far above normal."""
        assert codec.char_to_intensity('Q') == 26

    def test_it_peaked(self):
        """U = 30. Approximately 30 times the background noise."""
        assert codec.char_to_intensity('U') == 30

    def test_it_began_to_fade(self):
        """J = 19. Still strong, but declining."""
        assert codec.char_to_intensity('J') == 19

    def test_it_returned_to_baseline(self):
        """5 = 5. And then it was gone."""
        assert codec.char_to_intensity('5') == 5

    def test_the_rise_and_fall_was_symmetric(self):
        """Consistent with a point source tracked by Earth's rotation."""
        values = [codec.char_to_intensity(c) for c in codec.THE_SIGNAL]
        peak_idx = values.index(max(values))
        # Peak is roughly in the middle
        assert 1 <= peak_idx <= 4

    def test_it_came_from_sagittarius(self):
        """RA 19h 25m 31s, Dec -27° 03'."""
        assert codec.RIGHT_ASCENSION == "19h 25m 31s"
        assert codec.DECLINATION == "-27° 03'"


# ═══════════════════════════════════════════════════════
#   Act III — The Aftermath
# ═══════════════════════════════════════════════════════


class TestTheAftermath:
    """It has never been detected again."""

    def test_ehman_wrote_wow(self):
        """The most famous margin note in the history of science."""
        assert codec.THE_ANNOTATION == "Wow!"

    def test_decoding_recovers_intensities(self):
        """The signal can be fully decoded to its intensity values."""
        results = codec.decode(codec.THE_SIGNAL)
        intensities = [r['intensity'] for r in results]
        assert intensities == [6, 14, 26, 30, 19, 5]

    def test_peak_was_extraordinary(self):
        """The peak intensity was described as EXTRAORDINARY."""
        results = codec.decode(codec.THE_SIGNAL)
        peak = max(results, key=lambda r: r['intensity'])
        assert peak['description'] == "EXTRAORDINARY"

    def test_encoding_and_decoding_are_consistent(self):
        """What goes up must come down. What is encoded can be decoded."""
        for intensity in range(36):
            char = codec.intensity_to_char(intensity)
            recovered = codec.char_to_intensity(char)
            assert recovered == intensity

    def test_it_never_repeated(self):
        """
        Despite decades of follow-up observations,
        the signal has never been detected again.

        This test always passes.
        Because the signal is not here.
        """
        signal_found_again = False
        assert not signal_found_again


# ═══════════════════════════════════════════════════════
#   Epilogue
# ═══════════════════════════════════════════════════════


class TestEpilogue:
    """The telescope is gone. The signal remains."""

    def test_the_telescope_was_demolished_in_1998(self):
        """
        The Big Ear telescope was torn down in 1998
        to make way for a golf course and housing development.

        The longest-running SETI program in history,
        destroyed for real estate.
        """
        demolished = 1998
        first_light = 1963
        years_of_service = demolished - first_light
        assert years_of_service == 35

    def test_the_question_remains_open(self):
        """
        Was it a signal from an extraterrestrial civilization?
        A natural astrophysical phenomenon?
        A reflection of a terrestrial signal?

        We don't know.

        But we're still listening.
        """
        explained = False
        still_listening = True
        assert not explained
        assert still_listening
