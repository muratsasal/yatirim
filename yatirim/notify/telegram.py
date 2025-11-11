import os, requests
TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")
API = f"https://api.telegram.org/bot{TOKEN}/sendMessage" if TOKEN else None

def gonder(metin: str):
    if not (TOKEN and CHAT_ID and metin): return
    try:
        requests.post(API, json={"chat_id": CHAT_ID, "text": metin, "parse_mode": "Markdown"}, timeout=12)
    except Exception:
        pass
