import yfinance as yf
import pandas as pd
from datetime import datetime
from yatirim.notify.telegram import gonder
from yatirim.core.log import kayit_var_mi, kayit_ekle
import os

# -----------------------------
#  TECHNICAL INDICATORS
# -----------------------------

def macd(df):
    df["EMA12"] = df["Close"].ewm(span=12).mean()
    df["EMA26"] = df["Close"].ewm(span=26).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["SIGNAL"] = df["MACD"].ewm(span=9).mean()
    return df

def golden_cross(df):
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()
    return df

def volume_spike(df):
    df["VOL_SMA20"] = df["Volume"].rolling(20).mean()
    return df

# -----------------------------
#  TARAYICI
# -----------------------------

def sembol_listesi_yukle(dosya):
    if not os.path.exists(dosya): 
        return []
    with open(dosya, "r", encoding="utf-8") as f:
        return [x.strip() for x in f.readlines() if x.strip()]

def tarama(semboller, liste_adi="ENDEKS"):
    bugun = datetime.now().strftime("%Y-%m-%d")
    bulunan = []

    for s in semboller:
        try:
            df = yf.Ticker(s).history(period="2y", interval="1d")
            if df.empty or len(df) < 250: 
                continue

            df = macd(df)
            df = golden_cross(df)
            df = volume_spike(df)

            # Son değerler
            macd_prev, macd_now = df["MACD"].iloc[-2], df["MACD"].iloc[-1]
            sig_prev, sig_now = df["SIGNAL"].iloc[-2], df["SIGNAL"].iloc[-1]
            sma50, sma200 = df["SMA50"].iloc[-1], df["SMA200"].iloc[-1]
            vol, vol_avg = df["Volume"].iloc[-1], df["VOL_SMA20"].iloc[-1]

            # Sinyal Koşulları
            macd_cross = macd_prev < sig_prev and macd_now > sig_now
            golden_cross_signal = sma50 > sma200 and df["SMA50"].iloc[-2] <= df["SMA200"].iloc[-2]
            sma200_dip = df["Close"].iloc[-1] < sma200 * 1.02
            vol_spike = vol > vol_avg * 1.8

            if macd_cross or golden_cross_signal or sma200_dip or vol_spike:

                sinyal_turu = []
                if macd_cross: sinyal_turu.append("MACD Bullish Cross")
                if golden_cross_signal: sinyal_turu.append("Golden Cross")
                if sma200_dip: sinyal_turu.append("SMA200 Dip Bölgesi")
                if vol_spike: sinyal_turu.append("Volume Spike")

                sinyal_turu = ", ".join(sinyal_turu)

                # Aynı gün 2. kez gönderme
                if kayit_var_mi(f"{s}_teknik", bugun):
                    continue

                link = f"https://www.tradingview.com/chart/?symbol={s.replace('.IS','')}"
                ts = datetime.now().strftime("%d.%m.%Y %H:%M")

                mesaj = (
                    f"📌 *Teknik Analiz Sinyali* ({sinyal_turu})\n"
                    f"Endeks/Kripto/Emtia: ${s}\n"
                    f"Liste: {liste_adi}\n"
                    f"📈 Fiyat: {df['Close'].iloc[-1]:.2f}\n"
                    f"🕒 {ts}\n"
                    f"[Grafiği Aç]({link})"
                )

                gonder(mesaj, disable_preview=True)
                kayit_ekle(f"{s}_teknik", bugun)
                bulunan.append(s)

        except Exception:
            continue

    if not bulunan:
        pass  # test mesajları kaldırıldı


if __name__ == "__main__":
    endeks_list = sembol_listesi_yukle("yatirim/universes/endeks.txt")
    tarama(endeks_list, "ENDEKS")
