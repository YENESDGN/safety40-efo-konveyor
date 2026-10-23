#!/usr/bin/env python3
"""docs/report/*.md dosyalarından föy görünümünde PDF üretir.

Kullanım (repo kökünden):
    python scripts/build_pdf.py 00              # tek doküman
    python scripts/build_pdf.py 00 lab1         # birden fazla doküman
    python scripts/build_pdf.py all             # hepsi + birleşik rapor
    python scripts/build_pdf.py 00 --check      # üret + otomatik kontrol
    python scripts/build_pdf.py 00 --preview /tmp/onizleme   # sayfaları PNG'ye çevir

Markdown'da desteklenen ekler:
    Q1 | Soru metni                     -> föydeki numaralı soru rozeti
    [EFO-DOĞRULANMIŞ] [SEKTÖR-TİPİK] [ÇIKARIM] [VARSAYIM]  -> renkli etiket
    [R3] / [Y1, R30]                    -> kaynak; sonuna otomatik "Kaynaklar" listesi
    ```mermaid ... ```                  -> mermaid-cli (mmdc) ile PNG; ilk satır "%% caption: ..." olabilir
    <!-- include-code: yol -->          -> satır numaralı, renklendirilmiş kod
    <!-- include-text: yol -->          -> düz metin (ör. pytest çıktısı)
    <!-- include-md: yol -->            -> koddan üretilmiş markdown (sonuç tabloları)
    <!-- include-mermaid: yol | başlık --> -> koddan üretilmiş .mmd dosyasını çizer
"""
import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown
import yaml
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_for_filename
from pypdf import PdfReader
from weasyprint import CSS, HTML

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "report"
PDF_DIR = ROOT / "pdf"
DIAG_DIR = ROOT / "efo_sim" / "out" / "diagrams"
CSS_FILE = ROOT / "scripts" / "pdf_style.css"

# anahtar: (markdown dosyası, PDF adı)
DOCS = {
    "00": ("00_makine_profili.md", "00_Makine_Profili.pdf"),
    "lab1": ("lab1_safety_architecture.md", "LAB1_Safety_Architecture.pdf"),
    "lab2": ("lab2_zone_conduit.md", "LAB2_IEC62443_Zone_Conduit.pdf"),
    "lab3": ("lab3_risk_register.md", "LAB3_Threat_Risk_Register.pdf"),
    "lab4": ("lab4_secure_remote_access.md", "LAB4_Secure_Remote_Access.pdf"),
    "05": ("05_swot_varsayimlar.md", "05_SWOT_ve_Varsayimlar.pdf"),
}
FULL_PDF = "Efo_Safety40_Tam_Rapor.pdf"

TAGS = {"EFO-DOĞRULANMIŞ": "efo", "SEKTÖR-TİPİK": "sektor", "ÇIKARIM": "cikarim", "VARSAYIM": "varsayim"}
TAG_RE = re.compile(r"\[(" + "|".join(TAGS) + r")\]")
REF_RE = re.compile(r"\[((?:R|Y)\d+(?:\s*,\s*(?:R|Y)\d+)*)\]")
SORU_RE = re.compile(r"^Q([A-Z]*\d+)\s*\|\s*(.+)$", re.M)
INCLUDE_RE = re.compile(r"<!--\s*include-(code|text):\s*(\S+)\s*-->")
MERMAID_RE = re.compile(r"```mermaid\n(.*?)```", re.S)
INCLUDE_MD_RE = re.compile(r"<!--\s*include-md:\s*(\S+)\s*-->")
INCLUDE_MMD_RE = re.compile(r"<!--\s*include-mermaid:\s*(\S+)\s*(?:\|\s*(.*?))?\s*-->")
MERMAID_CONFIG = {
    "theme": "base",
    "themeVariables": {
        "fontFamily": "DejaVu Sans",
        "fontSize": "15px",
        "primaryColor": "#e6f3f1",
        "primaryBorderColor": "#16223a",
        "primaryTextColor": "#16223a",
        "lineColor": "#16223a",
        "clusterBkg": "#f7f9fb",
        "clusterBorder": "#9aa3b2",
    },
    "flowchart": {"htmlLabels": True, "curve": "basis"},
}


def split_front_matter(text):
    if text.startswith("---\n"):
        _, fm, body = text.split("---\n", 2)
        return yaml.safe_load(fm) or {}, body
    return {}, text


def inline_md(text):
    """Tek satırlık markdown'u <p> olmadan HTML'e çevirir."""
    out = markdown.markdown(text or "")
    return re.sub(r"^<p>|</p>$", "", out.strip())


