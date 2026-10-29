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
      `<button class="btn primary" data-doc="${esc(ana.id)}">${esc(ana.baslik)} — oku</button>` +
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
          <button class="btn primary sm" data-doc="${esc(d.id)}">Görüntüle</button>
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

  // Görüntüleyici
  const dlg = $("viewer");
  const isMobile = matchMedia("(max-width: 700px)").matches;

  function open(title, src, kind) {
    // Mobil tarayıcılar iframe içinde PDF göstermiyor; doğrudan aç.
    if (kind === "pdf" && isMobile) {
      window.open(src, "_blank", "noopener");
      return;
    }
    $("viewerTitle").textContent = title;
    $("viewerOpen").href = src;
    $("viewerDownload").href = src;
    $("viewerBody").innerHTML =
      kind === "pdf"
        ? `<iframe src="${esc(src)}#view=FitH" title="${esc(title)}"></iframe>`
        : `<img src="${esc(src)}" alt="${esc(title)}">`;
    dlg.showModal();
  }

  document.addEventListener("click", (e) => {
    const docBtn = e.target.closest("[data-doc]");
    if (docBtn) {
      const d = S.dokumanlar.find((x) => x.id === docBtn.dataset.doc);
      if (d) {
        open(d.baslik, d.dosya, "pdf");
        history.replaceState(null, "", "#doc=" + d.id);
      }
      return;
    }
    const figBtn = e.target.closest("[data-fig]");
    if (figBtn) {
      const f = S.figurler[+figBtn.dataset.fig];
      open(`${f.lab} · ${f.baslik}`, f.dosya, "img");
    }
  });

  $("viewerClose").addEventListener("click", () => dlg.close());
  dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });
  dlg.addEventListener("close", () => {
    $("viewerBody").innerHTML = "";
    if (location.hash.startsWith("#doc=")) history.replaceState(null, "", location.pathname);
  });

  // #doc=lab2 gibi doğrudan bağlantılar
  const m = location.hash.match(/^#doc=(.+)$/);
  if (m) {
    const d = S.dokumanlar.find((x) => x.id === m[1]);
    if (d) open(d.baslik, d.dosya, "pdf");
  }
})();
