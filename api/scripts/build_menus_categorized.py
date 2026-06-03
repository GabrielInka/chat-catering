"""
Normaliza api/menus.json:
- id en menú y en cada tramo
- por_categoria: cada categoría (frio | caliente | dulce | otro) aparece como máximo un bloque,
  con "lineas" (array de strings "N x ..."). Solo se incluyen categorías con al menos una línea.
- canapes en cada tramo (total de piezas)

Acepta entrada con incluye+categorias, incluye+objetos {linea,categoria}, o ya con por_categoria.

Regenera api/menus_compact.json.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MENUS_IN = ROOT / "menus.json"
MENUS_OUT = ROOT / "menus.json"
MENUS_COMPACT_OUT = ROOT / "menus_compact.json"

CATEGORIA_ORDEN = ("frio", "caliente", "dulce", "otro")


def slugify(text: str) -> str:
    s = unicodedata.normalize("NFKD", text)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "menu"


qty_prefix = re.compile(r"^\d+\s*x\s*", re.I)


def base_linea(linea: str) -> str:
    return qty_prefix.sub("", linea).strip()


def classify_item(base: str) -> str:
    s = base.strip()
    sl = s.lower()

    if s == "No disponible":
        return "otro"
    if "termo" in sl:
        return "otro"
    if sl.startswith("zumo ") or "agua 35" in sl:
        return "otro"

    if "gr nachos" in sl or "gr queso" in sl:
        return "frio"

    if "relleno" in sl and "croissant" in sl:
        return "frio"
    if sl == "croissants" or (sl.startswith("croissants") and "relleno" not in sl):
        return "dulce"

    if "brochetas de fruta" in sl:
        return "dulce"
    if "surtidos de macaron" in sl:
        return "dulce"

    if any(
        k in sl
        for k in (
            "brownies",
            "profiteroles",
            "piruleta",
            "piruletas infantiles",
            "mini magdalenas",
            "napolitanas",
            "palmeritas",
            "bizcocho de calabaza",
        )
    ):
        return "dulce"

    if "macaron" in sl and "foie" in sl:
        return "frio"

    if "bombones de queso" in sl:
        return "frio"

    if "mini patatas asadas" in sl:
        return "caliente"

    if any(
        k in sl
        for k in (
            "croquetas",
            "buñuelos",
            "nuggets",
            "merluza rebozada",
            "mini pizzas",
            "hamburguesita",
            "emapana",
            "empanadilla",
            "empanada de",
            "empanadillas",
            "huevos escoceses",
            "rollitos de morcilla",
            "rollitos de pasta brick",
            "rollitos de verduritas",
            "mini quiche",
            "mini quiches",
        )
    ):
        return "caliente"

    return "frio"


def tramo_id(menu_id: str, tipo_slug: str, comensales: int) -> str:
    return f"{menu_id}-{tipo_slug}-{comensales}"


def iter_lineas_categorias(tr: dict):
    """Produce (linea, categoria) en orden de recorrido del tramo."""
    por = tr.get("por_categoria") or tr.get("incluye_por_categoria")
    if por:
        for bloque in por:
            cat = str(bloque.get("categoria", "frio"))
            if cat not in CATEGORIA_ORDEN:
                cat = "frio"
            for linea in bloque.get("lineas", []):
                if isinstance(linea, str) and linea.strip():
                    yield linea.strip(), cat
        return

    incluye = tr.get("incluye", [])
    cats = tr.get("categorias", [])

    for i, x in enumerate(incluye):
        if isinstance(x, str):
            linea = x
            cat = cats[i] if i < len(cats) else classify_item(base_linea(linea))
        elif isinstance(x, dict) and "linea" in x:
            linea = str(x["linea"])
            cat = str(x.get("categoria") or classify_item(base_linea(linea)))
        else:
            continue
        yield linea, cat


def build_por_categoria(pairs: list[tuple[str, str]]) -> list[dict]:
    buckets: dict[str, list[str]] = {k: [] for k in CATEGORIA_ORDEN}
    for linea, cat in pairs:
        c = cat if cat in buckets else "frio"
        buckets[c].append(linea)
    return [{"categoria": k, "lineas": buckets[k]} for k in CATEGORIA_ORDEN if buckets[k]]


def transform_menus(data: list) -> list:
    used_slugs: dict[str, int] = {}
    out: list = []

    for menu in data:
        nombre = menu.get("nombre", "")
        menu_slug = slugify(nombre)
        if menu_slug in used_slugs:
            used_slugs[menu_slug] += 1
            menu_id = f"{menu_slug}-{used_slugs[menu_slug]}"
        else:
            used_slugs[menu_slug] = 0
            menu_id = menu_slug

        tipos_out = []
        for tm in menu.get("tipos_menu", []):
            tipo_nombre = tm.get("tipo", "")
            tipo_slug = slugify(tipo_nombre)
            tramos_out = []
            for tr in tm.get("tramos", []):
                comensales = int(tr.get("comensales", 0))
                pairs = list(iter_lineas_categorias(tr))
                por_categoria = build_por_categoria(pairs)

                tramos_out.append(
                    {
                        **{
                            k: v
                            for k, v in tr.items()
                            if k
                            not in (
                                "incluye",
                                "categorias",
                                "por_categoria",
                                "incluye_por_categoria",
                                "id",
                            )
                        },
                        "id": tramo_id(menu_id, tipo_slug, comensales),
                        "por_categoria": por_categoria,
                    }
                )
            tipos_out.append({**tm, "tramos": tramos_out})

        base_menu = {k: v for k, v in menu.items() if k not in ("tipos_menu", "id")}
        out.append({**base_menu, "id": menu_id, "tipos_menu": tipos_out})
    return out


def build_compact(data: list) -> list:
    compact: list = []
    for m in data:
        mid = m["id"]
        for tm in m.get("tipos_menu", []):
            tipo = tm.get("tipo", "")
            tipo_slug = slugify(tipo)
            for tr in tm.get("tramos", []):
                comensales = tr.get("comensales")
                plantilla: list = []
                for linea, cat in iter_lineas_categorias(tr):
                    mqty = re.match(r"^(\d+)\s*x\s*", linea, re.I)
                    u_por_comensal = (
                        int(mqty.group(1)) // int(comensales)
                        if mqty and comensales and int(comensales) > 0
                        else None
                    )
                    plantilla.append(
                        {
                            "texto_base": base_linea(linea),
                            "categoria": cat,
                            "unidades_por_comensal": u_por_comensal,
                        }
                    )
                compact.append(
                    {
                        "menu_id": mid,
                        "menu_nombre": m.get("nombre"),
                        "tipo_menu": tipo,
                        "tipo_menu_slug": tipo_slug,
                        "tramo_id": tr.get("id"),
                        "comensales": comensales,
                        "canapes": tr.get("canapes"),
                        "precio_eur": tr.get("precio_eur"),
                        "items_plantilla": plantilla,
                    }
                )
    return compact


def main() -> None:
    raw = json.loads(MENUS_IN.read_text(encoding="utf-8"))
    transformed = transform_menus(raw)

    MENUS_OUT.write_text(
        json.dumps(transformed, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    compact = build_compact(transformed)
    MENUS_COMPACT_OUT.write_text(
        json.dumps(compact, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {MENUS_OUT} ({len(transformed)} menus)")
    print(f"Wrote {MENUS_COMPACT_OUT} ({len(compact)} tramos)")


if __name__ == "__main__":
    main()
