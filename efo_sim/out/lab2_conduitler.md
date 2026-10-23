| Conduit | Nereden → nereye | Akışlar | Kontroller |
|---|---|---|---|
| **C1** | Z0 → Z2 | uzak bakım oturumu | VPN; MFA; kişisel hesap; varsayılan kapalı, tesis onayıyla açılır; tam oturum kaydı |
| **C2** | Z3 → Z2 | veri yansıtma | güvenlik duvarı; tek yönlü veri aktarımı (Z3 → Z2) |
| **C3** | Z2 → Z4 | mühendislik erişimi; HMI bakımı; invertör bakımı | güvenlik duvarı izin listesi (yalnız mühendislik portları); oturum kaydı; emniyetle ilgili invertör parametreleri parola + checksum ile kilitli |
| **C4** | Z3 → Z4 | üretim verisi | güvenlik duvarı; salt okuma protokol filtresi |
| **C5** | Z1 → Z2 | rapor okuma | güvenlik duvarı; kurumsal kimlik doğrulama; salt okuma |
| **C6** | Z2 → Z0 | telemetri gönderimi | yalnız giden bağlantı; TLS; güvenlik duvarı |
| **C7** | ZT → Z4 | yerel servis; reçete / güncelleme | fiziksel port kilidi; yalnız tesise kayıtlı ve taranmış cihaz; kişisel hesap; değişiklik kaydı |
| **C8** | Z5 → Z4 | emniyet durumu | kablolu, tek yönlü durum sinyali (Z5 → Z4) |
