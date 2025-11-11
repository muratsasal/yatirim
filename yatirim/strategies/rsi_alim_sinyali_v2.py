from datetime import datetime
import yfinance as yf, pandas as pd
from yatirim.core.indicators import rsi
from yatirim.notify.telegram import gonder
from yatirim.core.log import kayit_var_mi, kayit_ekle

ZAMAN_KATSAYILARI = {"1mo":40,"1wk":25,"1d":15,"4h":10}

def sma_katkisi(sma):
    if sma < 38: return 25
    if sma < 44: return 15
    if sma < 50: return 5
    return 0

def puan_hesapla(rsi31, sma31, interval):
    baz = 0
    if sma31 < 38 and rsi31 > 38: baz = 100  # dip kırılım
    elif rsi31 > 44 and sma31 < 44: baz = 80
    elif rsi31 > 44 and sma31 < 51: baz = 60
    elif 51 <= rsi31 <= 55: baz = 40
    elif rsi31 > 55: baz = 20
    return min(100, baz + sma_katkisi(sma31) + ZAMAN_KATSAYILARI.get(interval,0))

def sinyal_cubuk(puan):
    dolu, bos = int(puan/10), 10 - int(puan/10)
    return "🟩"*dolu + "⬛"*bos

def tarama(semboller, interval="1d"):
    bugun = datetime.now().strftime("%Y-%m-%d")
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
                bar=sinyal_cubuk(puan)
                link=f"https://www.tradingview.com/chart/?symbol=BIST:{s.replace('.IS','')}"
                ts=datetime.now().strftime("%d.%m.%Y %H:%M")
                tip="Dip Sinyali (RSI31 38 Yukarı Kırılımı)" if (mor_once<38 and mor_son>38) else "RSI31 44 Yukarı Kırılımı"
                mesaj=(f"📊 *{tip}*
Sembol: ${s.replace('.IS','')}
Zaman Dilimi: {interval}
"
                       f"RSI: {mor_son:.2f}
SMA31: {sma_son:.2f}
Sinyal Gücü: {puan}/100
"
                       f"{bar}
🕒 {ts}
📈 [Grafiği Aç]({link})")
                gonder(mesaj)
                kayit_ekle(s, bugun)
        except Exception:
            continue

if __name__=="__main__":
    SEMBOLLER=["THYAO.IS","ASELS.IS","BIMAS.IS","TUPRS.IS","SISE.IS","VAKBN.IS"]
    tarama(SEMBOLLER,"1d")
