"""LAB 5 — SBOM / CVE / yama kararı (eğitim amaçlı).

5.1 Üç şart: bileşen SBOM'da var mı, sürüm etkileniyor mu, açık ulaşılabilir mi?
    Ulaşılabilirlik LAB 4 saldırı grafından hesaplanır (giriş noktalarından o düğüme yol var mı).
5.2 Karar akışı: üretim durur mu, yama nerede test edilir, emniyet validasyonu etkilenir mi,
    yama yoksa hangi telafi edici önlemler açığı kapatır?
5.3 Karar zaman içinde: kayıt KEV'e girer, telafi uygulanır, yama gelir; karar her olayda yeniden hesaplanır.
5.4 SBOM sapması: sahadaki değişiklikler SBOM'a işlenmezse üç şart kontrolü yanlış "etkilemez" der.
5.5 Ömrü bitmiş bileşen: yama hiç gelmeyecekse telafi kalıcı olur ve bileşen değiştirme planına girer.

Simülasyon varyantları ürün önerisi değildir; mimari farkının karara etkisini göstermek içindir.

Çalıştırma (repo kökünden):  python -m efo_sim.lab5_vuln
"""
from itertools import combinations

from efo_sim import lab4_attack as lab4
from efo_sim import stil
from efo_sim.params import OUT_DIR, bolum_metni, d, sayi

MIMARILER = {
    "mevcut": ("Mevcut (varsayım)", lab4.MEVCUT | {"plc_web_sunucusu_acik": d("lab5.plc_web_sunucusu")["mevcut"]}),
    "hedef": ("Hedef, içeri girilmiş kabulü",
              lab4.HEDEF_ICERI_GIRILDI | {"plc_web_sunucusu_acik": d("lab5.plc_web_sunucusu")["hedef"]}),
}
KARARLAR = {
    "devam": "Devam: CVE bu hatta etkili değil",
    "devam_telafi": "Devam + planlı telafi; yama bakım penceresinde",
    "hemen_telafi": "Durdurmadan hemen telafi; yama test sonrası",
    "durdur": "Kontrollü durdur; telafi ya da yama sonrası yeniden doğrula",
}
KARAR_KISA = {"devam": "Devam", "devam_telafi": "Devam + planlı telafi",
              "hemen_telafi": "Hemen telafi", "durdur": "Kontrollü durdur"}
KARAR_TONU = {"devam": "iyi", "devam_telafi": "bilgi", "hemen_telafi": "uyari", "durdur": "kritik"}
YAMA_YOK = "yok"  # ilk_duzeltilmis alanında: düzeltme yayımlanmayacak (EOL)


def sbom():
    """Sahadaki gerçek SBOM (V16)."""
    return {b["id"]: dict(b) for b in d("lab5.sbom")}


def kayit(kayit_id):
    return next(k for k in d("lab5.kayitlar") + [d("lab5.eol_kaydi")] if k["id"] == kayit_id)


def surum(metin):
    return tuple(int(p) for p in metin.split("."))


def surum_etkileniyor(mevcut, ilk_duzeltilmis):
    """İlk düzeltilmiş sürümden önceki her sürüm etkilenir. Düzeltme hiç gelmeyecekse ("yok") hepsi."""
    if mevcut == "-" or ilk_duzeltilmis == "-":
        return False
    if ilk_duzeltilmis == YAMA_YOK:
        return True
    return surum(mevcut) < surum(ilk_duzeltilmis)


# ---------------------------------------------------------------- 5.1 Üç şart
def bilesen(k, sbom_=None):
    """Kayıttaki ürün SBOM'daki hangi bileşen? Yoksa None."""
    return next((b for b in (sbom_ or sbom()).values() if b["urun"] == k["urun"]), None)


def uc_sart(k, mimari, sbom_=None):
    b = bilesen(k, sbom_)
    var = b is not None
    etkilenir = var and surum_etkileniyor(b["surum"], k["ilk_duzeltilmis"])
    ulasilir = var and b["dugum"] in lab4.ulasilabilir(mimari) and all(mimari[c] for c in k["ek_kosullar"])
    return {"var": var, "surum": etkilenir, "ulasilabilir": ulasilir}


