| Varyant | Saldırı | Acil stop sonrası durum | Durma mesafesi | El besleme ağzına ulaşır mı? |
|---|---|---|---|---|
| Emniyet kararı PLC'de, durdurma invertör rampasıyla | Saldırı yok | GÜVENLİ_DURUM | 0,500 m | Hayır |
| Emniyet kararı PLC'de, durdurma invertör rampasıyla | PLC mantığı değişti (acil stop yok sayılır) | ÇALIŞIYOR | bant durmaz | **Evet** |
| Emniyet kararı PLC'de, durdurma invertör rampasıyla | İnvertör rampası 10 s | GÜVENLİ_DURUM | 2,875 m | **Evet** |
| Emniyet kararı PLC'de, durdurma invertör rampasıyla | İnvertör hızı 1,6× + rampa 10 s | GÜVENLİ_DURUM | 7,000 m | **Evet** |
| Kablolu emniyet rölesi, SS1-t ile STO | Saldırı yok | GÜVENLİ_DURUM | 0,500 m | Hayır |
| Kablolu emniyet rölesi, SS1-t ile STO | PLC mantığı değişti (acil stop yok sayılır) | GÜVENLİ_DURUM | 0,500 m | Hayır |
| Kablolu emniyet rölesi, SS1-t ile STO | İnvertör rampası 10 s | GÜVENLİ_DURUM | 0,931 m | Hayır |
| Kablolu emniyet rölesi, SS1-t ile STO | İnvertör hızı 1,6× + rampa 10 s | GÜVENLİ_DURUM | 1,600 m | **Evet** |
| Emniyet rölesi + SS1-t + emniyet tarafında hız izleme | Saldırı yok | GÜVENLİ_DURUM | 0,500 m | Hayır |
| Emniyet rölesi + SS1-t + emniyet tarafında hız izleme | PLC mantığı değişti (acil stop yok sayılır) | GÜVENLİ_DURUM | 0,500 m | Hayır |
| Emniyet rölesi + SS1-t + emniyet tarafında hız izleme | İnvertör rampası 10 s | GÜVENLİ_DURUM | 0,931 m | Hayır |
| Emniyet rölesi + SS1-t + emniyet tarafında hız izleme | İnvertör hızı 1,6× + rampa 10 s | GÜVENLİ_DURUM | 1,146 m | Hayır |

Güvenli mesafe 1,50 m; SS1-t gecikmesi 1,0 s; hız izleme eşiği nominalin 1,2 katı.
