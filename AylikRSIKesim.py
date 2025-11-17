import pandas as pd
import numpy as np
import yfinance as yf
import requests
from datetime import datetime

# Telegram Bot ayarları
TELEGRAM_TOKEN = "8256592463:AAHlJ3BQSvwUDOQuKCYAhKwAwMMWUFJXE4o"  # Telegram Bot ayarları
CHAT_ID = "-1003198250448"  # Günlük tarama grubu (istersen burayı 1008660822 yapıp kendine de gönderebilirsin)
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# BIST sembol listesi (gunlukTarama / OrtaVadeTrend ile aynı)
SYMBOLS = [
    "A1CAP.IS", "ADEL.IS", "ADESE.IS", "ADGYO.IS", "AEFES.IS", "AFYON.IS",
    "AGESA.IS", "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AHSGY.IS", "AKBNK.IS",
    "AKCNS.IS", "AKENR.IS", "AKFGY.IS", "AKFIS.IS", "AKFYE.IS", "AKGRT.IS",
    "AKMGY.IS", "AKSA.IS", "AKSEN.IS", "AKSGY.IS", "ALARK.IS", "ALBRK.IS",
    "ALCAR.IS", "ALCTL.IS", "ALFAS.IS", "ALGYO.IS", "ALKA.IS", "ALKIM.IS",
    "ALKLC.IS", "ALTNY.IS", "ALVES.IS", "ANELE.IS", "ANGEN.IS", "ANHYT.IS",
    "ANSGR.IS", "ARASE.IS", "ARCLK.IS", "ARDYZ.IS", "ARENA.IS", "ARMGD.IS",
    "ARSAN.IS", "ARTMS.IS", "ASELS.IS", "ASGYO.IS", "ASTOR.IS", "ASUZU.IS",
    "ATAKP.IS", "ATATP.IS", "AVPGY.IS", "AYCES.IS", "AYDEM.IS", "AYEN.IS",
    "AYES.IS", "AYGAZ.IS", "AZTEK.IS", "BAGFS.IS", "BAHKM.IS", "BAKAB.IS",
    "BALSU.IS", "BANVT.IS", "BARMA.IS", "BASCM.IS", "BASGZ.IS", "BEGYO.IS",
    "BERA.IS", "BESLR.IS", "BEYAZ.IS", "BFREN.IS", "BIENY.IS", "BIGCH.IS",
    "BIGEN.IS", "BIMAS.IS", "BINBN.IS", "BINHO.IS", "BIOEN.IS", "BIZIM.IS",
    "BJKAS.IS", "BLCYT.IS", "BMSTL.IS", "BOBET.IS", "BORLS.IS", "BORSK.IS",
    "BOSSA.IS", "BRISA.IS", "BRKVY.IS", "BRLSM.IS", "BRSAN.IS", "BRYAT.IS",
    "BSOKE.IS", "BTCIM.IS", "BUCIM.IS", "BULGS.IS", "BVSAN.IS", "CANTE.IS",
    "CATES.IS", "CCOLA.IS", "CELHA.IS", "CEMAS.IS", "CEMTS.IS", "CEMZY.IS",
    "CGCAM.IS", "CIMSA.IS", "CLEBI.IS", "CMBTN.IS", "CMENT.IS", "CONSE.IS",
    "CRFSA.IS", "CUSAN.IS", "CVKMD.IS", "CWENE.IS", "DAGI.IS", "DAPGM.IS",
    "DARDL.IS", "DCTTR.IS", "DERHL.IS", "DERIM.IS", "DESA.IS", "DEVA.IS",
    "DGATE.IS", "DGGYO.IS", "DGNMO.IS", "DITAS.IS", "DMRGD.IS", "DNISI.IS",
    "DOAS.IS", "DOBUR.IS", "DOCO.IS", "DOFER.IS", "DOHOL.IS", "DOKTA.IS",
    "DSTKF.IS", "DURKN.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "ECILC.IS",
    "ECZYT.IS", "EDIP.IS", "EFORC.IS", "EGEEN.IS", "EGEGY.IS", "EGEPO.IS",
    "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKGYO.IS", "EKOS.IS", "EKSUN.IS",
    "ELITE.IS", "EMKEL.IS", "ENDAE.IS", "ENERY.IS", "ENJSA.IS", "ENKAI.IS",
    "ENSRI.IS", "ENTRA.IS", "ERBOS.IS", "ERCB.IS", "EREGL.IS", "ESCAR.IS",
    "ESCOM.IS", "ESEN.IS", "EUPWR.IS", "EUREN.IS", "EYGYO.IS", "FENER.IS",
    "FMIZP.IS", "FONET.IS", "FORMT.IS", "FORTE.IS", "FROTO.IS", "FZLGY.IS",
    "GARAN.IS", "GARFA.IS", "GEDIK.IS", "GENIL.IS", "GENTS.IS", "GEREL.IS",
    "GESAN.IS", "GIPTA.IS", "GLCVY.IS", "GLRMK.IS", "GLRYH.IS", "GLYHO.IS",
    "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GOZDE.IS", "GRSEL.IS",
    "GRTHO.IS", "GSDHO.IS", "GSRAY.IS", "GUBRF.IS", "GUNDG.IS", "GWIND.IS",
    "GZNMI.IS", "HALKB.IS", "HATSN.IS", "HEDEF.IS", "HEKTS.IS", "HLGYO.IS",
    "HOROZ.IS", "HRKET.IS", "HTTBT.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS",
    "IEYHO.IS", "IHAAS.IS", "IHLAS.IS", "IHLGM.IS", "IMASM.IS", "INDES.IS",
    "INFO.IS", "INGRM.IS", "INTEK.IS", "INTEM.IS", "INVEO.IS", "INVES.IS",
    "IPEKE.IS", "ISBIR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISFIN.IS",
    "ISGSY.IS", "ISGYO.IS", "ISKPL.IS", "ISKUR.IS", "ISMEN.IS", "ISSEN.IS",
    "IZENR.IS", "IZFAS.IS", "IZMDC.IS", "JANTS.IS", "KAPLM.IS", "KAREL.IS",
    "KARSN.IS", "KARTN.IS", "KATMR.IS", "KAYSE.IS", "KBORU.IS", "KCAER.IS",
    "KCHOL.IS", "KENT.IS", "KGYO.IS", "KIMMR.IS", "KLGYO.IS", "KLKIM.IS",
    "KLMSN.IS", "KLNMA.IS", "KLRHO.IS", "KLSER.IS", "KLSYN.IS", "KLYPV.IS",
    "KMPUR.IS", "KNFRT.IS", "KOCMT.IS", "KONKA.IS", "KONTR.IS", "KONYA.IS",
    "KOPOL.IS", "KORDS.IS", "KOTON.IS", "KOZAA.IS", "KOZAL.IS", "KRDMA.IS",
    "KRDMB.IS", "KRDMD.IS", "KRONT.IS", "KRVGD.IS", "KSTUR.IS", "KTLEV.IS",
    "KTSKR.IS", "KUTPO.IS", "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS",
    "LIDER.IS", "LIDFA.IS", "LILAK.IS", "LINK.IS", "LKMNH.IS", "LMKDC.IS",
    "LOGO.IS", "LRSHO.IS", "LUKSK.IS", "LYDHO.IS", "LYDYE.IS", "MAALT.IS",
    "MACKO.IS", "MAGEN.IS", "MAKTK.IS", "MARBL.IS", "MARTI.IS", "MAVI.IS",
    "MEDTR.IS", "MEGMT.IS", "MEKAG.IS", "MERCN.IS", "MERIT.IS", "METUR.IS",
    "MGROS.IS", "MHRGY.IS", "MIATK.IS", "MNDRS.IS", "MNDTR.IS", "MOBTL.IS",
    "MOGAN.IS", "MOPAS.IS", "MPARK.IS", "MRGYO.IS", "MRSHL.IS", "MSGYO.IS",
    "MTRKS.IS", "NATEN.IS", "NETAS.IS", "NTGAZ.IS", "NTHOL.IS", "NUGYO.IS",
    "NUHCM.IS", "OBAMS.IS", "ODAS.IS", "ODINE.IS", "OFSYM.IS", "ONCSM.IS",
    "ONRYT.IS", "ORGE.IS", "ORMA.IS", "OSMEN.IS", "OTKAR.IS", "OTTO.IS",
    "OYAKC.IS", "OYYAT.IS", "OZATD.IS", "OZKGY.IS", "OZSUB.IS", "OZYSR.IS",
    "PAGYO.IS", "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS",
    "PCILT.IS", "PEKGY.IS", "PENTA.IS", "PETKM.IS", "PETUN.IS", "PGSUS.IS",
    "PINSU.IS", "PKENT.IS", "PLTUR.IS", "PNLSN.IS", "PNSUT.IS", "POLHO.IS",
    "POLTK.IS", "PRKAB.IS", "PRKME.IS", "PSGYO.IS", "QNBFK.IS", "QNBTR.IS",
    "QUAGR.IS", "RALYH.IS", "RAYSG.IS", "REEDR.IS", "RGYAS.IS", "RUZYE.IS",
    "RYGYO.IS", "RYSAS.IS", "SAFKR.IS", "SAHOL.IS", "SANFM.IS", "SANKO.IS",
    "SARKY.IS", "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGMN.IS", "SEGYO.IS",
    "SELEC.IS", "SERNT.IS", "SISE.IS", "SKBNK.IS", "SKYMD.IS", "SMRTG.IS",
    "SMRVA.IS", "SNGYO.IS", "SNICA.IS", "SNPAM.IS", "SOKE.IS", "SOKM.IS",
    "SONME.IS", "SRVGY.IS", "SUNTK.IS", "SURGY.IS", "SUWEN.IS", "TABGD.IS",
    "TARKM.IS", "TATEN.IS", "TATGD.IS", "TAVHL.IS", "TBORG.IS", "TCELL.IS",
    "TCKRC.IS", "TEHOL.IS", "TEKTU.IS", "TERA.IS", "TEZOL.IS", "TGSAS.IS",
    "THYAO.IS", "TKFEN.IS", "TKNSA.IS", "TMPOL.IS", "TMSN.IS", "TNZTP.IS",
    "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRHOL.IS", "TRILC.IS", "TSGYO.IS",
    "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS", "TUKAS.IS", "TUPRS.IS",
    "TUREX.IS", "TURGG.IS", "TURSG.IS", "UFUK.IS", "ULKER.IS", "ULUFA.IS",
    "ULUSE.IS", "ULUUN.IS", "UNLU.IS", "USAK.IS", "VAKBN.IS", "VAKFN.IS",
    "VAKKO.IS", "VBTYZ.IS", "VERTU.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS",
    "VKGYO.IS", "VRGYO.IS", "VSNMD.IS", "YAPRK.IS", "YATAS.IS", "YBTAS.IS",
    "YEOTK.IS", "YGGYO.IS", "YIGIT.IS", "YKBNK.IS", "YUNSA.IS", "YYLGD.IS",
    "ZOREN.IS", "ZRGYO.IS"
]

