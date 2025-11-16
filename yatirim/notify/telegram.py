import requests, os

TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

def gonder(metin, disable_preview=True):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {
        "chat_id": CHAT_ID,
        "text": metin,
        "parse_mode": "Markdown",
        "disable_web_page_preview": disable_preview
    }
    requests.post(url, params=params, timeout=10)
