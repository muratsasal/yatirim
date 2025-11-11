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
    payload = {
        "chat_id": chat_id,
        "text": metin,
        "parse_mode": "Markdown",
        "disable_web_page_preview": disable_preview
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print("Telegram gönderim hatası:", r.text)
    except Exception as e:
        print("Telegram bağlantı hatası:", e)
