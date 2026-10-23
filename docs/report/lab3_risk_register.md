---
bolum: "Laboratuvar 3 · Efo Makina · Besleme Bandı & Sarsak"
baslik: "Threat & Risk + Risk Matrix"
cikti: "Risk Register"
ep: "EP 04 Risk Assessment"
kavram: "Bir senaryo beş parçadan oluşur: **kim → hangi kapı → ne yapar → zincir → FİZİKSEL sonuç**. Skor = L × S × E (her biri 1–3). **Kural:** S=3 olan bir senaryo, skoru düşük kalsa bile öne alınır; insana verilen zarar görünür kalır. Bantlar: Kritik 18–27 · Yüksek 9–17 · Orta 4–8 · Düşük 1–3."
baglam: "**Kapılar (ipucu):** sürekli açık uzak destek bağlantısı (V5) · servis laptopu ve kilitsiz USB · PLC web arayüzü (CVE-2024-47100) · invertör WLAN modülü · bulut telemetri · içeriden birinin interlock'u köprülemesi. **Fiziksel sonuç adayları:** el ya da kolun yongalama makinesine çekilmesi, bakım sırasında beklenmedik çalışma, besleme ağzında yığılma ve sıkışma."
---

**Puanların yorumu** [VARSAYIM]: Föy L, S ve E'nin açılımını yazmıyor. Bu çalışmada **L = olasılık**, **S = şiddet**, **E = maruziyet** olarak alındı. S=3 ölüm ya da kalıcı uzuv kaybı, S=2 iyileşebilen ciddi yaralanma, S=1 fiziksel zararın olmaması anlamında kullanıldı.

## Risk Register

<!-- include-md: efo_sim/out/lab3_register.md -->

**Puanların dayanağı** (her puan bir kanıta ya da açık bir varsayıma bağlı):

<!-- include-md: efo_sim/out/lab3_dayanak.md -->

K1, föyün istediği üç senaryoya ek bir **kontrol senaryosudur**. Föyün altın kuralının nasıl uygulandığını gösterir. Telemetri hesabının ele geçirilmesi bir "veri çalındı" zinciridir. Bir adım daha ileri gidildiğinde de hattaki insana bir etkisi yok, çünkü telemetri yalnızca okuma yönünde. Bu yüzden K1 bir emniyet bulgusu sayılmadı (S=1).

![Risk ısı haritası](efo_sim/out/lab3_isi_haritasi.png)

Q1 | En yüksek öncelikli senaryonuz hangisi? Bir cümleyle: neden bu?

