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
RE_ESCALA = re.compile(r"(step|tier|escala|volume|mayorista|bulk|cantidad)", re.I)
RE_IMG = re.compile(r"\.(jpe?g|png|webp)(\?|$)", re.I)


def _precios(d, prof=0, out=None):
    """Junta (clave, valor) de precios dentro de d (anidado hasta 6 niveles)."""
    if out is None:
        out = []
    if prof > 6:
        return out
    if isinstance(d, dict):
        for k, val in d.items():
            if isinstance(val, list) and val and all(isinstance(x, (str, int, float)) for x in val[:3]) and RE_PRECIO.search(k):
                pv = precio_num(val[0])
                if pv and 50 <= pv <= 2_000_000:
                    out.append((k, pv))
                continue
            if isinstance(val, (dict, list)):
                if isinstance(val, list) and len(val) > 8:
                    continue
                if RE_ESCALA.search(k):  # precios por cantidad (lleva 3, paga menos): no son el precio normal
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
            if isinstance(x, str) and RE_IMG.search(x):
                return x
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


RE_MINQ = re.compile(r"(min|cant|quant|desde|from|units|qty)", re.I)


def _escalas(d, prof=0):
    """Precios por cantidad: lista de (cantidad mínima, precio unitario)."""
    res = []
    if prof > 3 or not isinstance(d, dict):
        return res
    for k, val in d.items():
        if RE_ESCALA.search(k) and isinstance(val, list):
            for e in val[:6]:
                if not isinstance(e, dict):
                    continue
                q = next((int(v) for kk, v in e.items() if RE_MINQ.search(kk) and isinstance(v, (int, float)) and 1 <= v <= 100), None)
                pr = [precio_num(v) for kk, v in e.items() if RE_PRECIO.search(kk) and not re.search(r"ppum|unit|per", kk, re.I)]
                pr = [x for x in pr if x and 50 <= x <= 2_000_000]
                if q and pr:
                    res.append((q, int(min(pr))))
        elif isinstance(val, dict):
            res += _escalas(val, prof + 1)
        elif isinstance(val, list):
            for x in val[:4]:
                res += _escalas(x, prof + 1)
    return res


def ordenar_escalas(precio, escalas):
    """Deja el precio normal y hasta 3 escalas [cantidad mínima, precio c/u] más baratas que ese precio."""
    # q = 1 es un precio especial por unidad (precio socio o promoción); se guarda aparte del precio normal
    mejor = {}
    for q, p in escalas:
        q = max(1, q)
        if p < precio and (q not in mejor or p < mejor[q]):
            mejor[q] = p
    lista, ultimo = [], precio
    for q in sorted(mejor):
        if mejor[q] < ultimo:
            lista.append([q, mejor[q]])
            ultimo = mejor[q]
    return precio, lista[:3]


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
    precio, escalas = ordenar_escalas(precio, _escalas(d))
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
        "escalas": escalas or None,
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
  const reUnidad = /(x|por|\/)\s*(kg|kilo|lt?|litro|un|unidad|100\s*(g|ml|gr))\b|c\/u/i;
  const out = [], vistos = new Set();
  const hojas = [...document.querySelectorAll('body *')].filter(e =>
      e && e.children && e.children.length === 0 && rePrecio.test(e.textContent || '') && (e.textContent || '').length < 40);
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
        const precios = lineas.filter(s => rePrecio.test(s) && !reUnidad.test(s)).map(s => (s.match(rePrecio) || [''])[0]);
        let nombre = lineas.filter(s => !/\$/.test(s) && !/agregar|añadir|oferta|despacho|%/i.test(s))
                             .sort((x, y) => y.length - x.length)[0] || '';
        // Si el sitio corta el nombre con "…", se usa el título del enlace o de la imagen
        const completo = [a.getAttribute('title'), img.getAttribute('alt'), a.getAttribute('aria-label')].filter(Boolean).sort((x, y) => y.length - x.length)[0] || '';
        if (completo.length > nombre.replace(/(\.\.\.|…)$/, '').length && !/\$/.test(completo)) nombre = completo;
        nombre = nombre.replace(/\s*(\.\.\.|…)$/, '');
        // Escalas: "Lleva 3 x $3.300", o "Desde 2 un" seguido de "$6.490" "c/u" en líneas separadas
        const escalas = [];
        for (let i = 0; i < lineas.length; i++) {
          const s = lineas[i];
          if (/desde\s*\d+\s*un/i.test(s) && !/\$/.test(s)) {
            const j = lineas.slice(i + 1, i + 3).findIndex(x => rePrecio.test(x));
            if (j >= 0) escalas.push(s + ' ' + lineas[i + 1 + j] + ' ' + (lineas[i + 2 + j] || ''));
          } else if (/\d+\s*(x|por|o\s*m[aá]s|un\.?|unidades)\b[^$]{0,25}\$\s?\d/i.test(s) && !reUnidad.test(s.replace(/c\/u/i, ''))) escalas.push(s);
        }
        out.push({nombre, precios, escalas, url: a.href, img: [img.getAttribute('data-src'), img.currentSrc, img.src, (img.getAttribute('srcset') || '').split(' ')[0]].find(u => u && /^https?:/.test(u)) || '',
                  marca: (lineas.find(s => s === s.toUpperCase() && s.length > 1 && s.length < 30 && !/[$%\d]/.test(s) && !/^(nuevo|oferta|agotado|exclusivo)/i.test(s)) || '')});
        break;
      }
    }
  }
  return out;
}
"""


RE_ESC_TXT = re.compile(r"(\d+)\s*(?:x|por|o\s*m[aá]s|un\.?|unidades)\b[^$]{0,25}\$\s?([\d.]+)(.*)", re.I)


def escalas_texto(lineas, precio):
    res = []
    for t in lineas or []:
        m = RE_ESC_TXT.search(t)
        if not m:
            continue
        q, total = int(m.group(1)), precio_num(m.group(2))
        if not total or not 1 <= q <= 50 or (q == 1 and not re.search(r"desde", t, re.I)):
            continue
        unit = total if re.search(r"c/u|cada|unidad", m.group(3) + t, re.I) or total < precio else total / q
        res.append((q, int(round(unit))))
    return res


def de_dom(items):
    res = []
    for it in items or []:
        nums = [precio_num(x) for x in it.get("precios", [])]
        nums = [n for n in nums if n and 50 <= n <= 2_000_000]
        if not nums or len(it.get("nombre", "")) < 4:
            continue
        esc = escalas_texto(it.get("escalas"), max(nums))
        # los montos que aparecen en textos de "lleva N" (total o c/u) no son el precio de 1 unidad
        en_esc = {u for _, u in esc}
        for t in it.get("escalas") or []:
            en_esc |= {precio_num(x) for x in re.findall(r"\$\s?[\d.]+", t)}
        solo = [n for n in nums if n not in en_esc]
        if esc and not solo:
            continue  # solo se ve el precio de promoción por cantidad: no se sabe el de 1 unidad
        nums = solo or nums
        precio, escalas = ordenar_escalas(int(min(nums)), esc)
        res.append({"nombre": it["nombre"][:200], "marca": (it.get("marca") or "")[:40], "precio": precio,
                    "escalas": escalas or None,
                    "normal": int(max(nums)) if max(nums) > precio else None,
                    "url": it.get("url", ""), "img": img_ok(it.get("img", ""))})
    return res
