"""Extrae productos (nombre, marca, precio...) de cualquier JSON que entregue un sitio.

No depende de la API exacta de cada supermercado: recorre el JSON buscando objetos que
tengan un nombre y un precio. Así sigue funcionando aunque cambien detalles del sitio.
"""
import re
from urllib.parse import urljoin

from texto import precio_num

K_NOMBRE = ("productName", "name", "displayName", "nombre", "title", "productTitle", "itemName")
K_PRODUCTO = ("brand", "brandName", "marca", "sku", "skuId", "productId", "itemId", "ean", "image", "images",
              "imageUrl", "imageUrls", "link", "linkText", "slug", "url", "productReference", "item_id", "displayName")
RE_PRECIO = re.compile(r"(price|precio|valor)", re.I)
RE_NO = re.compile(r"(list|regular|normal|old|before|antes|tax|unit|perunit|per_unit|perkg|per100|ppum|reference|without|max|high|"
                   r"card|tarjeta|tlmc|socio|club|member|cmr|cencosud|installment|cuota|shipping|despacho|discount|"
                   r"descuento|saving|ahorro|percent|range|min)", re.I)
RE_LISTA = re.compile(r"(list|regular|normal|old|before|antes|withoutdiscount|high)", re.I)
RE_IMG = re.compile(r"\.(jpe?g|png|webp)(\?|$)", re.I)


def _precios(d, prof=0, out=None):
    """Junta (clave, valor) de precios dentro de d (anidado hasta 6 niveles)."""
    if out is None:
        out = []
    if prof > 6:
        return out
    if isinstance(d, dict):
        for k, val in d.items():
            if isinstance(val, (dict, list)):
                if isinstance(val, list) and len(val) > 8:
                    continue
                _precios(val, prof + 1, out)
            elif RE_PRECIO.search(k):
                pv = precio_num(val)
                if pv and 50 <= pv <= 2_000_000:
                    out.append((k, pv))
    elif isinstance(d, list):
        for x in d[:8]:
            _precios(x, prof + 1, out)
    return out


def _texto(val):
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, dict):
        for k in ("name", "nombre", "value", "text"):
            if isinstance(val.get(k), str):
                return val[k].strip()
    if isinstance(val, list) and val:
        return _texto(val[0])
    return ""


def _imagen(d, prof=0):
    if prof > 3:
        return ""
    if isinstance(d, dict):
        for k, val in d.items():
            if "image" in k.lower() or "img" in k.lower() or k in ("src", "url", "imageUrl"):
                if isinstance(val, str) and (RE_IMG.search(val) or "image" in val):
                    return val
            if isinstance(val, (dict, list)) and ("image" in k.lower() or "img" in k.lower() or k == "items"):
                r = _imagen(val, prof + 1)
                if r:
                    return r
    elif isinstance(d, list):
        for x in d[:3]:
            r = _imagen(x, prof + 1)
            if r:
                return r
    return ""


def _url(d, base):
    for k in ("link", "url", "href", "productUrl", "linkText", "slug", "uri"):
        val = d.get(k)
        if isinstance(val, str) and val and not RE_IMG.search(val):
            if k in ("linkText", "slug") and not val.startswith(("/", "http")):
                val = "/" + val + "/p"
            return urljoin(base, val)
    return ""


def img_ok(u):
    """Solo direcciones http(s) cortas (descarta imágenes incrustadas o de relleno)."""
    return u if isinstance(u, str) and u.startswith(("http://", "https://", "//")) and len(u) < 400 else ""


def producto(d, base=""):
    nombre = ""
    for k in K_NOMBRE:
        if isinstance(d.get(k), str):
            nombre = d[k].strip()
            break
    if not (3 <= len(nombre) <= 200) or not any(k in d for k in K_PRODUCTO):
        return None
    pares = _precios(d)
    venta = [v for k, v in pares if not RE_NO.search(k)]
    lista = [v for k, v in pares if RE_LISTA.search(k)]
    if not venta:
        return None
    precio = min(venta)
    normal = max(lista + venta) if (lista or len(venta) > 1) else None
    marca = ""
    for k in ("brand", "brandName", "marca", "Brand"):
        if k in d:
            marca = _texto(d[k])
            if marca:
                break
    return {
        "nombre": nombre,
        "marca": marca[:40],
        "precio": int(round(precio)),
        "normal": int(round(normal)) if normal and normal > precio else None,
        "url": _url(d, base),
        "img": img_ok(urljoin(base, _imagen(d)) if _imagen(d).startswith("/") else _imagen(d)),
    }


