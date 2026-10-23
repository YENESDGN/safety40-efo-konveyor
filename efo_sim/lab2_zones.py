"""LAB 2 — IEC 62443 zone/conduit modeli (eğitim amaçlı).

Varlıklar, bölgeler, akışlar ve conduit kontrolleri veri olarak tanımlanır.
Mermaid diyagramı ve kural kontrolü aynı veriden üretilir; diyagram ile veri hep tutarlıdır.

İki mimari var:
  MEVCUT — tipik KOBİ kurulumu üzerinden kurulmuş varsayım (V3, V5); Efo'ya ait bir tespit değildir.
  HEDEF  — föyün ilkeleriyle yeniden gruplanmış mimari.

Çalıştırma (repo kökünden):  python -m efo_sim.lab2_zones
"""
from efo_sim.params import OUT_DIR, bolum_metni, d

EMNIYET, DIS, DMZ = "Z5", "Z0", "Z2"

# Varlık: ad, Efo'da durumu (var / yok / bilinmiyor), etiket, dayanak
VARLIKLAR = {
    "uzak_servis": ("Üretici uzak servis bilgisayarı", "bilinmiyor", "VARSAYIM", "V5"),
    "telefon": ("Telefon / tablet (WLAN menzilinde)", "bilinmiyor", "SEKTÖR-TİPİK", "Y17"),
    "bulut": ("Bulut telemetri (kestirimci bakım)", "bilinmiyor", "SEKTÖR-TİPİK", "R30, R71"),
    "ofis": ("Müşteri ofis ağı (ERP, e-posta)", "var", "ÇIKARIM", "müşteri tesisi"),
    "router": ("4G/VPN router (uzak destek)", "bilinmiyor", "VARSAYIM", "V5, R13"),
    "jump": ("Jump server + uzak erişim aracısı", "yok", "SEKTÖR-TİPİK", "Y15"),
    "ayna": ("Veri aynası (historian kopyası)", "yok", "SEKTÖR-TİPİK", "R57"),
    "scada": ("Müşteri SCADA / MES istemcisi", "bilinmiyor", "VARSAYIM", "-"),
    "plc": ("Hat PLC'si", "bilinmiyor", "VARSAYIM", "V3"),
    "hmi": ("Operatör paneli / HMI (kabin)", "bilinmiyor", "ÇIKARIM", "V3, Y3"),
    "vfd_bant": ("Bant invertörü", "bilinmiyor", "VARSAYIM", "V2"),
    "vfd_sarsak": ("Sarsak tahrik sürücüsü", "bilinmiyor", "VARSAYIM", "V2"),
    "yongalama": ("Yongalama makinesi kontrolörü", "bilinmiyor", "VARSAYIM", "V7"),
    "kumanda": ("Yerel kumanda kutusu (start/stop)", "var", "ÇIKARIM", "Y3"),
    "emniyet": ("Emniyet rölesi / Safety PLC", "bilinmiyor", "VARSAYIM", "V4"),
    "girisler": ("Acil stop, çekme ipi, kapak anahtarları, reset", "bilinmiyor", "VARSAYIM", "V4"),
    "sto": ("STO hattı (invertör STO girişleri)", "bilinmiyor", "VARSAYIM", "V2, V4"),
    "laptop": ("Servis laptopu", "bilinmiyor", "VARSAYIM", "R13"),
    "usb": ("USB bellek", "bilinmiyor", "VARSAYIM", "-"),
}

BOLGELER = {
    "Z0": "Dış bölge — internet, üretici servisi, WLAN menzili",
    "Z1": "Kurumsal bölge — müşteri ofis ağı",
    "Z2": "OT DMZ — jump server, veri aynası",
    "Z3": "Tesis denetim bölgesi — SCADA / MES",
    "Z4": "Hat kumanda bölgesi — PLC, HMI, invertörler",
    "Z5": "Emniyet bölgesi — emniyet rölesi, acil stop, STO",
    "ZT": "Geçici bakım cihazları — laptop, USB",
    "ZD": "Düz ağ — ofis, SCADA ve hat aynı ağda",
}

