"""LAB 1 — Emniyet fonksiyonu modelleri (eğitim amaçlı; emniyet doğrulaması değildir).

1.1 Durum makinesi: acil stop, çekme ipi, koruyucu kapak, yongalama interlock'u, reset.
    Tek arıza gösterimi: kaynamış kontaktörde tek ve iki kanallı yapı.
1.2 Durma mesafesi: el bant tarafından çekilirken bant, besleme ağzına ulaşmadan duruyor mu?
1.3 PLr: ISO 13849-1 risk grafiği (S, F, P → PLr a–e).

Çalıştırma (repo kökünden):  python -m efo_sim.lab1_safety
"""
import math

from efo_sim.params import OUT_DIR, bolum_metni, d, sayi

# ---------------------------------------------------------------- 1.1 Durum makinesi
CALISIYOR, DURUYOR, GUVENLI_DURUM, ARIZA = "ÇALIŞIYOR", "DURUYOR", "GÜVENLİ_DURUM", "ARIZA"
TETIKLEYICILER = ("acil_stop", "cekme_ipi", "kapak_acik")


def girisler(**degisen):
    """Varsayılan (her şey normal) giriş seti; yalnızca değişenler verilir."""
    g = {"acil_stop": False, "cekme_ipi": False, "kapak_acik": False,
         "yongalama_calisiyor": True, "reset": False, "start": False, "ariza_giderildi": False}
    g.update(degisen)
    return g


def sonraki_durum(durum, g):
    """Bir kumanda çevriminde durum geçişi.

    - Herhangi bir tetikleyici her durumdan GÜVENLİ_DURUM'a götürür (ARIZA hariç; arıza öncelikli).
    - GÜVENLİ_DURUM'dan çıkış yalnızca reset ile ve DURUYOR'a olur: reset makineyi çalıştırmaz.
    - Yongalama makinesi durursa bant DURUYOR'a geçer; yongalama yeniden çalışınca kendiliğinden başlamaz.
    - DURUYOR → ÇALIŞIYOR yalnızca ayrı bir start komutuyla.
    """
    tetik = any(g[t] for t in TETIKLEYICILER)
    if durum == ARIZA:
        return DURUYOR if (g["reset"] and g["ariza_giderildi"] and not tetik) else ARIZA
    if tetik:
        return GUVENLI_DURUM
    if durum == GUVENLI_DURUM:
        return DURUYOR if g["reset"] else GUVENLI_DURUM
    if durum == CALISIYOR and not g["yongalama_calisiyor"]:
        return DURUYOR
    if durum == DURUYOR and g["start"] and g["yongalama_calisiyor"]:
        return CALISIYOR
    return durum


def calistir(adimlar, durum=DURUYOR):
    """Giriş setleri listesini sırayla uygular, her adımdaki durumu döndürür."""
    gecmis = []
    for g in adimlar:
        durum = sonraki_durum(durum, g)
        gecmis.append(durum)
    return gecmis


def motor_gucu_kesildi_mi(kanal_sayisi, kaynamis):
    """Durdurma talebinde motor gücü kesiliyor mu?

    Kanallar seri bağlı kontaktörler (K1, K2) olarak modellenir. Kaynamış kontaktör açılmaz.
    Seri hatta en az bir kontaktör açılırsa motor enerjisiz kalır.
    """
    kanallar = [f"K{i + 1}" for i in range(kanal_sayisi)]
    return any(k not in kaynamis for k in kanallar)


def izleme_arizayi_gorur_mu(kanal_sayisi, kaynamis):
    """Geri besleme (EDM) izlemesi: iki kanallı yapıda kanallar arasındaki uyumsuzluk görülür."""
    return kanal_sayisi >= 2 and len(kaynamis) > 0


def tek_ariza_tablosu():
    """Tek arıza (K1 kaynaması) altında iki mimarinin davranışı."""
    satirlar = []
    for kanal, ad in ((1, "Tek kanal (K1)"), (2, "İki kanal + izleme (K1, K2)")):
        for kaynamis in ((), ("K1",)):
            satirlar.append({
                "mimari": ad,
                "ariza": "K1 kaynamış" if kaynamis else "arıza yok",
                "durur": motor_gucu_kesildi_mi(kanal, set(kaynamis)),
                "ariza_gorulur": izleme_arizayi_gorur_mu(kanal, set(kaynamis)),
            })
    return satirlar


