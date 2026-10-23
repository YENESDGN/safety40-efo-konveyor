"""LAB 4 — Saldırı yolu analizi ve emniyet bağımsızlığı (eğitim amaçlı).

4.1 Saldırı grafı: giriş noktası → varlıklar → emniyet fonksiyonu. Kenarlar ön koşullu;
    bir kenar, mimarideki bütün koşulları doğruysa açıktır. Mevcut ve hedef mimaride
    emniyet fonksiyonuna ulaşan yollar sayılır.
4.2 Bağımsızlık: saldırgan PLC mantığını ya da invertör parametrelerini değiştirir;
    acil stop yine güvenli duruma götürüyor mu? Varyantlar yalnızca gösterim içindir;
    föy çözüm değil gereksinim tanımlatır.

Çalıştırma (repo kökünden):  python -m efo_sim.lab4_attack
"""
import math

from efo_sim import lab1_safety as lab1
from efo_sim.params import OUT_DIR, bolum_metni, d, gecici, sayi

HEDEF_DUGUM = "sf"
GIRISLER = {
    "internet": "İnternet",
    "uzak_arac": "Uzak destek aracı",
    "usb": "USB",
    "hmi_yerel": "HMI (yerel)",
    "wifi": "Wi-Fi / WLAN",
}
DUGUMLER = {
    **GIRISLER,
    "router": "4G/VPN router",
    "jump": "Jump server",
    "hmi": "HMI",
    "plc": "PLC",
    "vfd": "Bant invertörü",
    "emniyet": "Emniyet rölesi / Safety PLC",
    "sf": "SF1 acil stop → STO",
}

# (kaynak, hedef, koşullar, açıklama) — koşulların hepsi doğruysa kenar açık
KENARLAR = [
    ("internet", "router", ["router_surekli_acik"], "sürekli açık 4G router"),
    ("internet", "jump", ["jump_var", "mfa_asildi"], "VPN + MFA aşıldı"),
    ("uzak_arac", "hmi", ["uzak_masaustu_kurulu"], "HMI'da uzak masaüstü aracı"),
    ("router", "plc", ["duz_ag"], "düz ağ"),
    ("router", "hmi", ["duz_ag"], "düz ağ"),
    ("router", "vfd", ["duz_ag"], "düz ağ"),
    ("jump", "plc", [], "izin listesindeki mühendislik portu"),
    ("jump", "hmi", [], "HMI bakımı"),
    ("jump", "vfd", ["vfd_emniyet_parametresi_acik"], "emniyetle ilgili parametre yazma"),
    ("jump", "emniyet", ["emniyet_programi_agdan_erisilebilir"], "emniyet programına ağdan erişim"),
    ("usb", "hmi", ["usb_kilitsiz"], "kilitsiz USB"),
    ("hmi_yerel", "hmi", ["hmi_varsayilan_parola"], "varsayılan parola"),
    ("wifi", "vfd", ["wlan_modulu_acik"], "WLAN modülü açık"),
    ("hmi", "plc", [], "HMI etiket yazma / forcing"),
    ("plc", "vfd", ["vfd_emniyet_parametresi_acik"], "PLC'den emniyetle ilgili parametre yazma"),
    ("plc", "sf", ["emniyet_plcye_bagimli"], "acil stop PLC mantığında"),
    ("vfd", "sf", ["sto_ss1_vfdde"], "durma rampası ve STO invertörde"),
    ("vfd", "sf", ["hiz_izleme_yok"], "hız, güvenli mesafe varsayımını aşar"),
    ("emniyet", "sf", [], "emniyet programı değişir"),
]

MEVCUT = {  # tipik KOBİ kurulumu üzerinden varsayım (V2–V5); Efo'ya ait tespit değildir
    "router_surekli_acik": True, "jump_var": False, "mfa_asildi": False,
    "uzak_masaustu_kurulu": True, "duz_ag": True, "vfd_emniyet_parametresi_acik": True,
    "emniyet_programi_agdan_erisilebilir": False, "usb_kilitsiz": True, "hmi_varsayilan_parola": True,
    "wlan_modulu_acik": True, "emniyet_plcye_bagimli": True, "sto_ss1_vfdde": True, "hiz_izleme_yok": True,
}
HEDEF = {k: False for k in MEVCUT} | {"jump_var": True}
HEDEF_ICERI_GIRILDI = HEDEF | {"mfa_asildi": True}  # "saldırgan tüm önlemlere rağmen içeri girerse"


