# Föyler hakkında not

Safety 4.0 Bootcamp laboratuvar föyleri (Genel Sürüm ve PaketPro 3000 Sürümü) bootcamp'in eğitim
materyalidir; bu klasöre konmaz ve `.gitignore` ile dışarıda tutulur (`docs/foyler/*.pdf`).
Analizde yalnızca **LAB 1–4** kullanıldı. Sorular Genel Sürüm'den birebir alındı; PaketPro sürümü,
genel soruların belirli bir makineye nasıl uyarlandığını gösteren örnek olarak kullanıldı.

| Lab | Genel Sürüm (esas) | PaketPro 3000 uyarlaması | Efo'ya aktarılan |
|---|---|---|---|
| LAB 1 | 8 soru; referans şema (normal yol / safety yolu / dijital kesişim) | "PaketPro bağlamı" kutusu: tehlike + koruma zinciri + internete açık uzak bakım modülü | "Efo bağlamı" kutusu: besleme ağzına çekilme + acil stop / çekme ipi / kapak kilidi → emniyet rölesi → STO + uzak destek varsayımı (V5) |
| LAB 2 | Genel varlık listesi; S2: "Safety PLC'yi hangi bölgeye koydunuz?" | Somut varlıklar (admin/admin, port 80 HMI, kartondaki Wi-Fi parolası, kilitsiz USB); S2: "Açık uzak bakım modülü hangi bölgeye düşüyor, orada kalabilir mi?" | Genel S2 cevaplandı; PaketPro S2'nin Efo karşılığı (uzak destek router'ı) QP2 olarak eklendi |
| LAB 3 | Tablo: senaryo, L, S, E, skor, öncelik | "Kapılar (ipucu)" kutusu | Efo kapıları kutusu + puanların dayanak tablosu |
| LAB 4 | Mevcut → hedef ("beş ilke"); gereksinim sorusu genel | "Işık perdesi zincirinin uzak bakım yolundan etkilenmemesi" gereksinimi | Acil stop / çekme ipi / kapak interlock zinciri için G1–G7; Kavram kutusundaki altı öğenin hepsi |
