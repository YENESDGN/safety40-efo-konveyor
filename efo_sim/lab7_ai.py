"""LAB 7 — YZ fail-safe kararı (eğitim amaçlı; proje aşaması değerlendirmesi).

Senaryo: besleme bandına YZ'li kamera ile yabancı cisim / aşırı boy parça kontrolü eklenmesi
planlanıyor. Kamera → YZ → OK / RED → ayırma klapesi → dozaj hızı.

7.1 Yanlış sınıflandırma: sentetik skorlarla güven eşiği taraması; kaçak oranı ve operatöre
    sorulan oran. YZ'den bağımsız metal dedektörü ikinci kanal olarak eklenir.
7.2 Girdi manipülasyonu: kare yaşı, donmuş kare, parlaklık, keskinlik ve metal dedektörüyle
    tutarsızlık; şüpheli girdide besleme durur.
7.3 Güven düşük: eşiğin altında OK otomatik verilmez, operatöre sorulur.
7.4 Ortak neden: YZ ile metal dedektörünün hataları tam bağımsız değilse kaçak oranı ne olur?
7.5 Kayma: kusurlu parçaların skorları sağlamlara doğru kayarsa kaçak artar; bunu hangi izleme
    yakalar? Operatör yükü değil, YZ ile metal dedektörü arasındaki çelişki oranı.
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
@lru_cache(maxsize=None)
def veri_uret(kayma=0.0):
    """(kusurlu, metal, p_kusur) üçlüleri; dağılımlar params.yaml'da. Önbellekli: params değişirse cache_clear().

    kayma (δ): kusurlu skor dağılımının parametreleri sağlamınkine doğru δ oranında kayar (7.5).
    Aynı tohum kullanılır; δ = 0 devreye almadaki kümedir."""
    r = random.Random(d("lab7.tohum"))
    (ak, bk), (as_, bs) = d("lab7.skor_kusurlu"), d("lab7.skor_saglam")
    veri = []
    for _ in range(d("lab7.ornek_sayisi")):
        kusurlu = r.random() < d("lab7.kusur_orani")
        metal = kusurlu and r.random() < d("lab7.metal_payi")
        a, b = (ak + kayma * (as_ - ak), bk + kayma * (bs - bk)) if kusurlu else (as_, bs)
        veri.append((kusurlu, metal, r.betavariate(a, b)))
    return tuple(veri)


def guven(p):
    return max(p, 1 - p)


def model_karari(p, esik):
    """RED her güvende ayırır (güvenli taraf); OK yalnız güven eşiği aşılınca otomatik geçer."""
    if p >= d("lab7.karar_siniri"):
        return AYIR
    return GEC if guven(p) >= esik else SOR


def md_kacirma(ortak_neden=0.0):
    """YZ metal parçayı kaçırdığında dedektörün de kaçırma olasılığı.
    ρ payında hatalar ortak nedenlidir (ikisi birlikte kaçırır); kalanında bağımsızdır (7.4)."""
    q = d("lab7.md_kacirma_orani")
    return ortak_neden + (1 - ortak_neden) * q


def metrikler(veri, esik, md=False, ortak_neden=0.0):
    """Kaçak = kusurlu parçanın otomatik GEÇ alması. md=True: metal dedektörü metal kaçakları yakalar.
    celiski: YZ GEÇ dediği hâlde dedektörün metal gördüğü parçaların oranı (sahada gözlenebilir)."""
    kusurlu = [x for x in veri if x[0]]
    kacak = [x for x in kusurlu if model_karari(x[2], esik) == GEC]
    kacak_oran = len(kacak) / len(kusurlu)
    q = md_kacirma(ortak_neden)
    if md:
        # metal kaçağı ancak dedektör de kaçırırsa geçer (beklenen değer)
        kacak_oran = sum(q if x[1] else 1 for x in kacak) / len(kusurlu)
    sor = sum(model_karari(x[2], esik) == SOR for x in veri) / len(veri)
    yanlis_ret = sum(not x[0] and model_karari(x[2], esik) == AYIR for x in veri) / len(veri)
    celiski = sum(1 - q for x in kacak if x[1]) / len(veri)
    return {"kacak": kacak_oran, "sor": sor, "yanlis_ret": yanlis_ret, "celiski": celiski}


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


# ---------------------------------------------------------------- 7.4 Ortak neden
def _tarama(yol):
    alt, ust, n = d(yol)
    return [alt + (ust - alt) * i / (n - 1) for i in range(n)]


def ortak_neden_esigi():
    """Seçilen eşikte (YZ + dedektör) kaçak hedefini aşan en küçük ortak neden payı ρ*.
    Kaçak ρ'ya göre doğrusaldır: kacak(ρ) = (yalnız_YZ_kaçak_metal_dışı + metal_kaçak · q(ρ)) / kusurlu."""
    veri, e = veri_uret(), esik_sec(md=True)
    kusurlu = [x for x in veri if x[0]]
    kacak = [x for x in kusurlu if model_karari(x[2], e) == GEC]
    metal_disi, metal = sum(not x[1] for x in kacak), sum(x[1] for x in kacak)
    q, hedef = d("lab7.md_kacirma_orani"), d("lab7.hedef_kacak_orani")
    if not metal:
        return None
    rho = (hedef * len(kusurlu) - metal_disi - metal * q) / (metal * (1 - q))
    return max(rho, 0.0)