def etkiler(k, mimari, sbom_=None):
    return all(uc_sart(k, mimari, sbom_).values())


# ---------------------------------------------------------------- 5.2 Karar akışı
def emniyete_yol(dugum, mimari):
    """Bu düğüm ele geçirilirse emniyet fonksiyonuna (LAB 4 grafı) yol var mı?"""
    return dugum == lab4.HEDEF_DUGUM or bool(lab4.yollar(mimari, dugum))


def validasyon_etkilenir(b, mimari):
    """Yama emniyet fonksiyonunun davranışını değiştirebilir mi? Evet ise yeniden doğrulama gerekir."""
    return b["dugum"] == "emniyet" or emniyete_yol(b["dugum"], mimari)


def telafi_plani(k, mimari, sbom_=None):
    """Açığı ulaşılamaz kılan en kısa süreli önlem kümesi (bütün alt kümeler denenir)."""
    onlemler = [t for t in d("lab5.telafi_onlemleri") if mimari.get(t["kosul"])]
    adaylar = []
    for n in range(1, len(onlemler) + 1):
        for kume in combinations(onlemler, n):
            m = mimari | {t["kosul"]: False for t in kume}
            if not etkiler(k, m, sbom_):
                adaylar.append((sum(t["saat"] for t in kume), len(kume), kume))
    if not adaylar:
        return None
    sure, _, kume = min(adaylar, key=lambda a: (a[0], a[1]))
    return {"onlemler": [t["id"] for t in kume], "saat": sure}


def telafili_mimari(k, mimari):
    """Telafi planı uygulanmış mimari (plan yoksa aynı mimari)."""
    plan = telafi_plani(k, mimari)
    if plan is None:
        return mimari
    onlem = {t["id"]: t for t in d("lab5.telafi_onlemleri")}
    return mimari | {onlem[i]["kosul"]: False for i in plan["onlemler"]}


def uretim_karari(k, mimari, istismar_belirtisi=False, sbom_=None):
    if not etkiler(k, mimari, sbom_):
        return "devam"
    b = bilesen(k, sbom_)
    if not emniyete_yol(b["dugum"], mimari):
        # Emniyet riski yok; ama aktif istismar kullanılabilirlik riskini büyütür: telafi öne çekilir.
        return "hemen_telafi" if istismar_belirtisi else "devam_telafi"
    plan = telafi_plani(k, mimari, sbom_)
    if istismar_belirtisi or plan is None or plan["saat"] > d("lab5.telafi_azami_sure"):
        return "durdur"
    return "hemen_telafi"


def yama_adimlari(k, mimari):
    """Yama doğrudan uygulanmaz: önce test. Validasyon etkileniyorsa emniyet testleri eklenir."""
    adimlar = ["Yedek CPU'lu test tezgâhında aynı firmware + proje ile yamayı uygula",
               "Normal fonksiyon testleri (start/stop, interlock, haberleşme)"]
    b = bilesen(k)
    if b and validasyon_etkilenir(b, mimari):
        adimlar.append("Emniyet fonksiyonu testleri: SF1–SF4 + durma süresi ölçümü (LAB 1)")
    adimlar += ["Bakım penceresinde hatta uygula; eski sürümün yedeği hazır",
                "Konfigürasyon CRC'sini yeni referans olarak kaydet"]
    return adimlar


# ---------------------------------------------------------------- 5.3 Karar zaman içinde
def olay_akisi(k, mimari):
    """Her olayda kararı yeniden hesaplar. Telafi ulaşılabilirliği, yama sürümü değiştirir."""
    sonuc = []
    for o in d("lab5.olay_akisi"):
        m = telafili_mimari(k, mimari) if o["telafi"] else mimari
        s = sbom()
        b = bilesen(k, s)
        if o["yama"] and b and k["yama"] and k["ilk_duzeltilmis"] not in ("-", YAMA_YOK):
            s[b["id"]]["surum"] = k["ilk_duzeltilmis"]
        karar = uretim_karari(k, m, istismar_belirtisi=o["istismar"], sbom_=s)
        dogrulama = bool(o["yama"] and b and validasyon_etkilenir(b, mimari))
        sonuc.append({"olay": o, "karar": karar, "sart": uc_sart(k, m, s), "dogrulama": dogrulama})
    return sonuc


