from datetime import datetime
import yfinance as yf
import os

from yatirim.core.indicators import rsi_tv
from yatirim.notify.telegram import gonder
from yatirim.core.log import kayit_oku, kayit_yaz, kayit_sil  # ACTIVE durumu için

# Zaman dilimi bazlı katsayılar (puanı biraz oynatmak için)
ZAMAN_KATS = {"1mo": 25, "1wk": 15, "1d": 10}


def sma_katkisi(sma: float) -> int:
    if sma < 38:
        return 25
    if sma < 44:
        return 15
    if sma < 50:
        return 5
    return 0


def puan_hesapla(rsi31: float, sma31: float, interval: str) -> int:
    baz = 0
    # Dip kırılım bölgesi
    if sma31 < 38 and rsi31 > 38:
        baz = 90
    elif rsi31 > 44 and sma31 < 44:
        baz = 70
    elif rsi31 > 44 and sma31 < 51:
        baz = 55
    elif 51 <= rsi31 <= 55:
        baz = 40
    elif rsi31 > 55:
        baz = 20

    puan = baz + sma_katkisi(sma31) * 0.5 + ZAMAN_KATS.get(interval, 0)
    return min(100, int(puan))


def yorum_etiketi(puan: int, interval: str) -> str:
    if interval == "1mo":
        return "💎 Uzun Vade Dip – Güçlü Alım"
    if interval == "1wk":
        return "🟢 Orta–Uzun Vade Alım"
    if interval == "1d":
        return "💹 Kısa Vadeli Alım (Günlük)"
    return "🌐 Sinyal"


def sinyal_cubuk(puan: int) -> str:
    dolu = int(puan / 10)
    bos = 10 - dolu
    return "🟩" * dolu + "⬛" * bos


def sembol_listesi_yukle(dosya_yolu: str):
    if not os.path.exists(dosya_yolu):
        return []
    with open(dosya_yolu, "r", encoding="utf-8") as f:
        return [satir.strip() for satir in f if satir.strip()]


def tarama(semboller, interval: str = "1d", liste_adi: str = "BIST"):
    """
    - 38 ve 44 kırılımlarını takip eder.
    - Her sembol + zaman dilimi için bir 'anahtar' oluşturur (örn: AKBNK.IS_1d).
    - kayit_oku / kayit_yaz / kayit_sil ile ACTIVE durumu yönetilir.
    """
    for s in semboller:
        anahtar = f"{s}_{interval}"
        durum = kayit_oku(anahtar)  # "ACTIVE" veya None

        try:
            df = yf.Ticker(s).history(period="2y", interval=interval)
            if df.empty or len(df) < 40:
                continue

            # TradingView'e uyumlu RSI hesabı
            df["RSI31"] = rsi_tv(df["Close"], 31)
            df["SMA31"] = df["RSI31"].rolling(31).mean()

            rsi_prev = df["RSI31"].iloc[-2]
            rsi_now = df["RSI31"].iloc[-1]
            sma_now = df["SMA31"].iloc[-1]

            # RESET: RSI tekrar 44 altına düştüyse sinyal durumunu temizle
            if durum == "ACTIVE" and rsi_now < 44:
                kayit_sil(anahtar)
                durum = None  # temizledik

            # Yeni kırılım var mı?
            kirilim = None
            if rsi_prev < 38 and rsi_now > 38:
                kirilim = "Dip Sinyali (RSI31 38 Üstü)"
            elif rsi_prev < 44 and rsi_now > 44:
                kirilim = "RSI31 44 Yukarı Kırılımı"

            # Kırılım yoksa devam
            if not kirilim:
                continue

            # Zaten ACTIVE ise, aynı dalganın içinde tekrar sinyal gönderme
            if durum == "ACTIVE":
                continue

            # Buraya geldiysek: yeni kırılım + daha önce ACTIVE değil → mesaj gönder
            puan = puan_hesapla(rsi_now, sma_now, interval)
            yorum = yorum_etiketi(puan, interval)
            bar = sinyal_cubuk(puan)
            ts = datetime.now().strftime("%d.%m.%Y %H:%M")
            sembol_kisa = s.replace(".IS", "")
            link = f"https://www.tradingview.com/chart/?symbol={sembol_kisa}"

            mesaj = (
                f"📊 *{kirilim}* {liste_adi} – *{interval.upper()}*\n"
                f"Sembol: ${sembol_kisa}\n"
                f"RSI: {rsi_now:.2f}\n"
                f"SMA31: {sma_now:.2f}\n"
                f"Sinyal Gücü: {puan}/100\n"
                f"{yorum}\n{bar}\n"
                f"🕒 {ts}\n"
                f"[📈 Grafiği Aç]({link})"
            )

            gonder(mesaj, disable_preview=True)

            # Sinyali ACTIVE olarak işaretle
            kayit_yaz(anahtar, "ACTIVE")

        except Exception:
            # Hata olursa o sembolü sessizce atlıyoruz
            continue


def calistir():
    # Repo kökünden göreli yollar (GitHub Actions'da da böyle çalışıyordu)
    bist_list = sembol_listesi_yukle("yatirim/universes/bist.txt")
    ndx_list = sembol_listesi_yukle("yatirim/universes/ndx.txt")
    endeks_list = sembol_listesi_yukle("yatirim/universes/endeks.txt")

    # 4h çok sinyal ürettiği için kaldırmıştık
    for interval in ["1mo", "1wk", "1d"]:
        if bist_list:
            tarama(bist_list, interval, "BIST")
        if ndx_list:
            tarama(ndx_list, interval, "NDX")
        if endeks_list:
            tarama(endeks_list, interval, "ENDEKS")


if __name__ == "__main__":
    calistir()
