"""LAB 7 gereksinimleri = testler (eğitim amaçlı model; sentetik veri)."""
import pytest

from efo_sim import lab1_safety as lab1
from efo_sim import lab7_ai as m

NORMAL = {"yas_ms": 40, "hash": "a1", "parlaklik": 0.5, "keskinlik": 0.6}
TUM_EYLEMLER = [m.GEC, m.AYIR, m.SOR, m.DURDUR]


# ---------------------------------------------------------------- 7.1 Yanlış sınıflandırma
def test_esiksiz_model_kacak_hedefini_karsilamaz():
    ilk = m.esik_taramasi()[0][1]
    assert ilk["kacak"] > m.d("lab7.hedef_kacak_orani")


def test_secilen_esik_kacak_hedefini_operator_kapasitesi_icinde_karsilar():
    e = m.esik_sec()
    assert e is not None
    r = m.metrikler(m.veri_uret(), e)
    assert r["kacak"] <= m.d("lab7.hedef_kacak_orani")
    assert r["sor"] <= m.d("lab7.insan_kapasitesi")


def test_bagimsiz_metal_dedektoru_operator_yukunu_azaltir():
    assert m.esik_sec(md=True) <= m.esik_sec()
    veri = m.veri_uret()
    assert m.metrikler(veri, m.esik_sec(md=True))["sor"] <= m.metrikler(veri, m.esik_sec())["sor"]


def test_esik_arttikca_kacak_azalir_operator_yuku_artar():
    tarama = m.esik_taramasi()
    kacak = [t[1]["kacak"] for t in tarama]
    sor = [t[1]["sor"] for t in tarama]
    assert kacak == sorted(kacak, reverse=True)
    assert sor == sorted(sor)


def test_red_guven_dusuk_olsa_da_ayirir():
    assert m.model_karari(m.d("lab7.karar_siniri"), esik=0.99) == m.AYIR


# ---------------------------------------------------------------- 7.2 Girdi manipülasyonu
def test_normal_girdi_supheli_degil():
    assert m.girdi_supheli(NORMAL, ["x", "y", "z", "w"]) == []


@pytest.mark.parametrize("kare,gecmis,neden", [
    (NORMAL | {"yas_ms": 900}, (), "kare eski"),
    (NORMAL, ["a1"] * 4, "donmuş kare"),
    (NORMAL | {"parlaklik": 0.99}, (), "parlaklık sınır dışı"),
    (NORMAL | {"keskinlik": 0.01}, (), "bulanık / kapalı lens"),
])
def test_supheli_girdide_besleme_durur(kare, gecmis, neden):
    eylem, aciklama = m.guvenli_davranis(0.01, kare, gecmis, esik=0.6)
    assert eylem == m.DURDUR and neden in aciklama


def test_metal_dedektoru_yz_ile_celisirse_parca_ayrilir():
    assert m.guvenli_davranis(0.01, NORMAL, metal_dedektoru=True, esik=0.6)[0] == m.AYIR


# ---------------------------------------------------------------- 7.3 Güven düşük
@pytest.mark.parametrize("p", [0.40, 0.45, 0.49])
def test_esigin_altinda_ok_otomatik_verilmez(p):
    e = m.esik_sec()
    assert m.guven(p) < e
    assert m.model_karari(p, e) == m.SOR


# ---------------------------------------------------------------- YZ emniyet zincirinde değil
@pytest.mark.parametrize("eylem", TUM_EYLEMLER)
@pytest.mark.parametrize("durum", [lab1.CALISIYOR, lab1.DURUYOR, lab1.GUVENLI_DURUM])
def test_yz_hicbir_ciktiyla_acil_stopu_etkilemez(durum, eylem):
    assert m.hat_cevrimi(durum, lab1.girisler(acil_stop=True), eylem) == lab1.GUVENLI_DURUM


