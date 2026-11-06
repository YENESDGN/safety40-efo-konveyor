"""LAB 6 gereksinimleri = testler (eğitim amaçlı model)."""
import pytest

from efo_sim import lab6_incident as m


# ---------------------------------------------------------------- 6.1 Emniyet doğrulaması
def test_referansla_karsilastirma_degisen_ayarlari_bulur():
    assert set(m.konfig_farki()) == {"plc_proje_crc", "rampa_suresi"}


def test_fark_yoksa_emniyet_guvende():
    ref = m.d("lab6.referans_konfig")
    assert m.konfig_farki(ref, dict(ref)) == []
    assert m.emniyet_degerlendirmesi("bagimli", fark=[])["guvende"]


def test_mevcut_bagimli_mimaride_okunan_konfigurasyonla_emniyet_guvende_degil():
    assert not m.emniyet_degerlendirmesi("bagimli")["guvende"]


@pytest.mark.parametrize("varyant", ["bagimsiz", "bagimsiz_hiz_izlemeli"])
def test_bagimsiz_emniyette_ayni_farklarla_acil_stop_guvenli_durdurur(varyant):
    assert m.emniyet_degerlendirmesi(varyant)["guvende"]


def test_emniyet_rolesi_ayari_degismisse_hicbir_mimaride_guvenilmez():
    for v in m.lab4.VARYANTLAR:
        assert not m.emniyet_degerlendirmesi(v, fark=["emniyet_rolesi_ayar"])["guvende"]


# ---------------------------------------------------------------- 6.2 Zaman çizgisi
def test_kanit_silinmeden_once_alinir():
    assert m.kanit_korunur(m.AKIS)


def test_resetleyip_devam_etmek_kaniti_siler():
    assert not m.kanit_korunur(m.AKIS_RESET)


def test_ilk_eylem_emniyet_ve_kurtarmadan_once_emniyet_degerlendirmesi():
    assert m.emniyet_ilk(m.AKIS)
    assert not m.emniyet_ilk(m.AKIS_RESET)


def test_ilk_15_dakikada_hat_durdurulur_ve_uzak_baglanti_kesilir():
    ilk = [e for e in m.AKIS if e[0] <= m.d("lab6.kilometre_taslari")["ilk_mudahale"]]
    assert any(e[3] == "emniyet" and "LOTO" in e[2] for e in ilk)
    assert any(e[3] == "erisim" for e in ilk)


def test_servis_hesabi_ilk_iki_saatte_kapanir():
    assert m.hesap_kapatma_dakikasi(m.AKIS) <= m.d("lab6.kilometre_taslari")["ilk_asama"]


def test_start_emniyet_fonksiyon_testinden_once_verilmez():
    assert m.yeniden_baslatma_testten_sonra(m.AKIS)
    assert not m.yeniden_baslatma_testten_sonra(m.AKIS_RESET)


def test_her_kanit_kimligi_tanimli():
    for e in m.AKIS + m.AKIS_RESET:
        assert set(e[4]) | set(e[5]) <= set(m.KANITLAR)


# ---------------------------------------------------------------- 6.3 CRA paketleri
@pytest.mark.parametrize("paket", list(m.CRA_PAKETLERI))
def test_cra_paketindeki_her_bilgi_suresinden_once_hazir(paket):
    for alan, (t, ok) in m.cra_hazirlik()[paket].items():
        assert ok, f"{paket} / {alan}: {t} dk"


def test_reset_akisi_cra_paketlerini_dolduramaz():
    h = m.cra_hazirlik(m.AKIS_RESET)
    assert not all(ok for alanlar in h.values() for _, ok in alanlar.values())


# ---------------------------------------------------------------- 6.4 Etki alanı
def _etki(duzen):
    return {r["kurulum"]["id"]: r for r in m.etki_alani(duzen)}


def test_paylasilan_hesap_ele_gecince_birden_cok_kurulum_etkilenir():
    e = _etki("mevcut")
    assert sum(r["ulasilir"] for r in e.values()) > 1
    assert sum(r["emniyet_riskte"] for r in e.values()) > 1


def test_kisisel_hesaplarda_etki_olayin_tesisiyle_sinirli_kalir():
    ulasilan = [i for i, r in _etki("kisisel").items() if r["ulasilir"]]
    assert ulasilan == [m.OLAY_KURULUMU]


@pytest.mark.parametrize("duzen", ["mevcut", "kisisel"])
def test_tesis_onayli_ya_da_kapali_uzak_erisimde_kurulum_ulasilamaz(duzen):
    for r in m.etki_alani(duzen):
        if r["kurulum"]["uzak"] != "surekli":
            assert not r["ulasilir"]


@pytest.mark.parametrize("duzen", ["mevcut", "kisisel"])
def test_bagimsiz_emniyetli_kurulumda_erisim_olsa_da_emniyet_guvende(duzen):
    for r in m.etki_alani(duzen):
        if r["kurulum"]["emniyet"] != "bagimli":
            assert not r["emniyet_riskte"]


# ---------------------------------------------------------------- 6.5 Kanıt ömrü
def test_bu_akista_her_kanit_omru_dolmadan_alinir():
    assert m.kanit_kayiplari(m.AKIS) == set()


def test_ilk_iki_saat_her_kanitin_omrunden_kisadir():
    assert all(o > m.d("lab6.kilometre_taslari")["ilk_asama"] for o in m.d("lab6.kanit_omru").values())


def test_gec_gelen_ekipte_router_logu_kaybolur():
    assert "K3" in m.kanit_kayiplari(m.gec_akis())


def test_kaybolan_kanit_cra_bildirimini_eksik_birakir():
    h = m.cra_hazirlik(m.gec_akis())
    assert not h["bildirim"]["Olayın genel niteliği"][1]
    assert m.cra_hazirlik()["bildirim"]["Olayın genel niteliği"][1]
