| Kural | Mevcut (varsayım) | Hedef |
|---|---|---|
| **K1** Dış bölgeden emniyet bölgesine doğrudan kenar yok | ✔ uyuyor | ✔ uyuyor |
| **K2** Bölgeler arası her kenar bir conduit'ten geçiyor | ✖ 6 ihlal: Telefon / tablet (WLAN menzilinde) → Bant invertörü; Hat PLC'si → Bulut telemetri (kestirimci bakım); Servis laptopu → Hat PLC'si; USB bellek → Operatör paneli / HMI (kabin); Acil stop, çekme ipi, kapak anahtarları, reset → Hat PLC'si; Hat PLC'si → STO hattı (invertör STO girişleri) | ✔ uyuyor |
| **K3** Her conduit'te en az bir kontrol tanımlı | ✖ 1 ihlal: C1 | ✔ uyuyor |
| **K4** Emniyet bölgesine dışarıdan yazma yönünde akış yok | ✖ 1 ihlal: Hat PLC'si → STO hattı (invertör STO girişleri) | ✔ uyuyor |
| **K5** Dış bölge yalnızca DMZ'ye bağlanıyor | ✖ 3 ihlal: Üretici uzak servis bilgisayarı → 4G/VPN router (uzak destek); Telefon / tablet (WLAN menzilinde) → Bant invertörü; Hat PLC'si → Bulut telemetri (kestirimci bakım) | ✔ uyuyor |