@pytest.mark.parametrize("eylem", TUM_EYLEMLER)
def test_yz_guvenli_durumdan_makineyi_calistiramaz(eylem):
    assert m.hat_cevrimi(lab1.GUVENLI_DURUM, lab1.girisler(start=True), eylem) == lab1.GUVENLI_DURUM


@pytest.mark.parametrize("istek", m.d("lab7.hiz_istegi_taramasi"))
def test_yz_hiz_istegi_normal_kumandada_kesilir(istek):
    assert m.normal_kumanda_hizi(istek) <= m.d("lab7.hiz_istegi_ust_siniri")


@pytest.mark.parametrize("istek", m.d("lab7.hiz_istegi_taramasi"))
def test_kumanda_atlatilsa_da_hiz_izleme_eli_korur(istek):
    assert not lab1.el_besleme_agzina_ulasir_mi(m.acil_stop_mesafesi(istek, kumanda_kesiyor=False))


@pytest.mark.xfail(strict=True, reason="emniyet tarafında hız izleme yoksa YZ hız isteği sınırı aşar (beklenen)")
def test_hiz_izleme_olmadan_da_eli_korur():
    for istek in m.d("lab7.hiz_istegi_taramasi"):
        assert not lab1.el_besleme_agzina_ulasir_mi(
            m.acil_stop_mesafesi(istek, kumanda_kesiyor=False, hiz_izleme=False))


# ---------------------------------------------------------------- 7.4 Ortak neden
def test_bagimsiz_hatalarda_ikinci_kanal_kacak_hedefini_saglar():
    r = m.metrikler(m.veri_uret(), m.esik_sec(md=True), md=True, ortak_neden=0.0)
    assert r["kacak"] <= m.d("lab7.hedef_kacak_orani")


def test_ortak_neden_payi_artinca_kacak_artar():
    kacaklar = [r["kacak"] for _, r in m.ortak_neden_taramasi()]
    assert kacaklar == sorted(kacaklar) and kacaklar[-1] > kacaklar[0]


def test_ortak_neden_esigi_asilinca_kacak_hedefi_asilir():
    """V20'deki bağımsızlık varsayımı kritik: küçük bir ortak neden payı hedefi bozar."""
    rho = m.ortak_neden_esigi()
    veri, e, hedef = m.veri_uret(), m.esik_sec(md=True), m.d("lab7.hedef_kacak_orani")
    assert m.metrikler(veri, e, md=True, ortak_neden=rho * 0.99)["kacak"] <= hedef
    assert m.metrikler(veri, e, md=True, ortak_neden=rho * 1.01)["kacak"] > hedef


# ---------------------------------------------------------------- 7.5 Kayma ve izleme
def test_kaymasiz_veri_devreye_almadaki_kumeyle_aynidir():
    assert m.veri_uret(0.0) == m.veri_uret()


def test_kusurlu_skorlar_saglama_kaydikca_kacak_hedefi_asilir():
    assert m.izleme_sonucu()["hedef_asim"] is not None


def test_operator_yuku_kaymayi_gostermez():
    """Kaçak toleransı aşıldığında bile operatöre sorulan oran alarm eşiğine ulaşmıyor."""
    iz = m.izleme_sonucu()
    assert iz["tolerans_asim"] is not None
    assert iz["alarm_sor"] is None or iz["alarm_sor"] > iz["tolerans_asim"]


def test_celiski_alarmi_kacak_toleransi_asilmadan_once_calar():
    """A7: YZ ile bağımsız dedektör arasındaki çelişki oranı izlenir; kayma tolerans içinde yakalanır."""
    iz = m.izleme_sonucu()
    assert iz["alarm_celiski"] is not None and iz["alarm_celiski"] < iz["tolerans_asim"]


@pytest.mark.xfail(strict=True, reason="Kaçak, devreye almada hedefe çok yakın; hiçbir izleme hedef aşılmadan önce davranamıyor")
def test_celiski_alarmi_kacak_hedefi_asilmadan_once_calar():
    iz = m.izleme_sonucu()
    assert iz["alarm_celiski"] < iz["hedef_asim"]
