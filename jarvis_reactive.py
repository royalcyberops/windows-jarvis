"""Reactive JARVIS turn: HEAR text -> THINK (qwen-fast) -> SAY (ElevenLabs) -> ACT (returns JSON for caller).
Stdlib only. Key read from HKCU\\Environment (setx), never from chat/files.
Usage: python jarvis_reactive.py "open youtube"  -> speaks reply, prints ACTION json last line.
"""
import json, os, re, subprocess, sys, urllib.request, winreg, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "skills-py"))
from sys_status import ram, wish, disk, now
from youtube import open_home, search as yt_search
from run_store import start as run_start, finish as run_finish

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("JARVIS_MODEL", "qwen3:4b")
GEORGE = "JBFqnCBsd6RMkjVDRZzb"

def reg_key():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
        v, _ = winreg.QueryValueEx(k, "ELEVENLABS_API_KEY")
        return v

def ollama_chat(user_text):
    sys_prompt = ("You are JARVIS, Windows reactive butler. Reply as JSON only: "
                  '{"say": "<one short spoken sentence>", "action": "<CLICK n | TYPE text | OPEN app | SAY | WAIT | DONE | BLOCKED>"} '
                  "Keep say under 20 words. No thinking trace.")
    body = json.dumps({"model": MODEL, "stream": False, "think": False,
                       "options": {"num_ctx": 4096},
                       "messages": [{"role": "system", "content": sys_prompt},
                                    {"role": "user", "content": user_text}]}).encode()
    req = urllib.request.Request(OLLAMA_URL + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        out = json.load(r)
    txt = out["message"]["content"].strip()
    m = re.search(r"\{.*\}", txt, re.S)
    raw = m.group(0) if m else json.dumps({"say": txt[:160], "action": "SAY"})
    try:
        return json.loads(raw)
    except Exception:
        return {"say": txt[:160], "action": "SAY"}

def speak(text):
    key = reg_key()
    body = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{GEORGE}",
        data=body, headers={"Content-Type": "application/json", "xi-api-key": key})
    with urllib.request.urlopen(req, timeout=60) as r:
        audio = r.read()
    fd, path = tempfile.mkstemp(prefix="jarvis-", suffix=".mp3")
    os.close(fd)
    open(path, "wb").write(audio)
    os.startfile(path)  # plays in Media Player
    return path

def local_intent(heard):
    h = heard.lower().strip()
    if h.startswith("search youtube for "):
        q = heard[len("search youtube for "):].strip() or "music"
        return yt_search(q), "OPEN youtube-search"
    if h == "open youtube" or h.startswith("open youtube"):
        return open_home(), "OPEN youtube"
    if "status report" in h or h in ("status", "system status", "how is my computer"):
        return wish() + " " + disk() + " " + now(), "SAY status"
    if "what time" in h or h == "time":
        return now(), "SAY time"
    if "disk" in h:
        return disk(), "SAY disk"
    if h in ("hello jarvis", "hello", "are you there"):
        return "At your service, sir.", "SAY hello"
    return None

def main():
    heard = " ".join(sys.argv[1:]).strip() or "Hello JARVIS"
    rid = run_start(heard, "jarvis")
    hit = local_intent(heard)
    if hit:
        say, action = hit
    else:
        try:
            turn = ollama_chat(heard)
            say, action = turn.get("say", "Yes, sir."), turn.get("action", "SAY")
        except Exception as e:
            say, action = f"Brain busy, sir. {ram()}.", "SAY fallback"
    print(f"HEARD: {heard}")
    print(f"SAY: {say}")
    try:
        mp3 = speak(say)
        print(f"AUDIO: {mp3}")
    except Exception as e:
        print(f"AUDIO-FAILED: {e}")
    try:
        run_finish(rid, "succeeded", event=action[:120])
    except Exception:
        pass
    print("ACTION " + json.dumps({"action": action, "heard": heard, "said": say}))

if __name__ == "__main__":
    main()