# ---------------------------------------------------------------- 5.4 SBOM sapması
def teslim_sbom():
    """Teslimde yazılan SBOM: sahadaki değişiklikler (D1, D2…) buna işlenmedi."""
    s = sbom()
    for deg in d("lab5.saha_degisiklikleri"):
        for bid, surum_ in deg["farklar"].items():
            if surum_ is None:
                s.pop(bid, None)
            else:
                s[bid]["surum"] = surum_
    return s


def sbom_farki(eski, gercek):
    """Kayıtlı SBOM ile sahadaki gerçek durum arasındaki farklı bileşenler."""
    return sorted(bid for bid in gercek if bid not in eski or eski[bid]["surum"] != gercek[bid]["surum"])


def yanlis_negatifler(kayitli_sbom, mimari):
    """Gerçekte etkileyen ama kayıtlı SBOM'a göre 'etkilemez' görünen kayıtlar."""
    return [k["id"] for k in d("lab5.kayitlar")
            if etkiler(k, mimari) and not etkiler(k, mimari, kayitli_sbom)]


def degisiklik_yonetimli_sbom():
    """Her saha değişikliği SBOM'a işlenir: kayıtlı SBOM sahadaki durumla aynıdır."""
    return sbom()


# ---------------------------------------------------------------- 5.5 Ömrü bitmiş bileşen
def kapanis(k, mimari):
    """Açık nasıl kapanır? Yama varsa yamayla; yoksa telafi kalıcı olur ve bileşen değiştirilir."""
    if not etkiler(k, mimari):
        return {"yontem": "gerekmez", "plan": None, "degistir": False}
    plan = telafi_plani(k, mimari)
    if k["ilk_duzeltilmis"] == YAMA_YOK:
        return {"yontem": "kalici_telafi", "plan": plan, "degistir": True}
    return {"yontem": "yama", "plan": plan, "degistir": False}


# ---------------------------------------------------------------- Çıktılar: tablolar
def _evet(x):
    return "✔" if x else "✖"


def sbom_md():
    s = ["| Bileşen | Sürüm | LAB 4 düğümü | Yazılım içerir |", "|---|---|---|---|"]
    for b in sbom().values():
        s.append(f"| {b['ad']} | {b['surum']} | {lab4.DUGUMLER[b['dugum']]} | {'evet' if b['yazilim'] else 'hayır'} |")
    return "\n".join(s) + "\n"


def karar_md():
    s = ["| Kayıt | CVSS | Mimari | Bileşen var | Sürüm etkilenir | Ulaşılabilir | Emniyete yol | Karar |",
         "|---|---|---|---|---|---|---|---|"]
    for k in d("lab5.kayitlar"):
        b = bilesen(k)
        for anahtar, (ad, m) in MIMARILER.items():
            u = uc_sart(k, m)
            yol = _evet(emniyete_yol(b["dugum"], m)) if b else "—"
            s.append(f"| {k['cve']} ({k['urun']}) | {sayi(k['cvss'], 1)} | {ad} | {_evet(u['var'])} | "
                     f"{_evet(u['surum'])} | {_evet(u['ulasilabilir'])} | {yol} | {KARARLAR[uretim_karari(k, m)]} |")
    s += ["", "Ulaşılabilirlik, LAB 4'teki giriş noktalarından (internet, uzak araç, USB, yerel HMI, Wi-Fi) "
              "bileşenin düğümüne açık bir yol olup olmadığıdır. Hedef sütununda saldırganın VPN ve MFA'yı "
              "aştığı kabul edildi."]
    return "\n".join(s) + "\n"


