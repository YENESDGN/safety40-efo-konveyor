"""LAB 5 gereksinimleri = testler (eğitim amaçlı model)."""
import pytest

from efo_sim import lab5_vuln as m

MEVCUT = m.MIMARILER["mevcut"][1]
HEDEF = m.MIMARILER["hedef"][1]


# ---------------------------------------------------------------- 5.1 Üç şart
@pytest.mark.parametrize("mevcut,duzeltilmis,beklenen", [
    ("2.4", "2.5", True), ("2.5", "2.5", False), ("2.10", "2.5", False),
    ("4.5", "4.7", True), ("4.7", "4.7", False), ("-", "2.5", False),
    ("7.1", "yok", True), ("-", "yok", False),
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


# ---------------------------------------------------------------- 5.3 Karar zaman içinde
def _akis(mimari):
    return {r["olay"]["id"]: r for r in m.olay_akisi(m.kayit("FOY-X"), m.MIMARILER[mimari][1])}


def test_kev_kaydi_bagimli_emniyette_karari_durdura_cevirir():
    a = _akis("mevcut")
    assert a["yayim"]["karar"] == "hemen_telafi"
    assert a["kev"]["karar"] == "durdur"


def test_bagimsiz_emniyette_aktif_istismar_telafiyi_one_ceker_ama_hatti_durdurmaz():
    a = _akis("hedef")
    assert a["yayim"]["karar"] == "devam_telafi"
    assert a["kev"]["karar"] == "hemen_telafi"
    assert all(r["karar"] != "durdur" for r in a.values())


@pytest.mark.parametrize("mimari", ["mevcut", "hedef"])
def test_telafiden_sonra_acik_ulasilamaz_ve_karar_devama_doner(mimari):
    r = _akis(mimari)["telafi"]
    assert not r["sart"]["ulasilabilir"] and r["karar"] == "devam"


@pytest.mark.parametrize("mimari", ["mevcut", "hedef"])
def test_yamadan_sonra_surum_artik_etkilenmez(mimari):
    r = _akis(mimari)["yama"]
    assert not r["sart"]["surum"] and r["karar"] == "devam"


def test_yamadan_sonra_yeniden_dogrulama_yalniz_bagimli_mimaride_gerekir():
    assert _akis("mevcut")["yama"]["dogrulama"]
    assert not _akis("hedef")["yama"]["dogrulama"]


# ---------------------------------------------------------------- 5.4 SBOM sapması
def test_her_saha_degisikligi_sbom_ile_saha_arasinda_fark_yaratir():
    teslim, gercek = m.teslim_sbom(), m.sbom()
    fark = set(m.sbom_farki(teslim, gercek))
    for deg in m.d("lab5.saha_degisiklikleri"):
        assert set(deg["farklar"]) <= fark


def test_eskimis_sbom_emniyete_yol_acan_acigi_etkilemez_gosterir():
    """Yedek CPU eski firmware'le geldi; teslim SBOM'u buna bakıp 'devam' diyor."""
    k = m.kayit("FOY-X")
    assert "FOY-X" in m.yanlis_negatifler(m.teslim_sbom(), MEVCUT)
    assert m.uretim_karari(k, MEVCUT, sbom_=m.teslim_sbom()) == "devam"
    assert m.emniyete_yol(m.bilesen(k)["dugum"], MEVCUT)


@pytest.mark.parametrize("mimari", ["mevcut", "hedef"])
def test_degisiklik_yonetimine_bagli_sbomda_yanlis_etkilemez_sonucu_sifir(mimari):
    assert m.yanlis_negatifler(m.degisiklik_yonetimli_sbom(), m.MIMARILER[mimari][1]) == []


# ---------------------------------------------------------------- 5.5 Ömrü bitmiş bileşen
def test_eol_kaydi_gercek_bir_sbom_bilesenine_baglidir():
    assert m.bilesen(m.d("lab5.eol_kaydi")) is not None


def test_yamasi_gelmeyecek_bilesende_telafi_kalici_olur_ve_degisim_planlanir():
    kp = m.kapanis(m.d("lab5.eol_kaydi"), MEVCUT)
    assert kp["yontem"] == "kalici_telafi" and kp["degistir"]
    assert kp["plan"] is not None and kp["plan"]["saat"] <= m.d("lab5.telafi_azami_sure")


def test_yamasi_olan_kayitta_kapanis_yamayla_olur():
    assert m.kapanis(m.kayit("FOY-X"), MEVCUT)["yontem"] == "yama"


def test_hedef_mimaride_eol_routera_ulasilamaz():
    k = m.d("lab5.eol_kaydi")
    assert not m.etkiler(k, HEDEF)
    assert m.kapanis(k, HEDEF)["yontem"] == "gerekmez"
