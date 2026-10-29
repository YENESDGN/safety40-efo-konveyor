// viewer.html?doc=<id> — data.js'teki dokümanı tam sayfa gösterir.
(function () {
  const S = window.SITE;
  const $ = (id) => document.getElementById(id);

  const esc = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const id = new URLSearchParams(location.search).get("doc");
  const d = S.dokumanlar.find((x) => x.id === id) || S.dokumanlar.find((x) => x.ana);

  document.title = `${d.baslik} · Efo Safety 4.0`;
  $("docBadge").textContent = d.rozet || "Rapor";
  $("docTitle").textContent = d.baslik;
  $("docOpen").href = d.dosya;
  $("docDownload").href = d.dosya;

  // Dokümanlar arası hızlı geçiş
  $("docNav").innerHTML =
    `<select id="docSelect" aria-label="Doküman seç">` +
    S.dokumanlar
      .map((x) => `<option value="${esc(x.id)}"${x === d ? " selected" : ""}>${esc(x.rozet ? x.rozet + " · " : "")}${esc(x.baslik)}</option>`)
      .join("") +
    `</select>`;
  $("docSelect").addEventListener("change", (e) => {
    location.href = "viewer.html?doc=" + encodeURIComponent(e.target.value);
  });

  // Mobil tarayıcılar gömülü PDF göstermiyor; bağlantı sun.
  if (matchMedia("(max-width: 700px)").matches) {
    $("docFrame").innerHTML =
      `<div class="wrap viewer-fallback">
        <p>${esc(d.aciklama || "")}</p>
        <a class="btn primary" href="${esc(d.dosya)}">PDF'i aç</a>
      </div>`;
  } else {
    $("docFrame").innerHTML = `<iframe src="${esc(d.dosya)}#view=FitH" title="${esc(d.baslik)}"></iframe>`;
  }
})();
