"""
# PURPOSE: Synthesize Act I procedural sound effects (maser, impacts, alarms, station chimes, teleprinter).
# CALLED BY: Standalone execution (`python -m video_game.tools.audio_sfx_builder`) or release pipeline.
# HOW TO MODIFY: Adjust waveform harmonics, frequency envelopes, or decay constants.
"""

import hashlib
import json
import math
from pathlib import Path
import random
import struct
from typing import Any, Callable, Dict, List, Tuple
import wave

AUDIO_DIR = Path(__file__).resolve().parents[2] / "src" / "assets" / "audio"
SAMPLE_RATE = 44100


def ensure_audio_dir():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def write_wav(file_path: Path, samples: List[float]):
    """Write normalized floating-point samples [-1.0, 1.0] to a 16-bit 44.1kHz mono WAV file."""
    data = bytearray()
    for s in samples:
        # Clamp to avoid integer overflow clipping
        clamped = max(-1.0, min(1.0, s))
        val = int(clamped * 32767.0)
        data.extend(struct.pack("<h", val))

    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(data)


def synth_maser_tap(duration: float = 0.16) -> List[float]:
    """1420 MHz waveguide maser tap fire: fast down-sweep with crisp electromagnetic snap."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        env = math.exp(-t * 22.0)  # Fast decay
        # Down sweep from 1420 Hz to 360 Hz
        freq = 1420.0 - (1420.0 - 360.0) * (t / duration) ** 0.5
        phase = 2.0 * math.pi * freq * t
        # Harmonic mix (sine + triangle/square overtone)
        sig = 0.65 * math.sin(phase) + 0.35 * (1.0 if math.sin(phase * 2.0) > 0 else -1.0)
        # Transient attack click
        click = 0.4 * (1.0 - t / 0.015) if t < 0.015 else 0.0
        samples.append(env * (sig * 0.7 + click))
    return samples


def synth_maser_charge(duration: float = 0.45) -> List[float]:
    """Charged plasma maser blast: sub-bass pulse, searing frequency sweep, and crackling decay."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        env = math.exp(-t * 7.0)
        # Sub-bass punch at start (60 Hz decaying)
        sub = math.sin(2.0 * math.pi * 60.0 * t) * math.exp(-t * 14.0)
        # Main plasma sweep (1800 Hz down to 220 Hz)
        freq = 1800.0 * math.exp(-t * 5.0) + 220.0
        phase = 2.0 * math.pi * freq * t
        beam = 0.5 * math.sin(phase) + 0.3 * math.sin(phase * 1.5) + 0.2 * math.sin(phase * 3.0)
        # High-energy plasma sizzle noise
        noise = (random.random() * 2.0 - 1.0) * 0.25 * math.exp(-t * 10.0)
        samples.append(env * 0.4 * sub + env * 0.7 * beam + noise)
    return samples


def synth_impact_spark(duration: float = 0.12) -> List[float]:
    """Metallic ricochet snap with brief high-pass noise burst."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        env = math.exp(-t * 32.0)
        # Metallic ring frequencies (3200 Hz, 4400 Hz)
        ring = 0.6 * math.sin(2.0 * math.pi * 3200.0 * t) + 0.4 * math.sin(2.0 * math.pi * 4400.0 * t)
        # Noise burst
        noise = (random.random() * 2.0 - 1.0) * 0.5 * math.exp(-t * 50.0)
        samples.append(env * (ring * 0.7 + noise))
    return samples


def synth_alarm_lock(duration: float = 0.15) -> List[float]:
    """High-frequency two-tone threat lock alert beep (1760 Hz to 2640 Hz)."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    half = num_samples // 2
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        freq = 1760.0 if i < half else 2640.0
        phase = 2.0 * math.pi * freq * t
        # Trapezoidal envelope for clean non-clicking beep
        local_t = t if i < half else (t - half / SAMPLE_RATE)
        seg_dur = duration / 2.0
        att = min(1.0, local_t / 0.005)
        rel = min(1.0, (seg_dur - local_t) / 0.005)
        env = att * rel
        sig = math.sin(phase)
        samples.append(env * sig * 0.6)
    return samples


def synth_station_chime(duration: float = 0.35) -> List[float]:
    """Warm analog terminal console acknowledge chime (C5-E5 major third bell tone)."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        env = math.exp(-t * 9.0)
        # 523.25 Hz (C5) and 659.25 Hz (E5)
        c5 = math.sin(2.0 * math.pi * 523.25 * t)
        e5 = math.sin(2.0 * math.pi * 659.25 * t)
        overtone = 0.2 * math.sin(2.0 * math.pi * 1046.5 * t) * math.exp(-t * 18.0)
        sig = 0.5 * c5 + 0.4 * e5 + overtone
        samples.append(env * sig * 0.7)
    return samples


def synth_printer_chatter(duration: float = 0.08) -> List[float]:
    """Teleprinter mechanical stepper motor strike click."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        env = math.exp(-t * 45.0)
        thump = math.sin(2.0 * math.pi * 120.0 * t)
        clack = (random.random() * 2.0 - 1.0) * math.exp(-t * 70.0)
        samples.append(env * (0.6 * thump + 0.4 * clack))
    return samples


