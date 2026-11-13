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

The assistant streams its response and remembers the last six conversation turns.
Use `/clear` to reset its memory, `/model` to see the active model, and `/exit` to
quit.

## Hardware notes

`qwen3:1.7b` is the recommended default for 8 GB RAM. Larger models may be slower
or force Windows to use the page file. Close memory-heavy applications while using
JARVIS, and avoid running more than one model at once.

## Sensible next upgrades

1. Add offline speech-to-text with `whisper.cpp` using a tiny or base model.
2. Add offline text-to-speech with Piper.
3. Add a small, allow-listed set of computer tools (open an app, tell the time,
   create a note). Require confirmation before destructive actions.
4. Store long-term facts in SQLite only after the text assistant is stable.
