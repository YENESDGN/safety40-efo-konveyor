"""LAB 3 — Risk register ve siber-fiziksel bağ (eğitim amaçlı; resmî risk değerlendirmesi değildir).

3.1 Skor = L × S × E; bant; öncelik sırası (S=3 kuralı).
    L = olasılık, S = şiddet, E = maruziyet (föy açılımı yazmıyor; bu yorum bir varsayımdır).
3.2 Duyarlılık: varsayıma dayalı her puan ±1 → öncelik sırası değişiyor mu?
3.3 Siberden fiziksele: invertör rampa/hız parametresi değişince LAB 1.2 modeli yeniden çalıştırılır.

Çalıştırma (repo kökünden):  python -m efo_sim.lab3_risk
"""
from efo_sim import lab1_safety as lab1
from efo_sim.params import OUT_DIR, bolum_metni, d, sayi

PARAMETRELER = ("L", "S", "E")
VARSAYIMA_DAYALI = {"VARSAYIM", "ÇIKARIM"}


# ---------------------------------------------------------------- 3.1 Register
def senaryolar():
    return d("lab3.senaryolar")


def puan(s, p):
    return s[p]["deger"]


def skor(s):
    return puan(s, "L") * puan(s, "S") * puan(s, "E")


def bant(deger):
    for b in d("lab3.bantlar"):
        if b["min"] <= deger <= b["max"]:
            return b["ad"]
    raise ValueError(f"bant dışı skor: {deger}")


def oncelik_sirasi(liste):
    """S=3 kuralı: şiddeti öncelikli seviyede olanlar skordan bağımsız öne alınır; sonra skora göre.
    Eşitlikte listedeki sıra korunur (sıralama kararlı)."""
    esik = d("lab3.oncelikli_siddet")
    return sorted(liste, key=lambda s: (puan(s, "S") < esik, -skor(s)))


def register(liste=None):
    liste = senaryolar() if liste is None else liste
    sira = oncelik_sirasi(liste)
    return [{"id": s["id"], "skor": skor(s), "bant": bant(skor(s)), "oncelik": sira.index(s) + 1, "s": s}
            for s in liste]


# ---------------------------------------------------------------- 3.2 Duyarlılık
def _degistir(s, p, yeni):
    kopya = {k: (dict(v) if isinstance(v, dict) else v) for k, v in s.items()}
    kopya[p]["deger"] = yeni
    return kopya


def duyarlilik():
    """Varsayıma dayalı her puanı ±1 değiştirir (1–3 aralığında); sıranın ve ilk önceliğin değişimini raporlar."""
    alt, ust = d("lab3.puan_araligi")
    adim = d("lab3.duyarlilik_adimi")
    temel = [s["id"] for s in oncelik_sirasi(senaryolar())]
    satirlar = []
    for i, s in enumerate(senaryolar()):
        for p in PARAMETRELER:
            if s[p]["etiket"] not in VARSAYIMA_DAYALI:
                continue
            for yon in (-adim, +adim):
                yeni = min(ust, max(alt, puan(s, p) + yon))
                if yeni == puan(s, p):
                    continue
                liste = [x if j != i else _degistir(s, p, yeni) for j, x in enumerate(senaryolar())]
                sira = [x["id"] for x in oncelik_sirasi(liste)]
                degisen = liste[i]
                satirlar.append({
                    "id": s["id"], "parametre": p, "eski": puan(s, p), "yeni": yeni,
                    "skor": skor(degisen), "bant": bant(skor(degisen)),
                    "sira": sira, "sira_degisti": sira != temel, "ilk_degisti": sira[0] != temel[0],
                })
    return temel, satirlar


# ---------------------------------------------------------------- 3.3 Siberden fiziksele
def el_varis_suresi(hiz):
    """El kapıldıktan sonra bant sabit hızla giderse besleme ağzına kaç saniyede varır."""
    return d("lab1.guvenli_mesafe") / hiz


def bant_durma_suresi(hiz, rampa_suresi=None):
    """Kategori 1, emniyet kumandaya bağımlı (STO rampa sonunda): kapılmadan durmaya geçen süre."""
    return lab1.toplam_gecikme() + hiz / lab1.ivme_rampa(rampa_suresi)


def el_yolu(t, hiz, rampa_suresi=None):
    """t anında elin aldığı yol (kat. 1, bağımlı varyant)."""
    g = lab1.toplam_gecikme()
    if t <= g:
        return hiz * t
    a = lab1.ivme_rampa(rampa_suresi)
    tau = min(t - g, hiz / a)
    return hiz * g + hiz * tau - a * tau ** 2 / 2


