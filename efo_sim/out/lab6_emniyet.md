| Ayar | Referans | Okunan | Fark |
|---|---|---|---|
| `plc_proje_crc` | 7A3F-19C2 | C04D-88E1 | **evet** |
| `emniyet_rolesi_ayar` | SS1-t 1,0 s | SS1-t 1,0 s | hayır |
| `rampa_suresi` | 0,5 | 10,0 | **evet** |
| `hiz_carpani` | 1,0 | 1,0 | hayır |

| Emniyet mimarisi | Fark → LAB 4 saldırısı | Durma mesafesi | Emniyet güvende mi? |
|---|---|---|---|
| Emniyet kararı PLC'de, durdurma invertör rampasıyla | PLC mantığı değişti (acil stop yok sayılır) | bant durmaz | **Hayır** |
| Emniyet kararı PLC'de, durdurma invertör rampasıyla | İnvertör rampası 10 s | 2,875 m | **Hayır** |
| Kablolu emniyet rölesi, SS1-t ile STO | PLC mantığı değişti (acil stop yok sayılır) | 0,500 m | Evet |
| Kablolu emniyet rölesi, SS1-t ile STO | İnvertör rampası 10 s | 0,931 m | Evet |
| Emniyet rölesi + SS1-t + emniyet tarafında hız izleme | PLC mantığı değişti (acil stop yok sayılır) | 0,500 m | Evet |
| Emniyet rölesi + SS1-t + emniyet tarafında hız izleme | İnvertör rampası 10 s | 0,931 m | Evet |

Güvenli mesafe 1,50 m. Mevcut (varsayım) mimari bağımlı varyanttır.