def telafi_md():
    onlem = {t["id"]: t for t in d("lab5.telafi_onlemleri")}
    k = kayit("FOY-X")
    s = ["| Mimari | En kısa telafi kümesi | Süre | Telafiden sonra ulaşılabilir mi? | Validasyon etkilenir mi? |",
         "|---|---|---|---|---|"]
    for ad, m in MIMARILER.values():
        p = telafi_plani(k, m)
        if p is None:
            s.append(f"| {ad} | bulunamadı | — | evet | — |")
            continue
        kume = "<br>".join(f"{i}: {onlem[i]['ad']}" for i in p["onlemler"])
        s.append(f"| {ad} | {kume} | {sayi(p['saat'])} sa | {'evet' if etkiler(k, telafili_mimari(k, m)) else 'hayır'} | "
                 f"{'**evet**' if validasyon_etkilenir(bilesen(k), m) else 'hayır'} |")
    s += ["", f"Telafi için kabul edilen azami süre: {sayi(d('lab5.telafi_azami_sure'), 1)} saat. "
              "Aktif istismar belirtisi varsa ve bileşenden emniyet fonksiyonuna yol varsa karar doğrudan "
              f"\"{KARARLAR['durdur']}\" olur."]
    return "\n".join(s) + "\n"


def _sart_ozeti(u):
    if not u["var"]:
        return "1. şart düştü (bileşen yok)"
    if not u["surum"]:
        return "2. şart düştü (sürüm etkilenmiyor)"
    if not u["ulasilabilir"]:
        return "3. şart düştü (ulaşılamaz)"
    return "üç şart sağlanıyor"


def zaman_md():
    k = kayit("FOY-X")
    akislar = {a: olay_akisi(k, m) for a, (_, m) in MIMARILER.items()}
    s = ["| # | Olay | Mevcut: karar | Mevcut: durum | Hedef: karar | Hedef: durum |", "|---|---|---|---|---|---|"]
    for i, o in enumerate(d("lab5.olay_akisi")):
        satir = [str(i + 1), o["ad"]]
        for a in MIMARILER:
            r = akislar[a][i]
            durum = _sart_ozeti(r["sart"]) + ("; SF1–SF4 yeniden doğrulanır" if r["dogrulama"] else "")
            satir += [f"**{KARAR_KISA[r['karar']]}**", durum]
        s.append("| " + " | ".join(satir) + " |")
    s += ["", "Telafi, LAB 5.2'deki en kısa önlem kümesidir. Yama, kaydın ilk düzeltilmiş sürümüne "
              "(Component X 2.5) geçiştir; mevcut mimaride PLC'den emniyet fonksiyonuna yol olduğu için "
              "yamadan sonra emniyet fonksiyonları yeniden doğrulanır."]
    return "\n".join(s) + "\n"


def sapma_md():
    gercek, teslim = sbom(), teslim_sbom()
    s = ["| Saha değişikliği | Teslim SBOM'unda | Sahada |", "|---|---|---|"]
    for deg in d("lab5.saha_degisiklikleri"):
        eski = "<br>".join(f"{gercek[b]['ad']}: {v if v is not None else 'yok'}" for b, v in deg["farklar"].items())
        yeni = "<br>".join(f"{gercek[b]['ad']}: {gercek[b]['surum']}" for b in deg["farklar"])
        s.append(f"| {deg['id']}: {deg['ad']} | {eski} | {yeni} |")
    s += ["", "| Kayıt | Mimari | Teslim SBOM'uyla karar | Güncel SBOM'la karar | Yanlış \"etkilemez\" |",
          "|---|---|---|---|---|"]
    for k in d("lab5.kayitlar"):
        for ad, m in MIMARILER.values():
            k_eski, k_yeni = uretim_karari(k, m, sbom_=teslim), uretim_karari(k, m)
            yanlis = k["id"] in yanlis_negatifler(teslim, m)
            s.append(f"| {k['cve']} | {ad} | {KARAR_KISA[k_eski]} | {KARAR_KISA[k_yeni]} | "
                     f"{'**evet**' if yanlis else 'hayır'} |")
    toplam_eski = sum(len(yanlis_negatifler(teslim, m)) for _, m in MIMARILER.values())
    toplam_yeni = sum(len(yanlis_negatifler(degisiklik_yonetimli_sbom(), m)) for _, m in MIMARILER.values())
    s += ["", f"Yanlış \"etkilemez\" sonucu: teslim SBOM'uyla **{toplam_eski}**, değişiklik yönetimine bağlı "
              f"SBOM'la **{toplam_yeni}**. SBOM'da görünmeyen ya da sürümü farklı bileşen sayısı: "
              f"{len(sbom_farki(teslim, gercek))}."]
    return "\n".join(s) + "\n"