def render_mermaid(code, name):
    """Mermaid kodunu PNG'ye çevirir; aynı içerik için yeniden çizmez."""
    if not shutil.which("mmdc"):
        sys.exit("mermaid-cli (mmdc) bulunamadı: npm install -g @mermaid-js/mermaid-cli")
    DIAG_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(code.encode("utf-8")).hexdigest()[:8]
    mmd = DIAG_DIR / f"{name}_{digest}.mmd"
    png = mmd.with_suffix(".png")
    if not png.exists():
        cfg = DIAG_DIR / "mermaid_config.json"
        cfg.write_text(json.dumps(MERMAID_CONFIG), encoding="utf-8")
        mmd.write_text(code, encoding="utf-8")
        r = subprocess.run(["mmdc", "-i", str(mmd), "-o", str(png), "-b", "white", "-s", "3", "-c", str(cfg)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            hata = [s for s in (r.stdout + r.stderr).splitlines() if "rror" in s][:3]
            sys.exit(f"mermaid çizilemedi ({mmd.name}): " + " | ".join(hata))
    return png


def code_block(rel_path):
    path = ROOT / rel_path
    src = path.read_text(encoding="utf-8")
    try:
        lexer = get_lexer_for_filename(path.name)
    except Exception:
        lexer = TextLexer()
    body = highlight(src, lexer, HtmlFormatter(linenos="inline", cssclass="highlight"))
    return f'<div class="kod-baslik">{html.escape(rel_path)}</div>{body}'


def text_block(rel_path):
    src = (ROOT / rel_path).read_text(encoding="utf-8")
    return f'<div class="kod-baslik">{html.escape(rel_path)}</div><pre class="metin">{html.escape(src)}</pre>'


def body_to_html(key, body, sources):
    """Markdown gövdesini HTML'e çevirir; kullanılan kaynak kimliklerini döndürür."""
    placeholders = {}

    def hold(fragment):
        token = f"PLACEHOLDER{len(placeholders)}X"
        placeholders[token] = fragment
        return f"\n\n{token}\n\n"

    def mermaid_sub(match):
        code = match.group(1)
        caption = ""
        first = code.splitlines()[0] if code.strip() else ""
        if first.startswith("%% caption:"):
            caption = first.split(":", 1)[1].strip()
        png = render_mermaid(code, f"{key}_{len(placeholders)}")
        rel = png.relative_to(ROOT).as_posix()
        cap = f"<figcaption>{html.escape(caption)}</figcaption>" if caption else ""
        return hold(f'<figure class="genis"><img src="{rel}">{cap}</figure>')

    body = INCLUDE_MD_RE.sub(lambda m: (ROOT / m.group(1)).read_text(encoding="utf-8"), body)
    body = INCLUDE_MMD_RE.sub(
        lambda m: "```mermaid\n%% caption: " + (m.group(2) or "") + "\n"
                  + (ROOT / m.group(1)).read_text(encoding="utf-8") + "```", body)
    body = MERMAID_RE.sub(mermaid_sub, body)
    body = INCLUDE_RE.sub(lambda m: hold(code_block(m.group(2)) if m.group(1) == "code" else text_block(m.group(2))), body)
    body = SORU_RE.sub(lambda m: f'<div class="soru"><span class="no">{m.group(1)}</span>'
                                 f'<span class="metin">{inline_md(m.group(2))}</span></div>', body)

    out = markdown.markdown(body, extensions=["tables", "fenced_code", "attr_list", "md_in_html", "sane_lists"])
    out = TAG_RE.sub(lambda m: f'<span class="tag tag-{TAGS[m.group(1)]}">{m.group(1)}</span>', out)

    used = []

    def ref_sub(match):
        ids = [i.strip() for i in match.group(1).split(",")]
        for i in ids:
            if i not in sources:
                sys.exit(f"{key}: kaynak listesinde olmayan kimlik: {i}")
            if i not in used:
                used.append(i)
        return f'<span class="ref">[{", ".join(ids)}]</span>'

    out = REF_RE.sub(ref_sub, out)
    for token, fragment in placeholders.items():
        out = out.replace(f"<p>{token}</p>", fragment).replace(token, fragment)
    return out, used


def sources_html(used, sources):
    def order(i):
        return (0 if i[0] == "R" else 1, int(i[1:]))

    items = []
    for i in sorted(used, key=order):
        s = sources[i]
        items.append(f'<li><span class="kid">{i}</span> {html.escape(s["title"])} — '
                     f'<a href="{s["url"]}">{html.escape(s["url"])}</a></li>')
    note = ("<p class='uyari'>R = derin araştırma raporundaki kaynak numarası; "
            "Y = bu çalışmada eklenen kaynak.</p>")
    return f'<h2>Kaynaklar</h2>{note}<ul class="kaynaklar">{"".join(items)}</ul>'


def doc_section(key, meta, sources):
    md_name, _ = DOCS[key]
    fm, body = split_front_matter((REPORT / md_name).read_text(encoding="utf-8"))
    body_html, used = body_to_html(key, body, sources)
    fields = [("Ad Soyad", meta["ad_soyad"]), ("Grup", meta["grup"]),
              ("Evidence Pack", fm.get("ep", "—")), ("Makine", meta["makine"])]
    fields_html = "".join(f"<div><span>{k}</span>{html.escape(str(v))}</div>" for k, v in fields)
    boxes = ""
    if fm.get("kavram"):
        boxes += f'<div class="kavram"><b>Kavram:</b> {inline_md(fm["kavram"])}</div>'
    if fm.get("baglam"):
        boxes += f'<div class="baglam"><b>Efo bağlamı:</b> {inline_md(fm["baglam"])}</div>'
    refs = sources_html(used, sources) if used else ""
    return (f'<section class="doc" id="doc-{key}">'
            f'<header class="band"><div class="kicker">{html.escape(fm["bolum"])}</div>'
            f'<h1>{html.escape(fm["baslik"])}</h1><div class="pill">Çıktı: {html.escape(fm["cikti"])}</div></header>'
            f'<div class="fields">{fields_html}</div><p class="uyari">{html.escape(meta["uyari"])}</p>'
            f"{boxes}{body_html}{refs}</section>"), fm


def wrap(sections, meta, title):
    footer = meta["altbilgi"].replace('"', '\\"')
    page_css = f'@page {{ @bottom-left {{ content: "{footer}"; }} }}'
    return (f'<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>{html.escape(title)}</title>'
            f'<meta name="author" content="{html.escape(meta["ad_soyad"])}"><style>{page_css}</style></head>'
            f'<body>{sections}</body></html>')


def write_pdf(doc_html, out_path, title):
    HTML(string=doc_html, base_url=str(ROOT)).write_pdf(
        out_path, stylesheets=[CSS(filename=str(CSS_FILE))],
        pdf_variant=None, presentational_hints=True)
    print(f"yazıldı: {out_path.relative_to(ROOT)}")


def build_single(key, meta, sources):
    section, fm = doc_section(key, meta, sources)
    out = PDF_DIR / DOCS[key][1]
    write_pdf(wrap(section, meta, fm["baslik"]), out, fm["baslik"])
    return out


def build_full(keys, meta, sources):
    sections, toc = [], []
    for key in keys:
        section, fm = doc_section(key, meta, sources)
        sections.append(section)
        toc.append(f'<li><a href="#doc-{key}">{html.escape(fm["baslik"])} — {html.escape(fm["cikti"])}</a></li>')
    cover = (f'<section class="kapak"><h1>Efo Makina — Besleme Bandı &amp; Sarsak</h1>'
             f'<div class="alt">Safety 4.0 Föy Analizi (LAB 1–4) + SWOT</div>'
             f'<div class="fields"><div><span>Ad Soyad</span>{html.escape(meta["ad_soyad"])}</div>'
             f'<div><span>Grup</span>{html.escape(meta["grup"])}</div></div>'
             f'<p class="uyari">{html.escape(meta["uyari"])}</p>'
             f'<h2>İçindekiler</h2><ul class="toc">{"".join(toc)}</ul></section>')
    out = PDF_DIR / FULL_PDF
    write_pdf(wrap(cover + "".join(sections), meta, "Efo Safety 4.0 Tam Rapor"), out, "Tam Rapor")
    return out


def check(pdf_path, meta):
    """Basit otomatik kontrol: Türkçe karakter, ham mermaid/markdown, altbilgi, boş sayfa."""
    reader = PdfReader(str(pdf_path))
    problems = []
    full_text = ""
    for n, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        full_text += text
        if len(text.strip()) < 40:
            problems.append(f"sayfa {n}: neredeyse boş")
        if meta["altbilgi"][:25] not in text.replace("\n", " "):
            problems.append(f"sayfa {n}: altbilgi bulunamadı")
        if "```" in text:
            problems.append(f"sayfa {n}: ham markdown kod çiti")
    for ch in "çğıİöşü":
        if ch not in full_text:
            problems.append(f"metinde '{ch}' yok (font sorunu olabilir)")
    status = "TAMAM" if not problems else "SORUN"
    print(f"kontrol {pdf_path.name}: {len(reader.pages)} sayfa — {status}")
    for p in problems:
        print("   -", p)
    return not problems


def preview(pdf_path, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdftoppm", "-r", "70", "-png", str(pdf_path), str(out_dir / pdf_path.stem)], check=True)
    print(f"önizleme: {out_dir}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docs", nargs="+", help="00, lab1, lab2, lab3, lab4, 05 ya da all")
    ap.add_argument("--check", action="store_true", help="üretilen PDF'leri kontrol et")
    ap.add_argument("--preview", metavar="KLASÖR", help="sayfaları PNG olarak bu klasöre yaz")
    args = ap.parse_args()

    meta = yaml.safe_load((REPORT / "meta.yaml").read_text(encoding="utf-8"))
    sources = yaml.safe_load((REPORT / "sources.yaml").read_text(encoding="utf-8"))
    PDF_DIR.mkdir(exist_ok=True)

    keys = list(DOCS) if args.docs == ["all"] else args.docs
    missing = [k for k in keys if k not in DOCS]
    if missing:
        sys.exit(f"bilinmeyen doküman: {missing}")
    keys = [k for k in keys if (REPORT / DOCS[k][0]).exists()]

    outputs = [build_single(k, meta, sources) for k in keys]
    if args.docs == ["all"]:
        outputs.append(build_full(keys, meta, sources))

    ok = True
    for pdf in outputs:
        if args.check:
            ok = check(pdf, meta) and ok
        if args.preview:
            preview(pdf, args.preview)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