# ---------------------------------------------------------------- 1.2 Durma mesafesi
def toplam_gecikme():
    return d("lab1.insan_reaksiyon_suresi") + d("lab1.sistem_tepki_suresi")


def ivme_kat0():
    """STO sonrası serbest duruş ivmesi (nominal hızdan durma süresinden)."""
    return d("lab1.bant_hizi") / d("lab1.durma_suresi_kat0")


def ivme_rampa(rampa_suresi=None):
    """İnvertör rampa ivmesi: rampa süresi nominal hızdan sıfıra tanımlıdır."""
    rampa = d("lab1.rampa_suresi_kat1") if rampa_suresi is None else rampa_suresi
    return d("lab1.bant_hizi") / rampa


def durma_mesafesi(hiz, kategori, rampa_suresi=None, ss1_emniyette=False):
    """Kapılma anından bant durana kadar elin aldığı yol (m).

    kategori 0: tork hemen kesilir, bant serbest durur.
    kategori 1: invertör rampasıyla yavaşlar, rampa sonunda STO.
      ss1_emniyette=False → STO'yu invertör/PLC rampa bitince verir (emniyet kumandaya bağımlı).
      ss1_emniyette=True  → SS1-t: emniyet rölesi sabit gecikme sonunda STO verir (bağımsız).
    """
    gecikme_yolu = hiz * toplam_gecikme()
    if kategori == 0:
        return gecikme_yolu + hiz ** 2 / (2 * ivme_kat0())
    a = ivme_rampa(rampa_suresi)
    rampa_zamani = hiz / a
    if not ss1_emniyette or rampa_zamani <= d("lab1.ss1_gecikmesi"):
        return gecikme_yolu + hiz ** 2 / (2 * a)
    t = d("lab1.ss1_gecikmesi")
    v1 = hiz - a * t
    rampa_yolu = (hiz + v1) / 2 * t
    serbest_yol = v1 ** 2 / (2 * ivme_kat0())
    return gecikme_yolu + rampa_yolu + serbest_yol


def el_besleme_agzina_ulasir_mi(mesafe):
    return mesafe >= d("lab1.guvenli_mesafe")


def sinir_hiz(kategori):
    """Durma mesafesinin güvenli mesafeye eşit olduğu bant hızı (ikinci derece denklem)."""
    a = ivme_kat0() if kategori == 0 else ivme_rampa()
    t, s = toplam_gecikme(), d("lab1.guvenli_mesafe")
    # v²/(2a) + v·t − s = 0
    return (-t + math.sqrt(t ** 2 + 2 * s / a)) * a


# ---------------------------------------------------------------- 1.3 PLr
def plr(S, F, P):
    return d("lab1.plr_grafigi")[f"{S}-{F}-{P}"]


def plr_tablosu():
    sil = d("lab1.pl_sil_karsiligi")
    kat = d("lab1.pl_tipik_kategori")
    tablo = []
    for sf in d("lab1.emniyet_fonksiyonlari"):
        seviye = plr(sf["S"], sf["F"], sf["P"])
        tablo.append({**sf, "PLr": seviye, "SIL": sil[seviye], "kategori": kat[seviye]})
    return tablo


