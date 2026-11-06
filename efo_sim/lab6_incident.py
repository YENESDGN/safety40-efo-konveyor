"""LAB 6 — CRA olay simülasyonu (eğitim amaçlı).

6.1 Emniyet doğrulaması: olay sırasında salt okunur alınan konfigürasyon, onaylı referansla
    karşılaştırılır; fark LAB 4 bağımsızlık modelinde bir saldırıya çevrilir ve acil stop
    yine güvenli duruma götürüyor mu diye bakılır.
6.2 Zaman çizgisi: eylemler, kanıtı silen eylemlerden önce kanıt alınmış mı, emniyet ilk mi,
    hesap 2 saat içinde kapanmış mı? "Resetleyip devam edelim" akışı karşı örnek olarak tutulur.
6.3 CRA paketleri: 24 sa / 72 sa / 14 gün için gereken her bilgi, süresinden önce tamamlanan
    bir eylemden geliyor mu?
6.4 Etki alanı: paylaşılan servis hesabı ele geçince filodaki hangi kurulumlara ulaşılır, hangilerinde
    emniyet riskte? Kişisel hesaplarda etki olayın tesisiyle sınırlı kalır.
6.5 Kanıt ömrü: router ve HMI logları belirli bir süre sonra kendiliğinden silinir. Ekip geç gelirse
    hangi kanıt kaybolur ve CRA paketlerinde hangi bilgi eksik kalır?

Kurulum filosu ve hesap düzenleri ürün önerisi değildir; etki alanının neye bağlı olduğunu göstermek içindir.

Çalıştırma (repo kökünden):  python -m efo_sim.lab6_incident
"""
import math

from efo_sim import stil
from efo_sim import lab4_attack as lab4
from efo_sim.params import OUT_DIR, bolum_metni, d, sayi

# ---------------------------------------------------------------- 6.1 Emniyet doğrulaması
FARK_SALDIRI = {  # konfigürasyon farkı → LAB 4'teki saldırı karşılığı
    "plc_proje_crc": "plc_mantigi",
    "rampa_suresi": "rampa",
    "hiz_carpani": "hiz_rampa",
}


def konfig_farki(referans=None, okunan=None):
    referans = referans or d("lab6.referans_konfig")
    okunan = okunan or d("lab6.okunan_konfig")
    return [k for k in referans if referans[k] != okunan[k]]


def emniyet_degerlendirmesi(varyant, fark=None):
    """Her fark için acil stop sonucu; en kötüsü belirleyicidir. Emniyet rölesi ayarı değiştiyse güven yok."""
    fark = konfig_farki() if fark is None else fark
    if "emniyet_rolesi_ayar" in fark:
        return {"guvende": False, "neden": "emniyet rölesi ayarı referanstan farklı", "sonuclar": {}}
    saldirilar = sorted({FARK_SALDIRI[f] for f in fark}) or ["yok"]
    sonuclar = {sa: lab4.acil_stop_sonucu(varyant, sa) for sa in saldirilar}
    kotu = [sa for sa, r in sonuclar.items() if r["ulasir"]]
    neden = ("; ".join(lab4.SALDIRI_ADI[sa] for sa in kotu) + " → el besleme ağzına ulaşır") if kotu \
        else "her farkta acil stop güvenli mesafede durduruyor"
    return {"guvende": not kotu, "neden": neden, "sonuclar": sonuclar}


# ---------------------------------------------------------------- 6.2 Zaman çizgisi
KANITLAR = {
    "K1": "PLC projesi + CRC (salt okunur çevrimiçi döküm)",
    "K2": "İnvertör parametre dökümü",
    "K3": "Router / VPN bağlantı logları",
    "K4": "HMI olay logları + uzak masaüstü aracı logları",
    "K5": "Pano, HMI ekranı ve parametre ekranlarının fotoğrafı",
    "K6": "Servis hesabının giriş kayıtları (üretici tarafı)",
}