def eol_md():
    k = d("lab5.eol_kaydi")
    onlem = {t["id"]: t for t in d("lab5.telafi_onlemleri")}
    yontem = {"gerekmez": "Gerekmez (ulaşılamaz)", "kalici_telafi": "**Kalıcı telafi + bileşen değişimi**",
              "yama": "Yama"}
    s = [f"Kayıt: {k['cve']}, {k['urun']}, CVSS {sayi(k['cvss'], 1)}, yama: {k['yama']}.", "",
         "| Mimari | Üç şart | Karar | Kapanış | Telafi kümesi |", "|---|---|---|---|---|"]
    for ad, m in MIMARILER.values():
        u = uc_sart(k, m)
        kp = kapanis(k, m)
        kume = ("<br>".join(f"{i}: {onlem[i]['ad']}" for i in kp["plan"]["onlemler"])
                if kp["plan"] else "—")
        s.append(f"| {ad} | {_sart_ozeti(u)} | {KARAR_KISA[uretim_karari(k, m)]} | {yontem[kp['yontem']]} | {kume} |")
    s += ["", "Yama gelmeyecekse telafi geçici değildir: bileşen ömrü boyunca yerinde kalır. Mevcut mimaride "
              "bu, uzak desteğin kalıcı olarak kesilmesi demektir; hedef mimaride router zaten emniyet "
              "fonksiyonuna giden bir yolun üzerinde değildir."]
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------- Çıktılar: diyagram
def mermaid_telafi(k, mimari):
    """Bileşen düğümüne giden yollar ve telafi planının kestiği kenarlar (LAB 4 grafı üzerinde)."""
    b = bilesen(k)
    onlem = {t["id"]: t for t in d("lab5.telafi_onlemleri")}
    plan = telafi_plani(k, mimari)
    kesen = {onlem[i]["kosul"]: i for i in (plan["onlemler"] if plan else [])}
    kenarlar = []
    for g in lab4.GIRISLER:
        for y in lab4.yollar(mimari, g, hedef=b["dugum"]):
            for kn in y:
                if kn not in kenarlar:
                    kenarlar.append(kn)
    emniyet = [kn for kn in lab4.acik_kenarlar(mimari) if kn[0] == b["dugum"] and kn[1] == lab4.HEDEF_DUGUM]
    dugumler = []
    for kn in kenarlar + emniyet:
        for n in kn[:2]:
            if n not in dugumler:
                dugumler.append(n)

    s = ["flowchart TB"]
    for n in dugumler:
        ad = lab4.DUGUMLER[n]
        if n in lab4.GIRISLER:
            s.append(f'  {n}(["{ad}"])')
        elif n == lab4.HEDEF_DUGUM:
            s.append(f'  {n}{{{{"{ad}"}}}}')
        elif n == b["dugum"]:
            s.append(f'  {n}["{ad}<br/>{k["urun"]} {b["surum"]}"]')
        else:
            s.append(f'  {n}["{ad}"]')
    stiller = []
    for i, kn in enumerate(kenarlar + emniyet):
        kes = next((kesen[c] for c in kn[2] if c in kesen), None)
        if kes:
            s.append(f'  {kn[0]} -.-|"✂ {kes} · {kn[3]}"| {kn[1]}')
            stiller.append(stil.kenar_stili(i, "iyi", kesik=True))
        elif kn in emniyet:
            s.append(f'  {kn[0]} ==>|"{kn[3]}"| {kn[1]}')
            stiller.append(stil.kenar_stili(i, "kritik", kalin=True))
        else:
            s.append(f'  {kn[0]} -->|"{kn[3]}"| {kn[1]}')
            stiller.append(stil.kenar_stili(i, "pasif"))
    s += [stil.classdef("giris", "giris"), stil.classdef("varlik", "bilgi"),
          stil.classdef("bilesen", "uyari", kalin=True), stil.classdef("hedef", "kritik", kalin=True)]
    gir = [n for n in dugumler if n in lab4.GIRISLER]
    var = [n for n in dugumler if n not in lab4.GIRISLER and n not in (b["dugum"], lab4.HEDEF_DUGUM)]
    if gir:
        s.append(f"  class {','.join(gir)} giris")
    if var:
        s.append(f"  class {','.join(var)} varlik")
    s.append(f"  class {b['dugum']} bilesen")
    if emniyet:
        s.append(f"  class {lab4.HEDEF_DUGUM} hedef")
    return "\n".join(s + stiller) + "\n"


