import os, requests
TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")
API = f"https://api.telegram.org/bot{TOKEN}/sendMessage" if TOKEN else None

import requests, os

def gonder(metin, disable_preview=False):
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    if not token or not chat_id:
        print("Telegram bilgileri eksik.")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": metin,
        "parse_mode": "Markdown",
        "disable_web_page_preview": str(disable_preview).lower()
    }
    try:
        requests.post(url, params=params, timeout=10)
    except Exception as e:
        print("Telegram gönderim hatası:", e)
