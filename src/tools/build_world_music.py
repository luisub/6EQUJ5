"""Render the original world scores to looping stereo Vorbis files.

Uses NumPy and the developer's ffmpeg executable; neither ffmpeg nor these
source scores are needed to play the game. All note/reverb tails wrap around
the loop, and a uniform mastering gain preserves that boundary.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCORE = ROOT / 'src/art/source/audio/world_themes.json'
MODES = {
    'minor': (0, 2, 3, 5, 7, 8, 10), 'dorian': (0, 2, 3, 5, 7, 9, 10),
    'major': (0, 2, 4, 5, 7, 9, 11), 'lydian': (0, 2, 4, 6, 7, 9, 11),
    'phrygian': (0, 1, 3, 5, 7, 8, 10),
}


def pitch(tonic, mode, degree):
    octave, step = divmod(degree, 7)
    return tonic + MODES[mode][step] + 12 * octave


def voice(midi, duration, kind, sr):
    """Band-limited additive/FM instruments with quiet attacks and releases."""
    release = 1.5 if kind in ('analog', 'silk', 'hollow') else 0.6
    t = np.arange(round((duration + release) * sr), dtype=np.float64) / sr
    hz = 440 * 2 ** ((midi - 69) / 12)
    p = 2 * np.pi * hz * t
    gate = np.minimum(t / 0.025, 1) * np.minimum((t[-1] - t) / 0.05, 1)
    if kind in ('analog', 'silk'):
        signal = np.sin(p) + .26 * np.sin(p * 1.002) + .18 * np.sin(p * 2) + .07 * np.sin(p * 3)
        attack = .65 if kind == 'silk' else .3
        env = np.minimum(t / attack, 1) * np.minimum(np.maximum(duration + release - t, 0) / release, 1)
        signal *= env * (.93 + .07 * np.sin(2 * np.pi * .18 * t))
    elif kind == 'hollow':
        signal = (np.sin(p) + .18 * np.sin(p * 3)) * np.minimum(t / .12, 1)
        signal *= np.exp(-t / max(duration, .3))
    elif kind in ('bell', 'glass'):
        ratio = 2.0 if kind == 'glass' else 2.76
        signal = np.sin(p + 1.4 * np.exp(-t * 3) * np.sin(p * ratio))
        signal *= np.exp(-t / (.9 if kind == 'bell' else .65))
    elif kind == 'keys':
        signal = np.sin(p) + .28 * np.sin(p * 2) * np.exp(-t * 5) + .1 * np.sin(p * 3)
        signal *= np.exp(-t / .95)
    elif kind == 'pluck':
        signal = sum(np.sin(p * h) * np.exp(-t * h * 3) / h for h in range(1, 6))
    elif kind in ('air', 'reed'):
        vibrato = .025 * np.sin(t * 2 * np.pi * 4.3) * np.minimum(t * 2, 1)
        signal = np.sin(p + vibrato) + (.12 if kind == 'air' else .3) * np.sin(p * 2 + vibrato)
        signal *= np.minimum(t / .1, 1) * np.minimum(np.maximum(duration + .3 - t, 0) / .3, 1)
    else:  # Rounded bass, with enough upper fundamental to survive laptop speakers.
        signal = (np.sin(p) + .22 * np.sin(2 * p)) * np.exp(-t / max(duration, .12))
    return (signal * np.clip(gate, 0, 1)).astype(np.float32)


def drum(kind, sr, rng):
    length = .5 if kind in ('kick', 'tom') else .22
    t = np.arange(round(length * sr)) / sr
    if kind in ('kick', 'tom'):
        base, sweep = (47, 85) if kind == 'kick' else (105, 75)
        phase = 2 * np.pi * (base * t + sweep * .035 * (1 - np.exp(-t / .035)))
        sound = np.sin(phase) * np.exp(-t * (11 if kind == 'kick' else 8))
    else:
        noise = rng.standard_normal(len(t))
        # Remove low noise energy without requiring a signal-processing dependency.
        noise = noise - np.convolve(noise, np.ones(9) / 9, mode='same')
        if kind == 'snare':
            sound = .4 * noise * np.exp(-t * 24) + .3 * np.sin(2 * np.pi * 180 * t) * np.exp(-t * 30)
        else:
            sound = .23 * noise * np.exp(-t * 65)
    envelope = np.minimum(t / .002, 1) * np.minimum((t[-1] - t) / .01, 1)
    return (sound * np.clip(envelope, 0, 1)).astype(np.float32)


def render(track, score):
    sr = score['sample_rate']
    beat = 60 / track['bpm']
    total_beats = score['bars'] * score['beats_per_bar']
    mix = np.zeros((round(total_beats * beat * sr), 2), dtype=np.float32)
    seed = int.from_bytes(hashlib.sha256(track['world_id'].encode()).digest()[:4], 'little')
    rng = np.random.default_rng(seed)
    drums = {kind: drum(kind, sr, rng) for kind in ('kick', 'snare', 'hat', 'tom')}
    cache = {}

    def add(sound, when, gain, pan=0):
        start = round(when * beat * sr) % len(mix)
        stereo = sound[:, None] * np.array([math.sqrt((1 - pan) / 2), math.sqrt((1 + pan) / 2)]) * gain
        first = min(len(stereo), len(mix) - start)
        mix[start:start + first] += stereo[:first]
        if first < len(stereo):
            mix[:len(stereo) - first] += stereo[first:]

    def note(degree, when, length, kind, gain, pan=0, octave=0):
        midi = pitch(track['tonic'], track['mode'], degree) + octave * 12
        key = (midi, length, kind)
        if key not in cache:
            cache[key] = voice(midi, length * beat, kind, sr)
        add(cache[key], when, gain, pan)

    rhythm = track['rhythm']
    sparse = rhythm in ('sparse', 'floating', 'memorial')
    for bar in range(score['bars']):
        start = bar * 4
        chord = track['progression'][(bar // 2) % len(track['progression'])]
        # Four eight-bar sections: establish, answer, breathe, return.
        section = bar // 8
        strength = (.82, 1.0, .62, .94)[section]
        if bar % 2 == 0:
            for index, offset in enumerate((0, 2, 4, 8)):
                note(chord + offset, start, 7.4, track['pad'], .052, (-.65, .55, -.3, .7)[index])
            if not (section == 2 and bar % 4 == 2):
                for when, degree, length in track['motif']:
                    # Anchor phrase endings to the harmony; retain the theme's contour.
                    melodic = degree if when < 6 else chord + (7 if degree >= 7 else 4)
                    note(melodic, start + when, length, track['lead'], .14 * strength, -.1)
                    if section == 1 and when in (0, 4):
                        note(melodic + 2, start + when + .035, length, track['lead'], .035, .45)
        bass_beats = (0, 2.5) if sparse else (0, 1.5, 2, 3.5)
        if rhythm == 'gravity':
            bass_beats = (0, 2.75)
        for index, when in enumerate(bass_beats):
            note(chord + (4 if index == len(bass_beats) - 1 else 0), start + when,
                 1.25 if sparse else .65, 'bass', .13 * strength, 0, -1)
        # Different ostinati and densities give each score its own motion.
        spacing = 1 if sparse or section == 2 else .5
        if rhythm == 'orbits':
            spacing = 4 / 7
        for index, when in enumerate(np.arange(0, 4, spacing)):
            if sparse and (bar + index) % 3:
                continue
            pattern = (0, 4, 2, 8, 4, 6, 2) if rhythm == 'orbits' else (0, 4, 8, 2)
            note(chord + pattern[index % len(pattern)] + 7, start + float(when), .32,
                 'glass' if rhythm in ('crystal', 'sparse') else 'pluck',
                 .033 * strength, .5 if index % 2 else -.5)
        kicks = (0,) if sparse else (0, 2)
        if rhythm in ('beacon', 'orbits', 'hunt'):
            kicks = (0, 1.75, 2.5)
        for when in kicks:
            add(drums['kick'], start + when, .2 * strength)
        if not sparse:
            for when in ((2,) if rhythm == 'half_time' else (1, 3)):
                add(drums['snare'], start + when, .11 * strength, .08)
        hat_spacing = 1 if sparse or section == 2 else .5
        for index, when in enumerate(np.arange(.5, 4, hat_spacing)):
            add(drums['hat'], start + float(when), .12 * strength * (1 if index % 2 else .65), -.35)
        if rhythm == 'hunt':
            for when in (.75, 2.25, 3.5):
                add(drums['tom'], start + when, .095 * strength, -.35 if when < 2 else .35)
        elif bar % 8 == 7 and section != 2:
            for when in (3, 3.5, 3.75):
                add(drums['tom'], start + when, .055 * strength, .25)
    # Circular stereo delay and diffuse early reflections: no silence at the seam.
    dry = mix.copy()
    for fraction, gain in ((.75, .19), (1.5, .10), (2.25, .05)):
        mix += np.roll(dry[:, ::-1], round(fraction * beat * sr), axis=0) * gain
    for seconds, gain in ((.071, .2), (.113, .16), (.179, .12), (.271, .08), (.419, .05)):
        mix += np.roll(dry[:, ::-1], round(seconds * sr), axis=0) * gain * track['space']
    mix -= mix.mean(axis=0)
    mix *= min(.7 / np.max(np.abs(mix)), .095 / np.sqrt(np.mean(mix ** 2)))
    return mix


def write_wav(path, samples, sr):
    with wave.open(str(path), 'wb') as stream:
        stream.setnchannels(2)
        stream.setsampwidth(2)
        stream.setframerate(sr)
        stream.writeframes((np.clip(samples, -1, 1) * 32767).astype('<i2').tobytes())


def build(output, score_path=SCORE):
    if not shutil.which('ffmpeg'):
        raise RuntimeError('Install ffmpeg to rebuild scores; playback does not require it.')
    score = json.loads(score_path.read_text())
    output.mkdir(parents=True, exist_ok=False)
    entries = {}
    with tempfile.TemporaryDirectory(prefix='6equj5-score-') as temporary:
        wav = Path(temporary) / 'score.wav'
        for track in score['tracks']:
            samples = render(track, score)
            write_wav(wav, samples, score['sample_rate'])
            filename = track['file']
            if Path(filename).name != filename or not filename.endswith('.ogg'):
                raise ValueError('Score output must be a single .ogg basename')
            path = output / filename
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(wav),
                            '-c:a', 'libvorbis', '-q:a', '5', '-map_metadata', '-1',
                            '-metadata', 'title=' + track['title'], '-metadata', 'artist=6EQUJ5',
                            str(path)], check=True)
            entries[filename] = {
                'world_id': track['world_id'], 'title': track['title'],
                'description': track['description'], 'role': 'world_exploration_guardian_contact',
                'loop': True, 'fade_ms': 1000, 'bpm': track['bpm'],
                'duration_seconds': round(len(samples) / score['sample_rate'], 3),
                'sample_rate': score['sample_rate'], 'channels': 2,
                'size_bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'source': 'art/source/audio/world_themes.json',
                'builder': 'tools/build_world_music.py',
            }
            print(f"{track['world_id']}: {track['title']} ({entries[filename]['duration_seconds']}s)", flush=True)
        (output / 'music_tracks.json').write_text(json.dumps(entries, indent=2) + '\n')
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='New staging directory, never the live audio bank')
    args = parser.parse_args()
    build(args.output)


if __name__ == '__main__':
    main()
