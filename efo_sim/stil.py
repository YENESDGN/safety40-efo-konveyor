"""Ortak görsel dil: grafikler (matplotlib) ve diyagramlar (Mermaid) aynı paleti kullanır.

Renkler anlam taşır, süs değildir:
    kritik  = emniyet fonksiyonuna giden yol, sınır aşımı, "durdur"
    uyari   = dikkat gerektiren ama emniyeti bozmayan durum, "hemen telafi"
    iyi     = güvenli / etkilemez / sınırın altında
    bilgi   = nötr varlık, soru düğümü, ana seri
    giris   = saldırı giriş noktası
    pasif   = kapalı kenar, kesilmiş yol, uygulanmayan durum
    dmz     = IEC 62443 DMZ / ara bölge
    notr    = kurumsal ya da kapsam dışı bölge

Bu modül yalnızca görünümü belirler; modeldeki hiçbir sayı burada tutulmaz.
"""

RENK = {
    "murekkep": "#16223a",
    "ikincil": "#5b6576",
    "cizgi": "#c3c8d0",
    "izgara": "#e3e7ed",
    "zemin": "#f7f9fb",
    "kritik": "#b3261e",
    "uyari": "#e2a91c",
    "iyi": "#1f8f86",
    "bilgi": "#2a78d6",
    "giris": "#d9572e",
    "vurgu": "#7a4fd0",
    "pasif": "#9aa3b2",
    "dmz": "#8a6d1f",
    "notr": "#5b6576",
}

DOLGU = {
    "kritik": "#fdecea",
    "uyari": "#fdf6e3",
    "iyi": "#e6f3f1",
    "bilgi": "#e9f1fb",
    "giris": "#fdeee6",
    "vurgu": "#efe9fb",
    "pasif": "#f2f4f7",
    "dmz": "#fbf6e6",
    "notr": "#f7f9fb",
}

# Kategorik seriler (sıra sabit; aynı kavram her grafikte aynı rengi alır)
SERI = [RENK["bilgi"], RENK["giris"], RENK["iyi"], RENK["vurgu"], RENK["uyari"], RENK["ikincil"]]

FONT = "DejaVu Sans"


# ---------------------------------------------------------------- matplotlib
def mpl():
    """Ortak ayarlarla matplotlib.pyplot döndürür (başsız, PDF'e uygun)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": FONT,
        "font.size": 8.5,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 10,
        "axes.labelsize": 8.5,
        "axes.labelcolor": RENK["ikincil"],
        "axes.edgecolor": RENK["cizgi"],
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "axes.prop_cycle": matplotlib.cycler(color=SERI),
        "grid.color": RENK["izgara"],
        "grid.linewidth": 0.8,
        "xtick.color": RENK["ikincil"],
        "ytick.color": RENK["ikincil"],
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.frameon": False,
        "legend.fontsize": 7.5,
        "text.color": RENK["murekkep"],
        "figure.dpi": 200,
        "savefig.dpi": 200,
        "savefig.facecolor": "white",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.12,
    })
    return plt


def eksen(ax, izgara="y"):
    """Sade eksen: yalnızca istenen yönde ince ızgara."""
    if izgara:
        ax.grid(axis=izgara)
        ax.set_axisbelow(True)
    ax.tick_params(length=0)
    return ax


def sinir_cizgisi(ax, y, metin, x_metin=None, renk=None):
    """Güvenli mesafe, hedef oran gibi bir eşiği kesikli çizgi + etiketle gösterir."""
    renk = renk or RENK["kritik"]
    ax.axhline(y, color=renk, lw=1.1, ls=(0, (4, 3)))
    x0, x1 = ax.get_xlim()
    ax.text(x_metin if x_metin is not None else x0, y, f" {metin}", va="bottom", ha="left",
            fontsize=7.5, color=renk, fontweight="bold")


# ---------------------------------------------------------------- Mermaid
def classdef(ad, ton, kalin=False, kesik=False, cerceve=None):
    """Mermaid classDef satırı: ton = RENK/DOLGU anahtarı; cerceve = farklı çerçeve tonu."""
    genislik = "3px" if kalin else "1.5px"
    ek = ",stroke-dasharray:6 4" if kesik else ""
    return (f"  classDef {ad} fill:{DOLGU[ton]},stroke:{RENK[cerceve or ton]},stroke-width:{genislik},"
            f"color:{RENK['murekkep']}{ek}")


def kenar_stili(indeks, ton, kalin=False, kesik=False):
    genislik = "3px" if kalin else ("1.2px" if ton == "pasif" else "2px")
    ek = ",stroke-dasharray:5 4" if kesik else ""
    return f"  linkStyle {indeks} stroke:{RENK[ton]},stroke-width:{genislik}{ek}"


def kume_stili(kume_id, ton=None):
    """Mermaid subgraph çerçevesi: varsayılan ince gri; ton verilirse o rengin açık hâli."""
    if ton:
        return f"  style {kume_id} fill:{DOLGU[ton]},stroke:{RENK[ton]},stroke-width:1.5px,color:{RENK[ton]}"
    return f"  style {kume_id} fill:{RENK['zemin']},stroke:{RENK['cizgi']},stroke-width:1px,color:{RENK['ikincil']}"
