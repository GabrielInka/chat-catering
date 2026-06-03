"""
Genera documentación en prosa (Markdown) en api/vector_docs/ a partir de los JSON,
pensada para subir a un Vector Store de OpenAI (chunks claros, títulos descriptivos).

Uso: python api/scripts/build_vector_docs.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "vector_docs"
MENUS = ROOT / "menus.json"
FAQS = ROOT / "faqs.json"
KB = ROOT / "kb.json"
COND = ROOT / "purchase_conditions.json"
CP = ROOT / "cp.json"


def slugify(text: str) -> str:
    s = unicodedata.normalize("NFKD", text)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "doc"


def esc_md(s: str) -> str:
    return (s or "").replace("|", "\\|").strip()


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.strip() + "\n", encoding="utf-8")


def build_kb_doc() -> str:
    rules = json.loads(KB.read_text(encoding="utf-8")).get("rules", {})
    lines = [
        "---",
        "document_type: reglas_servicio",
        "source: kb.json",
        "---",
        "",
        "# Datos clave del servicio (Catering Barú / Catering en Casa)",
        "",
        "Resumen operativo para atención al cliente. Los precios de producto en conversación deben indicarse con el literal **(IVA incluido)** cuando se cite un importe en euros.",
        "",
        "## Zona y horario",
        f"- **Zona de reparto:** {rules.get('delivery_area', 'Comunidad de Madrid')}.",
        f"- **Horario habitual:** {rules.get('hours', '')}.",
        f"- **Antelación orientativa:** {rules.get('advance_notice', '')}.",
        "",
        "## Pedidos y pagos",
        f"- **Pedido mínimo (referencia interna):** {rules.get('min_order_eur', '')} €.",
        f"- **Gastos de envío desde (referencia):** desde {rules.get('delivery_from_eur', '')} € según código postal.",
        f"- **Formas de pago (resumen):** {rules.get('payment', '')}; en conversación detallar también tarjeta en web, efectivo a la entrega, transferencia y Ticket Restaurante (Sodexo/Pluxee) según instrucciones del agente.",
        "",
        "## Contacto físico",
        f"- **Dirección:** {rules.get('address', '')}.",
        f"- **Teléfono:** {rules.get('phone', '')}.",
        f"- **WhatsApp (enlace):** {rules.get('whatsapp', '')}.",
        f"- **Email pedidos/consultas:** info@cateringencasa.com",
        "",
    ]
    return "\n".join(lines)


def build_faqs_doc() -> str:
    items = json.loads(FAQS.read_text(encoding="utf-8"))
    parts = [
        "---",
        "document_type: preguntas_frecuentes",
        "source: faqs.json",
        "---",
        "",
        "# Preguntas frecuentes (Catering Barú)",
        "",
        "Cada bloque es una pregunta típica y la respuesta orientativa para el cliente.",
        "",
    ]
    for it in items:
        q = esc_md(it.get("pregunta", ""))
        a = esc_md(it.get("respuesta", ""))
        parts.append(f"## {q}")
        parts.append("")
        parts.append(a)
        parts.append("")
    return "\n".join(parts)


def build_conditions_doc() -> str:
    rows = json.loads(COND.read_text(encoding="utf-8"))
    parts = [
        "---",
        "document_type: condiciones_compra",
        "source: purchase_conditions.json",
        "---",
        "",
        "# Condiciones de compra (resumen para el cliente)",
        "",
        "Texto derivado de las condiciones publicadas en la web. Para el detalle legal completo, remitir siempre a la URL oficial.",
        "",
    ]
    for r in rows:
        tit = esc_md(r.get("titulo", ""))
        parts.append(f"## {tit}")
        parts.append("")
        parts.append(esc_md(r.get("resumen", "")))
        parts.append("")
        parts.append(f"*Fuente:* {r.get('url', '')}")
        parts.append("")
    return "\n".join(parts)


def build_cp_doc() -> str:
    data = json.loads(CP.read_text(encoding="utf-8"))
    valid = []
    for x in data:
        cp = str(x.get("codigo_postal", "")).strip()
        if not re.match(r"^\d{5}$", cp):
            continue
        try:
            eur = float(x.get("precio_envio_eur", 0))
        except (TypeError, ValueError):
            continue
        if eur > 200:
            continue
        valid.append((cp, x.get("ciudad", ""), eur))
    precios = [t[2] for t in valid]
    parts = [
        "---",
        "document_type: envios_codigo_postal",
        "source: cp.json",
        "---",
        "",
        "# Envíos por código postal (Comunidad de Madrid)",
        "",
        "Catering Barú realiza entregas en **Comunidad de Madrid**. El **importe exacto de envío** depende del código postal y se **calcula en la web** al introducir la dirección o el CP durante el pedido.",
        "",
        "## Datos orientativos del listado interno",
        f"- **Códigos postales con precio válido en datos:** {len(valid)}.",
    ]
    if precios:
        parts.append(f"- **Rango de gastos de envío (€) en esos datos:** desde {min(precios):.0f} € hasta {max(precios):.0f} €.")
        parts.append(
            "- **Nota:** puede haber CP con precio 0 € (recogida o promociones según configuración comercial); confirmar siempre en el checkout."
        )
    parts.extend(
        [
            "",
            "## Cómo responder al cliente",
            "- Si pregunta por un CP concreto: indicar que el coste sale **al completar el pedido en la web** con ese código postal.",
            "- Si está fuera de la Comunidad de Madrid: indicar que el servicio habitual es solo Madrid; zonas limítrofe según política (email info@cateringencasa.com).",
            "",
            "## Ejemplos (no exhaustivo)",
            "",
            "| Código postal | Municipio (dato) | Envío (€) |",
            "|---|---|---|",
        ]
    )
    for cp, ciudad, eur in sorted(valid, key=lambda t: t[0])[:25]:
        parts.append(f"| {esc_md(cp)} | {esc_md(str(ciudad))} | {eur:.0f} |")
    parts.append("")
    parts.append("*La tabla anterior es solo una muestra; no usar como listado completo.*")
    parts.append("")
    return "\n".join(parts)


def format_tramo_prose(tr: dict) -> list[str]:
    lines: list[str] = []
    com = tr.get("comensales")
    lines.append(f"- **Comensales (tramo):** {com}")
    lines.append(f"- **Total piezas (canapés / unidades del menú en datos):** {tr.get('canapes', '')}")
    lines.append(f"- **Precio del tramo:** {tr.get('precio_eur', '')} € (IVA incluido)")
    lines.append("")
    for bloque in tr.get("por_categoria") or []:
        cat = bloque.get("categoria", "")
        tit = {"frio": "Canapés fríos", "caliente": "Canapés calientes", "dulce": "Canapés dulces", "otro": "Otros productos"}.get(
            cat, cat
        )
        lines.append(f"### {tit}")
        lines.append("")
        for ln in bloque.get("lineas", []):
            lines.append(f"- {esc_md(str(ln))}")
        lines.append("")
    return lines


def build_menu_intro() -> str:
    return "\n".join(
        [
            "---",
            "document_type: catalogo_menus_intro",
            "source: menus.json",
            "---",
            "",
            "# Cómo leer el catálogo de menús (Catering Barú)",
            "",
            "- Los menús online van por **múltiplos de 6 personas** (salvo menús especiales descritos en su ficha).",
            '- En datos internos, **"Picoteo"** corresponde a la opción ligera; **"Para comer"** a comida o cena con más cantidad; **"General"** agrupa formatos distintos (p. ej. coffee break).',
            "- Cada menú tiene un **identificador** (`menu_id`) y enlace de compra en la documentación por menú.",
            "- Los precios citados al cliente deben llevar **(IVA incluido)**.",
            "- El detalle de **canapés por categoría** (frío / caliente / dulce / otro) está en el archivo **detalle** de cada menú, normalmente para el **tramo de 6 personas** como referencia.",
            "",
        ]
    )


def tramo_por_comensales(tramos: list, n: int) -> dict | None:
    for tr in tramos:
        if int(tr.get("comensales", 0)) == n:
            return tr
    return None


def build_menu_catalog(menus: list, tipo_filtro: str, titulo: str, slug: str) -> str:
    rows: list[tuple[str, str, float, str]] = []
    for m in menus:
        mid = m.get("id", slugify(m.get("nombre", "")))
        nombre = m.get("nombre", "")
        link = m.get("link_compra", "")
        for tm in m.get("tipos_menu", []):
            if tm.get("tipo") != tipo_filtro:
                continue
            tr = tramo_por_comensales(tm.get("tramos", []), 6)
            if not tr:
                continue
            precio = float(tr.get("precio_eur") or 0)
            rows.append((nombre, mid, precio, link))
            break
    rows.sort(key=lambda x: x[0].lower())
    parts = [
        "---",
        f"document_type: catalogo_{slug}",
        "source: menus.json",
        "---",
        "",
        f"# {titulo}",
        "",
        "Listado de menús disponibles en datos para el tipo indicado. Precio de **referencia: tramo de 6 personas** con IVA incluido.",
        "",
        "| Menú | ID | Precio 6 pax (IVA incluido) | Enlace |",
        "|---|---|---|---|",
    ]
    for nombre, mid, precio, link in rows:
        parts.append(
            f"| {esc_md(nombre)} | `{esc_md(mid)}` | {precio:.2f} € | {esc_md(link)} |"
        )
    parts.append("")
    parts.append(f"*Total menús en listado: {len(rows)}.*")
    parts.append("")
    return "\n".join(parts)


def build_menu_detail(m: dict) -> str:
    mid = m.get("id", slugify(m.get("nombre", "")))
    nombre = m.get("nombre", "")
    parts = [
        "---",
        f"menu_id: {mid}",
        "document_type: detalle_menu",
        "source: menus.json",
        "---",
        "",
        f"# {esc_md(nombre)}",
        "",
        f"**Identificador:** `{mid}`",
        "",
        f"**Enlace de pedido:** {esc_md(m.get('link_compra', ''))}",
        "",
        "## Descripción",
        "",
        esc_md(m.get("concepto", "")),
        "",
    ]
    if m.get("preguntas_contexto"):
        parts.extend(["## Notas de contexto (interno / web)", ""])
        for p in m["preguntas_contexto"]:
            parts.append(f"- {esc_md(str(p))}")
        parts.append("")
    if m.get("alergenos"):
        parts.extend(["## Alérgenos por producto (resumen en datos)", ""])
        for a in m["alergenos"]:
            prod = esc_md(str(a.get("producto", "")))
            cont = esc_md(str(a.get("contiene", "")))
            parts.append(f"- **{prod}:** {cont}")
        parts.append("")
    for tm in m.get("tipos_menu", []):
        tipo = tm.get("tipo", "")
        parts.append(f"## Modalidad: {esc_md(tipo)}")
        parts.append("")
        tr = tramo_por_comensales(tm.get("tramos", []), 6)
        if not tr:
            parts.append("*No hay tramo de 6 personas en datos para esta modalidad.*")
            parts.append("")
            continue
        parts.append(
            "Detalle del **tramo de 6 personas** (referencia). Otros tramos (12, 18…) y precios actualizados: **web de pedido**."
        )
        parts.append("")
        parts.extend(format_tramo_prose(tr))
    return "\n".join(parts)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    menus_dir = OUT / "menus"
    menus_dir.mkdir(exist_ok=True)

    write(OUT / "00_reglas_servicio.md", build_kb_doc())
    write(OUT / "01_preguntas_frecuentes.md", build_faqs_doc())
    write(OUT / "02_condiciones_de_compra.md", build_conditions_doc())
    write(OUT / "03_envios_codigo_postal.md", build_cp_doc())

    menus = json.loads(MENUS.read_text(encoding="utf-8"))
    write(menus_dir / "00_intro_catalogo_menus.md", build_menu_intro())
    write(
        menus_dir / "catalogo_picoteo.md",
        build_menu_catalog(menus, "Picoteo", "Catálogo: menús Picoteo (referencia 6 personas)", "picoteo"),
    )
    write(
        menus_dir / "catalogo_comida_cena.md",
        build_menu_catalog(
            menus,
            "Para comer",
            "Catálogo: menús Comida / Cena (referencia 6 personas)",
            "comida_cena",
        ),
    )
    write(
        menus_dir / "catalogo_general.md",
        build_menu_catalog(menus, "General", "Catálogo: menús tipo General (coffee break, etc.)", "general"),
    )

    for m in menus:
        mid = m.get("id", slugify(m.get("nombre", "")))
        write(menus_dir / f"detalle_{mid}.md", build_menu_detail(m))

    readme = "\n".join(
        [
            "# Documentación para Vector Store (OpenAI)",
            "",
            "Markdown generado desde los JSON del proyecto. **No editar a mano** los contenidos derivados; regenerar con:",
            "",
            "```bash",
            "python api/scripts/build_vector_docs.py",
            "```",
            "",
            "## Contenido",
            "",
            "| Archivo | Origen |",
            "|---|---|",
            "| `00_reglas_servicio.md` | `kb.json` |",
            "| `01_preguntas_frecuentes.md` | `faqs.json` |",
            "| `02_condiciones_de_compra.md` | `purchase_conditions.json` |",
            "| `03_envios_codigo_postal.md` | `cp.json` (resumen + muestra) |",
            "| `menus/` | `menus.json` (intro, catálogos por tipo, un detalle por menú) |",
            "",
            "## Menús",
            "",
            "- `menus/00_intro_catalogo_menus.md`: cómo interpretar tipos y tramos.",
            "- `menus/catalogo_picoteo.md`, `catalogo_comida_cena.md`, `catalogo_general.md`: tablas con precio tramo 6 pax.",
            "- `menus/detalle_<menu_id>.md`: composición por categorías para tramo de 6 personas por modalidad.",
            "",
            "`blocked_contacts.json` no se incluye: es configuración interna, no documentación de cliente.",
            "",
        ]
    )
    write(OUT / "README.md", readme)

    n_menu_docs = len(list(menus_dir.glob("detalle_*.md")))
    print(f"Wrote {OUT} (menu detail files: {n_menu_docs})")


if __name__ == "__main__":
    main()