**S1.** Sürekli açık uzak destek bağlantısı (KOBİ'lerde yaygın bir pratik [R13]) üzerinden yapılan tek bir parametre değişikliği, acil stoptaki bandın besleme ağzına kadar kaymasına yol açar. Bu da en sık maruz kalınan noktada ölümcül bir çekilme demektir. Model bunu sayısal olarak gösteriyor: durma mesafesi 0,50 m'den 2,875 m'ye çıkıyor, güvenli mesafe ise 1,50 m (Kanıt kutusu).

Q2 | S=3 olup skoru düşük kalan senaryonuz var mı? Nasıl görünür kılacaksınız?

**Evet: S3.** Skoru 6 (Orta bandı); çünkü kullanıcı etkileşimi, ağ erişimi ve LOTO ihlalinin birlikte gerçekleşmesi gerekiyor (L=1) [Y12]. Ama sonucu, tambur yanındaki bakımcının kıstırılması ve bu ölümcül olabilir. Görünür kılmak için üç şey yapıldı:

1. **Öncelik kuralı:** Register sıralaması S=3 kuralını kodda uyguluyor. S3, K1 ile aynı skora (6) sahip olsa da öne alınıyor. Duyarlılık analizinde S3'ün skoru 3'e (Düşük) düşse bile hâlâ S=3 olmayan senaryoların önünde.
2. **Ayrı işaret:** Register'da S sütunu skordan ayrı gösteriliyor. Isı haritasında S3, S=3 satırında duruyor.
3. **Gereksinim olarak taşıma:** S3'ün fiziksel sonucunu önleyen önlem (bakımda enerjiyi kilitleme ve yeniden başlamayı önleme, SF4) LAB 4'te gereksinim olarak tanımlandı. Skor düşük diye kapsam dışı kalmıyor.

<div class="kural" markdown="1">
**Altın kural:** Zincir "veri çalındı" ile bitiyorsa bu bir emniyet bulgusu değildir; bir adım daha gidin: bu, hattaki insana ne yapar? S1–S3'ün hepsi bir fiziksel sonuçla bitiyor. K1 ise kuralın kontrol örneği olarak register'da tutuldu.
</div>

## 3.2 Duyarlılık analizi

Varsayıma dayalı (VARSAYIM ya da ÇIKARIM etiketli) her puan ±1 değiştirildi ve öncelik sırası yeniden hesaplandı. SEKTÖR-TİPİK etiketli şiddet puanları kaza verisine dayandığı için değiştirilmedi.

<!-- include-md: efo_sim/out/lab3_duyarlilik.md -->

**Sonuç:** Öncelik sırası büyük ölçüde sağlam. Tek kırılgan nokta **S1'in olasılık puanı**. Efo'nun uzak erişimi kalıcı değilse ya da korumalıysa (L=1), ilk öncelik S2'ye (servis laptopu) geçer. Bu bulgu Bölüm 05'teki varsayımlar tablosunda V5'in "yanlışsa ne değişir" sütununa taşındı.

## 3.3 Siberden fiziksele bağ

LAB 1.2'deki durma mesafesi modeli, saldırganın değiştirdiği invertör parametreleriyle yeniden çalıştırıldı. Rampa süresi 0,5 s'den 10 s'ye çıkarıldı; hız artışında maksimum frekans 1,6 katına çıkarıldı [Y17] [VARSAYIM]. Model, emniyetin invertöre bağımlı olduğu varyantı kullanıyor: STO rampa bittikten sonra geliyor.

<!-- include-md: efo_sim/out/lab3_siber_fiziksel.md -->

![Siberden fiziksele: elin bantla aldığı yol](efo_sim/out/lab3_siber_fiziksel.png)

- **Rampa uzatma:** Tek başına yeterli. El 3,0 s'de besleme ağzına varıyor, bant ise ancak 10,8 s'de duruyor.
- **Hız artışı:** Bu modelde nominal rampa korunduğunda tek başına sınırı aşmıyor. Ama rampa saldırısıyla birleşince durma mesafesi 7 m'ye çıkıyor.

Bu, LAB 3'teki S1'in fiziksel sonucunun sayısal kanıtıdır.

<div class="kanit" markdown="1">
**Kanıt: simülasyon (LAB 3)**

*Eğitim amaçlı modeldir; resmî bir risk değerlendirmesi ya da emniyet doğrulaması değildir. Puanlar ve parametreler `params.yaml`'dadır.*

**Ne gösterildi?**

- Skor, bant ve öncelik sırası koddan hesaplandı; S=3 kuralı sıralamada uygulandı.
- Duyarlılık analizi, varsayıma dayalı her puanın etkisini ölçtü.
- Siber bir parametre değişikliğinin fiziksel sonucu sayısal olarak gösterildi.

**Test sonuçları:**

<!-- include-md: efo_sim/out/lab3_testler.md -->

**Yorum:** Kodlanan kural ("S=3 her zaman önce") yapay bir uç örnekle de test edildi: skoru 18 olan S=2 senaryosu, skoru 3 olan S=3 senaryosunun arkasına düşüyor. Siber-fiziksel test, durma mesafesinin tek bir dijital parametreye ne kadar bağlı olduğunu gösteriyor. Bu bağ LAB 4'te bağımsızlık gereksinimiyle kesiliyor.
</div>

## Ek sorular: zafiyetler ve nasıl kapatılır

<div class="note" markdown="1">
Föy dışıdır; kullanıcı isteğiyle eklendi. Öneriler genel sektör pratiğidir; Efo'nun bunları uygulayıp uygulamadığı bilinmiyor.
</div>

QE1 | PLC hizmet dışı bırakılırsa (CVE-2020-28400, DCP seli) bant ne yapar?

- **Zafiyet:** Rapor bu durumu "interlock çalışmaz, mekanik patlama" olarak yorumluyordu. CPU STOP'a düştüğünde çıkışlar genelde sıfıra gider ve bant durur, yani doğrudan sonuç bir üretim kaybıdır [Y13] [ÇIKARIM]. Asıl risk, CPU yeniden RUN'a geçtiğinde bandın **kendiliğinden** çalışmasıdır.
- **Kapatma:** Yeniden başlamayı ayrı ve bilinçli bir start komutuna bağlamak (SF4). PROFINET ağını ayrı bir bölgeye almak (LAB 2, Z4). Firmware'i güncel tutmak [SEKTÖR-TİPİK].

QE2 | İçeriden biri kapak interlock'unu köprülerse ne olur?

- **Zafiyet:** Bu siber değil fiziksel bir manipülasyon, ama sonucu aynı: kapak açıkken tambur döner. Üretim baskısı altında kapak anahtarları sıkça köprülenir [R33] [ÇIKARIM].
- **Kapatma:** Manipülasyona dayanıklı (kodlu ya da RFID'li) kilit anahtarları kullanmak (ISO 14119). Köprülemeyi gerektiren ihtiyacı ortadan kaldırmak; örneğin sıkışma açmak için güvenli bir ayar modu ya da ters yön kumandası. Periyodik denetim yapmak [SEKTÖR-TİPİK].

QE3 | Hangi önlem hangi senaryonun hangi puanını düşürür?

| Önlem | S1 | S2 | S3 | Not |
|---|---|---|---|---|
| Uzak erişim varsayılan kapalı + MFA + jump server (LAB 2, C1) | L ↓ | — | L ↓ | Girişi zorlaştırır |
| Emniyetle ilgili invertör parametrelerini kilitlemek + değişiklik kaydı | L ↓ | — | — | Kapıyı daraltır |
| SS1-t / STO'yu emniyet rölesine bağlamak (LAB 4.2) | Fiziksel zincir kopar | — | — | S=3 kalır ama zincir tamamlanamaz |
| Yongalama interlock'unu emniyet zincirine almak + servis laptopu politikası | — | L ↓ | — | SF3 PLC'ye bağımlı olmaz |
| LOTO + reset ≠ start (SF4) | — | E ↓ | Zincir kopar | Bakımcı korunur |

Şiddet (S) hiçbir önlemle düşmüyor: çekilme her zaman ölümcül. Önlemler ya olasılığı ve maruziyeti düşürüyor ya da zinciri fiziksel sonuca ulaşmadan kesiyor. LAB 4'ün bağımsızlık gereksinimi bu ikinci yoldur.

## Ek — Kod

<!-- include-code: efo_sim/lab3_risk.py -->

<!-- include-code: efo_sim/tests/test_lab3_risk.py -->

**`params.yaml` — LAB 3 bölümü:**

<!-- include-code: efo_sim/out/lab3_params.yaml -->

**pytest çıktısı:**

<!-- include-text: efo_sim/out/pytest_lab3.txt -->
