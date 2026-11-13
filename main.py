
import json
import sys
import urllib.error
import urllib.request


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
    return [history[0], *history[-(MAX_TURNS * 2) :]]


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


def main():
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

        history.append({"role": "user", "content": command})
        print("JARVIS: ", end="", flush=True)

        try:
            answer = ask_jarvis(history)
            history.append({"role": "assistant", "content": answer})
            history = trimmed_history(history)
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


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nUnexpected JARVIS error: {error}", file=sys.stderr)
        sys.exit(1)