# ------------------------------------------------------------------ HEDEF mimari
HEDEF = {
    "atama": {
        "uzak_servis": "Z0", "bulut": "Z0",
        "ofis": "Z1",
        "jump": "Z2", "ayna": "Z2",
        "scada": "Z3",
        "plc": "Z4", "hmi": "Z4", "vfd_bant": "Z4", "vfd_sarsak": "Z4", "yongalama": "Z4", "kumanda": "Z4",
        "emniyet": "Z5", "girisler": "Z5", "sto": "Z5",
        "laptop": "ZT", "usb": "ZT",
    },
    "conduitler": {
        "C1": {"kisa": "VPN · MFA · kayıt<br/>varsayılan kapalı",
               "kontroller": ["VPN", "MFA", "kişisel hesap", "varsayılan kapalı, tesis onayıyla açılır",
                              "tam oturum kaydı"]},
        "C2": {"kisa": "tek yönlü veri", "kontroller": ["güvenlik duvarı", "tek yönlü veri aktarımı (Z3 → Z2)"]},
        "C3": {"kisa": "izin listesi · kayıt · parametre kilidi",
               "kontroller": ["güvenlik duvarı izin listesi (yalnız mühendislik portları)", "oturum kaydı",
                              "emniyetle ilgili invertör parametreleri parola + checksum ile kilitli"]},
        "C4": {"kisa": "salt okuma", "kontroller": ["güvenlik duvarı", "salt okuma protokol filtresi"]},
        "C5": {"kisa": "salt okuma · kimlik", "kontroller": ["güvenlik duvarı", "kurumsal kimlik doğrulama",
                                                          "salt okuma"]},
        "C6": {"kisa": "giden · TLS", "kontroller": ["yalnız giden bağlantı", "TLS", "güvenlik duvarı"]},
        "C7": {"kisa": "port kilidi · kayıtlı cihaz",
               "kontroller": ["fiziksel port kilidi", "yalnız tesise kayıtlı ve taranmış cihaz", "kişisel hesap",
                              "değişiklik kaydı"]},
        "C8": {"kisa": "kablolu tek yönlü durum", "kontroller": ["kablolu, tek yönlü durum sinyali (Z5 → Z4)"]},
    },
    # (kaynak, hedef, ne, yön, conduit)  yön: yazma = hedefin durumunu/komutunu değiştirir; okuma = yalnız okur
    "akislar": [
        ("uzak_servis", "jump", "uzak bakım oturumu", "yazma", "C1"),
        ("jump", "plc", "mühendislik erişimi", "yazma", "C3"),
        ("jump", "hmi", "HMI bakımı", "yazma", "C3"),
        ("jump", "vfd_bant", "invertör bakımı", "yazma", "C3"),
        ("scada", "plc", "üretim verisi", "okuma", "C4"),
        ("scada", "ayna", "veri yansıtma", "yazma", "C2"),
        ("ofis", "ayna", "rapor okuma", "okuma", "C5"),
        ("ayna", "bulut", "telemetri gönderimi", "yazma", "C6"),
        ("laptop", "plc", "yerel servis", "yazma", "C7"),
        ("usb", "hmi", "reçete / güncelleme", "yazma", "C7"),
        ("plc", "vfd_bant", "hız komutu", "yazma", None),
        ("plc", "vfd_sarsak", "hız komutu", "yazma", None),
        ("plc", "yongalama", "durum okuma", "okuma", None),
        ("kumanda", "plc", "start / stop", "yazma", None),
        ("girisler", "emniyet", "acil stop, ip, kapak, reset", "yazma", None),
        ("emniyet", "sto", "STO", "yazma", None),
        ("emniyet", "plc", "emniyet durumu", "yazma", "C8"),
    ],
}

