# safety40-efo-konveyor | Yağız Enes DOĞAN - 230542022 - GÜNDÜZ B

**Efo Makina — Besleme Bandı & Sarsak (Titreşimli Konveyör): Safety 4.0 Föy Analizi (LAB 1–7) + SWOT**

Yağız Enes Doğan · Gündüz - B · Safety 4.0 Bootcamp ders ödevi

> **Uyarı.** Bu, bağımsız bir akademik çalışmadır; Efo Makina ile hiçbir bağlantısı yoktur. Firmayla iletişim kurulmadı; bütün bilgiler kamuya açık kaynaklardan derlendi. Analizin birçok kısmı varsayıma dayanır ve **gerçek ürünün emniyet durumu hakkında bir iddia değildir**. Bu bir eğitim çıktısıdır; resmî denetim, risk değerlendirmesi ya da CE uygunluk değerlendirmesi değildir. Simülasyonlar basitleştirilmiş eğitim modelleridir; SISTEMA ya da ISO 13849-2 validasyonunun yerine geçmez.

## Ne var?

| Çıktı | Dosya | Evidence Pack |
|---|---|---|
| Rapor doğrulama + Makine Profili | `pdf/00_Makine_Profili.pdf` | — |
| LAB 1 · Safety Architecture → Safety Function Map | `pdf/LAB1_Safety_Architecture.pdf` | EP 03 |
| LAB 2 · IEC 62443 Mini Workshop → Zone / Conduit Diagram | `pdf/LAB2_IEC62443_Zone_Conduit.pdf` | EP 05 |
| LAB 3 · Threat & Risk + Risk Matrix → Risk Register | `pdf/LAB3_Threat_Risk_Register.pdf` | EP 04 |
| LAB 4 · Secure Remote Access → Secure Architecture | `pdf/LAB4_Secure_Remote_Access.pdf` | EP 02 + EP 06 |
| LAB 5 · SBOM / CVE / Patch → Vulnerability Decision | `pdf/LAB5_SBOM_CVE_Patch.pdf` | EP 09 · 10 · 11 |
| LAB 6 · CRA Incident Simulation → Incident Workflow | `pdf/LAB6_CRA_Incident.pdf` | EP 13 |
| LAB 7 · AI Safety Challenge → AI Fail-Safe Decision | `pdf/LAB7_AI_Safety.pdf` | EP 03 + EP 15 |
| SWOT + Varsayımlar ve sınırlılıklar | `pdf/05_SWOT_ve_Varsayimlar.pdf` | — |
| Hepsi tek dosyada, içindekiler sayfasıyla | `pdf/Efo_Safety40_Tam_Rapor.pdf` | — |

## Yöntem

1. **Kaynak doğrulama.** Daha önce hazırlanmış bağımsız bir derin araştırma raporu (`docs/research/`) ana kanıt kaynağı olarak alındı. Kritik iddiaları (S=3 gerekçeleri, PLr/SIL, CVE'ler, mevzuat tarihleri, Efo'ya ait görsel tespitler) linklerinden tek tek kontrol edildi. 16 düzeltme ve eklenen 21 kaynak `00_Makine_Profili.pdf`'te listeleniyor.
2. **Etiketleme.** Her bilgi dört etiketten birini taşır:

   | Etiket | Anlamı |
   |---|---|
   | `[EFO-DOĞRULANMIŞ]` | Efo'nun kendi kaynağı ya da AİMSAD/TWM |
   | `[SEKTÖR-TİPİK]` | Benzer makineler, standartlar, rehberler |
   | `[ÇIKARIM]` | Kaynağa dayalı yorum |
   | `[VARSAYIM]` | Kaynak yok; tipik kurulum üzerinden kabul |

   Varsayımlar V1–V23 kimlikleriyle `05_SWOT_ve_Varsayimlar.pdf`'te toplanıyor: her biri için hangi lab'da kullanıldığı ve yanlışsa sonucun nasıl değişeceği yazılı.
