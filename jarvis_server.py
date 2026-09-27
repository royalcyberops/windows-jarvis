"""Always-on JARVIS server. Stdlib only. 127.0.0.1 only.
GET  /            -> active voice page
POST /hear {text} -> local intent or qwen-fast -> ElevenLabs speak -> {say, action, audio}
GET  /audio/<f>   -> mp3
GET  /runs        -> recent runs (active listing)
Run: python jarvis_server.py  (then open http://127.0.0.1:8341)
"""
import json, os, sys, tempfile, threading, traceback, urllib.request, winreg
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ERRLOG = os.path.join(os.path.dirname(__file__), "server-errors.log")

def log_err(where, e):
    try:
        with open(ERRLOG, "a", encoding="utf-8") as f:
            import datetime
            f.write(f"\n[{datetime.datetime.now()}] {where}: {e}\n{traceback.format_exc()}\n")
    except Exception:
        pass

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "skills-py"))
from sys_status import ram, wish, disk, now
from youtube import open_home, search as yt_search
from run_store import start as run_start, finish as run_finish, conn

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("JARVIS_MODEL", "qwen3:4b")
GEORGE = "JBFqnCBsd6RMkjVDRZzb"
HOST, PORT = "127.0.0.1", 8341
AUDIO_DIR = os.path.join(tempfile.gettempdir(), "jarvis-audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

def reg_key():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
        v, _ = winreg.QueryValueEx(k, "ELEVENLABS_API_KEY")
        return v

def think_fallback(heard):
    sys_prompt = ("You are JARVIS, Windows reactive butler. JSON only: "
                  '{"say": "<<=20 words>", "action": "<SAY|WAIT|DONE|BLOCKED>"} No thinking trace.')
    body = json.dumps({"model": MODEL, "stream": False, "think": False,
                       "options": {"num_ctx": 4096},
                       "messages": [{"role": "system", "content": sys_prompt},
                                    {"role": "user", "content": heard}]}).encode()
    req = urllib.request.Request(OLLAMA_URL + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=100) as r:
        txt = json.load(r)["message"]["content"].strip()
    import re
    m = re.search(r"\{.*\}", txt, re.S)
    try:
        return json.loads(m.group(0) if m else txt)
    except Exception:
        return {"say": txt[:160], "action": "SAY"}

def decide(heard):
    h = heard.lower().strip()
    if h.startswith("search youtube for "):
        q = heard[len("search youtube for "):].strip() or "music"
        return yt_search(q), "OPEN youtube-search"
    if h.startswith("open youtube"):
        return open_home(), "OPEN youtube"
    if "status report" in h or h in ("status", "system status"):
        return wish() + " " + disk() + " " + now(), "SAY status"
    if "what time" in h or h == "time":
        return now(), "SAY time"
    if h in ("hello jarvis", "hello", "are you there", "hi"):
        return "At your service, sir. I am listening.", "SAY hello"
    t = think_fallback(heard)
    return t.get("say", "Yes, sir.")[:300], t.get("action", "SAY")

def speak(text):
    key = reg_key()
    body = json.dumps({"text": text[:500]}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{GEORGE}",
        data=body, headers={"Content-Type": "application/json", "xi-api-key": key})
    with urllib.request.urlopen(req, timeout=60) as r:
        audio = r.read()
    fd, path = tempfile.mkstemp(prefix="jv-", suffix=".mp3", dir=AUDIO_DIR)
    os.close(fd)
    open(path, "wb").write(audio)
    return os.path.basename(path)

PAGE = os.path.join(HERE, "voice_active.html")

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass
    def _send(self, code, body, ctype="application/json"):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        if self.path == "/":
            with open(PAGE, "rb") as f:
                self._send(200, f.read(), "text/html")
        elif self.path.startswith("/audio/"):
            name = os.path.basename(self.path)
            p = os.path.join(AUDIO_DIR, name)
            if os.path.exists(p):
                with open(p, "rb") as f:
                    self._send(200, f.read(), "audio/mpeg")
            else:
                self._send(404, "no audio")
        elif self.path == "/runs":
            c = conn()
            rows = c.execute("SELECT id,prompt,project,status,updated FROM runs ORDER BY id DESC LIMIT 15").fetchall()
            c.close()
            self._send(200, json.dumps([{"id": r[0], "prompt": r[1], "project": r[2], "status": r[3]} for r in rows]))
        else:
            self._send(404, "not found")
    def do_POST(self):
        if self.path != "/hear":
            return self._send(404, "not found")
        n = int(self.headers.get("Content-Length", 0))
        heard = json.loads(self.rfile.read(n) or b"{}").get("text", "").strip()[:300]
        if not heard:
            return self._send(400, json.dumps({"error": "empty"}))
        rid = run_start(heard, "jarvis-voice")
        try:
            say, action = decide(heard)
            audio = speak(say)
            run_finish(rid, "succeeded", event=action[:120])
            self._send(200, json.dumps({"say": say, "action": action, "audio": "/audio/" + audio, "run": rid}))
        except Exception as e:
            log_err("POST /hear", e)
            try:
                run_finish(rid, "failed", event=str(e)[:120])
            except Exception:
                pass
            self._send(500, json.dumps({"error": str(e)[:200]}))

if __name__ == "__main__":
    print(f"JARVIS active on http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()