# ------------------------------------------------------------------ MEVCUT mimari (varsayım)
MEVCUT = {
    "atama": {
        "uzak_servis": "Z0", "telefon": "Z0", "bulut": "Z0",
        "ofis": "ZD", "router": "ZD", "scada": "ZD",
        "plc": "ZD", "hmi": "ZD", "vfd_bant": "ZD", "vfd_sarsak": "ZD", "yongalama": "ZD", "kumanda": "ZD",
        "girisler": "Z5", "sto": "Z5",
        "laptop": "ZT", "usb": "ZT",
    },
    "conduitler": {
        # sürekli açık 4G router, paylaşılan parola — kontrol tanımlı değil
        "C1": {"kisa": "sürekli açık · paylaşılan parola", "kontroller": []},
    },
    "akislar": [
        ("uzak_servis", "router", "uzak masaüstü / VPN (sürekli açık)", "yazma", "C1"),
        ("telefon", "vfd_bant", "WLAN ile parametre", "yazma", None),
        ("plc", "bulut", "telemetri", "yazma", None),
        ("router", "plc", "programlama", "yazma", None),
        ("router", "hmi", "uzak ekran", "yazma", None),
        ("ofis", "plc", "web arayüzü (port 80)", "yazma", None),
        ("scada", "plc", "üretim verisi", "okuma", None),
        ("laptop", "plc", "yerel servis", "yazma", None),
        ("usb", "hmi", "güncelleme", "yazma", None),
        ("plc", "vfd_bant", "hız komutu", "yazma", None),
        ("plc", "vfd_sarsak", "hız komutu", "yazma", None),
        ("plc", "yongalama", "durum okuma", "okuma", None),
        ("kumanda", "plc", "start / stop", "yazma", None),
        ("girisler", "plc", "acil stop PLC girişinde", "okuma", None),
        ("plc", "sto", "STO'yu PLC çıkışı veriyor", "yazma", None),
    ],
}


# ------------------------------------------------------------------ Kurallar
def bolge(mimari, varlik):
    return mimari["atama"][varlik]


def bolgeler_arasi(mimari):
    return [a for a in mimari["akislar"] if bolge(mimari, a[0]) != bolge(mimari, a[1])]


def kural_disaridan_emniyete_dogrudan_kenar_yok(mimari):
    return [a for a in mimari["akislar"]
            if bolge(mimari, a[0]) == DIS and bolge(mimari, a[1]) == EMNIYET]


def kural_her_bolgeler_arasi_kenar_conduitten_gecer(mimari):
    return [a for a in bolgeler_arasi(mimari) if a[4] is None]


def kural_her_conduitte_kontrol_var(mimari):
    asgari = d("lab2.conduit_min_kontrol_sayisi")
    return [c for c, k in mimari["conduitler"].items() if len(k["kontroller"]) < asgari]


def kural_emniyete_disaridan_yazma_yok(mimari):
    return [a for a in mimari["akislar"]
            if bolge(mimari, a[1]) == EMNIYET and bolge(mimari, a[0]) != EMNIYET and a[3] == "yazma"]


def kural_dis_bolge_yalniz_dmzye_baglanir(mimari):
    return [a for a in mimari["akislar"]
            if DIS in (bolge(mimari, a[0]), bolge(mimari, a[1]))
            and DMZ not in (bolge(mimari, a[0]), bolge(mimari, a[1]))]


KURALLAR = [
    ("K1", "Dış bölgeden emniyet bölgesine doğrudan kenar yok", kural_disaridan_emniyete_dogrudan_kenar_yok),
    ("K2", "Bölgeler arası her kenar bir conduit'ten geçiyor", kural_her_bolgeler_arasi_kenar_conduitten_gecer),
    ("K3", "Her conduit'te en az bir kontrol tanımlı", kural_her_conduitte_kontrol_var),
    ("K4", "Emniyet bölgesine dışarıdan yazma yönünde akış yok", kural_emniyete_disaridan_yazma_yok),
    ("K5", "Dış bölge yalnızca DMZ'ye bağlanıyor", kural_dis_bolge_yalniz_dmzye_baglanir),
]


def kontrol(mimari):
    return {kid: fn(mimari) for kid, _, fn in KURALLAR}


