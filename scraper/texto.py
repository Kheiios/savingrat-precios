"""Normalización de nombres, filtro por variante y lectura del formato (1 L, 900 g, 6 x 1 L...)."""
import re
import unicodedata


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("ñ", "n")
    return re.sub(r"[^a-z0-9.,]+", " ", s).strip()


def _calza(nombre_n, termino):
    """termino: 'a|b' (cualquiera). '=x' exige palabra exacta; si no, inicio de palabra."""
    for alt in termino.split("|"):
        exacta = alt.startswith("=")
        a = norm(alt[1:] if exacta else alt)
        if not a:
            continue
        pat = r"(?<![a-z0-9])" + re.escape(a) + (r"(?![a-z0-9])" if exacta else "")
        if re.search(pat, nombre_n):
            return True
    return False


def cumple(nombre, variante):
    n = norm(nombre)
    if not all(_calza(n, t) for t in variante.get("inc", [])):
        return False
    if any(_calza(n, t) for t in variante.get("exc", [])):
        return False
    return True


_UNI = {
    "kg": ("kg", 1), "kgs": ("kg", 1), "kilo": ("kg", 1), "kilos": ("kg", 1),
    "g": ("kg", 0.001), "gr": ("kg", 0.001), "grs": ("kg", 0.001), "gramos": ("kg", 0.001), "grm": ("kg", 0.001),
    "l": ("l", 1), "lt": ("l", 1), "lts": ("l", 1), "litro": ("l", 1), "litros": ("l", 1), "ltr": ("l", 1),
    "ml": ("l", 0.001), "cc": ("l", 0.001), "cm3": ("l", 0.001),
}
_NUM = r"(\d+(?:[.,]\d+)?)"
_U = r"(kgs?|kilos?|gramos|grs?|grm|g|litros?|ltr|lts?|l|ml|cc|cm3)"
_CNT = r"(?:un|und|unid|unidades|u|rollos?|paquetes?|sachets?|capsulas?|bolsitas?|bolsas?|panales|toallitas|huevos)"


def _f(x):
    return float(x.replace(",", "."))


def formato(nombre):
    """Devuelve dict con medida {'kg'|'l': cantidad total} y 'un' (unidades) si se reconocen."""
    n = norm(nombre)
    res = {}
    # pack: "6 x 1 l", "pack 6 x 200 ml", "3 un x 90 g", "12 x 1lt"
    m = re.search(r"(\d+)\s*(?:un\s*)?x\s*" + _NUM + r"\s*" + _U + r"(?![a-z])", n)
    if m:
        k, (u, f) = int(m.group(1)), _UNI[m.group(3)]
        res[u] = k * _f(m.group(2)) * f
        res["un"] = k
    else:
        m = re.search(_NUM + r"\s*" + _U + r"\s*x\s*(\d+)(?![a-z0-9])", n)
        if m:
            k, (u, f) = int(m.group(3)), _UNI[m.group(2)]
            res[u] = k * _f(m.group(1)) * f
            res["un"] = k
        else:
            m = re.search(_NUM + r"\s*" + _U + r"(?![a-z])", n)
            if m:
                u, f = _UNI[m.group(2)]
                res[u] = _f(m.group(1)) * f
    m = re.search(r"(?:pack|caja|display)\s*(?:de\s*)?(\d+)", n)
    if m and "un" not in res:
        k = int(m.group(1))
        res["un"] = k
        for u in ("kg", "l"):
            if u in res and not re.search(r"\d+\s*x", n):
                res[u] *= k
    m = re.search(r"(\d+)\s*" + _CNT + r"(?![a-z])", n)
    if m and "un" not in res:
        res["un"] = int(m.group(1))
        # "4 un de 1 l" o "4 un 1 l" → total
        for u in ("kg", "l"):
            if u in res and res["un"] > 1 and re.search(r"\d+\s*" + _CNT + r"\s*(?:de\s*|x\s*)?\d", n):
                res[u] *= res["un"]
    if "un" not in res and ("kg" in res or "l" in res):
        res["un"] = 1
    return res


def cantidad(nombre, unidad):
    """Cantidad en la unidad de comparación de la variante (l, kg o un)."""
    f = formato(nombre)
    if unidad in f and f[unidad] > 0:
        return round(f[unidad], 4)
    if unidad == "un":
        return f.get("un") or 1
    return None


def precio_num(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not re.search(r"\d", s) or len(s) > 20:
        return None
    s = re.sub(r"[^\d.,]", "", s)
    if not s:
        return None
    # formato chileno: 1.290 o 1.290,00
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    elif "," in s:
        s = s.replace(",", ".") if re.fullmatch(r"\d+,\d{1,2}", s) else s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None
