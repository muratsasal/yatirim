from datetime import datetime
import yfinance as yf, pandas as pd
from yatirim.core.indicators import rsi
from yatirim.notify.telegram import gonder
from yatirim.universes import bist, ndx

def puan_hesapla(rsi31, sma31):
    if sma31 < 38: return 100
    if rsi31 > 44 and sma31 < 44: return 80
    if rsi31 > 44 and sma31 < 51: return 60
    if 51 <= rsi31 <= 55: return 40
    if rsi31 > 55: return 20
    return 0

def sinyal_cubuk(puan):
    dolu, bos = int(puan/10), 10 - int(puan/10)
    return "🟩"*dolu + "⬛"*bos

def tarama(liste, ad="BIST"):
    print(f"{ad} taraması başlıyor...")
    bulundu = []
    for sembol in liste:
        try:
            df = yf.Ticker(sembol).history(period="2y", interval="1d")
            if df.empty or len(df)<40: continue
            df["RSI31"]=rsi(df["Close"],31)
            df["SMA31"]=df["RSI31"].rolling(window=31).mean()
            mor_once, mor_son=df["RSI31"].iloc[-2], df["RSI31"].iloc[-1]
            if mor_once<44 and mor_son>44:
                sari_son=df["SMA31"].iloc[-1]
                puan=puan_hesapla(mor_son,sari_son)
                bar=sinyal_cubuk(puan)
                ts=datetime.now().strftime("%d.%m.%Y %H:%M")
                msg=(f"📈 *Alış Sinyali (RSI31 44 Yukarı Kırılımı)*\n"
                     f"Sembol: ${sembol.replace('.IS','')}\n"
                     f"Zaman Dilimi: Günlük\n"
                     f"RSI: {mor_son:.2f} ↗️ 44 üstü\n"
                     f"SMA31: {sari_son:.2f}\n"
                     f"🎯 Sinyal Gücü: {puan}/100\n"
                     f"{bar}\n🕒 {ts}")
                gonder(msg)
                bulundu.append(sembol)
        except Exception:
            continue
    if not bulundu:
        gonder(f"🧪 Test: Bugün {ad} listesinde kırılım bulunamadı. ({datetime.now():%d.%m.%Y})")

def main():
    print("RSI Alım Sinyali taraması başlıyor...")
    bist_liste=bist.SEMBOLLER
    ndx_liste=ndx.SEMBOLLER
    for i in range(0,len(bist_liste),200):
        tarama(bist_liste[i:i+200], ad=f"BIST-{int(i/200)+1}")
    tarama(ndx_liste, ad="NDX")
    print("Tamamlandı.")

if __name__=="__main__":
    main()