# ------------------------------------------------------------------ Mermaid üretimi
def mermaid(mimari):
    ihlal = {id(a) for ihlaller in kontrol(mimari).values() for a in ihlaller if isinstance(a, tuple)}
    satirlar = ["flowchart TB"]
    kullanilan = sorted(set(mimari["atama"].values()), key=lambda z: list(BOLGELER).index(z))
    for z in kullanilan:
        satirlar.append(f'  subgraph {z}["{z} · {BOLGELER[z]}"]')
        for v, vz in mimari["atama"].items():
            if vz == z:
                ad, durum = VARLIKLAR[v][0], VARLIKLAR[v][1]
                satirlar.append(f'    {v}["{ad}<br/><i>{durum}</i>"]')
        satirlar.append("  end")
    stiller = []
    for i, a in enumerate(mimari["akislar"]):
        k, h, ne, yon, c = a
        etiket = f"{c}: {ne}" if c else ne
        ok = "-->" if yon == "yazma" else "-.->"
        satirlar.append(f'  {k} {ok}|"{etiket}"| {h}')
        if id(a) in ihlal:
            stiller.append(f"  linkStyle {i} stroke:#b3261e,stroke-width:3px")
    satirlar += [
        "  classDef emniyet fill:#fdecea,stroke:#b3261e,stroke-width:2px,color:#16223a",
        "  classDef dis fill:#fdeee6,stroke:#d9572e,color:#16223a",
        "  classDef dmz fill:#fbf6e6,stroke:#8a6d1f,color:#16223a",
        "  classDef kumanda fill:#e9f1fb,stroke:#2a78d6,color:#16223a",
    ]
    sinif = {"Z5": "emniyet", "Z0": "dis", "Z2": "dmz", "Z4": "kumanda", "ZD": "kumanda"}
    for v, z in mimari["atama"].items():
        if z in sinif:
            satirlar.append(f"  class {v} {sinif[z]}")
    return "\n".join(satirlar + stiller) + "\n"


# Diyagramda düğümlerin yazılma sırası (kenarların başka bölgelerin arkasından geçmemesi için)
DIYAGRAM_SIRASI = ["Z0", "Z1", "Z3", "ZT", "Z2", "ZD", "Z5", "Z4"]


def kisa_ad(varlik):
    return VARLIKLAR[varlik][0].split(" (")[0]


def mermaid_bolge(mimari):
    """Bölge düzeyi zone/conduit diyagramı: düğüm = bölge, kenar = conduit (ya da kontrolsüz geçiş)."""
    satirlar = ["flowchart TB"]
    kullanilan = sorted(set(mimari["atama"].values()), key=lambda z: DIYAGRAM_SIRASI.index(z))
    for z in kullanilan:
        baslik, uyeler = BOLGELER[z].split(" — ")[0], [kisa_ad(v) for v, vz in mimari["atama"].items() if vz == z]
        satirlar.append(f'  {z}["<b>{z} · {baslik}</b><br/>{"<br/>".join(uyeler)}"]')
    gruplar = {}
    for k, h, ne, yon, c in bolgeler_arasi(mimari):
        gruplar.setdefault((bolge(mimari, k), bolge(mimari, h), c), []).append(ne)
    stiller = []
    for i, ((zk, zh, c), isler) in enumerate(gruplar.items()):
        if c is None:
            etiket, stil = "kontrolsüz: " + ", ".join(isler), "stroke:#b3261e,stroke-width:3px"
        elif not mimari["conduitler"][c]["kontroller"]:
            etiket, stil = f"{c} · " + mimari["conduitler"][c]["kisa"], "stroke:#b3261e,stroke-width:3px"
        else:
            etiket, stil = f"{c} · " + mimari["conduitler"][c]["kisa"], "stroke:#1f8f86,stroke-width:2px"
        satirlar.append(f'  {zk} -->|"{etiket}"| {zh}')
        stiller.append(f"  linkStyle {i} {stil}")
    sinif = {"Z5": "emniyet", "Z0": "dis", "Z2": "dmz", "Z4": "kumanda", "ZD": "duz", "ZT": "gecici",
             "Z1": "kurumsal", "Z3": "kurumsal"}
    satirlar += [
        "  classDef emniyet fill:#fdecea,stroke:#b3261e,stroke-width:3px,color:#16223a",
        "  classDef dis fill:#fdeee6,stroke:#d9572e,color:#16223a",
        "  classDef dmz fill:#fbf6e6,stroke:#8a6d1f,stroke-width:2px,color:#16223a",
        "  classDef kumanda fill:#e9f1fb,stroke:#2a78d6,stroke-width:2px,color:#16223a",
        "  classDef duz fill:#fdecea,stroke:#d9572e,stroke-width:2px,stroke-dasharray:6 4,color:#16223a",
        "  classDef gecici fill:#f2f5f8,stroke:#5b6576,color:#16223a",
        "  classDef kurumsal fill:#f7f9fb,stroke:#5b6576,color:#16223a",
    ]
    satirlar += [f"  class {z} {sinif[z]}" for z in kullanilan if z in sinif]
    # görünmez bağ: emniyet bölgesini kumanda bölgesinin altına yerleştirir (föydeki şema gibi)
    alt = [z for z in ("Z4", "ZD") if z in kullanilan]
    if alt and EMNIYET in kullanilan:
        satirlar.append(f"  {alt[0]} ~~~ {EMNIYET}")
    return "\n".join(satirlar + stiller) + "\n"