# ---------------------------------------------------------------- 4.1 Saldırı grafı
def acik_kenarlar(mimari):
    return [k for k in KENARLAR if all(mimari[c] for c in k[2])]


def yollar(mimari, baslangic, hedef=HEDEF_DUGUM):
    """Başlangıçtan hedefe giden bütün basit yollar (kenar dizileri)."""
    kenarlar = acik_kenarlar(mimari)
    sonuc = []

    def dfs(dugum, ziyaret, yol):
        if dugum == hedef:
            sonuc.append(list(yol))
            return
        for k in kenarlar:
            if k[0] == dugum and k[1] not in ziyaret:
                ziyaret.add(k[1])
                yol.append(k)
                dfs(k[1], ziyaret, yol)
                yol.pop()
                ziyaret.discard(k[1])

    dfs(baslangic, {baslangic}, [])
    return sonuc


def yol_ozeti(mimari, hedef=HEDEF_DUGUM):
    ozet = {}
    for g in GIRISLER:
        ys = yollar(mimari, g, hedef)
        en_kisa = min(ys, key=len) if ys else None
        ozet[g] = {"sayi": len(ys), "en_kisa": en_kisa}
    return ozet


def toplam_yol(mimari, hedef=HEDEF_DUGUM):
    return sum(v["sayi"] for v in yol_ozeti(mimari, hedef).values())


def ulasilabilir(mimari):
    """Herhangi bir giriş noktasından ulaşılabilen düğümler."""
    kenarlar = acik_kenarlar(mimari)
    gorulen = set(GIRISLER)
    degisti = True
    while degisti:
        degisti = False
        for k in kenarlar:
            if k[0] in gorulen and k[1] not in gorulen:
                gorulen.add(k[1])
                degisti = True
    return gorulen - set(GIRISLER)


# ---------------------------------------------------------------- 4.2 Bağımsızlık
VARYANTLAR = {
    "bagimli": "Emniyet kararı PLC'de, durdurma invertör rampasıyla",
    "bagimsiz": "Kablolu emniyet rölesi, SS1-t ile STO",
    "bagimsiz_hiz_izlemeli": "Emniyet rölesi + SS1-t + emniyet tarafında hız izleme",
}
SALDIRILAR = {
    "yok": {},
    "plc_mantigi": {"plc_mantigi": True},
    "rampa": {"rampa": True},
    "hiz_rampa": {"rampa": True, "hiz": True},
}
SALDIRI_ADI = {"yok": "Saldırı yok", "plc_mantigi": "PLC mantığı değişti (acil stop yok sayılır)",
               "rampa": "İnvertör rampası 10 s", "hiz_rampa": "İnvertör hızı 1,6× + rampa 10 s"}


def ele_gecirilmis_plc(durum, g):
    """Saldırganın değiştirdiği PLC mantığı: emniyet girişlerini yok sayar."""
    return lab1.sonraki_durum(durum, dict(g, acil_stop=False, cekme_ipi=False, kapak_acik=False))


def acil_stop_durumu(varyant, saldiri):
    """Model 1.1: çalışan bantta acil stop basılınca STO'yu belirleyen mantık hangi durumu verir?"""
    g = lab1.girisler(acil_stop=True)
    if varyant == "bagimli":
        mantik = ele_gecirilmis_plc if SALDIRILAR[saldiri].get("plc_mantigi") else lab1.sonraki_durum
        return mantik(lab1.CALISIYOR, g)
    return lab1.sonraki_durum(lab1.CALISIYOR, g)  # emniyet rölesi PLC'den bağımsız karar verir


