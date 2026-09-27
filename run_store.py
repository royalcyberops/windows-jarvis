"""Windows JARVIS run_store — every job is a SQLite row with terminal state. Port of run_store.py."""
import sqlite3, os, time, json

DB = os.path.join(os.path.dirname(__file__), "runs.db")
TERMINAL = ("succeeded", "failed", "timed_out", "cancelled")

def conn():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS runs
      (id INTEGER PRIMARY KEY, prompt TEXT, project TEXT, status TEXT,
       tokens INTEGER DEFAULT 0, cost_note TEXT DEFAULT '', events TEXT DEFAULT '[]',
       created REAL, updated REAL)""")
    return c

def start(prompt, project="default"):
    c = conn()
    now = time.time()
    cur = c.execute("INSERT INTO runs (prompt,project,status,created,updated) VALUES (?,?,?, ?,?)",
                    (prompt, project, "running", now, now))
    rid = cur.lastrowid
    c.commit(); c.close()
    return rid

def finish(rid, status, tokens=0, event=""):
    assert status in TERMINAL, f"must be terminal, got {status}"
    c = conn()
    row = c.execute("SELECT events FROM runs WHERE id=?", (rid,)).fetchone()
    ev = json.loads(row[0]) if row else []
    if event:
        ev.append({"t": time.time(), "e": event})
    c.execute("UPDATE runs SET status=?, tokens=?, events=?, updated=? WHERE id=?",
              (status, tokens, json.dumps(ev), time.time(), rid))
    c.commit(); c.close()

def needs_attention():
    c = conn()
    rows = c.execute("SELECT id,prompt,project,status FROM runs WHERE status IN ('running') ORDER BY updated DESC LIMIT 20").fetchall()
    c.close()
    return rows

if __name__ == "__main__":
    rid = start("test run", "jarvis")
    finish(rid, "succeeded", tokens=0, event="smoke test")
    print(f"ok run {rid}")
