"""Windows JARVIS brain — one long-lived Ollama chat, stolen idea from ethanplusai/jarvis brain.py.
Uses ollama/qwen3:4b (qwen-fast), 4096 ctx for speed, think=False.
Stdin transcript loop. Replies split into sentences so voice.html can speak first sentence while rest streams.
Env scrub: never pass ELEVENLABS_API_KEY / ANTHROPIC_* to the model process.
"""
import json, os, re, sys, urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("JARVIS_MODEL", "qwen3:4b")
MEM_INDEX = os.path.join(os.path.dirname(__file__), "memory", "index.md")

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

def scrub_env(env):
    return {k: v for k, v in env.items()
            if not k.startswith("ANTHROPIC_") and k != "ELEVENLABS_API_KEY" and not k.startswith("CLAUDE_CODE_")}

def load_memory_index():
    try:
        with open(MEM_INDEX, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "(no memory yet)"

def chat(messages, think=False):
    body = json.dumps({"model": MODEL, "messages": messages, "stream": False,
                        "think": think, "options": {"num_ctx": 4096}}).encode()
    req = urllib.request.Request(OLLAMA_URL + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.load(r)
    return out["message"]["content"]

def main():
    mem = load_memory_index()
    system = ("You are JARVIS, Windows butler. Concise. Fast subagent qwen3:4b. "
              "Memory index:\n" + mem + "\nNo thinking trace in final output.")
    history = [{"role": "system", "content": system}]
    print("JARVIS ready. Type, Ctrl+C to exit.", flush=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        history.append({"role": "user", "content": line})
        try:
            reply = chat(history)
        except Exception as e:
            print(f"[brain-error] {e}", flush=True)
            continue
        history.append({"role": "assistant", "content": reply})
        sentences = SENT_SPLIT.split(reply.strip())
        for i, s in enumerate(sentences):
            print(f"SAY[{i+1}/{len(sentences)}]: {s.strip()}", flush=True)
        print("DONE", flush=True)

if __name__ == "__main__":
    main()
