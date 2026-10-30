---
bolum: "Laboratuvar 6 · Efo Makina · Besleme Bandı & Sarsak"
baslik: "CRA Incident Simulation"
cikti: "Incident Workflow"
ep: "EP 13 Incident Response"
kavram: "Bir olayda en değerli iki şey **zaman** ve **kanıttır**. CRA'nın 24 sa / 72 sa / 14 gün yükümlülükleri, iyi bir müdahale akışının doğal kilometre taşlarıdır; ezber değil."
baglam: "**Senaryo (Efo uyarlaması, V19):** Saat 10:15. Üreticinin paylaşılan servis hesabıyla, sürekli açık 4G router üzerinden gece 03:00'te tanınmayan bir konumdan giriş yapıldığı görüldü. PLC konfigürasyonu değişmiş olabilir; acil stopun durma mesafesi henüz doğrulanmadı. Makine çalışıyor. Vardiya sorumlusu sizsiniz. Senaryo, PaketPro sürümündeki olayın (gece girişi, doğrulanmamış ışık perdesi parametreleri) Efo'ya aktarılmış hâlidir; mevcut mimari LAB 4'teki varsayımdır (V5)."
---

**Kim bildirir?** CRA'nın bildirim yükümlülüğü **üreticiye** aittir: Efo, dijital eleman içeren makineyi AB pazarına arz ettiyse Efo; açık PLC'nin kendisindeyse PLC üreticisi [Y22] [ÇIKARIM]. Vardiya sorumlusu bildirimi yapmaz. Ama bildirimin dayanacağı her bilgi onun ilk iki saatte koruduğu kanıttan gelir. CRA süresi, üreticinin olayı **öğrendiği andan** başlar. Bu akışta Efo +00:12'de aranıyor; çizelge yine de 10:15'ten sayıldı, yani ihtiyatlı.

## Görev — zaman çizgisini doldurun

![Olay akışı](efo_sim/out/lab6_zaman_cizelgesi.png)

Q1 | 10:15 — ilk 15 dk: Kimi ararsınız? İlk üç eyleminiz?

**Kimi ararım:**

1. Bakım / otomasyon sorumlusu: hattı durdurup kilitleyecek ve konfigürasyonu okuyacak kişi.
2. İSG uzmanı: emniyet kararı onun onayı olmadan kapanmaz.
3. BT/OT güvenlik sorumlusu (ya da dış destek): kanıt toplama.
4. Üretici (Efo): servis hesabı onların. **Bilinen telefon numarasından** aranır; ele geçirilen kanal (uzak bağlantı, o hesaba bağlı e-posta) kullanılmaz.

Ciddi bir olayda ulusal başvuru noktası USOM'dur [Y30] [SEKTÖR-TİPİK].

**İlk üç eylem:**

1. **Önce emniyet:** Bant başındaki operatör besleme ağzından uzaklaştırılır. Hat **normal stop ile kontrollü durdurulur** ve ana şalter kilitlenir (LOTO). **Reset yok.** Neden durduruyoruz: mevcut mimaride acil stop PLC'den ve invertör rampasından geçiyor (LAB 4). PLC değiştiyse acil stopa güvenilemez. Q2'deki doğrulama bu kararın doğru olduğunu gösteriyor.
2. **Erişimi kes, kanıtı silme:** 4G router'ın ağ kablosu çekilir. Router **kapatılmaz ve yeniden başlatılmaz**, çünkü bağlantı logları geçici bellekte olabilir (QE1).
3. **Gördüğünü kaydet:** Pano, HMI ekranı ve parametre ekranları fotoğraflanır. Kimin neye, ne zaman dokunduğu not edilir.

Q2 | İlk 2 saat: Emniyet güvende mi — nasıl doğrularsınız? Hangi kanıt korunur? Hangi hesap kapatılır?

**Nasıl doğrularız:** PLC projesi ve invertör parametreleri **salt okunur** olarak dökülür. Devreye almadaki onaylı referansla karşılaştırılır (CRC ve parametre listesi). Bulunan her fark, LAB 4'teki bağımsızlık modelinde bir saldırıya çevrilir. Sonra acil stopun bandı yine güvenli mesafede durdurup durdurmadığına bakılır.

<!-- include-md: efo_sim/out/lab6_emniyet.md -->

