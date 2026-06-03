import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
pat = re.compile(r"^\d+\s*x\s*", re.I)

with open(ROOT / "menus.json", encoding="utf-8") as f:
    data = json.load(f)

def lineas_de_tramo(tr):
    por = tr.get("por_categoria") or tr.get("incluye_por_categoria")
    if por:
        for bloque in por:
            for line in bloque.get("lineas", []):
                if isinstance(line, str) and line.strip():
                    yield line.strip()
        return
    for x in tr.get("incluye", []):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict) and "linea" in x:
            yield x["linea"]


items = sorted(
    {
        pat.sub("", line).strip()
        for m in data
        for tm in m.get("tipos_menu", [])
        for tr in tm.get("tramos", [])
        for line in lineas_de_tramo(tr)
    }
)

out = ROOT / "_unique_items.txt"
out.write_text("\n".join(items), encoding="utf-8")
print(f"Wrote {len(items)} lines to {out}")
