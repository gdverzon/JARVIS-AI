
import json
import argparse
import sys
import urllib.error
import urllib.request

from computer_control import handle_computer_command


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:1.7b"
MAX_TURNS = 6
SYSTEM_PROMPT = (
    "You are JARVIS, a private personal AI assistant running locally on the user's "
    "computer. Be concise, practical, and honest. Ask before suggesting destructive "
    "computer actions."
)


def trimmed_history(history):
    """Keep the system prompt plus only the most recent conversation turns."""
    return [history[0], *history[1:][-(MAX_TURNS * 2) :]]


def ask_jarvis(history):
    payload = json.dumps(
        {
            "model": MODEL,
            "messages": trimmed_history(history),
            "stream": True,
            "options": {"temperature": 0.6, "num_ctx": 4096},
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    answer_parts = []
    with urllib.request.urlopen(request, timeout=180) as response:
        for raw_line in response:
            if not raw_line.strip():
                continue
            chunk = json.loads(raw_line)
            text = chunk.get("message", {}).get("content", "")
            if text:
                answer_parts.append(text)
                print(text, end="", flush=True)

    print()
    return "".join(answer_parts)


def print_help():
    print(
        "Commands:\n"
        "  /clear  Forget this conversation\n"
        "  /model  Show the active local model\n"
        "  /help   Show these commands\n"
        "  /exit   Quit JARVIS"
    )


def run_turn(command, history, speak=None):
    """Handle one command and return the updated conversation history."""
    control_reply = handle_computer_command(command)
    if control_reply is not None:
        print(f"JARVIS: {control_reply}")
        if speak:
            speak(control_reply)
        return history

    history.append({"role": "user", "content": command})
    print("JARVIS: ", end="", flush=True)
    try:
        answer = ask_jarvis(history)
        history.append({"role": "assistant", "content": answer})
        history = trimmed_history(history)
        if speak:
            speak(answer)
    except urllib.error.URLError as error:
        history.pop()
        reason = getattr(error, "reason", error)
        print(
            "\nCould not reach Ollama. Start it and verify that "
            f"'{MODEL}' is installed. Details: {reason}"
        )
    except (json.JSONDecodeError, KeyError) as error:
        history.pop()
        print(f"\nOllama returned an unexpected response: {error}")
    return history


def run_text_mode(speak=None):
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    print(f"JARVIS is online using {MODEL}. Type /help for commands.")

    while True:
        try:
            command = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJARVIS: Shutting down.")
            return

        if not command:
            continue
        if command.lower() in {"exit", "quit", "/exit"}:
            print("JARVIS: Shutting down.")
            return
        if command.lower() == "/clear":
            history = [history[0]]
            print("JARVIS: Conversation cleared.")
            continue
        if command.lower() == "/model":
            print(f"JARVIS: The active model is {MODEL}.")
            continue
        if command.lower() == "/help":
            print_help()
            continue

        history = run_turn(command, history, speak=speak)


def run_chat_voice_mode():
    from voice import OfflineVoice, VoiceSetupError

    try:
        voice = OfflineVoice()
        voice.check_speech_setup()
    except VoiceSetupError as error:
        print(f"Voice setup error: {error}", file=sys.stderr)
        return 1
    print("Chat + voice mode: type your messages and JARVIS will speak his replies.")
    return run_text_mode(speak=voice.speak)


def run_voice_mode():
    from voice import OfflineVoice, VoiceSetupError

    try:
        voice = OfflineVoice()
        voice.check_setup()
    except VoiceSetupError as error:
        print(f"Voice setup error: {error}", file=sys.stderr)
        return 1

    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("JARVIS voice mode is online. Press Enter to record, or type /exit.")
    while True:
        try:
            action = input("\nPress Enter to speak: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJARVIS: Shutting down.")
            return 0
        if action.lower() in {"exit", "quit", "/exit"}:
            print("JARVIS: Shutting down.")
            return 0
        try:
            command = voice.listen()
        except VoiceSetupError as error:
            print(f"Voice error: {error}")
            continue
        if not command:
            print("JARVIS: I did not hear anything clearly.")
            continue
        print(f"You: {command}")
        if command.lower() in {"exit", "quit", "goodbye", "shut down jarvis"}:
            voice.speak("Shutting down.")
            return 0
        history = run_turn(command, history, speak=voice.speak)


def choose_mode():
    print(
        "JARVIS interface:\n"
        "  1. Chat (type messages)\n"
        "  2. Chat + voice (type messages, hear replies)\n"
        "  3. Full voice (speak through your microphone)\n"
        "  Q. Quit"
    )
    while True:
        try:
            choice = input("Choose an option [1]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nJARVIS: Shutting down.")
            return None
        if choice in {"", "1", "chat", "text"}:
            return "chat"
        if choice in {"2", "chat voice", "chat + voice", "hybrid"}:
            return "chat-voice"
        if choice in {"3", "voice", "full voice"}:
            return "voice"
        if choice in {"q", "quit", "exit"}:
            return None
        print("Please choose 1, 2, 3, or Q to quit.")


def main():
    parser = argparse.ArgumentParser(description="Private local JARVIS assistant")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--voice", action="store_true", help="use offline Whisper and Piper voice mode"
    )
    mode.add_argument(
        "--chat", action="store_true", help="use the typed terminal chat interface"
    )
    mode.add_argument(
        "--chat-voice",
        action="store_true",
        help="type messages and hear JARVIS speak each reply",
    )
    args = parser.parse_args()
    if args.voice:
        selected_mode = "voice"
    elif args.chat:
        selected_mode = "chat"
    elif args.chat_voice:
        selected_mode = "chat-voice"
    else:
        selected_mode = choose_mode()

    if selected_mode == "voice":
        return run_voice_mode()
    if selected_mode == "chat-voice":
        return run_chat_voice_mode()
    if selected_mode == "chat":
        return run_text_mode()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except Exception as error:
        print(f"\nUnexpected JARVIS error: {error}", file=sys.stderr)
        sys.exit(1)
