"""params.yaml okuyucu. Kodda sabit sayı tutulmaz; tüm değerler buradan gelir."""
from contextlib import contextmanager
from pathlib import Path

import yaml

PARAMS_FILE = Path(__file__).parent / "params.yaml"
OUT_DIR = Path(__file__).parent / "out"

with PARAMS_FILE.open(encoding="utf-8") as f:
    _P = yaml.safe_load(f)


def kayit(yol):
    """'lab1.bant_hizi' gibi bir yolun tam kaydını (deger, etiket, kaynak, not) döndürür."""
    node = _P
    for anahtar in yol.split("."):
        node = node[anahtar]
    return node


def d(yol):
    """Bir parametrenin yalnızca değerini döndürür."""
    return kayit(yol)["deger"]


def bolum(ad):
    return _P[ad]


def tum_kayitlar():
    """(yol, kayit) çiftleri — her değerin etiketli olduğunu test etmek için."""
    for bolum_adi, icerik in _P.items():
        for anahtar, k in icerik.items():
            yield f"{bolum_adi}.{anahtar}", k


def bolum_metni(ad):
    """params.yaml'ın yalnızca bir bölümünü yorum satırlarıyla birlikte metin olarak döndürür."""
    satirlar = PARAMS_FILE.read_text(encoding="utf-8").splitlines()
    cikti, icinde = [], False
    for s in satirlar:
        if s and not s.startswith((" ", "#")):
            icinde = s.startswith(f"{ad}:")
        if icinde:
            cikti.append(s)
    return "\n".join(cikti).rstrip() + "\n"


def sayi(x, basamak=2):
    """Sayıyı Türkçe ondalık virgülüyle yazar (0.5 → '0,50')."""
    return f"{x:.{basamak}f}".replace(".", ",")


@contextmanager
def gecici(yol, deger):
    """Bir parametreyi geçici olarak değiştirir (duyarlılık hesapları için)."""
    k = kayit(yol)
    eski = k["deger"]
    k["deger"] = deger
    try:
        yield
    finally:
        k["deger"] = eski
