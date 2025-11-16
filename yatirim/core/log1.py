import os

DOSYA = "gonderildi.txt"

def kayit_var_mi(sembol: str, tarih: str) -> bool:
    if not os.path.exists(DOSYA): return False
    with open(DOSYA, "r", encoding="utf-8") as f:
        for satir in f:
            if f"{sembol},{tarih}" in satir.strip():
                return True
    return False

def kayit_ekle(sembol: str, tarih: str):
    with open(DOSYA, "a", encoding="utf-8") as f:
        f.write(f"{sembol},{tarih}\n")
