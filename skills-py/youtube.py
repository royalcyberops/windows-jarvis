"""Light YouTube skill — stdlib only. Port of youtube.py (fixed 64-bit Chrome, no hardcoded x86)."""
import os, urllib.parse, webbrowser

CANDIDATES = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]

def _browser():
    for p in CANDIDATES:
        if os.path.exists(p):
            webbrowser.register("jarvis-chrome", None, webbrowser.BackgroundBrowser(p))
            return "jarvis-chrome"
    return None

def open_home():
    b = _browser()
    (webbrowser.get(b) if b else webbrowser).open_new_tab("https://youtube.com")
    return "YouTube home opening, sir."

def search(q):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(q)
    b = _browser()
    (webbrowser.get(b) if b else webbrowser).open_new_tab(url)
    return f"Searching YouTube for {q}, sir."
