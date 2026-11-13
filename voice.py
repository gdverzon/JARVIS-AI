"""Offline microphone, Whisper.cpp transcription, and Piper speech output."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import wave
import winsound


ROOT = Path(__file__).resolve().parent
WHISPER_EXE = Path(os.getenv("JARVIS_WHISPER_EXE", ROOT / "tools/whisper/whisper-cli.exe"))
WHISPER_MODEL = Path(
    os.getenv("JARVIS_WHISPER_MODEL", ROOT / "models/whisper/ggml-base.en.bin")
)
PIPER_VOICE = os.getenv("JARVIS_PIPER_VOICE", "en_GB-alan-medium")
PIPER_DATA = Path(os.getenv("JARVIS_PIPER_DATA", ROOT / "models/piper"))
SAMPLE_RATE = 16_000
RECORD_SECONDS = 6


class VoiceSetupError(RuntimeError):
    pass


class OfflineVoice:
    def check_speech_setup(self):
        try:
            import piper  # noqa: F401
        except ImportError as error:
            raise VoiceSetupError(
                "Install voice dependencies with: python -m pip install -r requirements-voice.txt"
            ) from error
        voice_model = PIPER_DATA / f"{PIPER_VOICE}.onnx"
        if not voice_model.is_file():
            raise VoiceSetupError(
                f"Piper voice was not found. Run: python -m piper.download_voices "
                f"--data-dir \"{PIPER_DATA}\" {PIPER_VOICE}"
            )

    def check_setup(self):
        self.check_speech_setup()
        try:
            import numpy  # noqa: F401
            import sounddevice  # noqa: F401
        except ImportError as error:
            raise VoiceSetupError(
                "Install voice dependencies with: python -m pip install -r requirements-voice.txt"
            ) from error
        if not WHISPER_EXE.is_file():
            raise VoiceSetupError(f"Whisper CLI was not found at {WHISPER_EXE}")
        if not WHISPER_MODEL.is_file():
            raise VoiceSetupError(f"Whisper model was not found at {WHISPER_MODEL}")

    def listen(self):
        import sounddevice as sd

        print(f"Listening for {RECORD_SECONDS} seconds...")
        try:
            audio = sd.rec(
                int(RECORD_SECONDS * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
            )
            sd.wait()
        except Exception as error:
            raise VoiceSetupError(f"Microphone recording failed: {error}") from error

        with tempfile.TemporaryDirectory(prefix="jarvis-") as temp_dir:
            wav_path = Path(temp_dir) / "speech.wav"
            output_base = Path(temp_dir) / "transcript"
            with wave.open(str(wav_path), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(SAMPLE_RATE)
                wav_file.writeframes(audio.tobytes())

            result = subprocess.run(
                [
                    str(WHISPER_EXE), "-m", str(WHISPER_MODEL), "-f", str(wav_path),
                    "-otxt", "-of", str(output_base), "-nt", "-np",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            transcript_path = output_base.with_suffix(".txt")
            if result.returncode != 0 or not transcript_path.exists():
                details = result.stderr.strip() or "no transcript was created"
                raise VoiceSetupError(f"Whisper failed: {details}")
            return transcript_path.read_text(encoding="utf-8").strip()

    def speak(self, text):
        if not text.strip():
            return
        with tempfile.TemporaryDirectory(prefix="jarvis-") as temp_dir:
            wav_path = Path(temp_dir) / "reply.wav"
            result = subprocess.run(
                [
                    sys.executable, "-m", "piper", "--data-dir", str(PIPER_DATA),
                    "-m", PIPER_VOICE, "--length-scale", "1.08",
                    "--sentence-silence", "0.18", "-f", str(wav_path), "--", text,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                print(f"Piper speech error: {result.stderr.strip()}")
                return
            winsound.PlaySound(str(wav_path), winsound.SND_FILENAME)