**Sonuç: mevcut mimaride emniyet güvende değil.** PLC projesi değişmiş ve rampa 10 s'ye çıkmış. Acil stop basıldığında bant ya hiç durmuyor ya da 2,875 m kayıyor. Q1'deki "önce durdur" kararı bu yüzden doğru. Bağımsız emniyet mimarisinde aynı farklar SF1'i bozmuyor (0,931 m). Orada hat yine de durdurulur, ama bunun nedeni üretim konfigürasyonunun bütünlüğüdür, insanın korunması değil.

**Korunan kanıt** (her birinin özet değeri / hash kaydedilir):

| Kimlik | Kanıt | Neden önemli |
|---|---|---|
| K1 | PLC projesi + CRC | Neyin değiştiğinin ana kanıtı; geri yükleme bunu siler |
| K2 | İnvertör parametre dökümü | Rampa / hız değişikliği; fabrika ayarına dönüş bunu siler |
| K3 | Router / VPN bağlantı logları | Giriş saati, kaynak IP; yeniden başlatma bunu silebilir |
| K4 | HMI olay logları + uzak masaüstü logları | Saldırganın hatta ne yaptığı |
| K5 | Fotoğraflar | Ekranların ilk hâli |
| K6 | Servis hesabının giriş kayıtları (üretici tarafı) | Hesabın nereden, ne zaman kullanıldığı |

**Kapatılan hesaplar:** Paylaşılan servis hesabı (Efo tarafında, +01:00). Aynı parolayı paylaşan diğer hesaplar: router yönetimi, HMI ve uzak masaüstü aracı. Kalıcı çözüm kişisel hesap + MFA'dır (LAB 4). Paylaşılan hesap, "kim girdi?" sorusunu cevapsız bırakır.

Q3 | 24 saat — CRA erken uyarı: Hangi bilgi hazır olmalı?

CRA md. 14(4)(a) uyarınca, ürünün güvenliğini etkileyen ağır bir olayda erken uyarı en az şunları içerir [Y22]:

- Olayın hukuka aykırı ya da kötü niyetli bir eylemden kaynaklandığı şüphesi (K6: tanınmayan konumdan gece girişi).
- Etkilenen ürün ve kurulum (K1).
- Ürünün bulunduğu üye devletler; Efo'nun diğer müşterileri de aynı hesabı kullanıyor mu? (+03:00 değerlendirmesi).

Bildirim, üreticinin koordinatör CSIRT'üne ve ENISA'ya tek bildirim platformu üzerinden yapılır [Y22].

Q4 | 72 saat — CRA bildirim: Kök neden, etki, önlem — kim ne yapıyor?

Olay bildirimi; olayın genel niteliğini, ilk değerlendirmeyi, alınan düzeltici önlemleri ve kullanıcıların alabileceği önlemleri içerir [Y22].

| Kim | Ne yapıyor | Bildirimdeki karşılığı |
|---|---|---|
| Üretici (Efo) | Kök neden: giriş yolu, değişen parametreler, aynı hesabın kullanıldığı diğer kurulumlar. Bildirimi gönderir; etkilenen kullanıcıları bilgilendirir [Y22]. | Niteliği, kullanıcı önlemleri |
| OT güvenlik | K1–K4 analizi; zaman çizgisi | Olayın genel niteliği |
| Bakım + İSG | Emniyet değerlendirmesi; referanstan geri yükleme; SF1–SF4 testi + durma süresi ölçümü; sonra reset ve start | İlk değerlendirme: ciddiyet ve etki |
| Müşteri yönetimi | Üretim kaybı, iletişim, sigorta | — |

**Geri yükleme kanıt alındıktan sonra yapılır** (+1 gün). Start, emniyet fonksiyon testinden sonra verilir.

Q5 | 14 gün — son rapor: Hangi loglar/kayıtlar korunmuş olmalı?

- K1–K6 ve her birinin hash'i.
- Zaman çizgisi (kim, neye, ne zaman dokundu) ve kanıtın el değiştirme kaydı.
- Referans konfigürasyon, olay anı dökümü ve geri yükleme sonrası yeni CRC.
- SF1–SF4 fonksiyon testi ve durma süresi ölçüm raporu.
- Uygulanan ve süren önlemler: kişisel hesaplar, MFA, varsayılan kapalı uzak erişim.

**Süre notu:** Föy 14 gün diyor. CRA'da 14 gün, **aktif olarak istismar edilen bir zafiyet** için düzeltici önlemin hazır olmasından sonraki süredir. **Ağır olayda** son rapor, olay bildiriminden sonra **bir ay** içinde verilir [Y22] [SEKTÖR-TİPİK]. Bu akış iki süreyi de karşılıyor (son rapor +12,5 gün).

