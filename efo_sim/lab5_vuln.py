"""LAB 5 — SBOM / CVE / yama kararı (eğitim amaçlı).

5.1 Üç şart: bileşen SBOM'da var mı, sürüm etkileniyor mu, açık ulaşılabilir mi?
    Ulaşılabilirlik LAB 4 saldırı grafından hesaplanır (giriş noktalarından o düğüme yol var mı).
5.2 Karar akışı: üretim durur mu, yama nerede test edilir, emniyet validasyonu etkilenir mi,
    yama yoksa hangi telafi edici önlemler açığı kapatır?

Çalıştırma (repo kökünden):  python -m efo_sim.lab5_vuln
"""
from itertools import combinations

from efo_sim import lab4_attack as lab4
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


def sbom():
    return {b["id"]: b for b in d("lab5.sbom")}


def kayit(kayit_id):
    return next(k for k in d("lab5.kayitlar") if k["id"] == kayit_id)


def surum(metin):
    return tuple(int(p) for p in metin.split("."))


def surum_etkileniyor(mevcut, ilk_duzeltilmis):
    """İlk düzeltilmiş sürümden önceki her sürüm etkilenir."""
    if mevcut == "-" or ilk_duzeltilmis == "-":
        return False
    return surum(mevcut) < surum(ilk_duzeltilmis)


# ---------------------------------------------------------------- 5.1 Üç şart
def bilesen(k):
    """Kayıttaki ürün SBOM'daki hangi bileşen? Yoksa None."""
    return next((b for b in sbom().values() if b["urun"] == k["urun"]), None)


def uc_sart(k, mimari):
    b = bilesen(k)
    var = b is not None
    etkilenir = var and surum_etkileniyor(b["surum"], k["ilk_duzeltilmis"])
    ulasilir = var and b["dugum"] in lab4.ulasilabilir(mimari) and all(mimari[c] for c in k["ek_kosullar"])
    return {"var": var, "surum": etkilenir, "ulasilabilir": ulasilir}


def etkiler(k, mimari):
    return all(uc_sart(k, mimari).values())


# ---------------------------------------------------------------- 5.2 Karar akışı
def emniyete_yol(dugum, mimari):
    """Bu düğüm ele geçirilirse emniyet fonksiyonuna (LAB 4 grafı) yol var mı?"""
    return dugum == lab4.HEDEF_DUGUM or bool(lab4.yollar(mimari, dugum))


def validasyon_etkilenir(b, mimari):
    """Yama emniyet fonksiyonunun davranışını değiştirebilir mi? Evet ise yeniden doğrulama gerekir."""
    return b["dugum"] == "emniyet" or emniyete_yol(b["dugum"], mimari)


def telafi_plani(k, mimari):
    """Açığı ulaşılamaz kılan en kısa süreli önlem kümesi (bütün alt kümeler denenir)."""
    onlemler = [t for t in d("lab5.telafi_onlemleri") if mimari.get(t["kosul"])]
    adaylar = []
    for n in range(1, len(onlemler) + 1):
        for kume in combinations(onlemler, n):
            m = mimari | {t["kosul"]: False for t in kume}
            if not etkiler(k, m):
                adaylar.append((sum(t["saat"] for t in kume), len(kume), kume))
    if not adaylar:
        return None
    sure, _, kume = min(adaylar, key=lambda a: (a[0], a[1]))
    return {"onlemler": [t["id"] for t in kume], "saat": sure}


def uretim_karari(k, mimari, istismar_belirtisi=False):
    if not etkiler(k, mimari):
        return "devam"
    b = bilesen(k)
    if not emniyete_yol(b["dugum"], mimari):
        return "devam_telafi"
    plan = telafi_plani(k, mimari)
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


# ---------------------------------------------------------------- Çıktılar
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
        m2 = m | {onlem[i]["kosul"]: False for i in p["onlemler"]}
        kume = "<br>".join(f"{i}: {onlem[i]['ad']}" for i in p["onlemler"])
        s.append(f"| {ad} | {kume} | {sayi(p['saat'])} sa | {'evet' if etkiler(k, m2) else 'hayır'} | "
                 f"{'**evet**' if validasyon_etkilenir(bilesen(k), m) else 'hayır'} |")
    s += ["", f"Telafi için kabul edilen azami süre: {sayi(d('lab5.telafi_azami_sure'), 1)} saat. "
              "Aktif istismar belirtisi varsa ve bileşenden emniyet fonksiyonuna yol varsa karar doğrudan "
              f"\"{KARARLAR['durdur']}\" olur."]
    return "\n".join(s) + "\n"


def main():
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "lab5_sbom.md").write_text(sbom_md(), encoding="utf-8")
    (OUT_DIR / "lab5_karar.md").write_text(karar_md(), encoding="utf-8")
    (OUT_DIR / "lab5_telafi.md").write_text(telafi_md(), encoding="utf-8")
    (OUT_DIR / "lab5_params.yaml").write_text(bolum_metni("lab5"), encoding="utf-8")
    print(karar_md())
    print(telafi_md())


if __name__ == "__main__":
    main()
