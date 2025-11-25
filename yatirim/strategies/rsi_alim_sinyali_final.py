from datetime import datetime
import yfinance as yf, pandas as pd, os, json

from yatirim.core.indicators import rsi
from yatirim.notify.telegram import gonder

# ---------------------------------------------------------
#   GITHUB ACTIONS UYUMLU KAYIT SİSTEMİ
#   (Artık asla hata vermez ve tekrar sinyal göndermez)
# ---------------------------------------------------------

CACHE_FILE = "signal_cache.json"

def cache_yukle():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def cache_kaydet(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)

def cache_kontrol(sembol, interval, bar_tarihi):
    anahtar = f"{sembol}_{interval}"
    return cache.get(anahtar) == bar_tarihi

def cache_ekle(sembol, interval, bar_tarihi):
    anahtar = f"{sembol}_{interval}"
    cache[anahtar] = bar_tarihi
    cache_kaydet(cache)

# ---------------------------------------------------------
# PUANLAMA
# ---------------------------------------------------------

ZAMAN_KATSAYILARI = {"1mo": 25, "1wk": 15, "1d": 10}

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

    puan = baz + sma_katkisi(sma31) * 0.5 + ZAMAN_KATSAYILARI.get(interval, 0)
    return min(100, int(puan))

def yorum_etiketi(puan):
    if puan >= 95: return "💎 Dip Bölgesi – Güçlü Alım"
    if puan >= 80: return "💪 Güçlü Alım Bölgesi"
    if puan >= 65: return "🟢 Orta–Uzun Vade Alım"
    if puan >= 50: return "🟡 İzleme Bölgesi"
    return "🔸 Zayıf Sinyal"

def sinyal_cubuk(puan):
    dolu = int(puan / 10)
    return "🟩" * dolu + "⬛" * (10 - dolu)

# ---------------------------------------------------------
# Sembol listesi yükleme
# ---------------------------------------------------------

def sembol_listesi_yukle(dosya):
    if not os.path.exists(dosya):
        return []
    with open(dosya, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]

# ---------------------------------------------------------
# TARAYICI
# ---------------------------------------------------------

def tarama(semboller, interval, liste_adi):
    bulunan = []
    
    for s in semboller:
        try:
            df = yf.Ticker(s).history(period="2y", interval=interval)
            if df.empty or len(df) < 40:
                continue

            df["RSI31"] = rsi(df["Close"], 31)
            df["SMA31"] = df["RSI31"].rolling(window=31).mean()

            r_prev, r_now = df["RSI31"].iloc[-2], df["RSI31"].iloc[-1]

            # 38 ve 44 kırılımı
            kirilim = False
            tip = None

            if r_prev < 38 < r_now:
                tip = "RSI31 38 Yukarı Kırılımı"
                kirilim = True

            elif r_prev < 44 < r_now:
                tip = "RSI31 44 Yukarı Kırılımı"
                kirilim = True

            if not kirilim:
                continue

            sma_son = df["SMA31"].iloc[-1]
            bar_tarihi = df.index[-1].strftime("%Y-%m-%d")

            # TEKRAR FİLTRESİ
            if cache_kontrol(s, interval, bar_tarihi):
                continue

            # PUAN
            puan = puan_hesapla(r_now, sma_son, interval)
            yorum = yorum_etiketi(puan)
            bar = sinyal_cubuk(puan)

            tv = s.replace(".IS", "")
            link = f"https://www.tradingview.com/chart/?symbol={tv}"
            ts = datetime.now().strftime("%d.%m.%Y %H:%M")

            mesaj = (
                f"📊 *{tip}* {liste_adi} – {interval.upper()}\n"
                f"Sembol: ${tv}\n"
                f"RSI: {r_now:.2f}\n"
                f"SMA31: {sma_son:.2f}\n"
                f"🎯 Sinyal Gücü: {puan}/100\n"
                f"{yorum}\n"
                f"{bar}\n"
                f"🕒 {ts}\n"
                f"[📈 Grafiği Aç]({link})"
            )

            gonder(mesaj, disable_preview=True)
            cache_ekle(s, interval, bar_tarihi)
            bulunan.append(s)

        except Exception:
            continue

# ---------------------------------------------------------
# ANA PROGRAM
# ---------------------------------------------------------

if __name__ == "__main__":
    global cache
    cache = cache_yukle()

    bist = sembol_listesi_yukle("yatirim/universes/bist.txt")
    ndx = sembol_listesi_yukle("yatirim/universes/ndx.txt")

    for interval in ["1mo", "1wk", "1d"]:
        tarama(bist, interval, "BIST")
        tarama(ndx, interval, "NDX")