# ---------------------------------------------------------------- Çıktılar
def _grafik_durma_mesafesi(yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker

    v_min, v_max = d("lab1.grafik_hiz_araligi")
    n = d("lab1.grafik_nokta_sayisi")
    hizlar = [v_min + (v_max - v_min) * i / (n - 1) for i in range(n)]
    kat0 = [durma_mesafesi(v, 0) for v in hizlar]
    kat1 = [durma_mesafesi(v, 1) for v in hizlar]
    sinir = d("lab1.guvenli_mesafe")

    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=200)
    ax.plot(hizlar, kat0, color="#2a78d6", lw=2, label="Stop kat. 0 (STO hemen)")
    ax.plot(hizlar, kat1, color="#eb6834", lw=2, label="Stop kat. 1 (rampa + STO)")
    ax.axhline(sinir, color="#16223a", lw=1.2, ls="--")
    ax.text(v_min, sinir * 1.03, f"güvenli mesafe sınırı {sayi(sinir)} m", fontsize=8, color="#16223a")
    v_nom = d("lab1.bant_hizi")
    ax.axvline(v_nom, color="#9aa3b2", lw=1, ls=":")
    ax.text(v_nom * 1.03, max(kat1) * 0.55, f"nominal hız\n{sayi(v_nom)} m/s", fontsize=8, color="#52514e")
    for kat, renk in ((0, "#2a78d6"), (1, "#eb6834")):
        vs = sinir_hiz(kat)
        ax.plot([vs], [sinir], "o", ms=6, color=renk, mec="white", mew=1.5)
        ax.annotate(f"{sayi(vs)} m/s", (vs, sinir), textcoords="offset points",
                    xytext=(8, -14) if kat == 0 else (-54, 6), fontsize=8, color="#52514e")
    virgul = matplotlib.ticker.FuncFormatter(lambda x, _: sayi(x))
    ax.xaxis.set_major_formatter(virgul)
    ax.yaxis.set_major_formatter(virgul)
    ax.set_xlabel("Bant hızı (m/s)")
    ax.set_ylabel("Durma mesafesi (m)")
    ax.set_title("Bant hızına karşı durma mesafesi (eğitim amaçlı model)", fontsize=10, loc="left")
    ax.grid(alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(yol)
    plt.close(fig)


def sonuc_durma_md():
    """PDF'e giren sonuç tabloları (değerler koddan üretilir)."""
    v = d("lab1.bant_hizi")
    s0, s1 = durma_mesafesi(v, 0), durma_mesafesi(v, 1)
    sinir = d("lab1.guvenli_mesafe")
    satirlar = [
        "| Durum | Durma mesafesi | Güvenli mesafe | El besleme ağzına ulaşır mı? |",
        "|---|---|---|---|",
        f"| Stop kat. 0, nominal hız {sayi(v)} m/s | {sayi(s0, 3)} m | {sayi(sinir)} m | "
        f"{'Evet' if el_besleme_agzina_ulasir_mi(s0) else 'Hayır'} |",
        f"| Stop kat. 1, nominal hız {sayi(v)} m/s | {sayi(s1, 3)} m | {sayi(sinir)} m | "
        f"{'Evet' if el_besleme_agzina_ulasir_mi(s1) else 'Hayır'} |",
        "",
        f"Sınır hızlar: durma mesafesi stop kat. 0'da **{sayi(sinir_hiz(0))} m/s**, "
        f"stop kat. 1'de **{sayi(sinir_hiz(1))} m/s** bant hızında güvenli mesafeye eşitleniyor.",
        "",
        "| Mimari | Arıza | Durdurma talebinde motor durur mu? | Arıza görülür mü? |",
        "|---|---|---|---|",
    ]
    for r in tek_ariza_tablosu():
        satirlar.append(f"| {r['mimari']} | {r['ariza']} | {'Evet' if r['durur'] else '**Hayır**'} | "
                        f"{'Evet' if r['ariza_gorulur'] else 'Hayır'} |")
    return "\n".join(satirlar) + "\n"


def sonuc_plr_md():
    satirlar = ["| Fonksiyon | S | F | P | PLr | Yaklaşık SIL | Tipik kategori |", "|---|---|---|---|---|---|---|"]
    for r in plr_tablosu():
        satirlar.append(f"| {r['id']} — {r['ad']} | {r['S']} | {r['F']} | {r['P']} | **{r['PLr']}** | "
                        f"{r['SIL']} | {r['kategori']} |")
    satirlar.append("")
    satirlar += [f"- **{r['id']}:** {r['gerekce']}" for r in plr_tablosu()]
    return "\n".join(satirlar) + "\n"


def main():
    OUT_DIR.mkdir(exist_ok=True)
    _grafik_durma_mesafesi(OUT_DIR / "lab1_durma_mesafesi.png")
    (OUT_DIR / "lab1_sonuclar_durma.md").write_text(sonuc_durma_md(), encoding="utf-8")
    (OUT_DIR / "lab1_sonuclar_plr.md").write_text(sonuc_plr_md(), encoding="utf-8")
    (OUT_DIR / "lab1_params.yaml").write_text(bolum_metni("lab1"), encoding="utf-8")
    print(sonuc_durma_md())
    print(sonuc_plr_md())


if __name__ == "__main__":
    main()