def etkin_parametreler(varyant, saldiri):
    s = SALDIRILAR[saldiri]
    v = d("lab1.bant_hizi") * (d("lab3.saldiri_hiz_carpani") if s.get("hiz") else 1)
    if varyant == "bagimsiz_hiz_izlemeli":
        v = min(v, d("lab1.bant_hizi") * d("lab4.hiz_izleme_esigi_carpani"))
    rampa = d("lab3.saldiri_rampa_suresi") if s.get("rampa") else d("lab1.rampa_suresi_kat1")
    return v, rampa


def acil_stop_sonucu(varyant, saldiri):
    durum = acil_stop_durumu(varyant, saldiri)
    if durum != lab1.GUVENLI_DURUM:
        return {"durum": durum, "mesafe": math.inf, "ulasir": True}
    v, rampa = etkin_parametreler(varyant, saldiri)
    mesafe = lab1.durma_mesafesi(v, 1, rampa_suresi=rampa, ss1_emniyette=(varyant != "bagimli"))
    return {"durum": durum, "mesafe": mesafe, "ulasir": lab1.el_besleme_agzina_ulasir_mi(mesafe)}


# ---------------------------------------------------------------- 4.3 Varsayım etkisi (Bölüm 05 için)
def _esik(fonksiyon, aralik):
    """fonksiyon(x) True'dan False'a döndüğü x'i ikiye bölmeyle bulur (artan x'te ulaşma başlar)."""
    alt, ust = aralik
    if not fonksiyon(ust):
        return None
    for _ in range(d("lab4.arama_adim_sayisi")):
        orta = (alt + ust) / 2
        alt, ust = (alt, orta) if fonksiyon(orta) else (orta, ust)
    return ust


def varsayim_etkileri():
    """Kritik sayısal varsayımlar değişirse hangi sonuç değişir? Bölüm 05'teki tabloyu besler."""
    sonuc = {"sinir_hiz_kat0": lab1.sinir_hiz(0), "sinir_hiz_kat1": lab1.sinir_hiz(1)}

    def ulasir(varyant, saldiri):
        return acil_stop_sonucu(varyant, saldiri)["ulasir"]

    with gecici("lab1.guvenli_mesafe", d("lab4.alternatif_guvenli_mesafe")):
        sonuc["kisa_mesafe"] = {
            (v, sa): ulasir(v, sa) for v in VARYANTLAR for sa in SALDIRILAR}
        sonuc["kisa_mesafe_sinir_hiz_kat1"] = lab1.sinir_hiz(1)

    def ss1_ulasir(t):
        with gecici("lab1.ss1_gecikmesi", t):
            return ulasir("bagimsiz", "rampa")

    def esik_ulasir(c):
        with gecici("lab4.hiz_izleme_esigi_carpani", c):
            return ulasir("bagimsiz_hiz_izlemeli", "hiz_rampa")

    sonuc["ss1_esik"] = _esik(ss1_ulasir, d("lab4.arama_araligi_ss1"))
    sonuc["izleme_esik"] = _esik(esik_ulasir, d("lab4.arama_araligi_esik"))
    return sonuc