# ---------------------------------------------------------------- Çıktılar: grafikler
def _grafik_uc_sart(yol):
    """Kayıt × mimari için şart zinciri: ilk düşen şarttan sonrası değerlendirilmez."""
    plt = stil.mpl()
    from matplotlib.patches import FancyBboxPatch

    sutunlar = ["Bileşen\nvar", "Sürüm\netkilenir", "Ulaşıla-\nbilir", "Emniyete\nyol"]
    satirlar = [(k, ad, m) for k in d("lab5.kayitlar") for ad, m in MIMARILER.values()]
    fig, ax = plt.subplots(figsize=(7.4, 0.42 * len(satirlar) + 1.0))
    ax.set_xlim(0, 11.4)
    ax.set_ylim(len(satirlar) - 0.4, -1.1)
    ax.axis("off")

    x_sutun = [4.05 + i * 1.05 for i in range(len(sutunlar))]
    x_karar = x_sutun[-1] + 0.65
    for x, baslik in zip(x_sutun, sutunlar):
        ax.text(x, -0.75, baslik, ha="center", va="center", fontsize=7.2, color=stil.RENK["ikincil"])
    ax.text(x_karar, -0.75, "Karar", ha="left", va="center", fontsize=7.2, color=stil.RENK["ikincil"])

    onceki = None
    for r, (k, ad, m) in enumerate(satirlar):
        if k["id"] != onceki:
            if onceki is not None:
                ax.axhline(r - 0.5, color=stil.RENK["izgara"], lw=0.8)
            ax.text(0.05, r, f"{k['cve']}", fontsize=7.6, fontweight="bold", va="center")
            ax.text(0.05, r + 0.36, f"{k['urun']} · CVSS {sayi(k['cvss'], 1)}", fontsize=6.4,
                    color=stil.RENK["ikincil"], va="center")
            onceki = k["id"]
        ax.text(2.35, r, ad.split(" (")[0].replace(", içeri girilmiş kabulü", "*"), fontsize=7, va="center",
                color=stil.RENK["ikincil"])
        u = uc_sart(k, m)
        b = bilesen(k)
        degerler = [u["var"], u["surum"], u["ulasilabilir"], emniyete_yol(b["dugum"], m) if b else False]
        dustu = False
        for x, v in zip(x_sutun, degerler):
            if dustu:
                ton, metin = "pasif", "–"
            elif v:
                ton, metin = "kritik", "✔"
            else:
                ton, metin, dustu = "iyi", "✖", True
            ax.add_patch(FancyBboxPatch((x - 0.36, r - 0.27), 0.72, 0.54, boxstyle="round,pad=0,rounding_size=0.12",
                                        fc=stil.DOLGU[ton], ec=stil.RENK[ton], lw=0.9))
            ax.text(x, r, metin, ha="center", va="center", fontsize=8.5, color=stil.RENK[ton], fontweight="bold")
        karar = uretim_karari(k, m)
        ton = KARAR_TONU[karar]
        ax.add_patch(FancyBboxPatch((x_karar, r - 0.27), 2.75, 0.54, boxstyle="round,pad=0,rounding_size=0.12",
                                    fc=stil.DOLGU[ton], ec=stil.RENK[ton], lw=0.9))
        ax.text(x_karar + 0.12, r, KARAR_KISA[karar], ha="left", va="center", fontsize=7.4,
                color=stil.RENK["murekkep"], fontweight="bold")
    ax.set_title("Üç şart zinciri: CVSS değil, ilk düşen şart kararı belirler", pad=4)
    ax.text(0.05, len(satirlar) - 0.25, "✔ şart sağlanıyor (risk sürüyor) · ✖ şart düştü · – değerlendirilmez · "
            "* saldırganın VPN + MFA'yı aştığı kabul edildi", fontsize=6.4, color=stil.RENK["ikincil"], va="top")
    fig.savefig(yol)
    plt.close(fig)


