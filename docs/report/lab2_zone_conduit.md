---
bolum: "Laboratuvar 2 · Efo Makina · Besleme Bandı & Sarsak"
baslik: "IEC 62443 Mini Workshop"
cikti: "Zone / Conduit Diagram"
ep: "EP 05 Zone & Conduit"
kavram: "**Zone**, benzer kritiklikteki cihazların toplandığı bölgedir. **Conduit**, bölgeler arasındaki her geçişe konan kontrollü bir kapıdır. Amaç 62443'ün maddelerini ezberlemek değil, mantığını uygulamaktır."
baglam: "Efo'nun ağ ve uzak erişim yapısı kamuya açık değil (V3, V5). Bu yüzden iki mimari kuruldu: tipik KOBİ pratiğine göre bir **mevcut durum varsayımı** ve föyün ilkeleriyle yeniden gruplanmış bir **hedef**. İkisi de `lab2_zones.py` içinde veri olarak tanımlı; diyagramlar ve kural kontrolü bu veriden üretildi."
---

## Görev A — Varlıkları bölgelere ayırın

Genel Sürüm'deki varlık listesi Efo'nun ünitesine çevrildi. Robot kontrolörünün bu ünitede karşılığı yok; onun yerini invertörler ve yongalama makinesinin kontrolörü alıyor. Her varlık için Efo'daki durum *var / yok / bilinmiyor* olarak işaretlendi:

<!-- include-md: efo_sim/out/lab2_varliklar.md -->

Motor-redüktörler Efo renderlarında görünüyor [Y2], ama ağa bağlı olmadıkları için bölge tablosuna alınmadı.

**PaketPro'daki zayıf noktaların Efo'daki olası karşılıkları.** Bunların hiçbiri Efo'da tespit edilmedi; satırlar, tipik bileşenlerde nereye bakılması gerektiğini gösteriyor:

