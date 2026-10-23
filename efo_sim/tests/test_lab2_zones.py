"""LAB 2 kuralları = testler. Hedef mimari her kurala uyar; mevcut (varsayım) mimaride kurallar ihlali yakalar."""
import pytest

from efo_sim import lab2_zones as m


def test_internetten_ya_da_uzak_erisimden_emniyet_bolgesine_dogrudan_kenar_yok():
    assert m.kural_disaridan_emniyete_dogrudan_kenar_yok(m.HEDEF) == []


def test_bolgeler_arasindaki_her_kenar_bir_conduitten_gecer():
    assert m.kural_her_bolgeler_arasi_kenar_conduitten_gecer(m.HEDEF) == []


def test_her_conduitte_en_az_bir_kontrol_tanimli():
    assert m.kural_her_conduitte_kontrol_var(m.HEDEF) == []


def test_emniyet_bolgesine_disaridan_yazma_yonunde_akis_yok():
    assert m.kural_emniyete_disaridan_yazma_yok(m.HEDEF) == []


def test_dis_bolge_yalnizca_dmzye_baglanir():
    assert m.kural_dis_bolge_yalniz_dmzye_baglanir(m.HEDEF) == []


def test_kullanilan_her_conduit_tanimli():
    for mimari in (m.HEDEF, m.MEVCUT):
        tanimli = set(mimari["conduitler"])
        assert {a[4] for a in mimari["akislar"] if a[4]} <= tanimli


def test_her_varlik_bir_bolgeye_atanmis_ve_akislar_bilinen_varliklari_kullanir():
    for mimari in (m.HEDEF, m.MEVCUT):
        for k, h, *_ in mimari["akislar"]:
            assert k in mimari["atama"] and h in mimari["atama"]
        assert set(mimari["atama"]) <= set(m.VARLIKLAR)


def test_emniyet_rolesi_kendi_bolgesinde_ve_yalniz_disari_durum_verir():
    assert m.bolge(m.HEDEF, "emniyet") == m.EMNIYET
    disari = [a for a in m.HEDEF["akislar"] if a[0] == "emniyet" and m.bolge(m.HEDEF, a[1]) != m.EMNIYET]
    assert all("durum" in a[2] for a in disari)


@pytest.mark.parametrize("kid", ["K2", "K3", "K4", "K5"])
def test_mevcut_varsayim_mimaride_kural_ihlali_yakalanir(kid):
    assert m.kontrol(m.MEVCUT)[kid], f"{kid} mevcut mimaride ihlal bulmalıydı"


def test_mermaid_veriden_uretilir_ve_her_akisi_icerir():
    metin = m.mermaid(m.HEDEF)
    assert metin.startswith("flowchart")
    assert metin.count("-->") + metin.count("-.->") == len(m.HEDEF["akislar"])
    for z in set(m.HEDEF["atama"].values()):
        assert f"subgraph {z}" in metin


def test_bolge_diyagrami_her_bolgeler_arasi_gecisi_gosterir():
    metin = m.mermaid_bolge(m.HEDEF)
    gecisler = {(m.bolge(m.HEDEF, a[0]), m.bolge(m.HEDEF, a[1]), a[4]) for a in m.bolgeler_arasi(m.HEDEF)}
    assert metin.count("-->") == len(gecisler)
    assert "kontrolsüz" not in metin
    assert "kontrolsüz" in m.mermaid_bolge(m.MEVCUT)