def saldiri_durumlari():
    v = d("lab1.bant_hizi")
    v_s = v * d("lab3.saldiri_hiz_carpani")
    r_n, r_s = d("lab1.rampa_suresi_kat1"), d("lab3.saldiri_rampa_suresi")
    return [
        ("Normal parametreler", v, r_n),
        ("Saldırı: yalnız hız artışı", v_s, r_n),
        ("Saldırı: yalnız rampa uzatma", v, r_s),
        ("Saldırı: hız + rampa", v_s, r_s),
    ]


def siber_fiziksel_tablo():
    satirlar = []
    for ad, hiz, rampa in saldiri_durumlari():
        mesafe = lab1.durma_mesafesi(hiz, 1, rampa_suresi=rampa)
        satirlar.append({"durum": ad, "hiz": hiz, "rampa": rampa, "mesafe": mesafe,
                         "ulasir": lab1.el_besleme_agzina_ulasir_mi(mesafe),
                         "varis": el_varis_suresi(hiz), "durma": bant_durma_suresi(hiz, rampa)})
    return satirlar


# ---------------------------------------------------------------- Grafikler
BANT_RENK = {"Kritik": "#b3261e", "Yüksek": "#e8613c", "Orta": "#e2a91c", "Düşük": "#5b6576"}