# (dakika, kim, eylem, kategori, alınan kanıtlar, silinen kanıtlar)
AKIS = [
    (0, "Vardiya sorumlusu", "Bant başındaki operatöre haber: besleme ağzından uzak dur, hattı izle", "emniyet", [], []),
    (2, "Vardiya sorumlusu", "Bakım/otomasyon sorumlusu, İSG uzmanı ve BT/OT güvenlik sorumlusunu ara", "iletisim", [], []),
    (5, "Bakım sorumlusu", "Hattı normal stop ile kontrollü durdur; ana şalteri kilitle (LOTO). Reset yok", "emniyet", [], []),
    (8, "Bakım sorumlusu", "4G router'ın ağ kablosunu çek (kapatma, yeniden başlatma yok)", "erisim", [], []),
    (10, "Vardiya sorumlusu", "Pano, HMI ve parametre ekranlarını fotoğrafla", "kanit", ["K5"], []),
    (12, "Vardiya sorumlusu", "Üreticiyi (Efo) bilinen telefon numarasından ara; ele geçirilen kanal kullanılmaz", "iletisim", [], []),
    (30, "OT güvenlik", "PLC projesini ve CRC'yi salt okunur dök; referansla karşılaştır", "kanit", ["K1"], []),
    (40, "OT güvenlik", "İnvertör parametrelerini dök", "kanit", ["K2"], []),
    (50, "OT güvenlik", "Router loglarını ve HMI loglarını dışa aktar; özet değerlerini (hash) kaydet", "kanit", ["K3", "K4"], []),
    (60, "Üretici (Efo)", "Paylaşılan servis hesabını kapat; giriş kayıtlarını dışa aktar", "erisim", ["K6"], []),
    (75, "Bakım + İSG", "Emniyet değerlendirmesi: konfigürasyon farkı → durma mesafesi (6.1)", "emniyet", [], []),
    (90, "Vardiya sorumlusu", "Olay kaydını aç: zaman çizgisi, kanıt listesi, kim neye dokundu", "kanit", [], []),
    (180, "Üretici (Efo)", "Aktif istismar ya da ağır olay mı? CRA kapsamına giriyor mu? Etkilenen müşteriler", "bildirim", [], []),
    (1200, "Üretici (Efo)", "CRA erken uyarı (CSIRT + ENISA, tek bildirim platformu)", "bildirim", [], []),
    (1440, "Bakım + OT güvenlik", "Referans yedekten PLC ve invertörü geri yükle", "kurtarma", [], ["K1", "K2"]),
    (1500, "Bakım + İSG", "SF1–SF4 fonksiyon testi + durma süresi ölçümü; sonra reset ve start", "emniyet", [], []),
    (2880, "Üretici (Efo)", "Kök neden analizi: giriş yolu, değişen parametreler, etkilenen kurulumlar", "bildirim", [], []),
    (4000, "Üretici (Efo)", "CRA olay bildirimi: genel bilgi, olayın niteliği, alınan ve kullanıcıya önerilen önlemler", "bildirim", [], []),
    (10080, "Üretici + müşteri", "Kişisel hesaplar + MFA + varsayılan kapalı uzak erişim (LAB 4 hedefi)", "kurtarma", [], []),
    (18000, "Üretici (Efo)", "CRA son rapor: ayrıntılı açıklama, ciddiyet, kök neden, uygulanan ve süren önlemler", "bildirim", [], []),
]

# Föydeki en sık hata: önce reset, sonra her şey
AKIS_RESET = [
    (0, "Vardiya sorumlusu", "Router'ı ve HMI'yı yeniden başlat, PLC'yi yedekten yükle, hattı resetleyip çalıştır",
     "kurtarma", [], ["K1", "K2", "K3", "K4"]),
    (30, "Vardiya sorumlusu", "Bakım sorumlusunu ara", "iletisim", [], []),
    (60, "Bakım sorumlusu", "Logları ve parametreleri topla", "kanit", ["K1", "K2", "K3", "K4"], []),
    (120, "Üretici (Efo)", "Servis hesabını kapat", "erisim", ["K6"], []),
]

HESAP_KAPATMA = "Paylaşılan servis hesabını kapat"


def kanit_korunur(akis):
    """Kanıtı silen her eylemden önce o kanıt alınmış olmalı."""
    alinan = set()
    for _, _, _, _, al, sil in sorted(akis, key=lambda e: e[0]):
        if any(k not in alinan for k in sil):
            return False
        alinan |= set(al)
    return True


