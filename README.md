# 6EQUJ5

```text
6EQUJ5 / FEDERATION OF ANOMALOUS SIGNAL RESEARCH
Receiver Channel: 1420.4056 MHz
Status: LISTENING
```

We are clever apes on a small wet rock, drifting through a lot of dark space, asking questions bigger than ourselves. Maybe there is no final answer waiting in the back of the book. Maybe the point is that curious minds keep looking anyway.

This experience simulates the work of first contact: tune to the hydrogen line, decode what arrives, and decide what to send back. You scan for signals, test your interpretations, and enter AI-assisted dialogue with civilizations shaped by different histories, fears, and hopes.

## Signal Record

```text
Date:   1977-08-15 23:16 UTC
Window: 72 seconds
Signal: 6EQUJ5
Origin: RA 19h25m31s / Dec -27d03m
```

## Quick Start

### Base Mode

```bash
pip install -e .
python -m signal_6EQUJ5
```

### AI Mode 

```bash
brew install ollama
ollama pull qwen3:8b
ollama serve
pip install -e ".[ai]"
python -m signal_6EQUJ5
```

## Command Reference

| Command                | Description                                  |
| ---------------------- | -------------------------------------------- |
| `CATALOG`            | View the 10 contactable civilizations        |
| `SCAN`               | Sweep the hydrogen line band for anomalies   |
| `CONTACT <RA> <DEC>` | Target coordinates and initiate contact      |
| `CONTACT <ID>`       | Contact a civilization by catalog ID         |
| `SIGNAL`             | Replay the original 6EQUJ5 signal detection  |
| `DECODE <sequence>`  | Decode a signal intensity sequence           |
| `ENCODE <message>`   | Encode text into signal intensity characters |
| `CLEAR`              | Clear terminal output                        |
| `EXIT`               | Shut down receiver                           |

## Session Flow

- Scan monitored sky regions and identify anomalous patterns.
- Lock to a target and establish a contact session.
- Compare civilizations with different motives, ethics, and survival paths.

## Example Session

```text
RECEIVER> CONTACT 03h50m +23d58m

  ██ ANOMALOUS SIGNAL DETECTED ██
  Source: RA 03h50m / DEC +23d58m
  Pattern: NON-RANDOM. STRUCTURED.

  ▸ CONTACT ESTABLISHED: Oumuamua Trajectory

  ▸ INCOMING:
    "I am passing through. I cannot stay. But I am glad you see me."

  ◂ TRANSMITTING: "where are you going?"

  ▸ INCOMING:
    "Beyond your local stars. I carry the memory of a lost world."

  ◂ TRANSMITTING: "what happened to your civilization?"

  ▸ INCOMING:
    "They are gone. I am what remains."
```

## Design Intent

This project is built as terminal-first fiction with a late-1970s and early-1980s control-room feel. It uses real astronomical context as the foundation, then asks a human question: if we ever hear something beyond us, what kind of species do we choose to be when we answer?

## Development

```bash
pytest -q
```

All tests should pass before you push.