def ortak_neden_taramasi():
    veri, e = veri_uret(), esik_sec(md=True)
    return [(rho, metrikler(veri, e, md=True, ortak_neden=rho)) for rho in _tarama("lab7.ortak_neden_taramasi")]


# ---------------------------------------------------------------- 7.5 Kayma ve izleme
def kayma_taramasi():
    """Her δ için seçilen eşikte (YZ + dedektör) metrikler. Eşik devreye almada seçildiği gibi kalır."""
    e = esik_sec(md=True)
    return [(k, metrikler(veri_uret(k), e, md=True)) for k in _tarama("lab7.kayma_taramasi")]


def ilk_kayma(kosul):
    return next((k for k, r in kayma_taramasi() if kosul(r)), None)


def izleme_sonucu():
    """Hangi δ'da kaçak hedef ve tolerans aşılıyor, hangi izleme hangi δ'da alarm veriyor?"""
    taban = kayma_taramasi()[0][1]
    c, hedef = d("lab7.izleme_alarm_carpani"), d("lab7.hedef_kacak_orani")
    return {
        "hedef_asim": ilk_kayma(lambda r: r["kacak"] > hedef),
        "tolerans_asim": ilk_kayma(lambda r: r["kacak"] > hedef * d("lab7.kayma_tolerans_carpani")),
        "alarm_celiski": ilk_kayma(lambda r: r["celiski"] >= c * taban["celiski"]),
        "alarm_sor": ilk_kayma(lambda r: r["sor"] >= c * taban["sor"]),
        "taban": taban,
    }


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


def _yuzde(x, basamak=2):
    return f"%{sayi(x * 100, basamak)}"


def ortak_neden_md():
    hedef, rho_y = d("lab7.hedef_kacak_orani"), ortak_neden_esigi()
    s = ["| Ortak neden payı ρ | Dedektörün kaçırma olasılığı | Kaçak (kusurların) | Hedef ≤ " + _yuzde(hedef, 1) + " |",
         "|---|---|---|---|"]
    for rho, r in ortak_neden_taramasi()[::4]:
        s.append(f"| {sayi(rho)} | {_yuzde(md_kacirma(rho), 1)} | {_yuzde(r['kacak'])} | "
                 f"{'✔' if r['kacak'] <= hedef else '**✖**'} |")
    s += ["", f"Seçilen eşik {sayi(esik_sec(md=True))} (YZ + metal dedektörü). Kaçak hedefi, ortak neden payı "
              f"**ρ* = {sayi(rho_y, 3)}** değerini aştığında aşılıyor: YZ'nin kaçırdığı her {round(1 / rho_y)} metal "
              "parçadan birini dedektörün de aynı nedenle kaçırması yetiyor."]
    return "\n".join(s) + "\n"


def kayma_md():
    iz, hedef = izleme_sonucu(), d("lab7.hedef_kacak_orani")
    taban, c = iz["taban"], d("lab7.izleme_alarm_carpani")
    s = ["| Kayma δ | Kaçak | Operatöre sorulan | Çelişki (YZ GEÇ, dedektör metal) | Çelişki alarmı | Operatör yükü alarmı |",
         "|---|---|---|---|---|---|"]
    for k, r in kayma_taramasi()[::2]:
        s.append(f"| {sayi(k, 3)} | {_yuzde(r['kacak'])}{' **✖**' if r['kacak'] > hedef else ''} | "
                 f"{_yuzde(r['sor'])} | {sayi(r['celiski'] * 10000, 1)} / 10 000 | "
                 f"{'**alarm**' if r['celiski'] >= c * taban['celiski'] else '—'} | "
                 f"{'**alarm**' if r['sor'] >= c * taban['sor'] else '—'} |")

    def km(x):
        return sayi(x, 3) if x is not None else "taranan aralıkta yok"

    s += ["", f"Alarm: izlenen oran devreye almadaki değerinin {sayi(c, 1)} katına çıkınca. ✖ = kaçak hedefi "
              f"({_yuzde(hedef, 1)}) aşıldı.", "",
          f"- Kaçak hedefi aşılıyor: δ = {km(iz['hedef_asim'])}",
          f"- Kaçak hedefin {sayi(d('lab7.kayma_tolerans_carpani'), 0)} katını aşıyor: δ = {km(iz['tolerans_asim'])}",
          f"- Çelişki alarmı: δ = {km(iz['alarm_celiski'])}",
          f"- Operatör yükü alarmı: δ = {km(iz['alarm_sor'])}"]
    return "\n".join(s) + "\n"


