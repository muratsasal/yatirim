import os, io
_here=os.path.dirname(__file__)

def oku(dosya):
    path=os.path.join(_here, dosya)
    with io.open(path, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]

bist=type("bist", (), {"SEMBOLLER": oku("bist.txt")})
ndx=type("ndx", (), {"SEMBOLLER": oku("ndx.txt")})