def calculate_rsi(data, periods=31):
    """RSI hesaplama fonksiyonu"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def send_telegram_message(message):
    """Telegram mesaj gönderme fonksiyonu"""
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(TELEGRAM_API_URL, json=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Telegram mesajı gönderildi")
        else:
            print(f"⚠️ Telegram hata: {r.text}")
    except Exception as e:
        print(f"❌ Telegram hatası: {str(e)}")

def main():
    print("🚀 Aylık RSI Mor>Sarı Tarayıcı Başlatıldı")
    print(f"📅 Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Toplam {len(SYMBOLS)} hisse analiz edilecek\n")

    kesenler = []

    for idx, symbol in enumerate(SYMBOLS, 1):
        try:
            print(f"[{idx}/{len(SYMBOLS)}] {symbol} (aylık) analiz ediliyor...", end=" ")

            # Aylık veri (10 yıl geriye kadar)
            df = yf.Ticker(symbol).history(period="10y", interval="1mo")

            if df.empty or len(df) < 33:  # 31 RSI + 2 bar
                print("❌ Yetersiz veri")
                continue

            df["RSI"] = calculate_rsi(df["Close"], periods=31)
            df["RSI_SMA"] = df["RSI"].rolling(window=31).mean()

            latest = df.iloc[-1]
            prev = df.iloc[-2]

            # Koşul: önce mor < sarı, şimdi mor > sarı (aylık bar)
            if (
                pd.notna(prev["RSI"]) and pd.notna(prev["RSI_SMA"]) and
                pd.notna(latest["RSI"]) and pd.notna(latest["RSI_SMA"]) and
                prev["RSI"] < prev["RSI_SMA"] and
                latest["RSI"] > latest["RSI_SMA"]
            ):
                kesenler.append({
                    "symbol": symbol.replace(".IS", ""),
                    "rsi": float(latest["RSI"]),
                    "sma": float(latest["RSI_SMA"]),
                    "close": float(latest["Close"])
                })
                print("✅ Mor sarıyı yukarı kesti")
            else:
                print("⚪ Koşul sağlanmadı")

        except Exception as e:
            print(f"❌ Hata: {e}")

    # Telegram mesajı
    message_parts = []
    message_parts.append("*📆 Aylık RSI Mor>Sarı Taraması*")
    message_parts.append(f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")

    if kesenler:
        message_parts.append(f"*🚀 Mor çizginin sarı çizgiyi AYLIK grafikte yukarı kestiği hisseler ({len(kesenler)} adet):*")
        for s in kesenler:
            message_parts.append(
                f"• {s['symbol']}: RSI {s['rsi']:.2f} > SMA {s['sma']:.2f} | Kapanış: {s['close']:.2f} TL"
            )
    else:
        # İstediğin gibi liste boşsa test mesajı gönderiliyor
        message_parts.append("*ℹ️ Bu taramada aylık grafikte mor çizginin sarı çizgiyi yukarı kestiği hisse bulunamadı.*")
        message_parts.append("_Test mesajı: Aylık RSI taraması sorunsuz çalışıyor._")

    message = "\n".join(message_parts)
    send_telegram_message(message)

    print("\n✅ Aylık RSI taraması tamamlandı!")
    print(f"🚀 Sinyal sayısı: {len(kesenler)}")

if __name__ == "__main__":
    main()