| PaketPro | Efo'da olası karşılığı | Durum | Dayanak |
|---|---|---|---|
| "admin/admin" servis hesabı | Paylaşılan servis hesabı; PLC/HMI'da değiştirilmemiş varsayılan parola | Bilinmiyor; parola prosedürü yayınlanmamış | Rapor Bölüm E [VARSAYIM] |
| Port 80'de açık HMI | PLC'nin dahili web sunucusu (S7-1200 < V4.7'de CSRF) | Bilinmiyor | [Y12] [SEKTÖR-TİPİK] |
| Parolası kartonda yazan Wi-Fi | İnvertör WLAN modülü (çalışma sırasında telefondan parametre); router Wi-Fi'ı | Bilinmiyor | [Y17] [SEKTÖR-TİPİK] |
| İki kilitsiz USB | HMI ve servis laptopundaki USB portları | Bilinmiyor | [VARSAYIM] |
| İnternete açık uzak bakım modülü | Kurulumdan sonra sürekli açık bırakılan 4G/VPN router ya da uzak masaüstü aracı | Bilinmiyor | [R13] [SEKTÖR-TİPİK] (V5) |

### Mevcut durum (varsayım)

<!-- include-mermaid: efo_sim/out/lab2_mevcut.mmd | Şekil 1 — Mevcut durum varsayımı: düz ağ. Kırmızı kenarlar kontrolsüz geçişleri gösteriyor. Efo'ya ait bir tespit değildir; tipik KOBİ kurulumundan kuruldu (V3, V5). -->

### Hedef — Zone / Conduit Diagram

<!-- include-mermaid: efo_sim/out/lab2_hedef.mmd | Şekil 2 — Hedef zone/conduit diyagramı. Her bölgeler arası geçiş bir conduit'ten geçiyor; emniyet bölgesine (Z5) giren kenar yok. Diyagram lab2_zones.py verisinden üretildi. -->

Q1 | Hangi varlıklar aynı bölgede? Bölgeleri adlandırıp gruplandırın.

<!-- include-md: efo_sim/out/lab2_bolgeler.md -->

Gruplama ölçütü kritikliktir [R12, R57] [SEKTÖR-TİPİK]:

- **Z4 (hat kumanda):** Bantı ve sarsağı doğrudan hareket ettiren her şey burada. Bu bölge ele geçirilirse makine istenmeyen şekilde hareket edebilir.
- **Z3 (SCADA/MES):** Müşterinin denetim sistemi Z4'ten ayrı tutuldu. Tesis genelindeki bir sorunun hatta doğrudan inmemesi için.
- **Z2 (DMZ):** Dışarıdan ve ofisten gelen her şey önce burada durur. DMZ'den ötesine doğrudan geçilemez.
- **ZT (geçici bakım cihazları):** Servis laptopu ve USB her bağlanışta yeni bir kapı açar. Bu yüzden kalıcı bir bölgeye konmadı.

Q2 | Safety PLC'yi (ya da emniyet rölesini) hangi bölgeye koydunuz, neden?

Emniyet rölesi ya da Safety PLC, acil stop, çekme ipi ve kapak anahtarlarıyla birlikte **kendi bölgesine (Z5)** kondu. Nedenleri:

1. **En yüksek kritiklik:** SF1 için PLr = e (LAB 1). Z4'teki bir arıza ya da saldırı bu bölgeyi etkilememelidir.
2. **Ağa ihtiyacı yok:** Emniyet fonksiyonunun çalışması için hiçbir ağ bağlantısı gerekmez. Bu yüzden Z5'e giren bir akış yok (kural K4).
3. **Tek yönlü iletişim:** Z5'ten çıkan tek akış, PLC'ye giden kablolu bir durum sinyalidir (C8). Reset butonu da emniyet devresine kablolu bağlıdır, PLC üzerinden geçmez.

Safety PLC ileride PROFIsafe gibi bir ağ protokolü kullanırsa, aynı fiziksel ağı paylaşsa bile Z5 mantıksal olarak ayrı kalmalı ve emniyet programına yalnızca yetkili mühendislik erişimi açılmalıdır [R51, R58] [SEKTÖR-TİPİK].

QP2 | (PaketPro uyarlaması) Uzak destek router'ı hangi bölgeye düşüyor; orada kalabilir mi?

- **Mevcut durumda (varsayım):** Router, PLC ve HMI ile aynı düz ağda (ZD), sürekli açık ve paylaşılan parolayla çalışıyor [R13] (V5). **Orada kalamaz.** Router, internetten hat kumandasına kontrolsüz bir kapı açıyor (kurallar K3 ve K5 ihlal ediliyor).
- **Hedefte:** Uzak bağlantı DMZ'de (Z2) sonlanır. Oturum jump server üzerinden kişisel hesap ve MFA ile açılır. Bağlantı varsayılan olarak kapalıdır ve tesis onayıyla açılır (C1). Z2'den Z4'e yalnızca izin listesindeki mühendislik portları geçer (C3) [Y15] [SEKTÖR-TİPİK].

Q3 | Bölgeler arası geçişler (conduit) nerede? Her geçişte ne kontrol edilecek?

<!-- include-md: efo_sim/out/lab2_conduitler.md -->

En kritik iki conduit şunlardır:

- **C1 (dış → DMZ):** Saldırganın ilk kapısı. Burada beş kontrolün hepsi gerekir (Görev B).
- **C3 (DMZ → hat kumanda):** Bant invertörüne kadar uzanır. Burada **emniyetle ilgili invertör parametreleri** (rampa, maksimum frekans, STO ayarları) ayrıca kilitlenmelidir. LAB 3'te bu parametrelerin değişmesinin elin besleme ağzına ulaşmasına yol açtığı gösteriliyor.

## Görev B — Uzak erişim kararı

| Karar | Seçenekler | Seçim ve nedeni |
|---|---|---|
| Aracı? | Doğrudan / Jump server | **Jump server.** Teknisyen PLC'ye IP düzeyinde doğrudan bağlanmaz; oturum DMZ'deki bir aracı makinede açılır. Kopyala-yapıştır ve sürücü yönlendirme kapalıdır [Y15, R14] [SEKTÖR-TİPİK]. |
| Tünel? | Açık / VPN | **VPN**, ama yalnızca DMZ'ye kadar. Tünelin ucu hat ağında değil, Z2'de [R57] [SEKTÖR-TİPİK]. |
| Kimlik? | Parola / MFA | **MFA.** ACSC rehberi her atlama için ayrı MFA öneriyor [Y15] [SEKTÖR-TİPİK]. |
| Hesap? | Paylaşılan / Kişisel | **Kişisel.** Paylaşılan hesapta oturumu kimin açtığı bilinemez. Bu, hem olay incelemesini hem de CRA'nın 24 saatlik bildirim yükümlülüğünü zorlaştırır [Y15, Y20]. |
| Kayıt? | Yok / Tam oturum kaydı | **Tam oturum kaydı.** 2023/1230 Ek III 1.1.9, yazılım ya da konfigürasyona yapılan yasal ya da yasa dışı müdahalenin kanıtının toplanmasını istiyor [Y16] [SEKTÖR-TİPİK]. |
| Zamanlama? | Sürekli açık / Varsayılan kapalı | **Varsayılan kapalı.** Bağlantı, tesis sorumlusunun onayıyla bakım penceresi boyunca açılır ve sonra kapanır. KOBİ'lerdeki en riskli pratik, sürekli açık tünellerdir [R13] [SEKTÖR-TİPİK]. |

<div class="kanit" markdown="1">
**Kanıt: simülasyon (LAB 2)**

*Eğitim amaçlı modeldir; emniyet doğrulaması ya da IEC 62443 uygunluk değerlendirmesi değildir.*

**Ne gösterildi?** Varlıklar, bölge atamaları, akışlar ve conduit kontrolleri veri olarak tanımlandı. Beş kural bu veri üzerinde kontrol edildi. Diyagramlar aynı veriden üretildiği için veriyle hep tutarlı.

<!-- include-md: efo_sim/out/lab2_kurallar.md -->

**Test sonuçları:**

<!-- include-md: efo_sim/out/lab2_testler.md -->

**Yorum:** Hedef mimari beş kuralın hepsine uyuyor. Mevcut durum varsayımında kurallar 11 ihlal yakalıyor. Bunlar PaketPro'daki zayıf noktaların Efo'daki olası karşılıklarıyla aynı yerlerde. K1 mevcut durumda da ihlal edilmiyor: dışarıdan emniyet bölgesine *doğrudan* kenar yok. Ama emniyet PLC'ye bağlı olduğu için dolaylı yol açık (K4 ihlali). Dolaylı yollar LAB 4'teki saldırı grafında sayılıyor.
</div>

## Ek sorular: zafiyetler ve nasıl kapatılır

<div class="note" markdown="1">
Föy dışıdır; kullanıcı isteğiyle eklendi. Öneriler genel sektör pratiğidir; Efo'nun bunları uygulayıp uygulamadığı bilinmiyor.
</div>

QE1 | Düz ağın asıl zafiyeti nedir?

- **Zafiyet:** Ofisteki bir bilgisayara bulaşan fidye yazılımı, aynı ağdaki PLC ve HMI'a doğrudan ulaşır. Raporda bu, tedarik zinciri saldırısının "filtresiz otobanı" olarak tarif ediliyor (Bölüm E.3) [ÇIKARIM].
- **Kapatma:** Hattı ayrı bir bölgeye almak ve fabrika ağıyla arasına, yalnızca gereken portlara izin veren bir güvenlik duvarı koymak (Z4 ve C3–C5). Bu, raporun Bölüm F'deki önerisiyle de örtüşüyor [R57, R58] [SEKTÖR-TİPİK].

QE2 | İnvertörün WLAN modülü bir conduit midir?

- **Zafiyet:** Evet, ama kontrolsüz bir conduit. WLAN menzilindeki herhangi bir telefon, çalışma sırasında invertör parametrelerini değiştirebilir [Y17]. Mevcut diyagramda bu, kontrolsüz kırmızı kenar olarak görünüyor.
- **Kapatma:** Modülü devreye almadan sonra sökmek ya da kapatmak. Kalması gerekiyorsa güçlü ve cihaza özel bir parola kullanmak, emniyetle ilgili parametreleri ayrıca kilitlemek ve değişiklikleri kaydetmek [SEKTÖR-TİPİK].

QE3 | Servis laptopu neden ayrı bir bölgede?

- **Zafiyet:** Laptop başka müşterilerin ağlarında da dolaşır. Bir tesisteki zararlı yazılımı başka bir tesise taşıyabilir [ÇIKARIM].
- **Kapatma:** Yalnızca bu iş için kullanılan, güncel ve taranmış bir servis laptopu. Pano içindeki mühendislik portuna fiziksel kilit. USB için izin listesi. Her yerel bağlantıyı kişisel hesapla ve kayıtla yapmak (C7) [Y15] [SEKTÖR-TİPİK].

## Ek — Kod

<!-- include-code: efo_sim/lab2_zones.py -->

<!-- include-code: efo_sim/tests/test_lab2_zones.py -->

**`params.yaml` — LAB 2 bölümü:**

<!-- include-code: efo_sim/out/lab2_params.yaml -->

**Koddan üretilen Mermaid kaynağı (hedef):**

<!-- include-code: efo_sim/out/lab2_hedef.mmd -->

**pytest çıktısı:**

<!-- include-text: efo_sim/out/pytest_lab2.txt -->
