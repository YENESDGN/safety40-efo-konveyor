// data.js içeriğini sayfaya basar ve PDF / figür görüntüleyiciyi yönetir.
(function () {
  const S = window.SITE;
  const $ = (id) => document.getElementById(id);

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const tagClass = {
    "EFO-DOĞRULANMIŞ": "t-efo",
    "SEKTÖR-TİPİK": "t-sektor",
    "ÇIKARIM": "t-cikarim",
    "VARSAYIM": "t-varsayim",
  };

  // Başlık alanı
  $("baslik").textContent = S.baslik;
  $("altBaslik").textContent = S.altBaslik;
  $("yazar").textContent = S.yazar;
  $("uyari").textContent = S.uyari;

  const ana = S.dokumanlar.find((d) => d.ana);
  if (ana) {
    $("heroActions").innerHTML =
      `<a class="btn primary" href="viewer.html?doc=${esc(ana.id)}">${esc(ana.baslik)} — oku</a>` +
      `<a class="btn" href="${esc(ana.dosya)}" download>PDF indir</a>` +
      (S.repo ? `<a class="btn" href="${esc(S.repo)}" target="_blank" rel="noopener">GitHub</a>` : "");
  }

  // Bulgular
  $("bulgular").innerHTML = S.bulgular
    .map(
      (b) => `<article class="stat">
        <div class="stat-v">${esc(b.deger)}</div>
        <div class="stat-t">${esc(b.baslik)}</div>
        <p>${esc(b.metin)}</p>
      </article>`
    )
    .join("");

  // Makine kartı
  $("makineListe").innerHTML = S.makine
    .map(
      (m) => `<div class="spec-row">
        <dt>${esc(m.ad)}</dt>
        <dd>${esc(m.deger)} <span class="tag ${tagClass[m.etiket] || ""}">${esc(m.etiket)}</span></dd>
      </div>`
    )
    .join("");

  // Dokümanlar (ana rapor zaten üstte)
  $("dokumanListe").innerHTML = S.dokumanlar
    .filter((d) => !d.ana)
    .map(
      (d) => `<article class="doc">
        ${d.rozet ? `<span class="badge">${esc(d.rozet)}</span>` : ""}
        <h3>${esc(d.baslik)}</h3>
        <p>${esc(d.aciklama)}</p>
        <div class="doc-actions">
          <a class="btn primary sm" href="viewer.html?doc=${esc(d.id)}">Görüntüle</a>
          <a class="btn sm" href="${esc(d.dosya)}" download>İndir</a>
        </div>
      </article>`
    )
    .join("");

  // Figürler
  $("figurListe").innerHTML = S.figurler
    .map(
      (f, i) => `<button class="fig" data-fig="${i}">
        <img src="${esc(f.dosya)}" alt="${esc(f.baslik)}" loading="lazy">
        <span><b>${esc(f.lab)}</b> · ${esc(f.baslik)}</span>
      </button>`
    )
    .join("");

  $("foot").innerHTML =
    `<p>${esc(S.yazar)}</p>` +
    (S.repo ? `<p><a href="${esc(S.repo)}" target="_blank" rel="noopener">Kaynak kod ve testler</a></p>` : "");

  // Figür görüntüleyici (PDF'ler viewer.html'de açılır)
  const dlg = $("viewer");

  document.addEventListener("click", (e) => {
    const figBtn = e.target.closest("[data-fig]");
    if (!figBtn) return;
    const f = S.figurler[+figBtn.dataset.fig];
    const title = `${f.lab} · ${f.baslik}`;
    $("viewerTitle").textContent = title;
    $("viewerOpen").href = f.dosya;
    $("viewerDownload").href = f.dosya;
    $("viewerBody").innerHTML = `<img src="${esc(f.dosya)}" alt="${esc(title)}">`;
    dlg.showModal();
  });

  $("viewerClose").addEventListener("click", () => dlg.close());
  dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });
  dlg.addEventListener("close", () => { $("viewerBody").innerHTML = ""; });

  // Eski #doc=lab2 bağlantıları yeni sayfaya yönlensin
  const m = location.hash.match(/^#doc=(.+)$/);
  if (m) location.replace("viewer.html?doc=" + encodeURIComponent(m[1]));
})();