<div class="kural" markdown="1">
**En sık hata:** "Resetleyip devam edelim." O düğme kanıtı sonsuza dek siler. Önce emniyet, hemen sonra kanıt. Model bunu bir karşı örnekle test ediyor: reset akışında kanıt kontrolü, emniyet sırası, start koşulu ve CRA paketleri kalıyor.
</div>

<div class="kanit" markdown="1">
**Kanıt: simülasyon (LAB 6)**

*Eğitim amaçlı modeldir; gerçek bir olay müdahale planı ya da hukuki görüş değildir. Senaryo ve konfigürasyon değerleri varsayımdır.*

**6.2 Akış.** Her eylemin zamanı, sorumlusu, türü ve aldığı ya da sildiği kanıt:

<!-- include-md: efo_sim/out/lab6_akis.md -->

**Kontroller:** Bu akış ile "resetleyip devam edelim" akışı aynı kontrollerden geçirildi.

<!-- include-md: efo_sim/out/lab6_kontroller.md -->

**6.3 CRA paketleri.** Her bilgi, süresinden önce tamamlanan bir eylemden ya da kanıttan geliyor mu?

<!-- include-md: efo_sim/out/lab6_cra.md -->

**Test sonuçları:**

<!-- include-md: efo_sim/out/lab6_testler.md -->

**Yorum:** Emniyet doğrulaması, LAB 1 ve LAB 4'teki durma mesafesi modelini olay anında kullanıyor. Bu yüzden "emniyet güvende mi?" sorusu bir tahmin değil, ölçülebilir bir karşılaştırma. Hazırlıksız bir hatta bu mümkün değil: onaylı bir referans konfigürasyon ve CRC yoksa karşılaştıracak bir şey de yoktur (QE2).
</div>

## Ek sorular: zafiyetler ve nasıl kapatılır

<div class="note" markdown="1">
Föy dışıdır; kullanıcı isteğiyle eklendi. Öneriler genel sektör pratiğidir; Efo'nun bunları uygulayıp uygulamadığı bilinmiyor.
</div>

QE1 | Router'ı kapatmak yerine neden kablosunu çekiyoruz?

- **Zafiyet:** Birçok küçük router ve VPN cihazı bağlantı loglarını geçici bellekte tutar. Kapatmak ya da yeniden başlatmak giriş saatini ve kaynak IP'yi siler [ÇIKARIM].
- **Kapatma:** Olay anında bağlantıyı fiziksel olarak kesip cihazı açık bırakmak. Kalıcı çözüm, logları cihazdan ayrı ve değiştirilemez bir yerde tutmaktır (LAB 4 QE1) [Y26, Y31] [SEKTÖR-TİPİK].

QE2 | Olaydan önce neyin hazır olması gerekirdi?

- **Zafiyet:** Referans konfigürasyon yoksa "PLC değişti mi?" sorusunun cevabı yoktur. İletişim listesi yoksa ilk 15 dakika telefon numarası aramakla geçer.
- **Kapatma** [Y31] [SEKTÖR-TİPİK]:
    - Devreye almada PLC, emniyet rölesi ve invertör için onaylı yedek ve CRC; makineden ayrı saklanır.
    - Rolleriyle birlikte bir iletişim listesi ve üreticinin doğrulanmış numarası.
    - Bu föydeki akışın bir sayfalık kartı panonun kapağında.
    - Yılda bir tatbikat.

QE3 | Bağımsız emniyet olay müdahalesini nasıl değiştirir?

- **Bulgu:** Bağımlı mimaride emniyet doğrulanana kadar hat durmak zorunda. Bağımsız mimaride SF1 aynı farklarla güvenli kalıyor (6.1); karar insanın korunmasından çok üretim bütünlüğüne dayanıyor [ÇIKARIM].
- **Sonuç:** Emniyetin bağımsızlığı, olayın etkisini bir emniyet olayından bir kullanılabilirlik olayına indiriyor. LAB 5'teki yama kararında da aynı etki görüldü.

## Ek — Kod

<!-- include-code: efo_sim/lab6_incident.py -->

<!-- include-code: efo_sim/tests/test_lab6_incident.py -->

**`params.yaml` — LAB 6 bölümü:**

<!-- include-code: efo_sim/out/lab6_params.yaml -->

**pytest çıktısı:**

<!-- include-text: efo_sim/out/pytest_lab6.txt -->
