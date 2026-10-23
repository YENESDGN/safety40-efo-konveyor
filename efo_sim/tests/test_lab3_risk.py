"""LAB 3 iddiaları = testler (eğitim amaçlı model)."""
import pytest

from efo_sim import lab1_safety as lab1
from efo_sim import lab3_risk as m
from efo_sim.params import d


def _senaryo(sid, L, S, E):
    return {"id": sid, **{p: {"deger": v, "etiket": "VARSAYIM", "dayanak": "test"} for p, v in
                          (("L", L), ("S", S), ("E", E))}}


# ---------------------------------------------------------------- 3.1
@pytest.mark.parametrize("skor,beklenen", [
    (27, "Kritik"), (18, "Kritik"), (17, "Yüksek"), (9, "Yüksek"),
    (8, "Orta"), (4, "Orta"), (3, "Düşük"), (1, "Düşük"),
])
def test_bant_sinirlari_dogru(skor, beklenen):
    assert m.bant(skor) == beklenen


def test_skor_olasilik_siddet_ve_maruziyetin_carpimidir():
    assert m.skor(_senaryo("X", 2, 3, 2)) == 12


def test_s3_olan_senaryo_skoru_ne_olursa_olsun_one_alinir():
    yuksek_skorlu_s2 = _senaryo("A", 3, 2, 3)   # skor 18, Kritik
    dusuk_skorlu_s3 = _senaryo("B", 1, 3, 1)    # skor 3, Düşük
    sira = m.oncelik_sirasi([yuksek_skorlu_s2, dusuk_skorlu_s3])
    assert [s["id"] for s in sira] == ["B", "A"]


def test_register_siralamasi_s3_kuralina_uyar():
    sira = m.oncelik_sirasi(m.senaryolar())
    s3_bitti = False
    for s in sira:
        if m.puan(s, "S") < d("lab3.oncelikli_siddet"):
            s3_bitti = True
        else:
            assert not s3_bitti, "S=3 senaryosu S<3 bir senaryonun arkasında kaldı"


def test_tum_puanlar_bir_ile_uc_arasinda_ve_dayanakli():
    alt, ust = d("lab3.puan_araligi")
    for s in m.senaryolar():
        for p in m.PARAMETRELER:
            assert alt <= m.puan(s, p) <= ust
            assert s[p]["dayanak"] and s[p]["etiket"]


def test_fizikse_baglanan_her_senaryo_insana_etkiyle_biter():
    for s in m.senaryolar():
        assert s["fiziksel_sonuc"]
        assert "veri çalındı" not in s["fiziksel_sonuc"].lower()


def test_yalniz_veri_okuyan_kontrol_senaryosu_emniyet_bulgusu_sayilmaz():
    k1 = next(s for s in m.senaryolar() if s["id"] == "K1")
    assert m.puan(k1, "S") == 1
    assert m.oncelik_sirasi(m.senaryolar())[-1]["id"] == "K1"


# ---------------------------------------------------------------- 3.2
def test_duyarlilik_varsayima_dayali_her_puani_iki_yonde_dener():
    _, satirlar = m.duyarlilik()
    beklenen = 0
    alt, ust = d("lab3.puan_araligi")
    for s in m.senaryolar():
        for p in m.PARAMETRELER:
            if s[p]["etiket"] in m.VARSAYIMA_DAYALI:
                beklenen += (m.puan(s, p) > alt) + (m.puan(s, p) < ust)
    assert len(satirlar) == beklenen


def test_duyarlilik_sayisal_tutarli():
    for r in m.duyarlilik()[1]:
        assert m.bant(r["skor"]) == r["bant"]


# ---------------------------------------------------------------- 3.3
def test_normal_parametrelerle_el_besleme_agzina_ulasmaz():
    normal = m.siber_fiziksel_tablo()[0]
    assert not normal["ulasir"]


def test_rampa_parametresi_degisirse_el_besleme_agzina_ulasir():
    v = d("lab1.bant_hizi")
    mesafe = lab1.durma_mesafesi(v, 1, rampa_suresi=d("lab3.saldiri_rampa_suresi"))
    assert lab1.el_besleme_agzina_ulasir_mi(mesafe)


def test_rampa_saldirisinda_el_bant_durmadan_agza_varir():
    rampa = next(r for r in m.siber_fiziksel_tablo() if r["durum"] == "Saldırı: yalnız rampa uzatma")
    assert rampa["varis"] < rampa["durma"]


def test_yalniz_hiz_artisi_nominal_rampada_siniri_asmaz():
    hiz = next(r for r in m.siber_fiziksel_tablo() if r["durum"] == "Saldırı: yalnız hız artışı")
    assert not hiz["ulasir"]


def test_el_yolu_durma_mesafesiyle_tutarli():
    for _, hiz, rampa in m.saldiri_durumlari():
        t_son = m.bant_durma_suresi(hiz, rampa)
        assert m.el_yolu(t_son, hiz, rampa) == pytest.approx(lab1.durma_mesafesi(hiz, 1, rampa_suresi=rampa))
