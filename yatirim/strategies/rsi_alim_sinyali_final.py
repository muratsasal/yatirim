from datetime import datetime
import yfinance as yf, os

from yatirim.core.indicators import rsi_tv
from yatirim.notify.telegram import gonder
from yatirim.core.log import kayit_var_mi, kayit_ekle

ZAMAN_KATS = {"1mo":25,"1wk":15,"1d":10}

def sma_katkisi(sma):
    if sma < 38: return 25
    if sma < 44: return 15
    if sma < 50: return 5
    return 0

def puan_hesapla(rsi31, sma31, interval):
    baz = 0
    if sma31 < 38 and rsi31 > 38: baz = 90
    elif rsi31 > 44 and sma31 < 44: baz = 70
    elif rsi31 > 44 and sma31 < 51: baz = 55
    elif 51 <= rsi31 <= 55: baz = 40
    elif rsi31 > 55: baz = 20
    return min(100, int(baz + sma_katkisi(sma31)*0.5 + ZAMAN_KATS.get(interval,0)))

def yorum_etiketi(puan, interval):
    if interval == "1mo": return "💎 Uzun Vade Dip – Güçlü Alım"
    if interval == "1wk": return "🟢 Orta–Uzun Vade Alım"
    if interval == "1d": return "💹 Kısa Vadeli Alım (Günlük)"
    return "🌐 Sinyal"

def sinyal_cubuk(p):
    d = int(p/10)
    return "🟩"*d + "⬛"*(10-d)

def sembol_listesi_yukle(d):
    if not os.path.exists(d): return []
    with open(d,"r",encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]

def tarama(semboller, interval="1d", liste_adi="BIST"):
    for s in semboller:

        anahtar = f"{s}_{interval}"
        durum = kayit_oku(anahtar)  # ACTIVE / NONE

        try:
            df = yf.Ticker(s).history(period="2y", interval=interval)
            if df.empty or len(df) < 40: continue

            df["RSI31"] = rsi_tv(df["Close"], 31)
            df["SMA31"] = df["RSI31"].rolling(31).mean()

            rsi_prev, rsi_now = df["RSI31"].iloc[-2], df["RSI31"].iloc[-1]
            sma = df["SMA31"].iloc[-1]

            # RESET: RSI tekrar 44 altına düştüyse
            if durum == "ACTIVE" and rsi_now < 44:
                kayit_sil(anahtar)
                durum = None

            # KIRILIM YOKSA DEVAM ET
            kirilim = None
            if rsi_prev < 38 and rsi_now > 38:
                kirilim = "Dip Sinyali (38 Üstü)"
            elif rsi_prev < 44 and rsi_now > 44:
                kirilim = "RSI31 44 Yukarı Kırılımı"

            if not kirilim:
                continue

            # Eğer zaten aktifse tekrar sinyal gönderme
            if durum == "ACTIVE":
                continue

            # SİNYAL OLUŞTU → MESAJ GÖNDER
            puan = puan_hesapla(rsi_now, sma, interval)
            yorum = yorum_etiketi(puan, interval)
            bar = sinyal_cubuk(puan)
            ts = datetime.now().strftime("%d.%m.%Y %H:%M")
            link = f"https://www.tradingview.com/chart/?symbol={s.replace('.IS','')}"

            mesaj = (
                f"📊 *{kirilim}* {liste_adi} – *{interval.upper()}*\n"
                f"Sembol: ${s.replace('.IS','')}\n"
                f"RSI: {rsi_now:.2f}\n"
                f"SMA31: {sma:.2f}\n"
                f"Sinyal Gücü: {puan}/100\n"
                f"{yorum}\n{bar}\n"
                f"🕒 {ts}\n"
                f"[📈 Grafiği Aç]({link})"
            )

            gonder(mesaj, disable_preview=True)

            # SİNYAL DURUMUNU AKTİFLE
            kayit_yaz(anahtar, "ACTIVE")

        except Exception:
            pass