def _grafik_isi_haritasi(yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle

    alt, ust = d("lab3.puan_araligi")
    degerler = list(range(alt, ust + 1))
    fig, eksenler = plt.subplots(1, len(degerler), figsize=(8.2, 3.6), dpi=200, sharey=True)
    for ax, e in zip(eksenler, degerler):
        for L in degerler:
            for S in degerler:
                sk = L * S * e
                renk = BANT_RENK[bant(sk)]
                ax.add_patch(Rectangle((L - 0.5, S - 0.5), 1, 1, facecolor=renk, edgecolor="white", lw=2, alpha=0.88))
                ax.text(L, S + 0.28, str(sk), ha="center", va="center", fontsize=7, color="white")
        for s in senaryolar():
            if puan(s, "E") == e:
                ax.plot(puan(s, "L"), puan(s, "S") - 0.08, "o", ms=17, mfc="white", mec="#16223a", mew=1.5)
                ax.text(puan(s, "L"), puan(s, "S") - 0.08, s["id"], ha="center", va="center", fontsize=7,
                        fontweight="bold", color="#16223a")
        ax.set_xlim(alt - 0.5, ust + 0.5)
        ax.set_ylim(alt - 0.5, ust + 0.5)
        ax.set_xticks(degerler)
        ax.set_yticks(degerler)
        ax.set_xlabel("L (olasılık)")
        ax.set_title(f"E = {e} (maruziyet)", fontsize=9)
        ax.set_aspect("equal")
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.tick_params(length=0)
    eksenler[0].set_ylabel("S (şiddet)")
    fig.legend(handles=[Patch(color=c, label=f"{b} {mn}–{mx}") for b, c, mn, mx in
                        [(x["ad"], BANT_RENK[x["ad"]], x["min"], x["max"]) for x in d("lab3.bantlar")]],
               loc="lower center", ncol=4, frameon=False, fontsize=8, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle("Risk ısı haritası: hücredeki sayı skor, daire senaryo", fontsize=10, x=0.01, ha="left")
    fig.subplots_adjust(left=0.07, right=0.99, top=0.84, bottom=0.25, wspace=0.08)
    fig.savefig(yol)
    plt.close(fig)


def _grafik_siber_fiziksel(yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker

    renkler = ["#2a78d6", "#1baf7a", "#eb6834", "#16223a"]
    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=200)
    t_max = max(r["durma"] for r in siber_fiziksel_tablo())
    n = d("lab1.grafik_nokta_sayisi") * 4
    for (ad, hiz, rampa), renk in zip(saldiri_durumlari(), renkler):
        ts = [t_max * i / (n - 1) for i in range(n)]
        ys = [el_yolu(t, hiz, rampa) for t in ts]
        ax.plot(ts, ys, color=renk, lw=2, label=ad)
    sinir = d("lab1.guvenli_mesafe")
    ax.axhline(sinir, color="#b3261e", lw=1.2, ls="--")
    ax.text(t_max * 0.99, sinir * 1.06, f"besleme ağzı ({sayi(sinir)} m)", ha="right", fontsize=8, color="#b3261e")
    virgul = matplotlib.ticker.FuncFormatter(lambda x, _: sayi(x, 1))
    ax.xaxis.set_major_formatter(virgul)
    ax.yaxis.set_major_formatter(virgul)
    ax.set_xlabel("Kapılmadan sonra geçen süre (s)")
    ax.set_ylabel("Elin bantla aldığı yol (m)")
    ax.set_title("Siberden fiziksele: acil stop basıldıktan sonra el nereye kadar gider?", fontsize=10, loc="left")
    ax.grid(alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(yol)
    plt.close(fig)


# ---------------------------------------------------------------- Markdown çıktıları
def register_md():
    s = ["| ID | Senaryo (kim → kapı → ne yapar → zincir → fiziksel sonuç) | L | S | E | Skor | Bant | Öncelik |",
         "|---|---|---|---|---|---|---|---|"]
    for r in sorted(register(), key=lambda x: x["oncelik"]):
        x = r["s"]
        metin = (f"**Kim:** {x['kim']}<br>**Kapı:** {x['kapi']}<br>**Ne yapar:** {x['ne_yapar']}<br>"
                 f"**Zincir:** {x['zincir']}<br>**Fiziksel sonuç:** {x['fiziksel_sonuc']}")
        s.append(f"| **{r['id']}** | {metin} | {puan(x, 'L')} | {puan(x, 'S')} | {puan(x, 'E')} | "
                 f"**{r['skor']}** | {r['bant']} | **{r['oncelik']}** |")
    return "\n".join(s) + "\n"


def dayanak_md():
    s = ["| ID | L | S | E |", "|---|---|---|---|"]
    for x in senaryolar():
        hucre = [f"**{puan(x, p)}** — {x[p]['dayanak']} [{x[p]['etiket']}]" for p in PARAMETRELER]
        s.append(f"| **{x['id']}** | " + " | ".join(hucre) + " |")
    return "\n".join(s) + "\n"


def duyarlilik_md():
    temel, satirlar = duyarlilik()
    s = [f"Temel öncelik sırası: **{' → '.join(temel)}**", "",
         "| Senaryo | Puan | Değişim | Yeni skor | Yeni bant | Yeni sıra | İlk öncelik değişti mi? |",
         "|---|---|---|---|---|---|---|"]
    for r in satirlar:
        s.append(f"| {r['id']} | {r['parametre']} | {r['eski']} → {r['yeni']} | {r['skor']} | {r['bant']} | "
                 f"{' → '.join(r['sira'])} | {'**Evet**' if r['ilk_degisti'] else 'Hayır'} |")
    degisen = [r for r in satirlar if r["ilk_degisti"]]
    s += ["", f"{len(satirlar)} değişimin {len(degisen)} tanesinde ilk öncelik değişiyor"
              + (": " + "; ".join(f"{r['id']} {r['parametre']} {r['eski']}→{r['yeni']}" for r in degisen) if degisen else "")
              + "."]
    return "\n".join(s) + "\n"


def siber_fiziksel_md():
    s = ["| Durum | Bant hızı | Rampa | Durma mesafesi | Elin ağza varışı | Bandın durması | El besleme ağzına ulaşır mı? |",
         "|---|---|---|---|---|---|---|"]
    for r in siber_fiziksel_tablo():
        s.append(f"| {r['durum']} | {sayi(r['hiz'])} m/s | {sayi(r['rampa'], 1)} s | {sayi(r['mesafe'], 3)} m | "
                 f"{sayi(r['varis'], 1)} s | {sayi(r['durma'], 1)} s | {'**Evet**' if r['ulasir'] else 'Hayır'} |")
    s += ["", f"Güvenli mesafe {sayi(d('lab1.guvenli_mesafe'))} m. Model: stop kategori 1, STO rampa bittikten sonra "
              "geliyor (emniyet invertöre bağımlı varyant)."]
    return "\n".join(s) + "\n"


def main():
    OUT_DIR.mkdir(exist_ok=True)
    _grafik_isi_haritasi(OUT_DIR / "lab3_isi_haritasi.png")
    _grafik_siber_fiziksel(OUT_DIR / "lab3_siber_fiziksel.png")
    (OUT_DIR / "lab3_register.md").write_text(register_md(), encoding="utf-8")
    (OUT_DIR / "lab3_dayanak.md").write_text(dayanak_md(), encoding="utf-8")
    (OUT_DIR / "lab3_duyarlilik.md").write_text(duyarlilik_md(), encoding="utf-8")
    (OUT_DIR / "lab3_siber_fiziksel.md").write_text(siber_fiziksel_md(), encoding="utf-8")
    (OUT_DIR / "lab3_params.yaml").write_text(bolum_metni("lab3"), encoding="utf-8")
    print(duyarlilik_md())
    print(siber_fiziksel_md())


if __name__ == "__main__":
    main()
