# Local JARVIS

A lightweight, private, text-based assistant that runs through Ollama. It is tuned
for a computer with 8 GB RAM and integrated graphics.

## Requirements

- Python 3.10 or newer
- Ollama
- The `qwen3:1.7b` model

## Run

```powershell
ollama pull qwen3:1.7b
python main.py
```

The startup menu lets you choose typed chat, typed chat with spoken replies, or
full offline voice. To skip the menu, use one of these commands:

```powershell
python main.py --chat
python main.py --chat-voice
python main.py --voice
```

The assistant streams its response and remembers the last six conversation turns.
Use `/clear` to reset its memory, `/model` to see the active model, and `/exit` to
quit.

## Offline voice mode

Voice mode uses the CPU-only Whisper.cpp `base.en` model for speech recognition,
Piper's British male `en_GB-alan-medium` voice for speech output, and your default
Windows microphone. From PowerShell, run
the one-time setup and then start voice mode:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_voice.ps1
python main.py --voice
```

Press Enter and speak for up to six seconds. Models and voice binaries are stored
under `models/` and `tools/`; both folders are excluded from Git because their
contents are large and can be downloaded again.

You can override the defaults with `JARVIS_WHISPER_EXE`,
`JARVIS_WHISPER_MODEL`, `JARVIS_PIPER_VOICE`, and `JARVIS_PIPER_DATA` environment
variables.

## Safe computer commands

The following phrases are recognized before a prompt reaches the language model:

- `open calculator`, `open notepad`, `open file explorer`, or `open settings`
- `what time is it` or `what is the date`
- `system status` or `disk space`
- `lock my computer` (requires typed confirmation)

JARVIS never turns model output into shell commands. Adding a new action requires
an explicit entry in `computer_control.py`.

## Hardware notes

`qwen3:1.7b` is the recommended default for 8 GB RAM. Larger models may be slower
or force Windows to use the page file. Close memory-heavy applications while using
JARVIS, and avoid running more than one model at once.

## Sensible next upgrades

1. Add voice activity detection so recording stops automatically.
2. Keep Piper loaded as a local service to reduce response latency.
3. Store long-term facts in SQLite only after the core assistant is stable.
