"""LAB 4 gereksinimleri = testler (eğitim amaçlı model).

Bağımlı varyantta beklenen başarısızlıklar xfail(strict=True) ile işaretli: test "kalıyor"
ve bu beklenen sonuç. Bağımsız varyantta aynı test geçiyor. Varyantlar yalnızca gösterim
içindir; föy çözüm değil gereksinim tanımlatır.
"""
import pytest

from efo_sim import lab1_safety as lab1
from efo_sim import lab4_attack as m

BAGIMLI_KALIR = pytest.mark.xfail(strict=True, reason="bağımlı varyant gereksinimi karşılamıyor (beklenen)")


# ---------------------------------------------------------------- 4.1
def test_mevcut_mimaride_emniyet_fonksiyonuna_ulasan_yol_var():
    assert m.toplam_yol(m.MEVCUT) > 0


def test_hedef_mimaride_emniyet_fonksiyonunu_degistirebilen_yol_sayisi_sifir():
    assert m.toplam_yol(m.HEDEF) == 0


def test_saldirgan_tum_onlemlere_ragmen_iceri_girse_de_emniyet_fonksiyonuna_ulasamaz():
    assert "plc" in m.ulasilabilir(m.HEDEF_ICERI_GIRILDI)
    assert m.toplam_yol(m.HEDEF_ICERI_GIRILDI) == 0


def test_mevcut_mimaride_en_kisa_yol_iki_adimdir():
    en_kisa = min(len(v["en_kisa"]) for v in m.yol_ozeti(m.MEVCUT).values() if v["en_kisa"])
    assert en_kisa == 2


def test_her_kenarin_kosullari_mimaride_tanimli():
    for k in m.KENARLAR:
        assert k[0] in m.DUGUMLER and k[1] in m.DUGUMLER
        for c in k[2]:
            assert c in m.MEVCUT and c in m.HEDEF


def test_her_giris_noktasi_grafta_bir_kenarla_baglidir():
    for g in m.GIRISLER:
        assert any(k[0] == g for k in m.KENARLAR)


# ---------------------------------------------------------------- 4.2
@pytest.mark.parametrize("varyant", [
    pytest.param("bagimli", marks=BAGIMLI_KALIR),
    "bagimsiz",
    "bagimsiz_hiz_izlemeli",
])
def test_plc_mantigi_degisse_de_acil_stop_guvenli_duruma_goturur(varyant):
    assert m.acil_stop_durumu(varyant, "plc_mantigi") == lab1.GUVENLI_DURUM


@pytest.mark.parametrize("varyant", [
    pytest.param("bagimli", marks=BAGIMLI_KALIR),
    "bagimsiz",
    "bagimsiz_hiz_izlemeli",
])
def test_invertor_rampasi_degisse_de_el_besleme_agzina_ulasmaz(varyant):
    assert not m.acil_stop_sonucu(varyant, "rampa")["ulasir"]


@pytest.mark.parametrize("varyant", [
    pytest.param("bagimli", marks=BAGIMLI_KALIR),
    pytest.param("bagimsiz", marks=pytest.mark.xfail(
        strict=True, reason="SS1-t tek başına hız varsayımını korumuyor (beklenen)")),
    "bagimsiz_hiz_izlemeli",
])
def test_hiz_ve_rampa_birlikte_degisse_de_el_besleme_agzina_ulasmaz(varyant):
    assert not m.acil_stop_sonucu(varyant, "hiz_rampa")["ulasir"]


@pytest.mark.parametrize("varyant", list(m.VARYANTLAR))
def test_saldiri_yokken_her_varyant_guvenli(varyant):
    r = m.acil_stop_sonucu(varyant, "yok")
    assert r["durum"] == lab1.GUVENLI_DURUM and not r["ulasir"]


# ---------------------------------------------------------------- 4.3
def test_varsayim_etkisi_hesaplari_tutarli():
    e = m.varsayim_etkileri()
    assert e["sinir_hiz_kat1"] < e["sinir_hiz_kat0"]
    assert e["ss1_esik"] is None or e["ss1_esik"] > m.d("lab1.ss1_gecikmesi")
    assert e["izleme_esik"] is None or e["izleme_esik"] > m.d("lab4.hiz_izleme_esigi_carpani")