def varsayim_etkileri_md():
    from efo_sim import lab3_risk

    e = varsayim_etkileri()
    alt = d("lab4.alternatif_guvenli_mesafe")
    bozulan = [f"{VARYANTLAR[v]} / {SALDIRI_ADI[sa]}" for (v, sa), u in e["kisa_mesafe"].items()
               if u and not acil_stop_sonucu(v, sa)["ulasir"]]
    temel, satirlar = lab3_risk.duyarlilik()
    ilk = [r for r in satirlar if r["ilk_degisti"]]
    s = ["| Varsayım | Koddan hesaplanan etki |", "|---|---|",
         f"| V6 bant hızı | Nominal parametrelerde durma mesafesi, bant hızı stop kat. 0'da {sayi(e['sinir_hiz_kat0'])} m/s'yi, "
         f"kat. 1'de {sayi(e['sinir_hiz_kat1'])} m/s'yi aşınca güvenli mesafeyi geçer. |",
         f"| V8 güvenli mesafe | Mesafe {sayi(alt)} m olsaydı kat. 1 sınır hızı {sayi(e['kisa_mesafe_sinir_hiz_kat1'])} m/s'ye "
         f"düşer; ek olarak sınırı aşan durumlar: " + ("; ".join(bozulan) if bozulan else "yok") + ". |",
         f"| V9 SS1-t gecikmesi | Bağımsız varyantta rampa saldırısı, gecikme "
         + (f"{sayi(e['ss1_esik'])} s'yi aşarsa" if e["ss1_esik"] else "aranan aralıkta hiçbir değerde")
         + " elin besleme ağzına ulaşmasına yol açar. |",
         f"| V14 hız izleme eşiği | Hız + rampa saldırısında eşik, nominalin "
         + (f"{sayi(e['izleme_esik'])} katını aşarsa" if e["izleme_esik"] else "aranan aralıkta hiçbir değerde")
         + " sınır aşılır. |",
         f"| V12 L/E puanları | {len(satirlar)} tek-puan değişiminin {len(ilk)} tanesinde ilk öncelik değişiyor"
         + (": " + "; ".join(f"{r['id']} {r['parametre']} {r['eski']}→{r['yeni']} (yeni ilk: {r['sira'][0]})" for r in ilk)
            if ilk else "") + ". |"]
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------- Çıktılar
def mermaid_saldiri(mimari):
    satirlar = ["flowchart TB"]
    for n, ad in DUGUMLER.items():
        if n in GIRISLER:
            satirlar.append(f'  {n}(["{ad}"])')
        elif n == HEDEF_DUGUM:
            satirlar.append(f'  {n}{{{{"{ad}"}}}}')
        else:
            satirlar.append(f'  {n}["{ad}"]')
    acik = acik_kenarlar(mimari)
    erisilen = ulasilabilir(mimari) | set(GIRISLER)
    yol_uzerinde = {KENARLAR.index(k) for g in GIRISLER for y in yollar(mimari, g) for k in y}
    stiller = []
    for i, k in enumerate(KENARLAR):
        if i in yol_uzerinde:
            satirlar.append(f'  {k[0]} -->|"{k[3]}"| {k[1]}')       # emniyet fonksiyonuna giden yol
            stiller.append(f"  linkStyle {i} stroke:#b3261e,stroke-width:3px")
        elif k in acik and k[0] in erisilen:
            satirlar.append(f'  {k[0]} -->|"{k[3]}"| {k[1]}')       # ulaşılabilir ama yol dışında
            stiller.append(f"  linkStyle {i} stroke:#e2a91c,stroke-width:2px")
        else:
            isaret = "✕ " if k not in acik else ""
            satirlar.append(f'  {k[0]} -.-|"{isaret}{k[3]}"| {k[1]}')  # kapalı ya da ulaşılamaz
            stiller.append(f"  linkStyle {i} stroke:#c3c8d0,stroke-width:1px")
    satirlar += [
        "  classDef giris fill:#fdeee6,stroke:#d9572e,color:#16223a",
        "  classDef hedef fill:#fdecea,stroke:#b3261e,stroke-width:3px,color:#16223a",
        "  classDef varlik fill:#e9f1fb,stroke:#2a78d6,color:#16223a",
        f"  class {','.join(GIRISLER)} giris",
        f"  class {HEDEF_DUGUM} hedef",
        "  class " + ",".join(n for n in DUGUMLER if n not in GIRISLER and n != HEDEF_DUGUM) + " varlik",
    ]
    return "\n".join(satirlar + stiller) + "\n"


def yol_md():
    def yol_metni(y):
        return " → ".join([DUGUMLER[y[0][0]]] + [DUGUMLER[k[1]] for k in y]) if y else "—"

    m, h, hi = yol_ozeti(MEVCUT), yol_ozeti(HEDEF), yol_ozeti(HEDEF_ICERI_GIRILDI)
    s = ["| Giriş noktası | Mevcut: yol sayısı | Mevcut: en kısa yol | Hedef | Hedef, içeri girilmiş |",
         "|---|---|---|---|---|"]
    for g, ad in GIRISLER.items():
        s.append(f"| {ad} | {m[g]['sayi']} | {yol_metni(m[g]['en_kisa'])} | {h[g]['sayi']} | {hi[g]['sayi']} |")
    s.append(f"| **Toplam** | **{toplam_yol(MEVCUT)}** | | **{toplam_yol(HEDEF)}** | **{toplam_yol(HEDEF_ICERI_GIRILDI)}** |")
    ic = sorted(DUGUMLER[n] for n in ulasilabilir(HEDEF_ICERI_GIRILDI))
    s += ["", f"Hedef mimaride saldırgan VPN ve MFA'yı aşmış kabul edildiğinde ulaşabildiği düğümler: "
              f"**{', '.join(ic)}**. Emniyet fonksiyonu bu listede yok."]
    return "\n".join(s) + "\n"