def recorrer(obj, prof=0):
    if prof > 14:
        return
    if isinstance(obj, dict):
        yield obj
        for val in obj.values():
            if isinstance(val, (dict, list)):
                yield from recorrer(val, prof + 1)
    elif isinstance(obj, list):
        for x in obj:
            if isinstance(x, (dict, list)):
                yield from recorrer(x, prof + 1)


def de_json(obj, base=""):
    vistos, res = set(), []
    for d in recorrer(obj):
        p = producto(d, base)
        if not p:
            continue
        clave = (p["nombre"].lower(), p["precio"])
        if clave in vistos:
            continue
        vistos.add(clave)
        res.append(p)
    # quita duplicados por nombre (p.ej. el producto y su SKU interno con el mismo nombre)
    por_nombre = {}
    for p in res:
        k = p["nombre"].lower()
        if k not in por_nombre or (p["marca"] and not por_nombre[k]["marca"]):
            por_nombre[k] = p
    return list(por_nombre.values())


def de_jsonld(obj, base=""):
    """schema.org Product / ItemList dentro de <script type=application/ld+json>."""
    res = []
    for d in recorrer(obj):
        if str(d.get("@type", "")).lower() == "product" and d.get("name"):
            off = d.get("offers") or {}
            if isinstance(off, list):
                off = off[0] if off else {}
            pv = precio_num(off.get("price") or off.get("lowPrice"))
            if pv:
                res.append({"nombre": d["name"].strip(), "marca": _texto(d.get("brand"))[:40], "precio": int(pv),
                            "normal": None, "url": urljoin(base, d.get("url") or ""),
                            "img": img_ok(_texto(d.get("image")))})
    return res


# Extracción desde la página ya dibujada, si el JSON no sirvió.
JS_DOM = r"""
() => {
  const rePrecio = /\$\s?\d{1,3}(?:\.\d{3})+|\$\s?\d{3,4}(?!\d)/;
  const out = [], vistos = new Set();
  const hojas = [...document.querySelectorAll('body *')].filter(e =>
      e.children.length === 0 && rePrecio.test(e.textContent || '') && (e.textContent || '').length < 40);
  for (const h of hojas) {
    let card = h;
    for (let i = 0; i < 8 && card; i++) {
      card = card.parentElement;
      if (!card) break;
      const a = card.querySelector('a[href]'), img = card.querySelector('img');
      const txt = (card.innerText || '').trim();
      if (a && img && txt.length > 15 && txt.length < 600) {
        if (vistos.has(card)) break;
        vistos.add(card);
        const lineas = txt.split('\n').map(s => s.trim()).filter(Boolean);
        const precios = lineas.filter(s => rePrecio.test(s)).map(s => (s.match(rePrecio) || [''])[0]);
        const nombre = lineas.filter(s => !/\$/.test(s) && !/agregar|añadir|oferta|despacho|%/i.test(s))
                             .sort((x, y) => y.length - x.length)[0] || '';
        out.push({nombre, precios, url: a.href, img: [img.getAttribute('data-src'), img.currentSrc, img.src, (img.getAttribute('srcset') || '').split(' ')[0]].find(u => u && /^https?:/.test(u)) || '',
                  marca: (lineas.find(s => s === s.toUpperCase() && s.length > 1 && s.length < 30 && !/\$/.test(s)) || '')});
        break;
      }
    }
  }
  return out;
}
"""


def de_dom(items):
    res = []
    for it in items or []:
        nums = [precio_num(x) for x in it.get("precios", [])]
        nums = [n for n in nums if n and 50 <= n <= 2_000_000]
        if not nums or len(it.get("nombre", "")) < 4:
            continue
        res.append({"nombre": it["nombre"][:200], "marca": (it.get("marca") or "")[:40], "precio": int(min(nums)),
                    "normal": int(max(nums)) if max(nums) > min(nums) else None,
                    "url": it.get("url", ""), "img": img_ok(it.get("img", ""))})
    return res