def synth_player_jump(duration: float = 0.10) -> List[float]:
    """Kinematic upward frequency sweep for player jump."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        env = math.sin(math.pi * (t / duration)) ** 0.5
        freq = 220.0 + (440.0 - 220.0) * (t / duration)
        sig = math.sin(2.0 * math.pi * freq * t)
        samples.append(env * sig * 0.45)
    return samples


def synth_player_land(duration: float = 0.09) -> List[float]:
    """Low gravel thud impact for landing."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        env = math.exp(-t * 35.0)
        thud = math.sin(2.0 * math.pi * 90.0 * t)
        gravel = (random.random() * 2.0 - 1.0) * 0.3 * math.exp(-t * 50.0)
        samples.append(env * (0.7 * thud + gravel))
    return samples


def synth_player_slide(duration: float = 0.25) -> List[float]:
    """Friction gravel slide rumble."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        env = math.sin(math.pi * (t / duration))
        # Filtered pink/brown noise
        rumble = (random.random() * 2.0 - 1.0) * 0.35
        tone = 0.25 * math.sin(2.0 * math.pi * 110.0 * t)
        samples.append(env * (rumble + tone))
    return samples


def synth_player_hurt(duration: float = 0.18) -> List[float]:
    """Impact damage thud."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        env = math.exp(-t * 18.0)
        thud = math.sin(2.0 * math.pi * (140.0 - 70.0 * (t / duration)) * t)
        noise = (random.random() * 2.0 - 1.0) * 0.25 * math.exp(-t * 25.0)
        samples.append(env * (0.8 * thud + noise))
    return samples


def synth_enemy_telegraph(duration: float = 0.30) -> List[float]:
    """Menacing Core drone windup charge hum (300 Hz to 750 Hz)."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        env = min(1.0, t / 0.05) * math.exp(-max(0.0, t - 0.22) * 20.0)
        freq = 300.0 + (750.0 - 300.0) * (t / duration) ** 2
        sig = math.sin(2.0 * math.pi * freq * t)
        vibrato = math.sin(2.0 * math.pi * 15.0 * t) * 0.15
        samples.append(env * (sig + vibrato) * 0.5)
    return samples


def synth_boss_mortar_launch(duration: float = 0.38) -> List[float]:
    """Heavy Greenkeeper pneumatic mortar thump and pressure hiss."""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = float(i) / SAMPLE_RATE
        env = math.exp(-t * 9.0)
        # Deep 80 Hz explosive punch
        punch = math.sin(2.0 * math.pi * 80.0 * t) * math.exp(-t * 20.0)
        # Pneumatic hiss
        hiss = (random.random() * 2.0 - 1.0) * 0.35 * math.exp(-t * 12.0)
        samples.append(env * (0.75 * punch + hiss))
    return samples


GENERATORS: Dict[str, Tuple[Callable[[], List[float]], str]] = {
    "maser_tap.wav": (synth_maser_tap, "1420 MHz waveguide maser tap fire sound"),
    "maser_charge.wav": (synth_maser_charge, "Charged plasma beam discharge sound"),
    "impact_spark.wav": (synth_impact_spark, "Metallic beam ricochet impact sound"),
    "alarm_lock.wav": (synth_alarm_lock, "Two-tone target lock threat alert warning"),
    "station_chime.wav": (synth_station_chime, "Analog terminal console acknowledge chime"),
    "printer_chatter.wav": (synth_printer_chatter, "Mechanical teleprinter printhead strike click"),
    "player_jump.wav": (synth_player_jump, "Kinematic player jump impulse"),
    "player_land.wav": (synth_player_land, "Gravel ground contact landing impact"),
    "player_slide.wav": (synth_player_slide, "Kinematic slide-kick ground friction rumble"),
    "player_hurt.wav": (synth_player_hurt, "Player damage impact thud"),
    "enemy_telegraph.wav": (synth_enemy_telegraph, "Core reconnaissance drone lock-on telegraph hum"),
    "boss_mortar_launch.wav": (synth_boss_mortar_launch, "Greenkeeper pneumatic mortar launch artillery thump"),
}


def build_all_sfx() -> Dict[str, Any]:
    """Synthesize and export all 12 sound effects with checksum manifest."""
    ensure_audio_dir()
    manifest_entries = {}

    for filename, (gen_func, desc) in GENERATORS.items():
        out_path = AUDIO_DIR / filename
        samples = gen_func()
        write_wav(out_path, samples)

        sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
        manifest_entries[filename] = {
            "file": filename,
            "description": desc,
            "sample_rate": SAMPLE_RATE,
            "channels": 1,
            "bit_depth": 16,
            "duration_seconds": round(len(samples) / SAMPLE_RATE, 3),
            "sha256": sha,
            "size_bytes": out_path.stat().st_size,
        }
        print(f"Generated {filename}: {manifest_entries[filename]['duration_seconds']}s ({manifest_entries[filename]['size_bytes']} bytes)")

    # Write audio manifest
    manifest_data = {
        "schema_version": 1,
        "description": "6EQUJ5 audio sound effect bank and provenance manifest",
        "sample_rate": SAMPLE_RATE,
        "sound_effects": manifest_entries,
        "music_tracks": {
            "Static_Bloom.mp3": {
                "role": "bunker_and_lab_ambient",
                "loop": True,
                "fade_ms": 1000
            },
            "Echoes_of_the_Static_Void.mp3": {
                "role": "field_ops_and_boss_combat",
                "loop": True,
                "fade_ms": 1200
            }
        }
    }

    manifest_path = AUDIO_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"Saved audio manifest: {manifest_path.name}")
    return manifest_data


if __name__ == "__main__":
    build_all_sfx()