def bagimsizlik_md():
    s = ["| Varyant | Saldırı | Acil stop sonrası durum | Durma mesafesi | El besleme ağzına ulaşır mı? |",
         "|---|---|---|---|---|"]
    for v, vad in VARYANTLAR.items():
        for sa in SALDIRILAR:
            r = acil_stop_sonucu(v, sa)
            mesafe = "bant durmaz" if math.isinf(r["mesafe"]) else f"{sayi(r['mesafe'], 3)} m"
            s.append(f"| {vad} | {SALDIRI_ADI[sa]} | {r['durum']} | {mesafe} | "
                     f"{'**Evet**' if r['ulasir'] else 'Hayır'} |")
    s += ["", f"Güvenli mesafe {sayi(d('lab1.guvenli_mesafe'))} m; SS1-t gecikmesi {sayi(d('lab1.ss1_gecikmesi'), 1)} s; "
              f"hız izleme eşiği nominalin {sayi(d('lab4.hiz_izleme_esigi_carpani'), 1)} katı."]
    return "\n".join(s) + "\n"


def _grafik_bagimsizlik(yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker

    saldirilar = ["yok", "rampa", "hiz_rampa"]
    renkler = {"bagimli": "#eb6834", "bagimsiz": "#2a78d6", "bagimsiz_hiz_izlemeli": "#1baf7a"}
    genislik = 0.26
    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=200)
    for i, (v, vad) in enumerate(VARYANTLAR.items()):
        xs = [j + (i - 1) * genislik for j in range(len(saldirilar))]
        ys = [acil_stop_sonucu(v, sa)["mesafe"] for sa in saldirilar]
        ax.bar(xs, ys, width=genislik - 0.03, color=renkler[v], label=vad)
        for x, y in zip(xs, ys):
            ax.text(x, y + 0.08, sayi(y, 2), ha="center", va="bottom", fontsize=7, color="#1d2433")
    sinir = d("lab1.guvenli_mesafe")
    ax.axhline(sinir, color="#b3261e", lw=1.2, ls="--")
    ax.text(-0.45, sinir + 0.12, f"güvenli mesafe {sayi(sinir)} m", ha="left", fontsize=8, color="#b3261e")
    ax.set_xticks(range(len(saldirilar)))
    ax.set_xticklabels([SALDIRI_ADI[s] for s in saldirilar], fontsize=8)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: sayi(x, 1)))
    ax.set_ylabel("Durma mesafesi (m)")
    ax.set_title("Parametre saldırısında durma mesafesi: emniyet mimarisine göre", fontsize=10, loc="left")
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(yol)
    plt.close(fig)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "lab4_saldiri_mevcut.mmd").write_text(mermaid_saldiri(MEVCUT), encoding="utf-8")
    (OUT_DIR / "lab4_saldiri_hedef.mmd").write_text(mermaid_saldiri(HEDEF_ICERI_GIRILDI), encoding="utf-8")
    (OUT_DIR / "lab4_yollar.md").write_text(yol_md(), encoding="utf-8")
    (OUT_DIR / "lab4_bagimsizlik.md").write_text(bagimsizlik_md(), encoding="utf-8")
    (OUT_DIR / "lab4_params.yaml").write_text(bolum_metni("lab4"), encoding="utf-8")
    _grafik_bagimsizlik(OUT_DIR / "lab4_bagimsizlik.png")
    (OUT_DIR / "varsayim_etkileri.md").write_text(varsayim_etkileri_md(), encoding="utf-8")
    print(yol_md())
    print(bagimsizlik_md())


if __name__ == "__main__":
    main()
