| Aşama | Zaman | Kim | Eylem | Tür | Kanıt |
|---|---|---|---|---|---|
| İlk 15 dk | +00:00 | Vardiya sorumlusu | Bant başındaki operatöre haber: besleme ağzından uzak dur, hattı izle | emniyet | — |
| İlk 15 dk | +00:02 | Vardiya sorumlusu | Bakım/otomasyon sorumlusu, İSG uzmanı ve BT/OT güvenlik sorumlusunu ara | iletisim | — |
| İlk 15 dk | +00:05 | Bakım sorumlusu | Hattı normal stop ile kontrollü durdur; ana şalteri kilitle (LOTO). Reset yok | emniyet | — |
| İlk 15 dk | +00:08 | Bakım sorumlusu | 4G router'ın ağ kablosunu çek (kapatma, yeniden başlatma yok) | erisim | — |
| İlk 15 dk | +00:10 | Vardiya sorumlusu | Pano, HMI ve parametre ekranlarını fotoğrafla | kanit | alır K5 |
| İlk 15 dk | +00:12 | Vardiya sorumlusu | Üreticiyi (Efo) bilinen telefon numarasından ara; ele geçirilen kanal kullanılmaz | iletisim | — |
| İlk 2 saat | +00:30 | OT güvenlik | PLC projesini ve CRC'yi salt okunur dök; referansla karşılaştır | kanit | alır K1 |
| İlk 2 saat | +00:40 | OT güvenlik | İnvertör parametrelerini dök | kanit | alır K2 |
| İlk 2 saat | +00:50 | OT güvenlik | Router loglarını ve HMI loglarını dışa aktar; özet değerlerini (hash) kaydet | kanit | alır K3, alır K4 |
| İlk 2 saat | +01:00 | Üretici (Efo) | Paylaşılan servis hesabını kapat; giriş kayıtlarını dışa aktar | erisim | alır K6 |
| İlk 2 saat | +01:15 | Bakım + İSG | Emniyet değerlendirmesi: konfigürasyon farkı → durma mesafesi (6.1) | emniyet | — |
| İlk 2 saat | +01:30 | Vardiya sorumlusu | Olay kaydını aç: zaman çizgisi, kanıt listesi, kim neye dokundu | kanit | — |
| 24 saate kadar | +03:00 | Üretici (Efo) | Aktif istismar ya da ağır olay mı? CRA kapsamına giriyor mu? Etkilenen müşteriler | bildirim | — |
| 24 saate kadar | +20:00 | Üretici (Efo) | CRA erken uyarı (CSIRT + ENISA, tek bildirim platformu) | bildirim | — |
| 24 saate kadar | +1 g 00:00 | Bakım + OT güvenlik | Referans yedekten PLC ve invertörü geri yükle | kurtarma | **siler K1**, **siler K2** |
| 72 saate kadar | +1 g 01:00 | Bakım + İSG | SF1–SF4 fonksiyon testi + durma süresi ölçümü; sonra reset ve start | emniyet | — |
| 72 saate kadar | +2 g 00:00 | Üretici (Efo) | Kök neden analizi: giriş yolu, değişen parametreler, etkilenen kurulumlar | bildirim | — |
| 72 saate kadar | +2 g 18:40 | Üretici (Efo) | CRA olay bildirimi: genel bilgi, olayın niteliği, alınan ve kullanıcıya önerilen önlemler | bildirim | — |
| 14 güne kadar | +7 g 00:00 | Üretici + müşteri | Kişisel hesaplar + MFA + varsayılan kapalı uzak erişim (LAB 4 hedefi) | kurtarma | — |
| 14 güne kadar | +12 g 12:00 | Üretici (Efo) | CRA son rapor: ayrıntılı açıklama, ciddiyet, kök neden, uygulanan ve süren önlemler | bildirim | — |

Zaman 10:15'ten itibaren (+gün sa:dk). Kanıt kimlikleri:

- **K1:** PLC projesi + CRC (salt okunur çevrimiçi döküm)
- **K2:** İnvertör parametre dökümü
- **K3:** Router / VPN bağlantı logları
- **K4:** HMI olay logları + uzak masaüstü aracı logları
- **K5:** Pano, HMI ekranı ve parametre ekranlarının fotoğrafı
- **K6:** Servis hesabının giriş kayıtları (üretici tarafı)