# ------------------------------------------------------------------ Tablolar
def varlik_tablosu_md():
    s = ["| Varlık | Efo'da | Etiket | Dayanak | Mevcut bölge | Hedef bölge |", "|---|---|---|---|---|---|"]
    for v, (ad, durum, etiket, dayanak) in VARLIKLAR.items():
        s.append(f"| {ad} | {durum} | [{etiket}] | {dayanak} | {MEVCUT['atama'].get(v, '—')} | "
                 f"{HEDEF['atama'].get(v, '—')} |")
    return "\n".join(s) + "\n"


def bolge_tablosu_md(mimari):
    s = ["| Bölge | Tanım | Varlıklar |", "|---|---|---|"]
    for z in BOLGELER:
        uyeler = [VARLIKLAR[v][0] for v, vz in mimari["atama"].items() if vz == z]
        if uyeler:
            s.append(f"| **{z}** | {BOLGELER[z]} | {'; '.join(uyeler)} |")
    return "\n".join(s) + "\n"


def conduit_tablosu_md(mimari):
    s = ["| Conduit | Nereden → nereye | Akışlar | Kontroller |", "|---|---|---|---|"]
    for c, k in mimari["conduitler"].items():
        kontroller = k["kontroller"]
        akislar = [a for a in mimari["akislar"] if a[4] == c]
        yonler = sorted({f"{bolge(mimari, a[0])} → {bolge(mimari, a[1])}" for a in akislar})
        s.append(f"| **{c}** | {', '.join(yonler)} | {'; '.join(a[2] for a in akislar)} | "
                 f"{'; '.join(kontroller) if kontroller else '**yok**'} |")
    return "\n".join(s) + "\n"


def kural_tablosu_md():
    m, h = kontrol(MEVCUT), kontrol(HEDEF)

    def ozet(ihlaller):
        if not ihlaller:
            return "✔ uyuyor"
        parcalar = [f"{VARLIKLAR[i[0]][0]} → {VARLIKLAR[i[1]][0]}" if isinstance(i, tuple) else i
                    for i in ihlaller]
        return f"✖ {len(ihlaller)} ihlal: " + "; ".join(parcalar)

    s = ["| Kural | Mevcut (varsayım) | Hedef |", "|---|---|---|"]
    for kid, ad, _ in KURALLAR:
        s.append(f"| **{kid}** {ad} | {ozet(m[kid])} | {ozet(h[kid])} |")
    return "\n".join(s) + "\n"


def main():
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "lab2_hedef.mmd").write_text(mermaid_bolge(HEDEF), encoding="utf-8")
    (OUT_DIR / "lab2_mevcut.mmd").write_text(mermaid_bolge(MEVCUT), encoding="utf-8")
    (OUT_DIR / "lab2_hedef_varlik.mmd").write_text(mermaid(HEDEF), encoding="utf-8")
    (OUT_DIR / "lab2_varliklar.md").write_text(varlik_tablosu_md(), encoding="utf-8")
    (OUT_DIR / "lab2_bolgeler.md").write_text(bolge_tablosu_md(HEDEF), encoding="utf-8")
    (OUT_DIR / "lab2_conduitler.md").write_text(conduit_tablosu_md(HEDEF), encoding="utf-8")
    (OUT_DIR / "lab2_kurallar.md").write_text(kural_tablosu_md(), encoding="utf-8")
    (OUT_DIR / "lab2_params.yaml").write_text(bolum_metni("lab2"), encoding="utf-8")
    print(kural_tablosu_md())


if __name__ == "__main__":
    main()
