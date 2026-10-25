# SavingRat · precios

Este repositorio busca cada día los precios de Lider, aCuenta, Jumbo, Santa Isabel y Alvi
para la app **SavingRat**, y los deja en `data/precios.json`.

- `catalogo.json`: categorías, productos y variantes que se buscan (se puede editar aquí mismo en GitHub).
- `tiendas.json`: dirección de búsqueda de cada supermercado.
- `scraper/`: el programa que busca los precios.
- `.github/workflows/precios.yml`: lo hace correr todos los días a las 06:17.

## Revisar si funciona

Pestaña **Actions → Actualizar precios → Run workflow**.
- Con "Solo prueba" marcado, revisa 3 productos por supermercado y guarda capturas en `data/debug/`
  y un resumen en `data/diagnostico.json`.
- Sin marcar, hace la búsqueda completa (unos 20 a 40 minutos).

Si un supermercado falla, sus precios anteriores se conservan y la app los muestra como antiguos.