def _grafik_zaman(yol):
    """Olay akışında kararın iki mimaride nasıl değiştiği (FOY-X)."""
    plt = stil.mpl()
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    k = kayit("FOY-X")
    olaylar = d("lab5.olay_akisi")
    n = len(olaylar)
    fig, ax = plt.subplots(figsize=(7.6, 3.05))
    ax.set_xlim(-1.55, n - 0.45)
    ax.set_ylim(2.05, -0.95)
    ax.axis("off")
    for i, o in enumerate(olaylar):
        ax.text(i, -0.62, f"{i + 1}", ha="center", va="center", fontsize=7.5, fontweight="bold", color="white",
                bbox=dict(boxstyle="circle,pad=0.25", fc=stil.RENK["murekkep"], ec="none"))
        ax.text(i, -0.25, o["ad"], ha="center", va="center", fontsize=7, color=stil.RENK["murekkep"])
    for r, (a, (ad, m)) in enumerate(MIMARILER.items()):
        y = r * 1.15 + 0.45
        ax.text(-1.5, y, ad.replace(", içeri girilmiş kabulü", "\n(içeri girilmiş)"), ha="left", va="center",
                fontsize=7.4, fontweight="bold", color=stil.RENK["ikincil"])
        akis = olay_akisi(k, m)
        for i, sonuc in enumerate(akis):
            ton = KARAR_TONU[sonuc["karar"]]
            ax.add_patch(FancyBboxPatch((i - 0.44, y - 0.3), 0.88, 0.6, boxstyle="round,pad=0,rounding_size=0.09",
                                        fc=stil.DOLGU[ton], ec=stil.RENK[ton], lw=1.1))
            ax.text(i, y - 0.06, KARAR_KISA[sonuc["karar"]].replace(" + ", " +\n"), ha="center", va="center",
                    fontsize=7, fontweight="bold", color=stil.RENK["murekkep"], linespacing=1.05)
            alt = "yeniden doğrula" if sonuc["dogrulama"] else _sart_ozeti(sonuc["sart"]).split(" (")[0]
            ax.text(i, y + 0.2, alt, ha="center", va="center", fontsize=5.6, color=stil.RENK["ikincil"])
            if i:
                ax.add_patch(FancyArrowPatch((i - 0.56, y), (i - 0.44, y), arrowstyle="-|>", mutation_scale=7,
                                             color=stil.RENK["cizgi"], lw=1))
    ax.set_title("Karar kapanmaz: her olayda yeniden hesaplanır (föy kaydı, CVSS 9,8)", pad=2)
    fig.savefig(yol)
    plt.close(fig)


