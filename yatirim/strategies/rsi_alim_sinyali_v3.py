from datetime import datetime
import yfinance as yf, pandas as pd, os
from yatirim.core.indicators import rsi
from yatirim.notify.telegram import gonder
from yatirim.core.log import kayit_var_mi, kayit_ekle

# Her zaman dilimi için katsayı (puanı sınırlandırmakta kullanılacak)
PUAN_LIMITLERI = {"1mo":100,"1wk":90,"1d":70,"4h":50}

def sma_katkisi(sma):
    if sma < 38: return 25
    if sma < 44: return 15
    if sma < 50: return 5
    return 0

def puan_hesapla(rsi31, sma31, interval):
    """RSI ve SMA değerlerine göre puan hesapla, zaman dilimine göre üst limit uygula."""
    baz = 0
    if sma31 < 38 and rsi31 > 38: baz = 90          # dip kırılım
    elif rsi31 > 44 and sma31 < 44: baz = 70
    elif rsi31 > 44 and sma31 < 51: baz = 55
    elif 51 <= rsi31 <= 55: baz = 40
    elif rsi31 > 55: baz = 20

    puan = baz + sma_katkisi(sma31)*0.5
    limit = PUAN_LIMITLERI.get(interval, 70)
    return min(limit, int(puan))

def yorum_etiketi(puan, interval):
    """Zaman dilimine göre yorum üret."""
    if interval == "1mo" and puan >= 90: return "💎 Uzun Vadeli Güçlü Alım (Aylık)"
    if interval == "1wk" and puan >= 80: return "💪 Orta Vadeli Güçlü Alım (Haftalık)"
    if interval == "1d" and puan >= 60: return "🟢 Kısa Vadeli Alım (Günlük)"
    if interval == "4h" and puan >= 40: return "🟡 Kısa Trade Fırsatı (4 Saatlik)"
    return "🔸 Zayıf veya Gecikmiş Sinyal"

def sinyal_cubuk(puan):
    dolu, bos = int(puan/10), 10 - int(puan/10)
    return "🟩"*dolu + "⬛"*bos

def sembol_listesi_yukle(dosya):
    if not os.path.exists(dosya): return []
    with open(dosya, "r", encoding="utf-8") as f:
        return [satir.strip() for satir in f if satir.strip()]

def tarama(semboller, interval="1d", liste_adi="BIST"):
    bugun = datetime.now().strftime("%Y-%m-%d")
    for s in semboller:
        try:
            df = yf.Ticker(s).history(period="2y", interval=interval)
            if df.empty or len(df) < 40: continue
            df["RSI31"]=rsi(df["Close"],31)
            df["SMA31"]=df["RSI31"].rolling(window=31).mean()

            mor_once, mor_son=df["RSI31"].iloc[-2], df["RSI31"].iloc[-1]
            if (mor_once<38 and mor_son>38) or (mor_once<44 and mor_son>44):
                if kayit_var_mi(f"{s}_{interval}", bugun): continue

                sma_son=df["SMA31"].iloc[-1]
                puan=puan_hesapla(mor_son,sma_son,interval)
                yorum=yorum_etiketi(puan, interval)
                bar=sinyal_cubuk(puan)
                link=f"https://www.tradingview.com/chart/?symbol={s.replace('.IS','')}"
                ts=datetime.now().strftime("%d.%m.%Y %H:%M")
                tip="Dip Sinyali (RSI31 38 Yukarı Kırılımı)" if (mor_once<38 and mor_son>38) else "RSI31 44 Yukarı Kırılımı"

                mesaj=(f"📊 *{tip}* [{liste_adi} – {interval.upper()}]\n"
                       f"Sembol: ${s.replace('.IS','')}\n"
                       f"RSI: {mor_son:.2f}\nSMA31: {sma_son:.2f}\n"
                       f"🎯 Sinyal Gücü: {puan}/100\n{yorum}\n{bar}\n🕒 {ts}\n"
                       f"[📈 Grafiği Aç]({link})")

                gonder(mesaj, disable_preview=True)
                kayit_ekle(f"{s}_{interval}", bugun)
        except Exception:
            continue

if __name__=="__main__":
    bist_list = sembol_listesi_yukle("yatirim/universes/bist.txt")
    ndx_list = sembol_listesi_yukle("yatirim/universes/ndx.txt")
    endeks_list = sembol_listesi_yukle("yatirim/universes/endeksler.txt")

    for interval in ["1mo","1wk","1d","4h"]:
        tarama(bist_list, interval, "BIST")
        tarama(ndx_list, interval, "NDX")
        tarama(endeks_list, interval, "ENDEKS")
