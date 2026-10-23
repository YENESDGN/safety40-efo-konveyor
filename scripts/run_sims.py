#!/usr/bin/env python3
"""Simülasyonları çalıştırır, grafikleri üretir ve her lab'ın pytest çıktısını kaydeder.

Kullanım (repo kökünden):
    python scripts/run_sims.py            # tüm lab'lar
    python scripts/run_sims.py lab1 lab3  # seçilenler

Çıktılar efo_sim/out/ altına yazılır:
    labN_*.png, labN_sonuclar.md      model çıktıları (PDF'e bu dosyalardan girer)
    pytest_labN.txt                   pytest -v çıktısı
    labN_testler.md                   geçti/kaldı tablosu (junit XML'den)
"""
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "efo_sim" / "out"
LABS = {
    "lab1": ("efo_sim.lab1_safety", ["test_params.py", "test_lab1_safety.py"]),
    "lab2": ("efo_sim.lab2_zones", ["test_lab2_zones.py"]),
    "lab3": ("efo_sim.lab3_risk", ["test_lab3_risk.py"]),
    "lab4": ("efo_sim.lab4_attack", ["test_lab4_attack.py"]),
}


def test_tablosu(xml_path):
    """junit XML → parametreli testleri gruplayan geçti/kaldı tablosu (markdown)."""
    gruplar = OrderedDict()
    for case in ET.parse(xml_path).getroot().iter("testcase"):
        ad = re.sub(r"\[.*\]$", "", case.get("name"))
        dosya = case.get("classname").split(".")[-1]
        if case.find("failure") is not None or case.find("error") is not None:
            sonuc = "kaldı"
        elif case.find("skipped") is not None and "xfail" in (case.find("skipped").get("type", "") +
                                                              case.find("skipped").get("message", "")):
            sonuc = "beklenen kalma"
        elif case.find("skipped") is not None:
            sonuc = "atlandı"
        else:
            sonuc = "geçti"
        param = re.search(r"\[(.*)\]$", case.get("name"))
        g = gruplar.setdefault((dosya, ad), {})
        g.setdefault(sonuc, []).append(param.group(1) if param else "")
    satirlar = ["| # | Test (dosya) | Sonuç |", "|---|---|---|"]
    for i, ((dosya, ad), sayac) in enumerate(gruplar.items(), 1):
        parca = []
        for sonuc in ("geçti", "beklenen kalma", "kaldı", "atlandı"):
            if sonuc in sayac:
                n, toplam = len(sayac[sonuc]), sum(len(v) for v in sayac.values())
                etiket = {"geçti": "✔ geçti", "beklenen kalma": "✖ kaldı (beklenen)",
                          "kaldı": "**✖ KALDI**", "atlandı": "atlandı"}[sonuc]
                metin = etiket + (f" ({n}/{toplam})" if toplam > 1 else "")
                if sonuc != "geçti" and any(sayac[sonuc]):
                    metin += ": " + ", ".join(f"`{x}`" for x in sayac[sonuc])
                parca.append(metin)
        satirlar.append(f"| {i} | `{ad}` ({dosya}) | {', '.join(parca)} |")
    return "\n".join(satirlar) + "\n"


def calistir(lab):
    modul, testler = LABS[lab]
    subprocess.run([sys.executable, "-m", modul], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    xml = OUT / f"pytest_{lab}.xml"
    sonuc = subprocess.run(
        [sys.executable, "-m", "pytest", *[f"efo_sim/tests/{t}" for t in testler], "-v",
         "--junitxml", str(xml), "-o", "junit_family=xunit1"],
        cwd=ROOT, capture_output=True, text=True)
    metin = re.sub(r"\n-+ generated xml file.*?-+\n", "\n", sonuc.stdout, flags=re.S)
    (OUT / f"pytest_{lab}.txt").write_text(metin, encoding="utf-8")
    (OUT / f"{lab}_testler.md").write_text(test_tablosu(xml), encoding="utf-8")
    xml.unlink()
    son = metin.strip().splitlines()[-1]
    print(f"{lab}: {son}")
    return sonuc.returncode == 0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    secim = sys.argv[1:] or list(LABS)
    ok = all([calistir(lab) for lab in secim if (ROOT / "efo_sim" / f"{LABS[lab][0].split('.')[-1]}.py").exists()])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
