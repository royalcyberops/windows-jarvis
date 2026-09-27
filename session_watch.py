"""Windows session_watch — which sessions need you? Port of session_watch.py.
Polls `ollama ps` (models) + run_store running rows. No AppleScript.
States: needs-you (run stuck >10m or ollama error), working, idle.
"""
import subprocess, time
from run_store import needs_attention

def ollama_ps():
    try:
        out = subprocess.check_output(["ollama", "ps"], text=True, timeout=10)
        return out.strip()
    except Exception as e:
        return f"ollama ps failed: {e}"

def main():
    print("== ollama ==")
    print(ollama_ps())
    print("== runs needing attention ==")
    rows = needs_attention()
    if not rows:
        print("idle — nothing running")
    for rid, prompt, project, status in rows:
        print(f"[{status}] run {rid} ({project}): {prompt[:100]}")

if __name__ == "__main__":
    main()