def emniyet_ilk(akis):
    """İlk eylem emniyet olmalı; ilk kurtarma eyleminden önce emniyet değerlendirmesi yapılmış olmalı."""
    sirali = sorted(akis, key=lambda e: e[0])
    if sirali[0][3] != "emniyet":
        return False
    kurtarma = [e[0] for e in sirali if e[3] == "kurtarma"]
    degerlendirme = [e[0] for e in sirali if e[3] == "emniyet" and "değerlendirme" in e[2].lower()]
    return not kurtarma or (bool(degerlendirme) and degerlendirme[0] < kurtarma[0])


def hesap_kapatma_dakikasi(akis):
    return next((e[0] for e in akis if HESAP_KAPATMA in e[2] or "Servis hesabını kapat" in e[2]), math.inf)


def yeniden_baslatma_testten_sonra(akis):
    """Start, emniyet fonksiyon testinden önce verilmemeli."""
    for t, _, eylem, _, _, _ in akis:
        if "start" in eylem.lower() or "çalıştır" in eylem.lower():
            if not any("fonksiyon testi" in e[2] and e[0] <= t for e in akis):
                return False
    return True


# ---------------------------------------------------------------- 6.3 CRA paketleri
# Bilgi alanı → hangi eylemden ya da kanıttan gelir (CRA md. 14; Y22)
CRA_PAKETLERI = {
    "erken_uyari": {
        "Kötü niyetli ya da hukuka aykırı eylem şüphesi": ["K6"],
        "Etkilenen ürün ve kurulum": ["K1"],
        "Ürünün bulunduğu üye devletler": ["Aktif istismar ya da ağır olay mı"],
    },
    "bildirim": {
        "Olayın genel niteliği": ["K1", "K2", "K3"],
        "İlk değerlendirme: ciddiyet ve etki": ["Emniyet değerlendirmesi"],
        "Alınan düzeltici / azaltıcı önlemler": [HESAP_KAPATMA, "4G router'ın ağ kablosunu çek"],
        "Kullanıcıların alabileceği önlemler": ["Kök neden analizi"],
    },
    "son_rapor": {
        "Ayrıntılı açıklama, ciddiyet ve etki": ["Kök neden analizi", "SF1–SF4 fonksiyon testi"],
        "Tehdit türü ya da kök neden": ["Kök neden analizi", "K3", "K4", "K6"],
        "Uygulanan ve süren önlemler": ["Kişisel hesaplar + MFA"],
    },
}
PAKET_ADI = {"erken_uyari": "24 sa — erken uyarı", "bildirim": "72 sa — olay bildirimi", "son_rapor": "14 gün — son rapor"}


def kaynak_tamam_dk(akis, kaynak):
    """Bir kanıt kimliği ya da eylem metni parçası akışta en erken ne zaman tamamlanıyor?
    Ömrü dolduktan sonra alınmaya çalışılan kanıt hiç alınmamış sayılır (6.5)."""
    if kaynak in kanit_kayiplari(akis):
        return math.inf
    for t, _, eylem, _, al, _ in sorted(akis, key=lambda e: e[0]):
        if kaynak in al or kaynak in eylem:
            return t
    return math.inf


def cra_hazirlik(akis=AKIS):
    """Her paket için: alan → (en geç tamamlanma dakikası, süre içinde mi)."""
    sonuc = {}
    for paket, alanlar in CRA_PAKETLERI.items():
        sinir = d("lab6.kilometre_taslari")[paket]
        sonuc[paket] = {}
        for alan, kaynaklar in alanlar.items():
            t = max(kaynak_tamam_dk(akis, k) for k in kaynaklar)
            sonuc[paket][alan] = (t, t <= sinir)
    return sonuc


# ---------------------------------------------------------------- 6.4 Etki alanı
OLAY_KURULUMU = "M1"
HESAP_DUZENLERI = {"mevcut": "Mevcut hesap düzeni (paylaşılan servis hesabı)",
                   "kisisel": "Kişisel hesap + MFA (LAB 4 hedefi)"}


def filo(duzen="mevcut"):
    kurulumlar = [dict(k) for k in d("lab6.kurulumlar")]
    if duzen == "kisisel":
        for k in kurulumlar:
            k["hesap"] = "kisisel"
    return kurulumlar


