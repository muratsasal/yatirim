import json
import os
from datetime import datetime
import yfinance as yf

# Mevcut kütüphaneleriniz (olduğu gibi bırakıldı)
try:
    from yatirim.core.indicators import rsi_tv
    from yatirim.notify.telegram import gonder
    from yatirim.core.log import kayit_var_mi, kayit_ekle
except ImportError:
    # Test için dummy fonksiyonlar (Siz kendi kütüphanenizi kullandığınızda burası çalışmayacak)
    print("Uyarı: 'yatirim' modülü bulunamadı, kodun çalışması için kendi ortamınızda olmalısınız.")

# --- AYARLAR ---
ZAMAN_KATS = {"1mo": 25, "1wk": 15, "1d": 10}
DURUM_DOSYASI = "rsi_takip_durumu.json"  # Sinyal durumlarını saklayacak dosya

# --- YARDIMCI FONKSİYONLAR ---

def durum_yukle():
    """Kaydedilmiş sinyal durumlarını dosyadan okur."""
    if not os.path.exists(DURUM_DOSYASI):
        return {}
    try:
        with open(DURUM_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def durum_kaydet(veri):
    """Sinyal durumlarını dosyaya yazar."""
    with open(DURUM_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, indent=4, ensure_ascii=False)

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
    puan = baz + sma_katkisi(sma31)*0.5 + ZAMAN_KATS.get(interval, 0)
    return min(100, int(puan))

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
    with open(d, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]

# --- ANA TARAMA ---

def tarama(semboller, interval="1d", liste_adi="BIST"):
    bugun = datetime.now().strftime("%Y-%m-%d")
    
    # Önceki durumları yükle
    durum_db = durum_yukle()
    degisiklik_var = False # Dosyayı sadece değişiklik varsa kaydedelim

    print(f"--- {liste_adi} ({interval}) Taraması Başlıyor ---")

    for s in semboller:
        try:
            # Veri çekme
            df = yf.Ticker(s).history(period="2y", interval=interval)
            if df.empty or len(df) < 50: continue

            # İndikatör hesaplama
            df["RSI31"] = rsi_tv(df["Close"], 31)
            df["SMA31"] = df["RSI31"].rolling(31).mean()

            rsi_prev = df["RSI31"].iloc[-2]
            rsi_now = df["RSI31"].iloc[-1]
            sma = df["SMA31"].iloc[-1]

            # -- DURUM YÖNETİMİ (STATE MANAGEMENT) --
            # Her sembol ve periyot için benzersiz bir anahtar
            durum_anahtari = f"{s}_{interval}"
            
            # Mevcut durumu al (yoksa boş sözlük)
            mevcut_durum = durum_db.get(durum_anahtari, {"sent_38": False, "sent_44": False})

            # 1. ADIM: RESETLEME KONTROLÜ
            # RSI 38'in altına indiyse, 38 kilidini aç (Tekrar sinyal atabilir hale getir)
            if rsi_now < 38 and mevcut_durum.get("sent_38") is True:
                mevcut_durum["sent_38"] = False
                degisiklik_var = True
            
            # RSI 44'ün altına indiyse, 44 kilidini aç
            if rsi_now < 44 and mevcut_durum.get("sent_44") is True:
                mevcut_durum["sent_44"] = False
                degisiklik_var = True

            # 2. ADIM: KIRILIM VE GÖNDERİM KONTROLÜ
            kirilim = None
            gonderilecek_tip = None

            # Kırılım 38 Kontrolü
            if rsi_prev < 38 and rsi_now > 38:
                # Eğer daha önce gönderilmediyse (veya resetlendiyse)
                if not mevcut_durum.get("sent_38"):
                    kirilim = "Dip Sinyali (38 Üstü)"
                    gonderilecek_tip = "38"
            
            # Kırılım 44 Kontrolü
            elif rsi_prev < 44 and rsi_now > 44:
                # Eğer daha önce gönderilmediyse (veya resetlendiyse)
                if not mevcut_durum.get("sent_44"):
                    kirilim = "RSI31 44 Yukarı Kırılımı"
                    gonderilecek_tip = "44"

            # Eğer geçerli bir kırılım yoksa veya zaten gönderilmişse pas geç
            if not kirilim:
                # Durum veritabanını güncelle (resetleme olmuş olabilir)
                durum_db[durum_anahtari] = mevcut_durum
                continue

            # Günlük tekrarı önlemek için ek koruma (Sizin mevcut yapınız)
            anahtar_log = f"{s}_{interval}"
            if kayit_var_mi(anahtar_log, bugun):
                continue

            # --- MESAJ HAZIRLAMA ---
            puan = puan_hesapla(rsi_now, sma, interval)
            yorum = yorum_etiketi(puan, interval)
            bar = sinyal_cubuk(puan)
            link = f"https://www.tradingview.com/chart/?symbol={s.replace('.IS','')}"
            ts = datetime.now().strftime("%d.%m.%Y %H:%M")

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

            # Gönderim ve Kayıt
            print(f"Sinyal gönderiliyor: {s} - {kirilim}")
            gonder(mesaj, disable_preview=True)
            kayit_ekle(anahtar_log, bugun)
            
            # Durumu güncelle (Kilitleri kapat)
            if gonderilecek_tip == "38":
                mevcut_durum["sent_38"] = True
            elif gonderilecek_tip == "44":
                mevcut_durum["sent_44"] = True
            
            durum_db[durum_anahtari] = mevcut_durum
            degisiklik_var = True

        except Exception as e:
            print(f"Hata ({s}): {e}")
            pass
    
    # Döngü bitince tüm durumları dosyaya kaydet
    if degisiklik_var:
        durum_kaydet(durum_db)

# --- ÇALIŞTIRMA ---
if __name__ == "__main__":
    # Dosya yollarını kendi sisteminize göre ayarladığınızdan emin olun
    bist = sembol_listesi_yukle("yatirim/universes/bist.txt")
    ndx = sembol_listesi_yukle("yatirim/universes/ndx.txt")
    endeks = sembol_listesi_yukle("yatirim/universes/endeks.txt")

    for iv in ["1mo", "1wk", "1d"]:
        tarama(bist, iv, "BIST")
        tarama(ndx, iv, "NDX")
        tarama(endeks, iv, "ENDEKS")