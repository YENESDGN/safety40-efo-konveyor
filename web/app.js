// data.js içeriğini sayfaya basar; figür görüntüleyiciyi ve süzgeçleri yönetir.
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
  const docUrl = (id) => "viewer.html?doc=" + encodeURIComponent(id);

  // Başlık alanı
  $("baslik").textContent = S.baslik;
  $("altBaslik").textContent = S.altBaslik;
  $("yazar").textContent = S.yazar;
  $("uyari").textContent = S.uyari;

  const ana = S.dokumanlar.find((d) => d.ana);
  if (ana) {
    $("heroActions").innerHTML =
      `<a class="btn primary" href="${docUrl(ana.id)}">Raporu oku <span aria-hidden="true">→</span></a>` +
      `<a class="btn ghost" href="${esc(ana.dosya)}" download>PDF indir</a>` +
      (S.repo ? `<a class="btn ghost" href="${esc(S.repo)}" target="_blank" rel="noopener">Kod ve testler</a>` : "");
  }

  // Bulgular
  $("bulguListe").innerHTML = S.bulgular
    .map(
      (b, i) => `<article class="stat" style="--i:${i}">
        <div class="stat-v">${esc(b.deger)}</div>
        <div class="stat-t">${esc(b.baslik)}</div>
        <p>${esc(b.metin)}</p>
      </article>`
    )
    .join("");

  // Lab zinciri
  if (S.zincir) {
    $("zincirListe").innerHTML = S.zincir
      .map(
        (z) => `<li class="link">
          <a class="link-card" href="${docUrl(z.doc)}">
            <span class="link-no">${esc(z.lab)}</span>
            <strong>${esc(z.baslik)}</strong>
            <span class="link-out">${esc(z.cikti)}</span>
            <span class="link-uses">${
              z.kullanir.length
                ? "kullanır: " + z.kullanir.map((k) => `<b>${esc(k)}</b>`).join(" ")
                : "temel model"
            }</span>
          </a>
        </li>`
      )
      .join("");
  }

  // Makine kartı
  $("makineListe").innerHTML = S.makine
    .map(
      (m) => `<div class="spec-row">
        <dt>${esc(m.ad)}</dt>
        <dd><span>${esc(m.deger)}</span> <span class="tag ${tagClass[m.etiket] || ""}">${esc(m.etiket)}</span></dd>
      </div>`
    )
    .join("");

  // Dokümanlar (ana rapor zaten üstte)
  $("dokumanListe").innerHTML = S.dokumanlar
    .filter((d) => !d.ana)
    .map(
      (d) => `<article class="doc">
        ${d.rozet ? `<span class="badge">${esc(d.rozet)}</span>` : ""}
        <h3><a href="${docUrl(d.id)}">${esc(d.baslik)}</a></h3>
        <p>${esc(d.aciklama)}</p>
        <div class="doc-actions">
          <a class="btn primary sm" href="${docUrl(d.id)}">Görüntüle</a>
          <a class="btn sm" href="${esc(d.dosya)}" download>İndir</a>
        </div>
      </article>`
    )
    .join("");

  // Figürler + lab süzgeci
  const labs = ["Tümü", ...new Set(S.figurler.map((f) => f.lab))];
  let secili = "Tümü";
  let gorunen = S.figurler.map((_, i) => i);

  function figurleriCiz() {
    gorunen = S.figurler.map((_, i) => i).filter((i) => secili === "Tümü" || S.figurler[i].lab === secili);
    $("figurListe").innerHTML = gorunen
      .map((i) => {
        const f = S.figurler[i];
        return `<button class="fig" type="button" data-fig="${i}">
          <span class="fig-img"><img src="${esc(f.dosya)}" alt="${esc(f.lab + " · " + f.baslik)}" loading="lazy"></span>
          <span class="fig-cap"><b>${esc(f.lab)}</b>${esc(f.baslik)}</span>
        </button>`;
      })
      .join("");
    $("figurFiltre").innerHTML = labs
      .map((l) => `<button type="button" class="chip" data-lab="${esc(l)}" aria-pressed="${l === secili}">${esc(l)}</button>`)
      .join("");
  }
  figurleriCiz();

  $("figurFiltre").addEventListener("click", (e) => {
    const b = e.target.closest("[data-lab]");
    if (!b) return;
    secili = b.dataset.lab;
    figurleriCiz();
  });

  $("foot").innerHTML =
    `<p><strong>${esc(S.yazar)}</strong></p>` +
    `<p>${esc(S.uyari)}</p>` +
    (S.repo ? `<p><a href="${esc(S.repo)}" target="_blank" rel="noopener">Kaynak kod ve testler (GitHub)</a></p>` : "");

  // Figür görüntüleyici (PDF'ler viewer.html'de açılır); ← → ile gezilir
  const dlg = $("viewer");
  let aktif = 0;

  function goster(i) {
    aktif = i;
    const f = S.figurler[i];
    const title = `${f.lab} · ${f.baslik}`;
    $("viewerTitle").textContent = title;
    $("viewerOpen").href = f.dosya;
    $("viewerDownload").href = f.dosya;
    $("viewerBody").innerHTML = `<img src="${esc(f.dosya)}" alt="${esc(title)}">`;
  }
  function kaydir(adim) {
    const k = gorunen.indexOf(aktif);
    goster(gorunen[(k + adim + gorunen.length) % gorunen.length]);
  }

  $("figurListe").addEventListener("click", (e) => {
    const b = e.target.closest("[data-fig]");
    if (!b) return;
    goster(+b.dataset.fig);
    dlg.showModal();
  });
  $("viewerPrev").addEventListener("click", () => kaydir(-1));
  $("viewerNext").addEventListener("click", () => kaydir(1));
  $("viewerClose").addEventListener("click", () => dlg.close());
  dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });
  dlg.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") kaydir(-1);
    if (e.key === "ArrowRight") kaydir(1);
  });
  dlg.addEventListener("close", () => { $("viewerBody").innerHTML = ""; });

  // Eski #doc=lab2 bağlantıları yeni sayfaya yönlensin
  const m = location.hash.match(/^#doc=(.+)$/);
  if (m) location.replace("viewer.html?doc=" + encodeURIComponent(m[1]));
})();
