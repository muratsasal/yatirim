import os

LOG_DOSYA = "gonderildi.txt"

def kayit_var_mi(anahtar, tarih):
    if not os.path.exists(LOG_DOSYA):
        return False
    with open(LOG_DOSYA, "r", encoding="utf-8") as f:
        return f"{anahtar}|{tarih}" in f.read()

def kayit_ekle(anahtar, tarih):
    with open(LOG_DOSYA, "a", encoding="utf-8") as f:
        f.write(f"{anahtar}|{tarih}\n")