def _grafik_karar_akisi(yol):
    """Karar akışı: sorular soldan sağa; her 'hayır' çıkışı sorusunun altında. Eşikler params.yaml'dan."""
    plt = stil.mpl()
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    R, D = stil.RENK, stil.DOLGU
    sure = sayi(d("lab5.telafi_azami_sure"), 0)
    sorular = ["1 · Bileşen\nSBOM'da\nvar mı?", "2 · Sürüm\netkileniyor\nmu?", "3 · Açık\nulaşılabilir\nmi?",
               "Emniyet\nfonksiyonuna\nyol var mı?", f"Telafi ≤ {sure} sa\nve istismar\nyok mu?"]
    son = ("Durdurmadan\nhemen telafi", KARAR_TONU["hemen_telafi"])
    cikislar = {  # soru indeksi → (metin, ton, kaç sütun kaplar); satırlar kutuya sığacak kadar kısa
        0: ("Etkilemez:\ngerekçesiyle kayda geç", KARAR_TONU["devam"], 2),
        2: ("Şimdilik\netkilemez:\nkoşulu izle", KARAR_TONU["devam"], 1),
        3: ("Devam +\nplanlı telafi\n(KEV: hemen)", KARAR_TONU["devam_telafi"], 1),
        4: ("Kontrollü\ndurdur +\ndoğrulama", KARAR_TONU["durdur"], 1),
    }
    G, Y, ARA = 1.1, 0.74, 1.36  # kutu genişliği, yüksekliği, sütun aralığı (çizim birimi)
    fig, ax = plt.subplots(figsize=(7.6, 2.85))
    ax.set_xlim(-1.25, len(sorular) * ARA + 0.62)
    ax.set_ylim(2.4, -0.5)
    ax.axis("off")

    def kutu(x, y, metin, ton, genislik=G, kalin=False):
        ax.add_patch(FancyBboxPatch((x - genislik / 2, y - Y / 2), genislik, Y,
                                    boxstyle="round,pad=0,rounding_size=0.07",
                                    fc=D[ton], ec=R[ton], lw=1.6 if kalin else 1.0))
        ax.text(x, y, metin, ha="center", va="center", fontsize=6.2, color=R["murekkep"], linespacing=1.2)

    def ok(x0, y0, x1, y1, etiket=None, dikey=False):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=8,
                                     color=R["ikincil"], lw=1.0, shrinkA=0, shrinkB=0))
        if etiket:
            xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
            ax.text(xm + (0.06 if dikey else 0), ym - (0 if dikey else 0.06), etiket, fontsize=5.6,
                    color=R["ikincil"], ha="left" if dikey else "center", va="center" if dikey else "bottom",
                    fontweight="bold")

    ax.text(-1.2, 0, "CVE\nkaydı", ha="left", va="center", fontsize=6.6, fontweight="bold", color=R["murekkep"])
    ok(-0.78, 0, -G / 2, 0)
    for i, metin in enumerate(sorular):
        x = i * ARA
        kutu(x, 0, metin, "bilgi")
        if i:
            ok(x - ARA + G / 2, 0, x - G / 2, 0, "evet")
    x_son = len(sorular) * ARA
    kutu(x_son, 0, son[0], son[1], kalin=True)
    ok(x_son - ARA + G / 2, 0, x_son - G / 2, 0, "evet")

    y_alt = 1.6
    for i, (metin, ton, kapla) in cikislar.items():
        x = i * ARA + (kapla - 1) * ARA / 2
        kutu(x, y_alt, metin, ton, genislik=G + (kapla - 1) * ARA, kalin=True)
        for j in range(i, i + kapla):
            ok(j * ARA, Y / 2, j * ARA, y_alt - Y / 2, "hayır", dikey=True)
    ax.text(-1.2, 2.3, "Renk kararın ağırlığını gösterir: yeşil etkilemez · mavi planlı · sarı acil telafi · "
            "kırmızı durdur. CVSS bu akışta bir eşik değildir.", fontsize=5.8, color=R["ikincil"], va="center")
    fig.savefig(yol)
    plt.close(fig)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    yaz = {
        "lab5_sbom.md": sbom_md(),
        "lab5_karar.md": karar_md(),
        "lab5_telafi.md": telafi_md(),
        "lab5_zaman.md": zaman_md(),
        "lab5_sapma.md": sapma_md(),
        "lab5_eol.md": eol_md(),
        "lab5_telafi_mevcut.mmd": mermaid_telafi(kayit("FOY-X"), MIMARILER["mevcut"][1]),
        "lab5_params.yaml": bolum_metni("lab5"),
    }
    for ad, metin in yaz.items():
        (OUT_DIR / ad).write_text(metin, encoding="utf-8")
    _grafik_karar_akisi(OUT_DIR / "lab5_karar_akisi.png")
    _grafik_uc_sart(OUT_DIR / "lab5_uc_sart.png")
    _grafik_zaman(OUT_DIR / "lab5_karar_zaman.png")
    print(karar_md())
    print(zaman_md())
    print(sapma_md())
    print(eol_md())


if __name__ == "__main__":
    main()
