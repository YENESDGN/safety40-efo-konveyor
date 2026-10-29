// Sitenin tüm içeriği burada. Yeni doküman, bulgu ya da figür eklemek için
// ilgili diziye bir nesne ekleyin; başka dosyaya dokunmaya gerek yok.
// Yollar repo köküne göredir (index.html kökte durur).

window.SITE = {
  baslik: "Efo Makina · Besleme Bandı & Sarsak",
  altBaslik: "Safety 4.0 Föy Analizi (LAB 1–4) + SWOT",
  yazar: "Yağız Enes Doğan · Gündüz - B · Safety 4.0 Bootcamp",
  repo: "https://github.com/YENESDGN/safety40-efo-konveyor",
  uyari:
    "Bağımsız akademik çalışmadır; Efo Makina ile bağlantısı yoktur. Analizin birçok kısmı " +
    "varsayıma dayanır ve gerçek ürünün emniyet durumu hakkında bir iddia değildir. " +
    "Eğitim çıktısıdır; resmî denetim veya uygunluk değerlendirmesi değildir.",

  // Makine kartı: etiket = [EFO-DOĞRULANMIŞ] | [SEKTÖR-TİPİK] | [ÇIKARIM] | [VARSAYIM]
  makine: [
    { ad: "Üretici", deger: "Efo Makina İnşaat Gıda San. ve Tic. Ltd. Şti., Torbalı / İzmir", etiket: "EFO-DOĞRULANMIŞ" },
    { ad: "İncelenen ünite", deger: "Yonga hattında besleme bandı + sarsak (titreşimli konveyör)", etiket: "EFO-DOĞRULANMIŞ" },
    { ad: "Sarsak sayısı", deger: "İki: büyük olan dozajlıyor, diğeri taşıyor", etiket: "EFO-DOĞRULANMIŞ" },
    { ad: "Besleme ağzına komşu ünite", deger: "Besleme bandı (V1)", etiket: "ÇIKARIM" },
    { ad: "PLC / invertör", deger: "Bilinmiyor; S7-1200 + Lenze/SEW VFD kabul edildi (V2–V3)", etiket: "VARSAYIM" },
    { ad: "Teknik veri", deger: "Güç, kapasite, hız, sensör, emniyet donanımı hiçbir kaynakta yok", etiket: "EFO-DOĞRULANMIŞ" },
  ],

  // Öne çıkan bulgular
  bulgular: [
    { deger: "PLr e", baslik: "En ciddi tehlike", metin: "Besleme ağzında el/kolun yongalama makinesine çekilmesi. Acil stop / çekme ipi için S2, F2, P2." },
    { deger: "0,50 → 2,875 m", baslik: "Siberden fiziksele", metin: "Emniyet invertöre bağımlıyken tek bir rampa parametresi durma mesafesini güvenli sınırın (1,50 m) çok üstüne çıkarıyor." },
    { deger: "19 → 0", baslik: "Bağımsızlık", metin: "Emniyet fonksiyonuna saldırı yolu: mevcut durumda 19, hedef mimaride VPN + MFA aşılsa bile 0." },
    { deger: "109 + 4", baslik: "Gereksinim = test", metin: "109 test geçti, 4 beklenen kalma (xfail). PDF'teki sonuçlar testlerin gerçek çıktısıdır." },
  ],

  // PDF dokümanlar. ana: true olan, üstte "tam rapor" olarak öne çıkar.
  dokumanlar: [
    { id: "tam", baslik: "Tam Rapor", aciklama: "Bütün bölümler tek dosyada, içindekiler sayfasıyla.", dosya: "pdf/Efo_Safety40_Tam_Rapor.pdf", ana: true },
    { id: "profil", rozet: "Bölüm 0", baslik: "Makine Profili", aciklama: "Rapor doğrulama (16 düzeltme), makine profili, varsayım kimlikleri.", dosya: "pdf/00_Makine_Profili.pdf" },
    { id: "lab1", rozet: "LAB 1 · EP 03", baslik: "Safety Architecture", aciklama: "Safety Function Map, durma mesafesi, PLr tablosu.", dosya: "pdf/LAB1_Safety_Architecture.pdf" },
    { id: "lab2", rozet: "LAB 2 · EP 05", baslik: "IEC 62443 Zone / Conduit", aciklama: "Bölge ve conduit diyagramı, varlık envanteri, kurallar.", dosya: "pdf/LAB2_IEC62443_Zone_Conduit.pdf" },
    { id: "lab3", rozet: "LAB 3 · EP 04", baslik: "Threat & Risk Register", aciklama: "Risk register, ısı haritası, siber-fiziksel bağ, duyarlılık.", dosya: "pdf/LAB3_Threat_Risk_Register.pdf" },
    { id: "lab4", rozet: "LAB 4 · EP 02 + 06", baslik: "Secure Remote Access", aciklama: "Saldırı grafı, bağımsızlık testi, G1–G7 gereksinimleri.", dosya: "pdf/LAB4_Secure_Remote_Access.pdf" },
    { id: "swot", rozet: "Bölüm 5", baslik: "SWOT ve Varsayımlar", aciklama: "SWOT, V1–V15 varsayımları ve yanlışsa etkileri.", dosya: "pdf/05_SWOT_ve_Varsayimlar.pdf" },
    { id: "arastirma", rozet: "Kaynak", baslik: "Derin Araştırma Raporu", aciklama: "Analizin ana kanıt kaynağı olan bağımsız araştırma.", dosya: "docs/research/Efo_Makina_Derin_Arastirma_Raporu.pdf" },
  ],

  // Figürler (simülasyon çıktıları)
  figurler: [
    { baslik: "Hat akışı ve analiz kapsamı", lab: "Bölüm 0", dosya: "efo_sim/out/diagrams/00_0_cb6b3f9c.png" },
    { baslik: "Safety Function Map", lab: "LAB 1", dosya: "efo_sim/out/diagrams/lab1_0_355f8273.png" },
    { baslik: "Durma mesafesi", lab: "LAB 1", dosya: "efo_sim/out/lab1_durma_mesafesi.png" },
    { baslik: "Zone / conduit · mevcut", lab: "LAB 2", dosya: "efo_sim/out/diagrams/lab2_0_e3514d01.png" },
    { baslik: "Zone / conduit · hedef", lab: "LAB 2", dosya: "efo_sim/out/diagrams/lab2_1_3e9e223d.png" },
    { baslik: "Risk ısı haritası", lab: "LAB 3", dosya: "efo_sim/out/lab3_isi_haritasi.png" },
    { baslik: "Siber-fiziksel bağ", lab: "LAB 3", dosya: "efo_sim/out/lab3_siber_fiziksel.png" },
    { baslik: "Bağımsızlık testi", lab: "LAB 4", dosya: "efo_sim/out/lab4_bagimsizlik.png" },
    { baslik: "Uzaktan erişim yolu", lab: "LAB 4", dosya: "efo_sim/out/diagrams/lab4_0_4f3b6b97.png" },
    { baslik: "Saldırı grafı · mevcut", lab: "LAB 4", dosya: "efo_sim/out/diagrams/lab4_1_7e0e63b7.png" },
    { baslik: "Saldırı grafı · hedef", lab: "LAB 4", dosya: "efo_sim/out/diagrams/lab4_2_7576ccd7.png" },
  ],
};
