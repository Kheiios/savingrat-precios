"""Busca los precios de cada variante del catálogo en cada supermercado y escribe data/precios.json.

Uso:
  python scraper/buscar.py            búsqueda completa (la que corre cada día)
  python scraper/buscar.py --prueba   3 productos por súper + diagnóstico con capturas
  python scraper/buscar.py --tiendas lider,alvi --max 10
"""
import argparse
import asyncio
import datetime as dt
import json
import os
import random
import re
import sys
import time
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraer import JS_DOM, de_dom, de_json, de_jsonld  # noqa: E402
from texto import cantidad, cumple  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("DATA_DIR") or os.path.join(BASE, "data")
MAX_POR_TIENDA = 12
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0.0.0 Safari/537.36")
RE_BLOQUEO = re.compile(r"access denied|just a moment|robot|captcha|forbidden|attention required|blocked", re.I)
PRUEBA = ["leche-entera", "arroz-g2", "papel-higienico"]


def ahora():
    return dt.datetime.now(dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=-3))).isoformat(timespec="minutes")


def variantes(catalogo):
    for c in catalogo["categorias"]:
        for p in c["p"]:
            for v in p["v"]:
                yield v


class Buscador:
    def __init__(self, tid, cfg, ctx, depurar=False):
        self.tid, self.cfg, self.ctx, self.depurar = tid, cfg, ctx, depurar
        self.plantilla = None
        self.diag = []
        self.page = None

    async def abrir(self):
        self.page = await self.ctx.new_page()

        async def ruta(route):
            if route.request.resource_type in ("image", "media", "font"):
                await route.abort()
            else:
                await route.continue_()
        await self.page.route("**/*", ruta)

    async def _una(self, url, q):
        page, cuerpos, tareas = self.page, [], []

        async def tomar(resp):
            try:
                ct = resp.headers.get("content-type", "")
                if resp.status != 200 or "json" not in ct or resp.request.resource_type not in ("xhr", "fetch"):
                    return
                largo = int(resp.headers.get("content-length") or 0)
                if largo > 8_000_000:
                    return
                cuerpos.append((resp.url, await resp.json()))
            except Exception:
                pass

        def al_responder(resp):
            tareas.append(asyncio.ensure_future(tomar(resp)))

        page.on("response", al_responder)
        d = {"q": q, "url": url}
        try:
            r = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            d["estado"] = r.status if r else None
            try:
                await page.wait_for_load_state("networkidle", timeout=12000)
            except Exception:
                pass
            await page.mouse.wheel(0, 2500)
            await page.wait_for_timeout(1500)
            if tareas:
                await asyncio.wait(tareas, timeout=10)
            d["final"] = page.url
            d["titulo"] = (await page.title())[:120]
            html = await page.content()
            productos = []
            for u, cuerpo in cuerpos:
                productos += de_json(cuerpo, page.url)
            # JSON incrustado en la página (Next.js, estado inicial, schema.org)
            for m in re.finditer(r'<script[^>]*(?:id="__NEXT_DATA__"|type="application/(?:ld\+)?json")[^>]*>(.*?)</script>', html, re.S):
                try:
                    obj = json.loads(m.group(1))
                    # schema.org primero: trae marca y foto
                    productos = de_jsonld(obj, page.url) + productos + de_json(obj, page.url)
                except Exception:
                    pass
            d["json_urls"] = [u[:160] for u, _ in cuerpos][:20]
            d["n_json"] = len(productos)
            if len(productos) < 3:
                dom = de_dom(await page.evaluate(JS_DOM))
                d["n_dom"] = len(dom)
                productos += dom
            if RE_BLOQUEO.search(d["titulo"]) and not productos:
                d["error"] = "bloqueado: " + d["titulo"]
            vistos, unicos = {}, []
            for p in productos:
                k = (p["nombre"].lower(), p["precio"])
                if k not in vistos:
                    vistos[k] = p
                    unicos.append(p)
                else:  # completa marca, foto o enlace que le falten
                    for campo in ("marca", "img", "url"):
                        if not vistos[k].get(campo) and p.get(campo):
                            vistos[k][campo] = p[campo]
            d["n"] = len(unicos)
            d["muestra"] = [f'{p["nombre"]} | {p["marca"]} | ${p["precio"]}' + (f' | escalas {p["escalas"]}' if p.get("escalas") else '') for p in unicos[:5]]
            if self.depurar:
                os.makedirs(os.path.join(DATA, "debug"), exist_ok=True)
                base = os.path.join(DATA, "debug", f"{self.tid}-{re.sub(r'[^a-z0-9]+', '-', q)}")
                try:
                    await page.screenshot(path=base + ".png", full_page=False)
                except Exception:
                    pass
                with open(base + ".html", "w", encoding="utf-8") as f:
                    f.write(html[:400_000])
            return unicos, d
        except Exception as e:
            d["error"] = f"{type(e).__name__}: {str(e)[:200]}"
            return [], d
        finally:
            page.remove_listener("response", al_responder)

    async def buscar(self, q):
        if self.plantilla:
            prods, d = await self._una(self.plantilla.replace("{q}", quote(q)), q)
            self.diag.append(d)
            return prods
        for plantilla in self.cfg["buscar"]:
            prods, d = await self._una(plantilla.replace("{q}", quote(q)), q)
            self.diag.append(d)
            if prods:
                self.plantilla = plantilla
                return prods
        return []


def ordenar(lista, u):
    def clave(x):
        cant = x[4]
        return (x[2] / cant) if cant else x[2] * 1e6
    return sorted(lista, key=clave)


