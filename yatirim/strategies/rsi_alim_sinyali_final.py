from datetime import datetime
import yfinance as yf, pandas as pd, os

from yatirim.core.indicators import rsi
from yatirim.notify.telegram import gonder
from yatirim.core.log import kayit_var_mi, kayit_ekle

# Zaman dilimi katsayilari (puan ayari)
ZAMAN_KATSAYILARI = {"1mo": 25, "1wk": 15, "1d": 10}

def sma_katkisi(sma):  # RSI'nin ortalamasina gore ekstra puan
    if sma < 38: return 25
    if sma < 44: return 15
    if sma < 50: return 5
    return 0

def puan_hesapla(rsi31, sma31, interval):  # Genel puan hesaplama
    baz = 0
    if sma31 < 38 and rsi31 > 38: baz = 90              # Dip kirilimi
    elif rsi31 > 44 and sma31 < 44: baz = 70
    elif rsi31 > 44 and sma31 < 51: baz = 55
    elif 51 <= rsi31 <= 55: baz = 40
    elif rsi31 > 55: baz = 20

    puan = baz + sma_katkisi(sma31) * 0.5 + ZAMAN_KATSAYILARI.get(interval, 0)
    return min(100, int(puan))

def yorum_etiketi(puan):  # Puan yazisi
    if puan >= 95: return "💎 Dip Bölgesi – Güçlü Alım"
    if puan >= 80: return "💪 Güçlü Alım Bölgesi"
    if puan >= 65: return "🟢 Orta Seviye Alım"
    if puan >= 50: return "🟡 İzleme Bölgesi"
    return "🔸 Zayıf veya Gecikmiş Sinyal"

def sinyal_cubuk(puan):  # Yesil / siyah bar
    dolu = int(puan / 10)
    bos = 10 - dolu
    return "🟩" * dolu + "⬛" * bos

def sembol_listesi_yukle(dosya):  # txt'den sembol listesi okuma
    if not os.path.exists(dosya): return []
    with open(dosya, "r", encoding="utf-8") as f:
        return [satir.strip() for satir in f if satir.strip()]

def tarama(semboller, interval="1d", liste_adi="BIST"):
    for s in semboller:
        try:
            df = yf.Ticker(s).history(period="2y", interval=interval)
            if df.empty or len(df) < 40:  # yeterli veri yoksa atlanir
                continue

            df["RSI31"] = rsi(df["Close"], 31)
            df["SMA31"] = df["RSI31"].rolling(window=31).mean()

            mor_once, mor_son = df["RSI31"].iloc[-2], df["RSI31"].iloc[-1]

            # 38 veya 44 yukari kirilimi
            if not ((mor_once < 38 < mor_son) or (mor_once < 44 < mor_son)):
                continue

            sma_son = df["SMA31"].iloc[-1]

            # 🔑 Tekrari engellemek icin: bar tarihiyle kayit tutuyoruz
            bar_tarihi = df.index[-1].strftime("%Y-%m-%d")
            anahtar = f"{s}_{interval}"
            if kayit_var_mi(anahtar, bar_tarihi):  # ayni bar icin once gonderilmisse
                continue

            puan = puan_hesapla(mor_son, sma_son, interval)
            yorum = yorum_etiketi(puan)
            bar = sinyal_cubuk(puan)

            # TradingView linki (BIST icin .IS kaldiriliyor)
            tv_sembol = s.replace(".IS", "")
            link = f"https://www.tradingview.com/chart/?symbol={tv_sembol}"

            ts = datetime.now().strftime("%d.%m.%Y %H:%M")

            if mor_once < 38 < mor_son:
                tip = "RSI31 38 Yukarı Kırılımı"
            else:
                tip = "RSI31 44 Yukarı Kırılımı"

            mesaj = (
                f"📊 *{tip}* {liste_adi} – {interval.upper()}\n"
                f"Sembol: ${tv_sembol}\n"
                f"RSI: {mor_son:.2f}\n"
                f"SMA31: {sma_son:.2f}\n"
                f"🎯 Sinyal Gücü: {puan}/100\n"
                f"{yorum}\n"
                f"{bar}\n"
                f"🕒 {ts}\n"
                f"[📈 Grafiği Aç]({link})"
            )

            gonder(mesaj, disable_preview=True)
            kayit_ekle(anahtar, bar_tarihi)  # Bu bar icin sinyal gonderildi olarak isaretlenir

        except Exception:
            # Herhangi bir hissede hata olsa bile digerlerini bozmamasi icin
            continue

if __name__ == "__main__":
    bist_list = sembol_listesi_yukle("yatirim/universes/bist.txt")
    ndx_list = sembol_listesi_yukle("yatirim/universes/ndx.txt")

    # 4H tarama iptal; sadece aylik / haftalik / gunluk
    for interval in ["1mo", "1wk", "1d"]:
        tarama(bist_list, interval, "BIST")
        tarama(ndx_list, interval, "NDX")