def etki_alani(duzen="mevcut"):
    """Olayda kullanılan kimlik bilgisiyle hangi kurulumlara ulaşılır? Ulaşılanda emniyet güvende mi?
    Ulaşmak için: uzak erişim sürekli açık olmalı ve kurulum ya olayın kendi tesisi olmalı ya da
    ele geçen hesap paylaşılan bir hesap olup o kurulumda da kullanılıyor olmalı."""
    kurulumlar = filo(duzen)
    olay = next(k for k in kurulumlar if k["id"] == OLAY_KURULUMU)
    sonuc = []
    for k in kurulumlar:
        ayni_hesap = k["id"] == OLAY_KURULUMU or (olay["hesap"] == "paylasilan" and k["hesap"] == "paylasilan")
        ulasilir = ayni_hesap and k["uzak"] == "surekli"
        riskte = ulasilir and not emniyet_degerlendirmesi(k["emniyet"])["guvende"]
        sonuc.append({"kurulum": k, "ulasilir": ulasilir, "emniyet_riskte": riskte})
    return sonuc


# ---------------------------------------------------------------- 6.5 Kanıt ömrü
def kanit_kayiplari(akis):
    """Ömrü dolmadan alınamayan kanıtlar (halka tampon, log döndürme)."""
    ilk = {}
    for t, _, _, _, al, _ in sorted(akis, key=lambda e: e[0]):
        for k in al:
            ilk.setdefault(k, t)
    return {k for k, omur in d("lab6.kanit_omru").items() if ilk.get(k, math.inf) > omur}


def gec_akis(akis=AKIS):
    """OT güvenlik ekibi ertesi sabah gelir: onun eylemleri gecikme kadar kayar."""
    g = d("lab6.gec_ekip_gecikmesi")
    return [(t + g if "OT güvenlik" in kim else t, kim, eylem, tur, al, sil) for t, kim, eylem, tur, al, sil in akis]


# ---------------------------------------------------------------- Çıktılar
def saat_metni(dk):
    if math.isinf(dk):
        return "yok"
    gun, kalan = divmod(int(dk), 1440)
    sa, mn = divmod(kalan, 60)
    return (f"+{gun} g " if gun else "+") + f"{sa:02d}:{mn:02d}"


def akis_md():
    kt = d("lab6.kilometre_taslari")
    asamalar = [(kt["ilk_mudahale"], "İlk 15 dk"), (kt["ilk_asama"], "İlk 2 saat"), (kt["erken_uyari"], "24 saate kadar"),
                (kt["bildirim"], "72 saate kadar"), (kt["son_rapor"], "14 güne kadar")]
    s = ["| Aşama | Zaman | Kim | Eylem | Tür | Kanıt |", "|---|---|---|---|---|---|"]
    for t, kim, eylem, tur, al, sil in AKIS:
        asama = next(ad for sinir, ad in asamalar if t <= sinir)
        kanit = ", ".join([f"alır {k}" for k in al] + [f"**siler {k}**" for k in sil]) or "—"
        s.append(f"| {asama} | {saat_metni(t)} | {kim} | {eylem} | {tur} | {kanit} |")
    s += ["", "Zaman 10:15'ten itibaren (+gün sa:dk). Kanıt kimlikleri:", ""]
    s += [f"- **{k}:** {v}" for k, v in KANITLAR.items()]
    return "\n".join(s) + "\n"


def _deger(x):
    return sayi(x, 1) if isinstance(x, float) else x