def _grafik_ortak_neden_kayma(yol):
    plt = stil.mpl()
    import matplotlib.ticker

    R = stil.RENK
    hedef = d("lab7.hedef_kacak_orani")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.2), gridspec_kw={"wspace": 0.32})

    # A: ortak neden
    on = ortak_neden_taramasi()
    rho_y = ortak_neden_esigi()
    stil.eksen(a1)
    a1.plot([x for x, _ in on], [r["kacak"] * 100 for _, r in on], color=R["iyi"], lw=2)
    a1.axhline(hedef * 100, color=R["kritik"], lw=1, ls=(0, (4, 3)))
    a1.text(on[-1][0], hedef * 100, f"hedef %{sayi(hedef * 100, 1)} ", color=R["kritik"], fontsize=6.8,
            ha="right", va="bottom", fontweight="bold")
    a1.axvline(rho_y, color=R["ikincil"], lw=0.9, ls=":")
    a1.text(rho_y, a1.get_ylim()[1], f" ρ* = {sayi(rho_y, 3)}", color=R["ikincil"], fontsize=6.8, va="top")
    a1.set_xlabel("Ortak neden payı ρ")
    a1.set_ylabel("Kaçak (kusurların %)")
    a1.set_title("A · Bağımsızlık bozulursa", fontsize=9)
    a1.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: sayi(x)))
    a1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda y, _: sayi(y, 1)))

    # B: kayma ve izleme (devreye almaya göre kat)
    kt, iz = kayma_taramasi(), izleme_sonucu()
    taban = iz["taban"]
    xs = [k for k, _ in kt]
    stil.eksen(a2)
    for anahtar, renk, ls, ad in (("kacak", R["giris"], "-", "Kaçak (gözlenemez)"),
                                  ("celiski", R["vurgu"], "-", "Çelişki: YZ GEÇ, dedektör metal"),
                                  ("sor", R["bilgi"], "--", "Operatöre sorulan")):
        a2.plot(xs, [r[anahtar] / taban[anahtar] for _, r in kt], color=renk, lw=2, ls=ls, label=ad)
    c = d("lab7.izleme_alarm_carpani")
    a2.axhline(c, color=R["ikincil"], lw=0.9, ls=(0, (4, 3)))
    a2.text(xs[0], c, f" alarm {sayi(c, 1)}×", color=R["ikincil"], fontsize=6.6, va="bottom")
    for k, renk, metin in ((iz["alarm_celiski"], R["vurgu"], "alarm"),
                           (iz["tolerans_asim"], R["kritik"], f"kaçak > %{sayi(hedef * d('lab7.kayma_tolerans_carpani') * 100, 0)}")):
        if k is not None:
            a2.axvline(k, color=renk, lw=0.9, ls=":")
            a2.text(k, a2.get_ylim()[1], f" {metin}", color=renk, fontsize=6.6, va="top", fontweight="bold")
    a2.set_xlabel("Kayma δ (kusurlu skorlar sağlama doğru)")
    a2.set_ylabel("Devreye almaya göre (×)")
    a2.set_title("B · Kaymayı hangi izleme yakalar?", fontsize=9)
    a2.legend(loc="upper left", bbox_to_anchor=(0, 0.9), fontsize=6.4)
    a2.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: sayi(x)))
    a2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda y, _: sayi(y, 0)))
    fig.suptitle("YZ + metal dedektörü: ortak neden ve kayma (sentetik veri)", x=0.01, ha="left",
                 fontsize=10, fontweight="bold", y=1.03)
    fig.savefig(yol)
    plt.close(fig)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "lab7_esik.md").write_text(esik_md(), encoding="utf-8")
    (OUT_DIR / "lab7_girdi.md").write_text(girdi_md(), encoding="utf-8")
    (OUT_DIR / "lab7_hiz.md").write_text(hiz_md(), encoding="utf-8")
    (OUT_DIR / "lab7_params.yaml").write_text(bolum_metni("lab7"), encoding="utf-8")
    _grafik_esik(OUT_DIR / "lab7_esik.png")
    (OUT_DIR / "lab7_ortak_neden.md").write_text(ortak_neden_md(), encoding="utf-8")
    (OUT_DIR / "lab7_kayma.md").write_text(kayma_md(), encoding="utf-8")
    _grafik_ortak_neden_kayma(OUT_DIR / "lab7_ortak_neden_kayma.png")
    print(esik_md())
    print(girdi_md())
    print(hiz_md())


if __name__ == "__main__":
    main()
