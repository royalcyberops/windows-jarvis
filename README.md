# Windows JARVIS (stolen from ethanplusai/jarvis, ported)

Original: macOS + Claude Code + Fish Audio. This port: Windows 11 + Ollama `qwen3:4b` (qwen-fast) + ElevenLabs.

What was stolen and how mapped:
- brain = one long-lived process -> `brain.py` keeps one Ollama chat session alive via `http://localhost:11434/api/chat`, stdin transcript, sentence-split for TTS streaming.
- memory as Markdown folder -> `memory/` one fact per file + `index.md`. Brain always loads index.
- runs as SQLite rows -> `run_store.py`, table `runs` with terminal states only.
- voice -> `voice.html` uses Chrome Web Speech API (works on your Chrome), TTS via ElevenLabs (ELEVENLABS_API_KEY), no Fish.
- session_watch -> `session_watch.py` polls `ollama ps` + opencode sessions, reports NEEDS-YOU / WORKING / IDLE.
- safety -> scrub `ANTHROPIC_*`, `ELEVENLABS_API_KEY` from child env; taint gate: turn that read web/screen/MCP = no acting tools that turn.

Give ElevenLabs key as env var only, never in file:
  setx ELEVENLABS_API_KEY "sk_..."
  restart terminal / opencode after setx.