def emniyet_md():
    fark = konfig_farki()
    ref, ok = d("lab6.referans_konfig"), d("lab6.okunan_konfig")
    s = ["| Ayar | Referans | Okunan | Fark |", "|---|---|---|---|"]
    for k in ref:
        s.append(f"| `{k}` | {_deger(ref[k])} | {_deger(ok[k])} | {'**evet**' if k in fark else 'hayır'} |")
    s += ["", "| Emniyet mimarisi | Fark → LAB 4 saldırısı | Durma mesafesi | Emniyet güvende mi? |", "|---|---|---|---|"]
    for v, vad in lab4.VARYANTLAR.items():
        e = emniyet_degerlendirmesi(v, fark)
        for sa, r in e["sonuclar"].items():
            mesafe = "bant durmaz" if math.isinf(r["mesafe"]) else f"{sayi(r['mesafe'], 3)} m"
            s.append(f"| {vad} | {lab4.SALDIRI_ADI[sa]} | {mesafe} | {'Evet' if not r['ulasir'] else '**Hayır**'} |")
    s += ["", f"Güvenli mesafe {sayi(d('lab1.guvenli_mesafe'))} m. Mevcut (varsayım) mimari bağımlı varyanttır."]
    return "\n".join(s) + "\n"


def kontrol_md():
    satirlar = [("Kanıt, silinmeden önce alınıyor", kanit_korunur),
                ("İlk eylem emniyet; kurtarmadan önce emniyet değerlendirmesi", emniyet_ilk),
                ("Servis hesabı 2 saat içinde kapanıyor",
                 lambda a: hesap_kapatma_dakikasi(a) <= d("lab6.kilometre_taslari")["ilk_asama"]),
                ("Start, emniyet fonksiyon testinden sonra", yeniden_baslatma_testten_sonra)]
    s = ["| Kontrol | Bu akış | \"Resetleyip devam edelim\" |", "|---|---|---|"]
    for ad, f in satirlar:
        s.append(f"| {ad} | {'✔' if f(AKIS) else '✖'} | {'✔' if f(AKIS_RESET) else '**✖**'} |")
    return "\n".join(s) + "\n"


def etki_md():
    UZAK = {"surekli": "sürekli açık", "onayli": "tesis onaylı", "yok": "yok"}
    s = ["| Kurulum | Hesap | Uzak erişim | Emniyet mimarisi | " + " | ".join(
        f"{ad.split(' (')[0]}: ulaşılır / emniyet" for ad in HESAP_DUZENLERI.values()) + " |",
         "|---|---|---|---|---|---|"]
    sonuclar = {duz: {r["kurulum"]["id"]: r for r in etki_alani(duz)} for duz in HESAP_DUZENLERI}

    def hucre(r):
        if not r["ulasilir"]:
            return "ulaşılamaz"
        return "ulaşılır / " + ("**riskte**" if r["emniyet_riskte"] else "güvende")

    for k in filo():
        s.append(f"| {k['id']} · {k['ad']} | {k['hesap'].replace('paylasilan', 'paylaşılan').replace('kisisel', 'kişisel')} | "
                 f"{UZAK[k['uzak']]} | {lab4.VARYANTLAR[k['emniyet']]} | "
                 + " | ".join(hucre(sonuclar[duz][k['id']]) for duz in HESAP_DUZENLERI) + " |")
    ozet = []
    for duz, ad in HESAP_DUZENLERI.items():
        e = etki_alani(duz)
        ozet.append(f"- **{ad}:** {sum(r['ulasilir'] for r in e)} kurulum ulaşılır, "
                    f"{sum(r['emniyet_riskte'] for r in e)} kurulumda emniyet riskte.")
    s += ["", "Emniyet, olaydaki konfigürasyon farkının (6.1) o kurulumun mimarisinde acil stopu bozup bozmadığına "
              "göre değerlendirildi.", ""] + ozet
    return "\n".join(s) + "\n"


def kanit_omru_md():
    kt = d("lab6.kilometre_taslari")
    s = ["| Kanıt | Ömrü | Bu akışta alındığı an | Ekip geç gelirse alındığı an | Sonuç |", "|---|---|---|---|---|"]
    gec = gec_akis()
    kayip = kanit_kayiplari(gec)
    for k, omur in d("lab6.kanit_omru").items():
        s.append(f"| {k}: {KANITLAR[k]} | {saat_metni(omur)} | {saat_metni(kaynak_tamam_dk(AKIS, k))} | "
                 f"{saat_metni(min(e[0] for e in gec if k in e[4]))} | {'**kayboldu**' if k in kayip else 'korundu'} |")
    h, hg = cra_hazirlik(), cra_hazirlik(gec)
    eksik = [(paket, alan) for paket in CRA_PAKETLERI for alan in CRA_PAKETLERI[paket]
             if h[paket][alan][1] and not hg[paket][alan][1]]
    s += ["", f"Ekip geç gelirse OT güvenlik eylemleri {saat_metni(d('lab6.gec_ekip_gecikmesi'))} kayıyor. "
              "Kaybolan kanıt yüzünden süresinde hazırlanamayan CRA bilgileri:", ""]
    s += [f"- {PAKET_ADI[p]}: {a}" for p, a in eksik] or ["- yok"]
    s += ["", f"İlk 2 saat (≤ {saat_metni(kt['ilk_asama'])}) kanıtın hâlâ cihazda olduğu penceredir."]
    return "\n".join(s) + "\n"


