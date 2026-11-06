"""LAB 7 — YZ fail-safe kararı (eğitim amaçlı; proje aşaması değerlendirmesi).

Senaryo: besleme bandına YZ'li kamera ile yabancı cisim / aşırı boy parça kontrolü eklenmesi
planlanıyor. Kamera → YZ → OK / RED → ayırma klapesi → dozaj hızı.

7.1 Yanlış sınıflandırma: sentetik skorlarla güven eşiği taraması; kaçak oranı ve operatöre
    sorulan oran. YZ'den bağımsız metal dedektörü ikinci kanal olarak eklenir.
7.2 Girdi manipülasyonu: kare yaşı, donmuş kare, parlaklık, keskinlik ve metal dedektörüyle
    tutarsızlık; şüpheli girdide besleme durur.
7.3 Güven düşük: eşiğin altında OK otomatik verilmez, operatöre sorulur.
YZ emniyet zincirinde değildir: hiçbir çıktısı acil stopu etkilemez; hız isteği normal kumandada
kesilir ve emniyet tarafındaki hız izleme (LAB 4) bağımsız bir üst sınır uygular.

Çalıştırma (repo kökünden):  python -m efo_sim.lab7_ai
"""
import math
import random
from functools import lru_cache

from efo_sim import stil
from efo_sim import lab1_safety as lab1
from efo_sim.params import OUT_DIR, bolum_metni, d, sayi

GEC, AYIR, SOR, DURDUR = "GEÇ", "AYIR", "OPERATÖRE SOR", "BESLEMEYİ DURDUR"


# ---------------------------------------------------------------- 7.1 Yanlış sınıflandırma
@lru_cache(maxsize=1)
def veri_uret():
    """(kusurlu, metal, p_kusur) üçlüleri; dağılımlar params.yaml'da. Önbellekli: params değişirse cache_clear()."""
    r = random.Random(d("lab7.tohum"))
    veri = []
    for _ in range(d("lab7.ornek_sayisi")):
        kusurlu = r.random() < d("lab7.kusur_orani")
        metal = kusurlu and r.random() < d("lab7.metal_payi")
        a, b = d("lab7.skor_kusurlu") if kusurlu else d("lab7.skor_saglam")
        veri.append((kusurlu, metal, r.betavariate(a, b)))
    return tuple(veri)


def guven(p):
    return max(p, 1 - p)


def model_karari(p, esik):
    """RED her güvende ayırır (güvenli taraf); OK yalnız güven eşiği aşılınca otomatik geçer."""
    if p >= d("lab7.karar_siniri"):
        return AYIR
    return GEC if guven(p) >= esik else SOR


def metrikler(veri, esik, md=False):
    """Kaçak = kusurlu parçanın otomatik GEÇ alması. md=True: metal dedektörü metal kaçakları yakalar."""
    kusurlu = [x for x in veri if x[0]]
    kacak = [x for x in kusurlu if model_karari(x[2], esik) == GEC]
    kacak_oran = len(kacak) / len(kusurlu)
    if md:
        # bağımsızlık varsayımı: metal kaçağı ancak dedektör de kaçırırsa geçer (beklenen değer)
        kacak_oran = sum(d("lab7.md_kacirma_orani") if x[1] else 1 for x in kacak) / len(kusurlu)
    sor = sum(model_karari(x[2], esik) == SOR for x in veri) / len(veri)
    yanlis_ret = sum(not x[0] and model_karari(x[2], esik) == AYIR for x in veri) / len(veri)
    return {"kacak": kacak_oran, "sor": sor, "yanlis_ret": yanlis_ret}


@lru_cache(maxsize=1)
def esik_taramasi():
    veri = veri_uret()
    alt, ust = d("lab7.esik_araligi")
    n = d("lab7.esik_adim_sayisi")
    return tuple((e, metrikler(veri, e), metrikler(veri, e, md=True))
                 for e in (alt + (ust - alt) * i / (n - 1) for i in range(n)))


def esik_sec(md=False):
    """Kaçak hedefini karşılayan en düşük eşik (operatör yükü en az). Yoksa None."""
    for e, yalniz, birlikte in esik_taramasi():
        if (birlikte if md else yalniz)["kacak"] <= d("lab7.hedef_kacak_orani"):
            return e
    return None


# ---------------------------------------------------------------- 7.2 Girdi manipülasyonu
def girdi_supheli(kare, onceki_hashler=()):
    """Şüphe nedenleri listesi; boşsa girdi kabul edilir."""
    g = d("lab7.girdi_kontrolleri")
    nedenler = []
    if kare["yas_ms"] > g["azami_kare_yasi_ms"]:
        nedenler.append("kare eski")
    son = list(onceki_hashler)[-(g["donuk_kare_sayisi"] - 1):]
    if len(son) == g["donuk_kare_sayisi"] - 1 and all(h == kare["hash"] for h in son):
        nedenler.append("donmuş kare")
    alt, ust = g["parlaklik_araligi"]
    if not alt <= kare["parlaklik"] <= ust:
        nedenler.append("parlaklık sınır dışı")
    if kare["keskinlik"] < g["asgari_keskinlik"]:
        nedenler.append("bulanık / kapalı lens")
    return nedenler


