# CLAUDE.md

Safety 4.0 Bootcamp ödevi: Efo Makina besleme bandı ve sarsak için LAB 1–7 föy analizi + SWOT. Bağımsız akademik çalışmadır; firmayla iletişim yoktur, analizin çoğu varsayıma dayanır. Dil: **Türkçe** (kod tanımlayıcıları da Türkçe ve ASCII: `durma_mesafesi`, `uc_sart`).

## Komutlar

```bash
pytest                                        # tüm testler (228 geçti, 5 xfail)
python scripts/run_sims.py [lab5 ...]         # modeller + lab başına pytest → efo_sim/out/
PATH=$HOME/.local/bin:$PATH python scripts/build_pdf.py all --check   # PDF'ler + birleşik rapor
python scripts/build_pdf.py lab5 --preview /tmp/onizleme              # sayfaları PNG'ye çevir
python -m http.server 8000                    # web arayüzü (index.html)
```

`mmdc` (mermaid-cli) `~/.local/bin`'de; PATH'e eklemeden `build_pdf.py` diyagram çizemez.

## Yapı ve akış

- `docs/report/*.md` → `scripts/build_pdf.py` → `pdf/*.pdf`. Yeni doküman: `DOCS` sözlüğüne ekle.
- `efo_sim/labN_*.py` modeli `efo_sim/out/` altına tablo (`.md`), grafik (`.png`), `.mmd` ve `labN_params.yaml` yazar. Markdown bunları `<!-- include-md: ... -->`, `include-mermaid`, `include-code`, `include-text` ile alır. **PDF'teki sonuçlar elle yazılmaz, koddan gelir.**
- Yeni lab: `scripts/run_sims.py` içindeki `LABS` sözlüğüne modül + test dosyası ekle.
- Web: statik, derleme ve veritabanı yok; içerik elle eklenir. `index.html` (ana sayfa, `web/app.js`) + `viewer.html?doc=<id>` (PDF ayrı sayfada açılır, `web/viewer.js`; modal değil). Figürler ana sayfada modalda büyür. Eski `index.html#doc=<id>` bağlantıları `viewer.html`'e yönlenir. Mobilde gömülü PDF yerine "PDF'i aç" düğmesi çıkar. Yollar repo köküne göredir; `.nojekyll` kökte durur.
- Web içeriği yalnızca `web/data.js`'te (makine kartı, bulgular, dokümanlar, figürler); yeni PDF/figür = ilgili diziye bir satır, `id` `viewer.html?doc=` için kullanılır. Diyagram PNG'lerinin adı içerik hash'i taşır (`lab5_0_ac138fb6.png`); diyagram değişince `data.js`'teki yolu güncelle ve eski `efo_sim/out/diagrams/` dosyalarını sil.

## Kurallar

- **Kodda sabit sayı yok.** Her sayısal değer `efo_sim/params.yaml`'da `deger`, `etiket` (SEKTÖR-TİPİK | VARSAYIM | ÇIKARIM) ve `kaynak` taşır; `test_params.py` bunu her kayıt için kontrol eder. Okuma: `d("lab1.bant_hizi")`; geçici değişiklik: `gecici(...)`. Sayıları metne `sayi()` ile Türkçe virgüllü yaz.
- **Etiketler:** Metindeki her iddia `[EFO-DOĞRULANMIŞ]`, `[SEKTÖR-TİPİK]`, `[ÇIKARIM]` ya da `[VARSAYIM]` taşır. Kaynaklar `[R12]` / `[Y22]` biçiminde; kimlik `docs/report/sources.yaml`'da yoksa build hata verir. R = derin araştırma raporu, Y = bu çalışmada eklenen; yeni kaynağı eklemeden önce linki kontrol et.
- **Varsayımlar** V1–V23 kimlikli; yenisi `05_swot_varsayimlar.md` tablosuna "yanlışsa ne değişir" sütunuyla eklenir.
- **Gereksinim = test.** Her iddia bir teste bağlanır; test adları cümle gibi Türkçe (`test_hedef_mimaride_..._sifir`). Gereksinimi karşılamaması beklenen varyantlar `xfail(strict=True)`.
- **Lab'lar birbirine bağlı:** LAB 1 durma mesafesi ve durum makinesi; LAB 4 saldırı grafı (`MEVCUT`, `HEDEF`, `HEDEF_ICERI_GIRILDI`) ve bağımsızlık varyantları LAB 5–7'de yeniden kullanılır. LAB 4'te bir koşul değişirse LAB 4 çıktılarının değişmediğini kontrol et.
- **Föy yapısı (markdown):** front matter (`bolum`, `baslik`, `cikti`, `ep`, `kavram`, `baglam`); föy soruları `Q1 | ...`, föy dışı ek sorular `QE1 | ...` (zafiyet → kapatma); kutular `<div class="kanit|note|kural" markdown="1">`; test bağlantısı `<span class="test-ref">`.
- **Tarafsızlık:** Föyler çözüm değil gereksinim tanımlatır. Simülasyon varyantları ürün önerisi değildir; bunu metinde belirt. Efo hakkında kesin hüküm kurma.
- **Mermaid:** Alt grafiklere dışarıdan kenar verilirse iç `direction` yok sayılır; sıralama için `~~~` kullan. Eşkenar dörtgen düğümler PDF'te diyagramı küçültür. Çizdikten sonra `--preview` ile bak.

## Git

- Föy PDF'leri (`docs/foyler/*.pdf`) bootcamp materyalidir; `.gitignore`'da, commit'lenmez.
- GitHub Pages `main` / root'tan yayınlanır.
- İş bitince commit ve push at.
- `origin` HTTPS ve token tanımlı değil, o yüzden HTTPS push başarısız olur. SSH anahtarı çalışıyor; push'u SSH adresiyle yap (remote'u değiştirmeden): `git push git@github.com:YENESDGN/safety40-efo-konveyor.git <dal>`.
- Kullanıcı README'yi bazen GitHub web arayüzünden düzenliyor; push reddedilirse önce `git fetch git@github.com:YENESDGN/safety40-efo-konveyor.git <dal>` ile gelen commit'e bak, sonra `git rebase FETCH_HEAD`.