3. **Föyler.** Sorular Genel Sürüm'den birebir alındı. PaketPro 3000 sürümü, uyarlamanın nasıl yapılacağına örnek olarak kullanıldı (`docs/foyler/NOT.md`). Her lab'a föy dışı "zafiyetler ve nasıl kapatılır" soruları eklendi.
4. **Gereksinim = test.** Lab'lardaki iddialar `efo_sim/` altında basit Python modellerine çevrildi. Her test bir iddiayı ya da gereksinimi doğrular. Bütün sayısal değerler `efo_sim/params.yaml`'dadır ve her biri etiket + kaynak taşır; kodda sabit sayı yoktur.
5. **Tek kaynaktan PDF.** Lab metinleri `docs/report/*.md` dosyalarındadır. Sonuç tabloları, grafikler, Mermaid diyagramları ve pytest çıktıları PDF'e doğrudan `efo_sim/out/` dosyalarından girer. Bu sayede PDF'teki sonuçlar testlerin gerçek çıktısıyla birebir aynıdır.

## Ana bulgular

- **En ciddi tehlike:** Besleme ağzında el ya da kolun malzemeyle birlikte yongalama makinesine çekilmesi. Acil stop / çekme ipi fonksiyonu için PLr = **e** (S2, F2, P2).
- **Siberden fiziksele:** Model, emniyet invertöre bağımlı olduğunda tek bir rampa parametresi değişikliğinin acil stoptaki durma mesafesini 0,50 m'den 2,875 m'ye çıkardığını gösteriyor (güvenli mesafe 1,50 m). Yani el, bant durmadan besleme ağzına ulaşıyor.
- **Bağımsızlık:** Saldırı grafında mevcut durum varsayımında emniyet fonksiyonuna 19 yol var. Hedef mimaride, saldırganın VPN ve MFA'yı aştığı kabul edilse bile yol sayısı **0**.
- **Önemli koşul:** Bağımsızlık yalnızca sinyal yolunu değil, emniyet hesabının dayandığı varsayımları da (bant hızı) kapsamalı. LAB 4'teki G1–G7 gereksinimleri bunu tanımlıyor.
- **Zafiyet kararı:** CVSS 9,8'lik aynı PLC açığı, bağımlı mimaride acil telafi (4 önlem, 1,5 saat) ve emniyet yeniden doğrulaması gerektiriyor. Bağımsız mimaride tek önlemle planlı bir bakım işine dönüşüyor. CVSS'i yüksek ama bileşeni SBOM'da olmayan bir kayıt (SSA-688146) ilk şartta eleniyor. Karar her olayda yeniden hesaplanıyor: kayıt KEV'e girince bağımlı mimaride hat kontrollü duruyor, bağımsız mimaride durmuyor. Sahadaki değişiklikleri işlenmemiş bir SBOM 3 kaydı yanlışlıkla "etkilemez" gösteriyor; yaması gelmeyecek bir bileşende telafi kalıcı hâle geliyor.
- **Olay anında emniyet:** Okunan konfigürasyon (PLC CRC farkı + rampa 10 s) referansla karşılaştırılıp durma mesafesi modeline verildiğinde, mevcut mimaride acil stopa güvenilemiyor. "Resetleyip devam edelim" akışı kanıt, emniyet sırası ve CRA paketi kontrollerinde kalıyor.
- **YZ fail-safe:** Sentetik veride güven eşiği (0,61) ve YZ'den bağımsız metal dedektörüyle kaçak oranı %6,57'den %0,88'e iniyor. YZ'nin hiçbir çıktısı acil stopu etkilemiyor; hız önerisi emniyet tarafındaki hız izlemeyle sınırlanıyor (A1–A6).

## Klasör yapısı

