from datetime import datetime
import yfinance as yf, pandas as pd, os
from yatirim.core.indicators import rsi
from yatirim.notify.telegram import gonder
from yatirim.core.log import kayit_var_mi, kayit_ekle

ZAMAN_KATSAYILARI = {"1mo":25,"1wk":15,"1d":10,"4h":5}

def sma_katkisi(sma):
    if sma < 38: return 25
    if sma < 44: return 15
    if sma < 50: return 5
    return 0

def puan_hesapla(rsi31, sma31, interval):
    baz = 0
    if sma31 < 38 and rsi31 > 38: baz = 90          # dip kırılım
    elif rsi31 > 44 and sma31 < 44: baz = 70
    elif rsi31 > 44 and sma31 < 51: baz = 55
    elif 51 <= rsi31 <= 55: baz = 40
    elif rsi31 > 55: baz = 20

    puan = baz + sma_katkisi(sma31)*0.5 + ZAMAN_KATSAYILARI.get(interval,0)
    return min(100, int(puan))

def yorum_etiketi(puan):
    if puan >= 95: return "💎 Dip Bölgesi – Güçlü Alım"
    if puan >= 80: return "💪 Güçlü Alım Bölgesi"
    if puan >= 65: return "🟢 Orta Seviye Alım"
    if puan >= 50: return "🟡 İzleme Bölgesi"
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
    bulunan = []
    for s in semboller:
        try:
            df = yf.Ticker(s).history(period="2y", interval=interval)
            if df.empty or len(df) < 40: continue
            df["RSI31"]=rsi(df["Close"],31)
            df["SMA31"]=df["RSI31"].rolling(window=31).mean()
            mor_once, mor_son=df["RSI31"].iloc[-2], df["RSI31"].iloc[-1]
            if (mor_once<38 and mor_son>38) or (mor_once<44 and mor_son>44):
                if kayit_var_mi(s, bugun): continue
                sma_son=df["SMA31"].iloc[-1]
                puan=puan_hesapla(mor_son,sma_son,interval)
                yorum=yorum_etiketi(puan)
                bar=sinyal_cubuk(puan)
                link=f"https://www.tradingview.com/chart/?symbol={s.replace('.IS','')}"
                ts=datetime.now().strftime("%d.%m.%Y %H:%M")
                tip="Dip Sinyali (RSI31 38 Yukarı Kırılımı)" if (mor_once<38 and mor_son>38) else "RSI31 44 Yukarı Kırılımı"
                mesaj=(f"📊 *{tip}* [{liste_adi}]\nSembol: ${s.replace('.IS','')}\nZaman Dilimi: {interval}\n"
                       f"RSI: {mor_son:.2f}\nSMA31: {sma_son:.2f}\nSinyal Gücü: {puan}/100\n{yorum}\n"
                       f"{bar}\n🕒 {ts}\n📈 [Grafiği Aç]({link})")
                gonder(mesaj)
                kayit_ekle(s, bugun)
                bulunan.append(s)
        except Exception:
            continue
    if not bulunan:
        gonder(f"🧾 Test: Bugün {liste_adi} listesinde kırılım bulunamadı. ({bugun})")

if __name__=="__main__":
    from yatirim.notify.telegram import gonder
    gonder("🧪 Test: GitHub Actions bağlantısı aktif, RSI v2.1 tarama başlatıldı.")

    bist_list = sembol_listesi_yukle("yatirim/universes/bist.txt")
    ndx_list = sembol_listesi_yukle("yatirim/universes/ndx.txt")

    tarama(bist_list, "1d", "BIST")
    tarama(ndx_list, "1d", "NDX")