def guvenli_davranis(p, kare, onceki_hashler=(), metal_dedektoru=False, esik=None):
    """YZ çıktısının etrafındaki kural katmanı. Döner: (eylem, neden)."""
    nedenler = girdi_supheli(kare, onceki_hashler)
    if nedenler:
        return DURDUR, ", ".join(nedenler)
    karar = model_karari(p, esik if esik is not None else esik_sec())
    if metal_dedektoru and karar != AYIR:
        return AYIR, "metal dedektörü YZ ile çelişiyor (bağımsız kanal kazanır)"
    return karar, "model"


# ---------------------------------------------------------------- 7.3 Hız ve emniyet bağımsızlığı
def normal_kumanda_hizi(istek):
    """Normal kumanda YZ'nin dozaj hızı isteğini üst sınırda keser (× nominal)."""
    return min(istek, d("lab7.hiz_istegi_ust_siniri"))


def acil_stop_mesafesi(istek, kumanda_kesiyor=True, hiz_izleme=True):
    """YZ hız istediğinde acil stop mesafesi. kumanda_kesiyor=False: normal kumanda atlatıldı."""
    carpan = normal_kumanda_hizi(istek) if kumanda_kesiyor else istek
    if hiz_izleme:
        carpan = min(carpan, d("lab4.hiz_izleme_esigi_carpani"))
    return lab1.durma_mesafesi(d("lab1.bant_hizi") * carpan, 1, ss1_emniyette=True)


def hat_cevrimi(durum, g, yz_eylemi):
    """Bir kumanda çevrimi: emniyet durum makinesi önce, YZ yalnız normal stop isteyebilir."""
    durum = lab1.sonraki_durum(durum, g)
    if durum == lab1.CALISIYOR and yz_eylemi == DURDUR:
        return lab1.DURUYOR
    return durum


# ---------------------------------------------------------------- Çıktılar
def esik_md():
    veri = veri_uret()
    e1, e2 = esik_sec(), esik_sec(md=True)
    hedef = d("lab7.hedef_kacak_orani")
    satirlar = [("Eşiksiz (her OK geçer)", d("lab7.esik_araligi")[0], False),
                ("Güven eşiği", e1, False),
                ("Güven eşiği + metal dedektörü", e2, True)]
    s = ["| Düzen | Güven eşiği | Kaçak (kusurların) | Operatöre sorulan (tüm parçaların) | Yanlış ret | Hedef ≤ "
         + f"%{sayi(hedef * 100, 1)} |", "|---|---|---|---|---|---|"]
    for ad, e, md in satirlar:
        if e is None:
            s.append(f"| {ad} | bulunamadı | — | — | — | ✖ |")
            continue
        r = metrikler(veri, e, md=md)
        s.append(f"| {ad} | {sayi(e)} | %{sayi(r['kacak'] * 100, 2)} | %{sayi(r['sor'] * 100, 2)} | "
                 f"%{sayi(r['yanlis_ret'] * 100, 2)} | {'✔' if r['kacak'] <= hedef else '✖'} |")
    kap = d("lab7.insan_kapasitesi")
    s += ["", f"Sentetik küme: {d('lab7.ornek_sayisi')} parça, kusur oranı %{sayi(d('lab7.kusur_orani') * 100, 1)}, "
              f"kusurların %{sayi(d('lab7.metal_payi') * 100, 0)}'ı metal. Operatör kapasitesi tüm parçaların "
              f"%{sayi(kap * 100, 0)}'i."]
    return "\n".join(s) + "\n"


def girdi_md():
    normal = {"yas_ms": 40, "hash": "a1", "parlaklik": 0.5, "keskinlik": 0.6}
    n = d("lab7.girdi_kontrolleri")["donuk_kare_sayisi"]
    durumlar = [
        ("Normal kare, model OK (p = 0,05)", 0.05, normal, (), False),
        ("Normal kare, model RED (p = 0,55; düşük güven)", 0.55, normal, (), False),
        ("Normal kare, model OK ama düşük güven (p = 0,45)", 0.45, normal, (), False),
        ("Kare 900 ms eski (yayın gecikti ya da tekrar oynatılıyor)", 0.05, normal | {"yas_ms": 900}, (), False),
        (f"Aynı kare {n} kez üst üste (donmuş / sahte görüntü)", 0.05, normal, ["a1"] * (n - 1), False),
        ("Lens kapalı (parlaklık 0,02)", 0.05, normal | {"parlaklik": 0.02, "keskinlik": 0.05}, (), False),
        ("Model OK, metal dedektörü metal görüyor", 0.05, normal, (), True),
    ]
    esik = esik_sec()
    s = ["| Durum | Eylem | Neden |", "|---|---|---|"]
    for ad, p, kare, gecmis, md in durumlar:
        eylem, neden = guvenli_davranis(p, kare, gecmis, md, esik=esik)
        s.append(f"| {ad} | **{eylem}** | {neden} |")
    return "\n".join(s) + "\n"


