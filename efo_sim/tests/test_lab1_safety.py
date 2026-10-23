"""LAB 1 iddiaları = testler (eğitim amaçlı model; emniyet doğrulaması değildir)."""
import pytest

from efo_sim import lab1_safety as m
from efo_sim.params import d

TUM_DURUMLAR = (m.CALISIYOR, m.DURUYOR, m.GUVENLI_DURUM)


# ---------------------------------------------------------------- 1.1 Durum makinesi
@pytest.mark.parametrize("tetikleyici", m.TETIKLEYICILER)
@pytest.mark.parametrize("baslangic", TUM_DURUMLAR)
def test_her_tetikleyici_her_durumdan_guvenli_duruma_goturur(tetikleyici, baslangic):
    assert m.sonraki_durum(baslangic, m.girisler(**{tetikleyici: True})) == m.GUVENLI_DURUM


def test_acil_stop_her_durumda_guvenli_duruma_gecer():
    # start ile birlikte basılsa bile acil stop kazanır
    assert m.sonraki_durum(m.CALISIYOR, m.girisler(acil_stop=True, start=True)) == m.GUVENLI_DURUM


def test_reset_yapilmadan_makine_yeniden_baslamaz():
    gecmis = m.calistir([
        m.girisler(start=True),            # çalışıyor
        m.girisler(cekme_ipi=True),        # çekme ipi → güvenli durum
        m.girisler(),                      # ip bırakıldı, reset yok
        m.girisler(start=True),            # reset olmadan start
    ])
    assert gecmis == [m.CALISIYOR, m.GUVENLI_DURUM, m.GUVENLI_DURUM, m.GUVENLI_DURUM]


def test_reset_makineyi_calistirmaz_ayri_start_gerekir():
    gecmis = m.calistir([
        m.girisler(start=True),
        m.girisler(kapak_acik=True),
        m.girisler(reset=True),            # reset → yalnızca DURUYOR
        m.girisler(),                      # kendiliğinden başlamaz
        m.girisler(start=True),            # bilinçli start
    ])
    assert gecmis == [m.CALISIYOR, m.GUVENLI_DURUM, m.DURUYOR, m.DURUYOR, m.CALISIYOR]


def test_tetikleyici_surerken_reset_ise_yaramaz():
    assert m.sonraki_durum(m.GUVENLI_DURUM, m.girisler(acil_stop=True, reset=True)) == m.GUVENLI_DURUM


def test_yongalama_makinesi_durursa_bant_da_durur():
    assert m.sonraki_durum(m.CALISIYOR, m.girisler(yongalama_calisiyor=False)) == m.DURUYOR


def test_yongalama_yeniden_calisinca_bant_kendiliginden_baslamaz():
    gecmis = m.calistir([
        m.girisler(start=True),
        m.girisler(yongalama_calisiyor=False),
        m.girisler(),                      # yongalama yeniden çalışıyor, start yok
    ])
    assert gecmis[-1] == m.DURUYOR


def test_yongalama_dururken_start_bandi_calistirmaz():
    assert m.sonraki_durum(m.DURUYOR, m.girisler(start=True, yongalama_calisiyor=False)) == m.DURUYOR


# ---------------------------------------------------------------- Tek arıza (kategori/PL farkı)
def test_tek_arizada_iki_kanalli_yapi_yine_durur():
    assert m.motor_gucu_kesildi_mi(kanal_sayisi=2, kaynamis={"K1"})


def test_tek_arizada_tek_kanalli_yapi_durmaz():
    assert not m.motor_gucu_kesildi_mi(kanal_sayisi=1, kaynamis={"K1"})


def test_iki_kanalli_yapida_kaynamis_kontaktor_izlemeyle_gorulur():
    assert m.izleme_arizayi_gorur_mu(kanal_sayisi=2, kaynamis={"K1"})
    assert not m.izleme_arizayi_gorur_mu(kanal_sayisi=1, kaynamis={"K1"})


def test_ariza_durumundan_ariza_giderilmeden_cikilmaz():
    assert m.sonraki_durum(m.ARIZA, m.girisler(reset=True)) == m.ARIZA
    assert m.sonraki_durum(m.ARIZA, m.girisler(reset=True, ariza_giderildi=True)) == m.DURUYOR


# ---------------------------------------------------------------- 1.2 Durma mesafesi
@pytest.mark.parametrize("kategori", [0, 1])
def test_hedef_parametrelerle_durma_mesafesi_sinirin_altinda_kalir(kategori):
    s = m.durma_mesafesi(d("lab1.bant_hizi"), kategori)
    assert s < d("lab1.guvenli_mesafe")
    assert not m.el_besleme_agzina_ulasir_mi(s)


def test_durma_mesafesi_hizla_artar():
    v = d("lab1.bant_hizi")
    for kat in (0, 1):
        assert m.durma_mesafesi(2 * v, kat) > m.durma_mesafesi(v, kat)


@pytest.mark.parametrize("kategori", [0, 1])
def test_sinir_hizda_durma_mesafesi_guvenli_mesafeye_esittir(kategori):
    vs = m.sinir_hiz(kategori)
    assert m.durma_mesafesi(vs, kategori) == pytest.approx(d("lab1.guvenli_mesafe"))


def test_nominal_hiz_sinir_hizlarin_altinda():
    assert d("lab1.bant_hizi") < min(m.sinir_hiz(0), m.sinir_hiz(1))


# ---------------------------------------------------------------- 1.3 PLr
@pytest.mark.parametrize("S,F,P,beklenen", [
    ("S2", "F2", "P2", "e"),
    ("S1", "F1", "P1", "a"),
    ("S2", "F1", "P2", "d"),
    ("S2", "F2", "P1", "d"),
    ("S1", "F2", "P2", "c"),
])
def test_risk_grafigi_bilinen_kombinasyonlari_dogru_verir(S, F, P, beklenen):
    assert m.plr(S, F, P) == beklenen


def test_risk_grafigi_sekiz_kombinasyonun_hepsini_kapsar():
    assert len(d("lab1.plr_grafigi")) == 8


def test_besleme_agzi_fonksiyonu_en_yuksek_plr_alir():
    tablo = {r["id"]: r["PLr"] for r in m.plr_tablosu()}
    assert tablo["SF1"] == "e"
    assert tablo["SF1"] == max(tablo.values())
