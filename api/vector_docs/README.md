# Documentación para Vector Store (OpenAI)

Markdown generado desde los JSON del proyecto. **No editar a mano** los contenidos derivados; regenerar con:

```bash
python api/scripts/build_vector_docs.py
```

## Contenido

| Archivo | Origen |
|---|---|
| `00_reglas_servicio.md` | `kb.json` |
| `01_preguntas_frecuentes.md` | `faqs.json` |
| `02_condiciones_de_compra.md` | `purchase_conditions.json` |
| `03_envios_codigo_postal.md` | `cp.json` (resumen + muestra) |
| `menus/` | `menus.json` (intro, catálogos por tipo, un detalle por menú) |

## Menús

- `menus/00_intro_catalogo_menus.md`: cómo interpretar tipos y tramos.
- `menus/catalogo_picoteo.md`, `catalogo_comida_cena.md`, `catalogo_general.md`: tablas con precio tramo 6 pax.
- `menus/detalle_<menu_id>.md`: composición por categorías para tramo de 6 personas por modalidad.

`blocked_contacts.json` no se incluye: es configuración interna, no documentación de cliente.
