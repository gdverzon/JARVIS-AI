"""Small, explicit allow-list of safe local computer commands."""

from datetime import datetime
import ctypes
from pathlib import Path
import shutil
import subprocess


APP_COMMANDS = {
    "open calculator": ["calc.exe"],
    "open notepad": ["notepad.exe"],
    "open file explorer": ["explorer.exe"],
    "open explorer": ["explorer.exe"],
    "open settings": ["cmd.exe", "/c", "start", "", "ms-settings:"],
}


def _system_status():
    total, used, free = shutil.disk_usage(Path.home())
    return (
        f"Your home drive has {free / 2**30:.1f} gigabytes free out of "
        f"{total / 2**30:.1f} gigabytes."
    )


def handle_computer_command(command):
    """Execute only recognized commands; return None for ordinary AI chat."""
    normalized = " ".join(command.lower().strip().rstrip(".?!").split())

    if normalized in {"what time is it", "tell me the time", "time"}:
        return f"It is {datetime.now():%I:%M %p}."
    if normalized in {"what is the date", "tell me the date", "date"}:
        return f"Today is {datetime.now():%A, %B %d, %Y}."
    if normalized in {"system status", "computer status", "disk space"}:
        return _system_status()
    if normalized in APP_COMMANDS:
        try:
            subprocess.Popen(
                APP_COMMANDS[normalized],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return f"Opening {normalized.removeprefix('open ')}."
        except OSError as error:
            return f"I could not open that application: {error}"
    if normalized in {"lock computer", "lock my computer", "lock the computer"}:
        answer = input("JARVIS: Lock the computer now? [y/N]: ").strip().lower()
        if answer in {"y", "yes"}:
            ctypes.windll.user32.LockWorkStation()
            return "Computer locked."
        return "Lock cancelled."
    return None
