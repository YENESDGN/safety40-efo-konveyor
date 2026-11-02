| Saha değişikliği | Teslim SBOM'unda | Sahada |
|---|---|---|
| D1: Arızalı CPU yedek parçayla değişti; yedek CPU eski firmware'le geldi | PLC firmware (S7-1200 sınıfı): 4.7<br>Component X (PLC firmware kütüphanesi): 2.5 | PLC firmware (S7-1200 sınıfı): 4.5<br>Component X (PLC firmware kütüphanesi): 2.4 |
| D2: Servis teknisyeni HMI'ya uzak masaüstü aracı kurdu | Uzak masaüstü aracı (HMI'da): yok | Uzak masaüstü aracı (HMI'da): 15.0 |

| Kayıt | Mimari | Teslim SBOM'uyla karar | Güncel SBOM'la karar | Yanlış "etkilemez" |
|---|---|---|---|---|
| CVE-XXXX-XXXX | Mevcut (varsayım) | Devam | Hemen telafi | **evet** |
| CVE-XXXX-XXXX | Hedef, içeri girilmiş kabulü | Devam | Devam + planlı telafi | **evet** |
| CVE-2024-47100 | Mevcut (varsayım) | Devam | Hemen telafi | **evet** |
| CVE-2024-47100 | Hedef, içeri girilmiş kabulü | Devam | Devam | hayır |
| SSA-688146 | Mevcut (varsayım) | Devam | Devam | hayır |
| SSA-688146 | Hedef, içeri girilmiş kabulü | Devam | Devam | hayır |

Yanlış "etkilemez" sonucu: teslim SBOM'uyla **3**, değişiklik yönetimine bağlı SBOM'la **0**. SBOM'da görünmeyen ya da sürümü farklı bileşen sayısı: 3.
