"""params.yaml kuralı: her değerin etiketi ve kaynağı var."""
import pytest

from efo_sim.params import tum_kayitlar

ETIKETLER = {"SEKTÖR-TİPİK", "VARSAYIM", "ÇIKARIM"}
KAYITLAR = list(tum_kayitlar())


@pytest.mark.parametrize("yol,kayit", KAYITLAR, ids=[y for y, _ in KAYITLAR])
def test_her_parametrenin_etiketi_ve_kaynagi_var(yol, kayit):
    assert "deger" in kayit, f"{yol}: değer yok"
    assert kayit.get("etiket") in ETIKETLER, f"{yol}: etiket eksik ya da geçersiz"
    assert kayit.get("kaynak"), f"{yol}: kaynak eksik"