async def correr_tienda(tid, cfg, browser, vars_, depurar, salida, resumen):
    ctx = await browser.new_context(user_agent=UA, locale="es-CL", timezone_id="America/Santiago",
                                    viewport={"width": 1366, "height": 900})
    await ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
    b = Buscador(tid, cfg, ctx, depurar)
    await b.abrir()
    ok, t0, fallos_seguidos = 0, time.time(), 0
    for i, v in enumerate(vars_):
        prods = await b.buscar(v["q"])
        filas = []
        for p in prods:
            if not cumple(p["nombre"], v):
                continue
            cant = cantidad(p["nombre"], v["u"])
            fila = [p["nombre"], p["marca"], p["precio"], p["normal"], cant, p["url"], p["img"]]
            if p.get("escalas"):
                fila.append(p["escalas"])  # [[cantidad mínima, precio c/u], ...]
            filas.append(fila)
        if filas:
            ok += 1
            salida.setdefault(v["id"], {})[tid] = ordenar(filas, v["u"])[:MAX_POR_TIENDA]
        fallos_seguidos = 0 if prods else fallos_seguidos + 1
        print(f"[{tid}] {i + 1}/{len(vars_)} {v['q']!r}: {len(prods)} encontrados, {len(filas)} sirven", flush=True)
        if fallos_seguidos >= 8 and ok == 0:
            print(f"[{tid}] sin resultados en 8 búsquedas seguidas; se detiene esta tienda", flush=True)
            break
        await asyncio.sleep(random.uniform(1.5, 3.5))
    errores = [d.get("error") for d in b.diag if d.get("error")]
    resumen[tid] = {"n": cfg["n"], "fecha": ahora(), "ok": ok, "total": len(vars_),
                    "plantilla": b.plantilla, "minutos": round((time.time() - t0) / 60, 1),
                    "error": errores[0] if errores and ok == 0 else None}
    await ctx.close()
    return b.diag


async def principal(args):
    from playwright.async_api import async_playwright

    with open(os.path.join(BASE, "catalogo.json"), encoding="utf-8") as f:
        catalogo = json.load(f)
    with open(os.environ.get("TIENDAS_JSON") or os.path.join(BASE, "tiendas.json"), encoding="utf-8") as f:
        tiendas = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    manuales = {k: v for k, v in tiendas.items() if v.get("auto") is False}
    tiendas = {k: v for k, v in tiendas.items() if v.get("auto") is not False}
    if args.tiendas:
        tiendas = {k: v for k, v in tiendas.items() if k in args.tiendas.split(",")}
    vars_ = list(variantes(catalogo))
    if args.prueba:
        vars_ = [v for v in vars_ if v["id"] in PRUEBA]
    if args.max:
        vars_ = vars_[: args.max]

    salida, resumen, diags = {}, {}, {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        res = await asyncio.gather(*[correr_tienda(t, c, browser, vars_, args.prueba, salida, resumen)
                                     for t, c in tiendas.items()], return_exceptions=True)
        for t, r in zip(tiendas, res):
            diags[t] = r if not isinstance(r, Exception) else [{"error": repr(r)}]
            if isinstance(r, Exception):
                resumen[t] = {"n": tiendas[t]["n"], "fecha": ahora(), "ok": 0, "total": len(vars_), "error": repr(r)[:200]}
        await browser.close()

    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "diagnostico.json"), "w", encoding="utf-8") as f:
        json.dump({"generado": ahora(), "prueba": args.prueba, "resumen": resumen, "detalle": diags},
                  f, ensure_ascii=False, indent=1)

    destino = os.path.join(DATA, "prueba.json" if args.prueba else "precios.json")
    previo = {}
    if not args.prueba and os.path.exists(destino):
        try:
            with open(destino, encoding="utf-8") as f:
                previo = json.load(f)
        except Exception:
            previo = {}
    # Si una tienda falló completa, se conservan sus precios anteriores (marcados como antiguos).
    for tid in tiendas:
        if resumen.get(tid, {}).get("ok", 0) == 0 and previo:
            for vid, porti in previo.get("v", {}).items():
                if tid in porti:
                    salida.setdefault(vid, {})[tid] = porti[tid]
            ant = previo.get("tiendas", {}).get(tid)
            if ant:
                resumen[tid] = {**ant, "antiguo": True, "error": resumen[tid].get("error")}
    for tid, info in previo.get("tiendas", {}).items():
        if tid not in resumen:
            resumen[tid] = info
            for vid, porti in previo.get("v", {}).items():
                if tid in porti:
                    salida.setdefault(vid, {})[tid] = porti[tid]

    for tid, cfg in manuales.items():
        resumen[tid] = {"n": cfg["n"], "manual": True, "nota": cfg.get("nota", "")}
    with open(destino, "w", encoding="utf-8") as f:
        json.dump({"generado": ahora(), "tiendas": resumen, "v": salida}, f, ensure_ascii=False, separators=(",", ":"))
    print("\nResumen:")
    for t, r in resumen.items():
        if r.get("manual"):
            print(f"  {r['n']:<13} solo precios de boletas")
            continue
        print(f"  {r['n']:<13} {r.get('ok', 0):>3}/{r.get('total', 0)} variantes con precio"
              + (f"  ERROR: {r['error']}" if r.get("error") else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prueba", action="store_true")
    ap.add_argument("--tiendas", default="")
    ap.add_argument("--max", type=int, default=0)
    asyncio.run(principal(ap.parse_args()))