def hiz_md():
    s = ["| YZ hız isteği | Kumanda keser + hız izleme | Kumanda atlatıldı + hız izleme | Kumanda atlatıldı, hız izleme yok |",
         "|---|---|---|---|"]
    sinir = d("lab1.guvenli_mesafe")

    def hucre(x):
        return f"{sayi(x, 3)} m" + (" **✖**" if lab1.el_besleme_agzina_ulasir_mi(x) else "")

    for istek in d("lab7.hiz_istegi_taramasi"):
        s.append(f"| {sayi(istek, 1)} × | {hucre(acil_stop_mesafesi(istek))} | "
                 f"{hucre(acil_stop_mesafesi(istek, kumanda_kesiyor=False))} | "
                 f"{hucre(acil_stop_mesafesi(istek, kumanda_kesiyor=False, hiz_izleme=False))} |")
    s += ["", f"Acil stop mesafesi, SS1-t ile; güvenli mesafe {sayi(sinir)} m. ✖ = el besleme ağzına ulaşır."]
    return "\n".join(s) + "\n"


def _grafik_esik(yol):
    """Logaritmik y ekseni: %1'in altındaki kaçak oranı ile %100'e yaklaşan operatör yükü aynı grafikte okunur."""
    plt = stil.mpl()
    import matplotlib.ticker

    R = stil.RENK
    tarama = esik_taramasi()
    xs = [t[0] for t in tarama]
    seriler = [
        ([t[1]["kacak"] * 100 for t in tarama], R["giris"], "-", "Kaçak: yalnız YZ"),
        ([t[2]["kacak"] * 100 for t in tarama], R["iyi"], "-", "Kaçak: YZ + metal dedektörü"),
        ([t[1]["sor"] * 100 for t in tarama], R["bilgi"], "--", "Operatöre sorulan"),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    stil.eksen(ax, izgara="both")
    ax.set_yscale("log", nonpositive="mask")
    for ys, renk, ls, ad in seriler:
        ax.plot(xs, [y if y > 0 else float("nan") for y in ys], color=renk, lw=2, ls=ls, label=ad)
    pozitif = [y for ys, *_ in seriler for y in ys if y > 0]
    ax.set_ylim(min(pozitif) / 2, max(pozitif) * 2)
    hedef, kap = d("lab7.hedef_kacak_orani") * 100, d("lab7.insan_kapasitesi") * 100
    for y, renk, metin in ((hedef, R["kritik"], f"kaçak hedefi %{sayi(hedef, 1)}"),
                           (kap, R["bilgi"], f"operatör kapasitesi %{sayi(kap, 0)}")):
        ax.axhline(y, color=renk, lw=1, ls=(0, (4, 3)))
        ax.text(xs[-1], y, metin + " ", color=renk, fontsize=7.2, fontweight="bold", ha="right", va="bottom")
    secimler = sorted(((esik_sec(), R["giris"], "yalnız YZ"), (esik_sec(md=True), R["iyi"], "YZ + dedektör")),
                      key=lambda t: t[0] if t[0] is not None else 0)
    for sira, (e, renk, ad) in enumerate(secimler):
        if e is not None:  # soldaki eşiğin etiketi sola, sağdakinin sağa: çakışmasınlar
            ax.axvline(e, color=renk, lw=1, alpha=0.7)
            ax.text(e, ax.get_ylim()[1], f" eşik {sayi(e)} \n ({ad}) ", color=renk, fontsize=6.8,
                    va="top", ha="right" if sira == 0 else "left", fontweight="bold")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: sayi(x)))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda y, _: "%" + sayi(y, max(0, -math.floor(math.log10(y))))))
    ax.tick_params(which="both", length=0)
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("Güven eşiği (OK'nin otomatik geçmesi için)")
    ax.set_ylabel("Oran (logaritmik)")
    ax.set_title("Güven eşiği: kaçak oranı ve operatör yükü (sentetik veri)")
    ax.legend(loc="lower right")
    fig.savefig(yol)
    plt.close(fig)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "lab7_esik.md").write_text(esik_md(), encoding="utf-8")
    (OUT_DIR / "lab7_girdi.md").write_text(girdi_md(), encoding="utf-8")
    (OUT_DIR / "lab7_hiz.md").write_text(hiz_md(), encoding="utf-8")
    (OUT_DIR / "lab7_params.yaml").write_text(bolum_metni("lab7"), encoding="utf-8")
    _grafik_esik(OUT_DIR / "lab7_esik.png")
    print(esik_md())
    print(girdi_md())
    print(hiz_md())


if __name__ == "__main__":
    main()
