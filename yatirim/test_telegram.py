import os, requests
TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

print("TOKEN:", TOKEN[:10] if TOKEN else "YOK")
print("CHAT_ID:", CHAT_ID)

if TOKEN and CHAT_ID:
    msg = "🧪 GitHub Actions test mesajı — bağlantı kontrolü başarılı!"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    print("Durum:", r.status_code, r.text)
else:
    print("❌ TOKEN veya CHAT_ID bulunamadı.")
