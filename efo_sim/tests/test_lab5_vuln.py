"""LAB 5 gereksinimleri = testler (eğitim amaçlı model)."""
import pytest

from efo_sim import lab5_vuln as m

MEVCUT = m.MIMARILER["mevcut"][1]
HEDEF = m.MIMARILER["hedef"][1]


# ---------------------------------------------------------------- 5.1 Üç şart
@pytest.mark.parametrize("mevcut,duzeltilmis,beklenen", [
    ("2.4", "2.5", True), ("2.5", "2.5", False), ("2.10", "2.5", False),
    ("4.5", "4.7", True), ("4.7", "4.7", False), ("-", "2.5", False),
])
def test_surum_karsilastirmasi_sayisaldir(mevcut, duzeltilmis, beklenen):
    assert m.surum_etkileniyor(mevcut, duzeltilmis) is beklenen


def test_foydeki_kayit_mevcut_mimaride_uc_sarti_da_saglar():
    assert m.uc_sart(m.kayit("FOY-X"), MEVCUT) == {"var": True, "surum": True, "ulasilabilir": True}


def test_sbomda_olmayan_urun_cvss_yuksek_olsa_da_etkilemez():
    k = m.kayit("SSA-688146")
    assert k["cvss"] >= 9.0
    assert not m.uc_sart(k, MEVCUT)["var"]
    assert m.uretim_karari(k, MEVCUT) == "devam"


def test_web_sunucusu_kapaliysa_csrf_acigi_ulasilamaz():
    k = m.kayit("CVE-2024-47100")
    assert m.etkiler(k, MEVCUT)
    assert m.uc_sart(k, HEDEF)["surum"] and not m.uc_sart(k, HEDEF)["ulasilabilir"]


def test_her_sbom_bileseni_saldiri_grafinda_bir_dugume_baglidir():
    for b in m.sbom().values():
        assert b["dugum"] in m.lab4.DUGUMLER


def test_telafi_onlemleri_mimarideki_kosullari_kapatir():
    for t in m.d("lab5.telafi_onlemleri"):
        assert t["kosul"] in MEVCUT and t["kosul"] in HEDEF


# ---------------------------------------------------------------- 5.2 Karar akışı
def test_cvss_tek_basina_karari_belirlemez():
    """Aynı 9,8'lik kayıt mimariye göre farklı karar alır."""
    k = m.kayit("FOY-X")
    assert m.uretim_karari(k, MEVCUT) != m.uretim_karari(k, HEDEF)


def test_bagimsiz_emniyette_plc_acigi_uretimi_durdurmaz():
    assert m.uretim_karari(m.kayit("FOY-X"), HEDEF) == "devam_telafi"


def test_bagimli_emniyette_istismar_belirtisi_varsa_hat_kontrollu_durur():
    assert m.uretim_karari(m.kayit("FOY-X"), MEVCUT, istismar_belirtisi=True) == "durdur"


def test_telafi_plani_acigi_ulasilamaz_kilar_ve_azami_surede_biter():
    k = m.kayit("FOY-X")
    onlem = {t["id"]: t for t in m.d("lab5.telafi_onlemleri")}
    for _, mim in m.MIMARILER.values():
        p = m.telafi_plani(k, mim)
        assert p is not None and p["saat"] <= m.d("lab5.telafi_azami_sure")
        assert not m.etkiler(k, mim | {onlem[i]["kosul"]: False for i in p["onlemler"]})


def test_plc_yamasi_validasyonu_yalniz_bagimli_mimaride_etkiler():
    plc = m.sbom()["PLC_FW"]
    assert m.validasyon_etkilenir(plc, MEVCUT)
    assert not m.validasyon_etkilenir(plc, HEDEF)


def test_emniyet_rolesi_degisikligi_her_mimaride_validasyon_gerektirir():
    role = m.sbom()["EMNIYET_RELE"]
    assert m.validasyon_etkilenir(role, MEVCUT) and m.validasyon_etkilenir(role, HEDEF)


@pytest.mark.parametrize("mimari", ["mevcut", "hedef"])
def test_yama_once_test_tezgahinda_denenir(mimari):
    adimlar = m.yama_adimlari(m.kayit("FOY-X"), m.MIMARILER[mimari][1])
    assert "test tezgâhı" in adimlar[0]
    emniyet_testi = any("SF1" in a for a in adimlar)
    assert emniyet_testi is (mimari == "mevcut")