```
safety40-efo-konveyor/
  README.md
  requirements.txt
  pytest.ini
  .gitignore
  docs/
    prompts/analiz_promptu.md        # analiz promptu
    research/                        # derin araştırma raporu (PDF)
    foyler/NOT.md                    # föy PDF'leri buraya KONMAZ; yalnızca not
    report/                          # PDF'lerin kaynağı (markdown)
      00_makine_profili.md
      lab1_safety_architecture.md ... lab7_ai_safety.md
      05_swot_varsayimlar.md
      meta.yaml                      # ad soyad, grup, altbilgi
      sources.yaml                   # kaynak listesi (R = rapor, Y = eklenen)
  efo_sim/
    params.yaml                      # tüm sayısal varsayımlar, etiket + kaynak
    params.py                        # params.yaml okuyucu
    stil.py                          # ortak palet: grafikler ve diyagramlar aynı renkleri kullanır
    lab1_safety.py                   # durum makinesi, durma mesafesi, PLr
    lab2_zones.py                    # zone/conduit verisi, kurallar, Mermaid üretimi
    lab3_risk.py                     # risk register, S=3 kuralı, duyarlılık, siber-fiziksel bağ
    lab4_attack.py                   # saldırı grafı, bağımsızlık testi, varsayım etkileri
    lab5_vuln.py                     # SBOM, üç şart, yama kararı, telafi, KEV akışı, SBOM sapması, EOL
    lab6_incident.py                 # olay akışı, kanıt koruma, emniyet doğrulaması, CRA paketleri
    lab7_ai.py                       # güven eşiği, girdi kontrolleri, YZ'den bağımsız emniyet
    tests/                           # gereksinim = test
    out/                             # grafikler, Mermaid dosyaları, sonuç tabloları, pytest çıktıları
  scripts/
    run_sims.py                      # modelleri ve testleri çalıştırır, out/ dosyalarını üretir
    build_pdf.py                     # docs/report → pdf/
    pdf_style.css                    # föy görünümüne yakın PDF stili
  pdf/                               # üretilen PDF'ler
```

## Çalıştırma

```bash
pip install -r requirements.txt
npm install -g @mermaid-js/mermaid-cli     # yalnızca PDF üretimi için

# Testler
pytest                                      # 228 geçti, 5 beklenen kalma (xfail)

# Simülasyonlar + lab başına pytest çıktıları (efo_sim/out/)
python scripts/run_sims.py                  # ya da: python scripts/run_sims.py lab3

# Tek bir model
python -m efo_sim.lab1_safety

# PDF'ler
python scripts/build_pdf.py all --check     # hepsi + birleşik rapor, otomatik kontrol
python scripts/build_pdf.py lab2 --preview /tmp/onizleme   # sayfaları PNG'ye çevir
```

**Beklenen kalmalar:** LAB 4'te, emniyetin kumanda sistemine bağımlı olduğu varyant, bağımsızlık gereksinimini karşılamamalıdır. LAB 7'de, emniyet tarafında hız izleme olmayan düzen YZ'nin hız isteğine karşı eli korumamalıdır. Bu testler `xfail(strict=True)` ile işaretli: kalmaları beklenen sonuçtur; beklenmedik şekilde geçerlerse test paketi başarısız olur.

## Web arayüzü

Kökteki `index.html` statik bir sayfadır: PDF'leri tarayıcıda açar, indirir ve figürleri gösterir. Derleme ya da veritabanı gerekmez.

```bash
python -m http.server 8000                  # http://localhost:8000
```

GitHub Pages için: Settings → Pages → `main` / `(root)`. İçerik (makine bilgileri, bulgular, dokümanlar, figürler) yalnızca `web/data.js` dosyasındadır; yeni bir PDF ya da figür eklemek için ilgili diziye bir satır eklemek yeterli. PDF'ler ayrı bir sayfada açılır; tek bir dokümana doğrudan bağlantı: `viewer.html?doc=lab2`.

## Lab durumu

| Bölüm | Durum | Testler |
|---|---|---|
| Rapor doğrulama + Makine Profili | Tamamlandı | — |
| LAB 1 · Safety Architecture | Tamamlandı | 82 geçti (49'u `params.yaml` etiket kontrolü) |
| LAB 2 · IEC 62443 Zone / Conduit | Tamamlandı | 14 geçti |
| LAB 3 · Threat & Risk Register | Tamamlandı | 21 geçti |
| LAB 4 · Secure Remote Access | Tamamlandı | 15 geçti, 4 beklenen kalma |
| LAB 5 · SBOM / CVE / Patch | Tamamlandı | 19 geçti |
| LAB 6 · CRA Incident Simulation | Tamamlandı | 17 geçti |
| LAB 7 · AI Safety Challenge | Tamamlandı | 40 geçti, 1 beklenen kalma |
| SWOT + Varsayımlar | Tamamlandı | — |


## Kaynaklar

Kaynak listesinin tamamı `docs/report/sources.yaml` dosyasında ve her PDF'in sonunda. `R` kimlikleri derin araştırma raporundaki kaynak numaralarıdır; `Y` kimlikleri bu çalışmada eklenen kaynaklardır.