def cra_md():
    h = cra_hazirlik()
    kt = d("lab6.kilometre_taslari")
    s = ["| Paket | Bilgi | Kaynağı | Hazır olduğu an | Süre içinde |", "|---|---|---|---|---|"]
    for paket, alanlar in CRA_PAKETLERI.items():
        for alan, kaynaklar in alanlar.items():
            t, ok = h[paket][alan]
            s.append(f"| {PAKET_ADI[paket]} (≤ {saat_metni(kt[paket])}) | {alan} | {', '.join(kaynaklar)} | "
                     f"{saat_metni(t)} | {'✔' if ok else '**✖**'} |")
    return "\n".join(s) + "\n"


def _grafik_zaman(yol):
    import matplotlib
    stil.mpl()
    import matplotlib.pyplot as plt

    turler = ["emniyet", "kanit", "erisim", "iletisim", "kurtarma", "bildirim"]
    adlar = {"emniyet": "Emniyet", "kanit": "Kanıt", "erisim": "Erişim", "iletisim": "İletişim",
             "kurtarma": "Kurtarma", "bildirim": "Bildirim"}
    renk = {"emniyet": stil.RENK["kritik"], "kanit": stil.RENK["bilgi"], "erisim": stil.RENK["giris"], "iletisim": stil.RENK["pasif"],
            "kurtarma": stil.RENK["iyi"], "bildirim": stil.RENK["vurgu"]}
    fig, ax = plt.subplots(figsize=(7.4, 3.4), dpi=200)
    for t, _, _, tur, _, sil in AKIS:
        y = turler.index(tur)
        ax.plot(max(t, 1), y, "o", ms=7 if not sil else 9, color=renk[tur],
                mec=stil.RENK["murekkep"] if sil else "white", mew=1.5)
    kt = d("lab6.kilometre_taslari")
    for anahtar, ad in (("ilk_mudahale", "15 dk"), ("ilk_asama", "2 sa"), ("erken_uyari", "24 sa"),
                        ("bildirim", "72 sa"), ("son_rapor", "14 gün")):
        ax.axvline(kt[anahtar], color=stil.RENK["murekkep"], lw=0.8, ls="--", alpha=0.6)
        ax.text(kt[anahtar], len(turler) - 0.35, ad, ha="center", fontsize=7.5, color=stil.RENK["murekkep"])
    ax.set_xscale("log")
    ax.set_xlim(0.8, kt["son_rapor"] * 1.6)
    ax.set_ylim(-0.6, len(turler) - 0.1)
    ax.set_yticks(range(len(turler)))
    ax.set_yticklabels([adlar[t] for t in turler], fontsize=8)
    ax.set_xticks([1, 10, 60, 600, 1440, 10080])
    ax.set_xticklabels(["+1 dk", "+10 dk", "+1 sa", "+10 sa", "+1 g", "+7 g"], fontsize=7.5)
    ax.set_title("Olay akışı (logaritmik zaman; koyu kenarlı nokta = kanıtı silen eylem)", fontsize=9.5, loc="left")
    ax.grid(axis="x", alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(yol)
    plt.close(fig)


def _grafik_etki_alani(yol):
    """Filo kutucukları: her hesap düzeninde hangi kurulum ulaşılır, hangisinde emniyet riskte."""
    plt = stil.mpl()
    from matplotlib.patches import FancyBboxPatch

    R, D = stil.RENK, stil.DOLGU
    UZAK = {"surekli": "sürekli açık", "onayli": "tesis onaylı", "yok": "erişim yok"}
    EMN = {"bagimli": "bağımlı", "bagimsiz": "bağımsız", "bagimsiz_hiz_izlemeli": "bağımsız + hız"}
    duzenler = list(HESAP_DUZENLERI.items())
    n = len(d("lab6.kurulumlar"))
    fig, ax = plt.subplots(figsize=(7.6, 3.1))
    ax.set_xlim(-2.2, n + 0.05)
    ax.set_ylim(len(duzenler) * 1.25 + 0.3, -0.55)
    ax.axis("off")
    for r, (duz, ad) in enumerate(duzenler):
        y = r * 1.25
        e = etki_alani(duz)
        ax.text(-2.15, y + 0.5, ad.replace(" (", "\n("), fontsize=7.2, fontweight="bold", color=R["ikincil"], va="center")
        ozet = f"{sum(x['ulasilir'] for x in e)} ulaşılır · {sum(x['emniyet_riskte'] for x in e)} emniyet riskte"
        ax.text(-2.15, y + 0.98, ozet, fontsize=6.3, color=R["ikincil"], va="center")
        for i, x in enumerate(e):
            k = x["kurulum"]
            ton = "kritik" if x["emniyet_riskte"] else ("uyari" if x["ulasilir"] else "iyi")
            ax.add_patch(FancyBboxPatch((i + 0.06, y), 0.88, 1.0, boxstyle="round,pad=0,rounding_size=0.08",
                                        fc=D[ton], ec=R[ton], lw=2.2 if k["id"] == OLAY_KURULUMU else 1.0))
            ax.text(i + 0.5, y + 0.2, k["id"], ha="center", va="center", fontsize=8.5, fontweight="bold",
                    color=R["murekkep"])
            hesap = "paylaşılan" if k["hesap"] == "paylasilan" else "kişisel"
            ax.text(i + 0.5, y + 0.62, f"{hesap}\n{UZAK[k['uzak']]}\n{EMN[k['emniyet']]}", ha="center", va="center",
                    fontsize=5.6, color=R["ikincil"], linespacing=1.35)
    for i, (ton, metin) in enumerate((("kritik", "ulaşılır, emniyet riskte"), ("uyari", "ulaşılır, emniyet güvende"),
                                      ("iyi", "ulaşılamaz"))):
        x0 = i * 1.95
        ax.add_patch(FancyBboxPatch((x0, -0.42), 0.22, 0.22, boxstyle="round,pad=0,rounding_size=0.04",
                                    fc=D[ton], ec=R[ton], lw=1))
        ax.text(x0 + 0.3, -0.31, metin, fontsize=6.6, va="center", color=R["murekkep"])
    ax.text(0.06, len(duzenler) * 1.25 + 0.12, f"Kutuda sırasıyla: hesap · uzak erişim · emniyet mimarisi (LAB 4). "
            f"Kalın çerçeve: olayın tesisi ({OLAY_KURULUMU}).", fontsize=6.2, va="center", color=R["ikincil"])
    ax.set_title("Ele geçen servis hesabının etki alanı: hesap düzenine göre", pad=6)
    fig.savefig(yol)
    plt.close(fig)


def main():
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "lab6_akis.md").write_text(akis_md(), encoding="utf-8")
    (OUT_DIR / "lab6_emniyet.md").write_text(emniyet_md(), encoding="utf-8")
    (OUT_DIR / "lab6_kontroller.md").write_text(kontrol_md(), encoding="utf-8")
    (OUT_DIR / "lab6_cra.md").write_text(cra_md(), encoding="utf-8")
    (OUT_DIR / "lab6_params.yaml").write_text(bolum_metni("lab6"), encoding="utf-8")
    _grafik_zaman(OUT_DIR / "lab6_zaman_cizelgesi.png")
    (OUT_DIR / "lab6_etki.md").write_text(etki_md(), encoding="utf-8")
    (OUT_DIR / "lab6_kanit_omru.md").write_text(kanit_omru_md(), encoding="utf-8")
    _grafik_etki_alani(OUT_DIR / "lab6_etki_alani.png")
    print(emniyet_md())
    print(kontrol_md())
    print(cra_md())


if __name__ == "__main__":
    main()
