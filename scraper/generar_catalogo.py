"""Genera catalogo.json: categorías → productos → variantes.

Cada variante es lo que se busca en los supermercados:
  q    texto de búsqueda en el sitio del súper
  inc  palabras que el nombre DEBE tener (todas). "a|b" = cualquiera de ellas.
  exc  palabras que el nombre NO debe tener (ninguna).
  u    unidad para comparar: "l" (litro), "kg" o "un" (unidad)
  g    (en el producto) 1 = es un grupo; se muestra solo el nombre de la variante
  x    1 = no se incluye cuando en la lista se pide "cualquier tipo" del producto
Las palabras comparan por inicio de palabra ("descrem" calza con "descremada").
Con "=" adelante deben calzar exacta ("=sal" no calza con "salsa").

Para agregar productos se puede editar catalogo.json directamente en GitHub.
"""
import json, os

SABORES = ["chocolate", "frutilla", "vainilla", "platano", "manjar", "sabor", "cafe"]
LECHE_NO = ["condensada", "evaporada", "cabra", "almendra", "avena", "soya", "coco", "crema",
            "cultivada", "yogh", "yogur", "infantil", "formula", "cereal", "galleta", "chocolat"]


def v(id, n, q, inc, exc=(), u="un"):
    return {"id": id, "n": n, "q": q, "inc": list(inc), "exc": list(exc), "u": u}


def p(id, n, variantes):
    return {"id": id, "n": n, "v": variantes}


C = [
 {"id": "lacteos", "n": "Lácteos y huevos", "e": "🥛", "p": [
  p("leche", "Leche", [
    v("leche-entera", "Entera", "leche entera", ["leche", "entera|natural"], ["polvo", "lactosa", "descrem", "semi"] + SABORES + LECHE_NO, "l"),
    v("leche-semi", "Semidescremada", "leche semidescremada", ["leche", "semidesc|semi desc|semi-desc"], ["polvo", "lactosa"] + SABORES + LECHE_NO, "l"),
    v("leche-descremada", "Descremada", "leche descremada", ["leche", "descrem"], ["semi", "polvo", "lactosa"] + SABORES + LECHE_NO, "l"),
    v("leche-sl", "Sin lactosa", "leche sin lactosa", ["leche", "lactosa"], ["polvo"] + SABORES + LECHE_NO, "l"),
    v("leche-sl-descremada", "Sin lactosa descremada", "leche sin lactosa descremada", ["leche", "lactosa", "descrem"], ["semi", "polvo"] + SABORES + LECHE_NO, "l"),
    v("leche-sl-semi", "Sin lactosa semidescremada", "leche sin lactosa semidescremada", ["leche", "lactosa", "semi"], ["polvo"] + SABORES + LECHE_NO, "l"),
    v("leche-polvo", "En polvo", "leche en polvo", ["leche", "polvo"], ["infantil", "formula", "etapa", "chocolate", "saborizante"], "kg"),
    v("leche-sabor", "Con sabor", "leche chocolate", ["leche", "chocolate|frutilla|vainilla|platano|sabor"], ["polvo", "condensada", "galleta", "barra", "tableta"], "l"),
    v("bebida-vegetal", "Bebida vegetal", "bebida vegetal", ["bebida|leche", "almendra|avena|soya|coco|vegetal"], ["polvo", "galleta"], "l"),
  ]),
  p("yogur", "Yogur", [
    v("yogur-batido", "Batido", "yoghurt batido", ["yogh|yogur"], ["griego", "protein", "bebible", "cereal"], "kg"),
    v("yogur-griego", "Griego", "yoghurt griego", ["yogh|yogur", "griego"], [], "kg"),
    v("yogur-bebible", "Bebible", "yoghurt bebible", ["yogh|yogur", "bebible|liquido"], [], "l"),
    v("yogur-protein", "Proteína", "yoghurt protein", ["yogh|yogur", "protein"], [], "kg"),
  ]),
  p("queso", "Queso", [
    v("queso-laminado", "Laminado", "queso laminado", ["queso", "lamin|rebanad|tajad"], ["crema", "rallado"], "kg"),
    v("queso-gauda", "Gauda (trozo)", "queso gauda", ["queso", "gauda"], ["lamin", "rallado"], "kg"),
    v("queso-mantecoso", "Mantecoso", "queso mantecoso", ["queso", "mantecoso"], ["rallado"], "kg"),
    v("queso-rallado", "Rallado", "queso rallado", ["queso", "rallado"], [], "kg"),
    v("quesillo", "Quesillo / fresco", "quesillo", ["quesillo|queso fresco"], [], "kg"),
    v("queso-crema", "Queso crema", "queso crema", ["queso", "crema"], [], "kg"),
  ]),
  p("mantequilla", "Mantequilla y margarina", [
    v("mantequilla", "Mantequilla", "mantequilla", ["mantequilla"], ["mani", "galleta"], "kg"),
    v("margarina", "Margarina", "margarina", ["margarina"], [], "kg"),
  ]),
  p("crema", "Crema y otros", [
    v("crema-leche", "Crema de leche", "crema de leche", ["crema"], ["helado", "corporal", "facial", "dental", "mani", "queso"], "l"),
    v("leche-condensada", "Leche condensada", "leche condensada", ["condensada"], [], "kg"),
    v("manjar", "Manjar", "manjar", ["manjar"], ["galleta", "alfajor", "leche sabor", "yogh"], "kg"),
  ]),
  p("huevos", "Huevos", [
    v("huevos", "Cualquiera", "huevos", ["huevo"], ["chocolate", "pascua", "codorniz", "kinder", "fideo", "pasta"], "un"),
    v("huevos-blancos", "Blancos", "huevos blancos", ["huevo", "blanco"], ["chocolate", "pascua", "codorniz"], "un"),
    v("huevos-color", "De color", "huevos color", ["huevo", "color"], ["chocolate", "pascua", "codorniz"], "un"),
  ]),
 ]},
 {"id": "desayuno", "n": "Pan y desayuno", "e": "🍞", "p": [
  p("pan", "Pan", [
    v("pan-molde-blanco", "Molde blanco", "pan de molde blanco", ["pan", "molde|blanco"], ["integral", "rallado", "pita", "hamburguesa", "hot dog"], "kg"),
    v("pan-molde-integral", "Molde integral", "pan de molde integral", ["pan", "integral"], ["rallado", "pita", "galleta"], "kg"),
    v("marraqueta", "Marraqueta", "marraqueta", ["marraqueta"], [], "kg"),
    v("hallulla", "Hallulla", "hallulla", ["hallulla"], [], "kg"),
    v("pan-pita", "Pita / tortillas", "pan pita", ["pita|tortilla|wrap"], ["chips"], "kg"),
  ]),
  p("cereales", "Cereales y avena", [
    v("avena", "Avena", "avena", ["avena"], ["bebida", "leche", "galleta", "barra", "jabon", "shampoo"], "kg"),
    v("cereal", "Cereal de desayuno", "cereal", ["cereal"], ["barra", "yogh", "infantil"], "kg"),
    v("granola", "Granola", "granola", ["granola"], ["barra"], "kg"),
  ]),
  p("cafe", "Café y té", [
    v("cafe-instantaneo", "Café instantáneo", "cafe instantaneo", ["cafe"], ["capsula", "grano", "molido", "leche", "galleta", "cafetera"], "kg"),
    v("cafe-molido", "Café molido / grano", "cafe molido", ["cafe", "molido|grano"], ["capsula", "cafetera"], "kg"),
    v("cafe-capsulas", "Cápsulas", "capsulas cafe", ["capsula"], ["cafetera"], "un"),
    v("te", "Té", "te bolsitas", ["=te"], ["helado", "frio"], "un"),
    v("hierbas", "Hierbas / infusiones", "infusion hierbas", ["infusion|hierba|manzanilla|menta|boldo"], [], "un"),
    v("saborizante", "Saborizante (Milo, Nesquik)", "saborizante leche", ["saborizante|milo|nesquik|cola cao"], [], "kg"),
  ]),
  p("azucar", "Azúcar y endulzante", [
    v("azucar", "Azúcar", "azucar", ["azucar"], ["flor", "sin azucar", "galleta", "bebida"], "kg"),
    v("endulzante", "Endulzante", "endulzante", ["endulzante|stevia|sucralosa"], [], "un"),
  ]),
  p("untables", "Para untar", [
    v("mermelada", "Mermelada", "mermelada", ["mermelada"], ["galleta"], "kg"),
    v("mantequilla-mani", "Mantequilla de maní", "mantequilla de mani", ["mani"], ["confitado", "salado", "japones"], "kg"),
    v("palta-pasta", "Pasta de palta / paté", "pate", ["pate"], [], "kg"),
  ]),
 ]},
 {"id": "despensa", "n": "Despensa", "e": "🍝", "p": [
  p("arroz", "Arroz", [
    v("arroz", "Cualquiera", "arroz", ["arroz"], ["integral", "galleta", "leche", "bebida", "fideo", "harina", "jabon", "chips"], "kg"),
    v("arroz-g1", "Grado 1", "arroz grado 1", ["arroz", "g1|grado 1"], ["integral"], "kg"),
    v("arroz-g2", "Grado 2", "arroz grado 2", ["arroz", "g2|grado 2"], ["integral"], "kg"),
    v("arroz-integral", "Integral", "arroz integral", ["arroz", "integral"], ["galleta"], "kg"),
  ]),
  p("fideos", "Fideos", [
    v("fideos", "Cualquiera", "fideos", ["fideo|pasta|spaghetti|tallarin|espiral|corbata|rigati|cabello|quifaro|mostachol|penne|fusilli"], ["dental", "salsa", "pastelera", "hoja", "lasana"], "kg"),
    v("spaghetti", "Spaghetti / tallarines", "spaghetti", ["spaghetti|espagueti|tallarin"], ["salsa"], "kg"),
    v("espirales", "Espirales", "fideos espirales", ["espiral|fusilli"], [], "kg"),
    v("corbatas", "Corbatas", "fideos corbatas", ["corbata"], [], "kg"),
    v("lasana", "Lasaña", "lasaña", ["lasana"], ["congelad", "lista"], "kg"),
  ]),
  p("aceite", "Aceite", [
    v("aceite-vegetal", "Vegetal", "aceite vegetal", ["aceite", "vegetal"], ["oliva", "motor", "bebe", "corporal", "spray", "atun", "jurel"], "l"),
    v("aceite-maravilla", "Maravilla", "aceite maravilla", ["aceite", "maravilla"], ["atun", "jurel"], "l"),
    v("aceite-canola", "Canola", "aceite canola", ["aceite", "canola"], ["atun", "jurel"], "l"),
    v("aceite-oliva", "Oliva", "aceite de oliva", ["aceite", "oliva"], ["atun", "jurel", "sardina", "corporal"], "l"),
  ]),
  p("harina", "Harina", [
    v("harina-polvos", "Con polvos", "harina con polvos", ["harina", "polvo"], ["maiz", "integral", "pescado"], "kg"),
    v("harina-sin-polvos", "Sin polvos", "harina sin polvos", ["harina", "sin polvo"], ["maiz", "integral"], "kg"),
    v("harina-integral", "Integral", "harina integral", ["harina", "integral"], [], "kg"),
  ]),
  p("legumbres", "Legumbres", [
    v("lentejas", "Lentejas", "lentejas", ["lenteja"], ["sopa", "crema"], "kg"),
    v("porotos", "Porotos", "porotos", ["poroto"], ["verde", "sopa"], "kg"),
    v("garbanzos", "Garbanzos", "garbanzos", ["garbanzo"], ["hummus"], "kg"),
  ]),
  p("conservas", "Conservas", [
    v("atun-agua", "Atún en agua", "atun en agua", ["atun", "agua"], ["gato", "perro"], "kg"),
    v("atun-aceite", "Atún en aceite", "atun en aceite", ["atun", "aceite"], ["gato", "perro"], "kg"),
    v("jurel", "Jurel", "jurel", ["jurel"], ["gato", "perro"], "kg"),
    v("choclo-conserva", "Choclo", "choclo en conserva", ["choclo"], ["congelad", "chips", "pastel"], "kg"),
    v("arvejas-conserva", "Arvejas", "arvejas en conserva", ["arveja"], ["congelad"], "kg"),
    v("salsa-tomate", "Salsa de tomate", "salsa de tomate", ["salsa|pomarola", "tomate|pomarola"], ["ketchup"], "kg"),
    v("tomate-trozos", "Tomate en trozos / pelado", "tomate en trozos", ["tomate", "trozo|pelado|triturado|picado"], ["salsa"], "kg"),
  ]),
  p("aderezos", "Aderezos", [
    v("mayonesa", "Mayonesa", "mayonesa", ["mayonesa"], [], "kg"),
    v("ketchup", "Ketchup", "ketchup", ["ketchup"], [], "kg"),
    v("mostaza", "Mostaza", "mostaza", ["mostaza"], [], "kg"),
    v("sal", "Sal", "sal fina", ["=sal"], ["galleta", "papas", "mani", "salsa", "sales de"], "kg"),
    v("caldo", "Caldo en cubos", "caldo cubos", ["caldo"], [], "un"),
  ]),
  p("snacks", "Galletas y snacks", [
    v("galletas", "Galletas dulces", "galletas", ["galleta"], ["soda", "agua", "perro", "gato", "arroz"], "kg"),
    v("galletas-soda", "Galletas de soda / agua", "galletas soda", ["galleta", "soda|agua"], [], "kg"),
    v("papas-fritas", "Papas fritas", "papas fritas", ["papa", "frita|chips"], ["congelad", "prefrita"], "kg"),
    v("frutos-secos", "Frutos secos / maní", "mani", ["mani|almendra|nuez|frutos secos|mix"], ["mantequilla", "bebida", "leche", "chocolate"], "kg"),
  ]),
 ]},
 {"id": "verduras", "n": "Frutas y verduras", "e": "🥑", "p": [
  p("verduras", "Verduras", [
    v("papa", "Papa", "papa", ["=papa|=papas"], ["frita", "chips", "pure", "prefrita", "congelad", "mayo"], "kg"),
    v("tomate", "Tomate", "tomate", ["tomate"], ["salsa", "trozo", "pelado", "ketchup", "pasta", "cherry", "seco"], "kg"),
    v("cebolla", "Cebolla", "cebolla", ["cebolla"], ["frita", "polvo", "sopa", "chips"], "kg"),
    v("zanahoria", "Zanahoria", "zanahoria", ["zanahoria"], ["congelad", "papilla", "jugo"], "kg"),
    v("lechuga", "Lechuga", "lechuga", ["lechuga"], [], "un"),
    v("ajo", "Ajo", "ajo", ["=ajo"], ["polvo", "sal", "pasta"], "un"),
    v("zapallo", "Zapallo", "zapallo", ["zapallo"], ["crema", "sopa"], "kg"),
  ]),
  p("frutas", "Frutas", [
    v("palta", "Palta", "palta hass", ["palta"], ["pasta", "aceite", "salsa", "guacamole"], "kg"),
    v("platano", "Plátano", "platano", ["platano"], ["leche", "yogh", "chips", "papilla", "sabor"], "kg"),
    v("manzana", "Manzana", "manzana", ["manzana"], ["jugo", "nectar", "compota", "papilla", "vinagre", "sabor", "yogh"], "kg"),
    v("naranja", "Naranja", "naranja", ["naranja"], ["jugo", "nectar", "sabor", "bebida"], "kg"),
    v("limon", "Limón", "limon", ["limon"], ["jugo", "sucedaneo", "bebida", "sabor", "lavaloza", "detergente", "te"], "kg"),
    v("mandarina", "Mandarina", "mandarina", ["mandarina"], ["jugo", "nectar", "sabor"], "kg"),
  ]),
 ]},
 {"id": "carnes", "n": "Carnes y embutidos", "e": "🍗", "p": [
  p("pollo", "Pollo", [
    v("pechuga-pollo", "Pechuga", "pechuga de pollo", ["pechuga"], ["pavo", "apanad", "nugget", "perro", "gato"], "kg"),
    v("trutro-pollo", "Trutro", "trutro de pollo", ["trutro"], ["pavo", "apanad", "perro", "gato"], "kg"),
    v("pollo-entero", "Pollo entero", "pollo entero", ["pollo", "entero"], ["perro", "gato"], "kg"),
  ]),
  p("vacuno", "Vacuno", [
    v("carne-molida", "Carne molida", "carne molida", ["molida"], ["soya", "pavo", "pollo", "cerdo", "vegetal"], "kg"),
    v("posta-negra", "Posta negra", "posta negra", ["posta"], [], "kg"),
    v("asiento", "Asiento / bistec", "asiento picana", ["asiento|bistec|picana"], [], "kg"),
  ]),
  p("cerdo", "Cerdo", [
    v("chuleta-cerdo", "Chuleta", "chuleta de cerdo", ["chuleta"], [], "kg"),
    v("costillar-cerdo", "Costillar", "costillar de cerdo", ["costillar"], [], "kg"),
  ]),
  p("embutidos", "Embutidos", [
    v("vienesas", "Vienesas", "vienesas", ["vienesa|salchicha"], ["perro", "gato"], "kg"),
    v("jamon", "Jamón", "jamon", ["jamon"], ["serrano", "queso crema"], "kg"),
    v("hamburguesas", "Hamburguesas", "hamburguesas", ["hamburguesa"], ["pan", "vegetal", "soya"], "kg"),
  ]),
 ]},
 {"id": "congelados", "n": "Congelados", "e": "❄️", "p": [
  p("congelados", "Congelados", [
    v("verduras-congeladas", "Verduras congeladas", "verduras congeladas", ["congelad"], ["helado", "pizza", "papas", "pescado", "pollo"], "kg"),
    v("papas-prefritas", "Papas prefritas", "papas prefritas", ["papa", "prefrita|congelad|corte"], ["chips"], "kg"),
    v("helado", "Helado", "helado", ["helado"], ["te helado", "cafe"], "l"),
    v("pescado-congelado", "Pescado (merluza, reineta)", "merluza congelada", ["merluza|reineta|tilapia|salmon"], ["gato", "perro", "conserva"], "kg"),
  ]),
 ]},
 {"id": "bebidas", "n": "Bebidas", "e": "🥤", "p": [
  p("bebidas", "Bebidas", [
    v("agua", "Agua mineral", "agua mineral", ["agua"], ["tonica", "oxigenada", "galleta", "colonia", "micelar", "destilada", "perfume"], "l"),
    v("bebida-cola", "Bebida cola", "bebida cola", ["cola"], ["cola cao", "colageno", "zero cal"], "l"),
    v("bebida", "Bebida (cualquiera)", "bebida", ["bebida"], ["vegetal", "energetica", "isotonica", "lactea", "polvo", "soya", "almendra", "avena"], "l"),
    v("jugo-liquido", "Jugo / néctar", "nectar", ["jugo|nectar"], ["polvo"], "l"),
    v("jugo-polvo", "Jugo en polvo", "jugo en polvo", ["jugo", "polvo"], [], "un"),
    v("cerveza", "Cerveza", "cerveza", ["cerveza"], ["sin alcohol"], "l"),
  ]),
 ]},
 {"id": "limpieza", "n": "Limpieza", "e": "🧽", "p": [
  p("ropa", "Lavado de ropa", [
    v("detergente-liquido", "Detergente líquido", "detergente liquido", ["detergente", "liquido"], ["loza", "lavaloza"], "l"),
    v("detergente-polvo", "Detergente en polvo", "detergente en polvo", ["detergente", "polvo"], [], "kg"),
    v("suavizante", "Suavizante", "suavizante", ["suavizante"], [], "l"),
    v("quitamanchas", "Quitamanchas", "quitamanchas", ["quitamancha"], [], "l"),
  ]),
  p("hogar", "Hogar", [
    v("lavalozas", "Lavalozas", "lavalozas", ["lavaloza|loza"], ["juego", "plato"], "l"),
    v("cloro", "Cloro", "cloro", ["cloro"], ["gel", "piscina"], "l"),
    v("limpiador-pisos", "Limpiador de pisos", "limpiador pisos", ["limpiador|limpia", "piso|multiuso"], [], "l"),
    v("esponjas", "Esponjas", "esponja", ["esponja"], ["maquillaje", "bano"], "un"),
    v("bolsas-basura", "Bolsas de basura", "bolsas de basura", ["bolsa", "basura"], [], "un"),
  ]),
  p("papel", "Papel", [
    v("papel-higienico", "Papel higiénico", "papel higienico", ["papel", "higienic"], [], "un"),
    v("toalla-papel", "Toalla de papel", "toalla de papel", ["toalla", "papel|nova|cocina"], ["higienica", "humeda"], "un"),
    v("servilletas", "Servilletas", "servilletas", ["servilleta"], [], "un"),
  ]),
 ]},
 {"id": "higiene", "n": "Higiene personal", "e": "🧴", "p": [
  p("cabello", "Cabello", [
    v("shampoo", "Shampoo", "shampoo", ["shampoo|champu"], ["perro", "gato", "bebe", "auto"], "l"),
    v("acondicionador", "Acondicionador", "acondicionador", ["acondicionador"], ["perro"], "l"),
  ]),
  p("cuerpo", "Cuerpo", [
    v("jabon-barra", "Jabón en barra", "jabon barra", ["jabon"], ["liquido", "ropa", "loza", "lavaloza"], "un"),
    v("jabon-liquido", "Jabón líquido", "jabon liquido", ["jabon", "liquido"], ["ropa", "loza", "lavaloza"], "l"),
    v("desodorante", "Desodorante", "desodorante", ["desodorante"], ["ambiental", "auto", "bano"], "un"),
    v("toallas-higienicas", "Toallas higiénicas", "toallas higienicas", ["toalla", "higienica|femenin"], [], "un"),
  ]),
  p("dental", "Dental", [
    v("pasta-dental", "Pasta dental", "pasta dental", ["dental|dientes", "pasta|crema"], ["cepillo", "perro"], "un"),
    v("cepillo-dental", "Cepillo de dientes", "cepillo dental", ["cepillo", "dental|dientes"], ["perro"], "un"),
  ]),
 ]},
 {"id": "bebe", "n": "Bebé", "e": "👶", "p": [
  p("panales", "Pañales", [
    v("panales-rn", "Talla RN", "pañales recien nacido", ["panal", "=rn|recien nacido|prematuro"], ["adulto", "toallita"], "un"),
    v("panales-p", "Talla P", "pañales talla p", ["panal", "=p"], ["adulto", "toallita"], "un"),
    v("panales-m", "Talla M", "pañales talla m", ["panal", "=m"], ["adulto", "toallita"], "un"),
    v("panales-g", "Talla G", "pañales talla g", ["panal", "=g"], ["adulto", "toallita"], "un"),
    v("panales-xg", "Talla XG", "pañales talla xg", ["panal", "=xg"], ["adulto", "toallita"], "un"),
    v("panales-xxg", "Talla XXG", "pañales talla xxg", ["panal", "=xxg"], ["adulto", "toallita"], "un"),
  ]),
  p("bebe-otros", "Cuidado del bebé", [
    v("toallitas-humedas", "Toallitas húmedas", "toallitas humedas", ["toallita"], ["desmaquill", "lentes"], "un"),
    v("formula-infantil", "Fórmula infantil", "formula infantil", ["formula|leche infantil|etapa"], [], "kg"),
    v("papilla", "Papillas / colados", "colado bebe", ["papilla|colado|compota"], [], "kg"),
  ]),
 ]},
 {"id": "mascotas", "n": "Mascotas", "e": "🐾", "p": [
  p("perro", "Perro", [
    v("alimento-perro", "Alimento perro adulto", "alimento perro adulto", ["perro"], ["cachorro", "senior", "humedo", "lata", "sobre", "pouch", "snack", "premio", "galleta", "hueso", "juguete", "shampoo", "cama", "correa", "plato", "bolsa"], "kg"),
    v("perro-cachorro", "Alimento perro cachorro", "alimento perro cachorro", ["perro|cachorro", "cachorro|puppy"], ["humedo", "lata", "sobre", "snack", "premio", "juguete"], "kg"),
    v("perro-senior", "Alimento perro senior", "alimento perro senior", ["perro", "senior|7+|adulto mayor"], ["humedo", "lata", "sobre", "snack"], "kg"),
    v("perro-humedo", "Comida húmeda perro (latas, sobres)", "alimento humedo perro", ["perro", "humedo|lata|sobre|pouch"], ["snack", "juguete"], "un"),
    v("perro-snack", "Snacks y premios perro", "snack perro", ["perro", "snack|premio|galleta|hueso|dental|stick"], ["juguete", "cama"], "kg"),
    v("bolsas-fecas", "Bolsas para fecas", "bolsas fecas perro", ["bolsa", "fecas|desecho|perro|mascota"], ["basura cocina"], "un"),
  ]),
  p("gato", "Gato", [
    v("alimento-gato", "Alimento gato adulto", "alimento gato adulto", ["gato"], ["gatito", "kitten", "humedo", "lata", "sobre", "pouch", "arena", "snack", "premio", "juguete", "cama", "plato", "rascador"], "kg"),
    v("gato-gatito", "Alimento gatito", "alimento gatito", ["gatito|kitten"], ["humedo", "lata", "sobre", "arena", "juguete"], "kg"),
    v("gato-humedo", "Comida húmeda gato (sobres, latas)", "alimento humedo gato", ["gato|gatito", "humedo|lata|sobre|pouch"], ["arena", "snack", "juguete"], "un"),
    v("arena-gato", "Arena para gato", "arena gato", ["arena"], ["construccion"], "kg"),
    v("gato-snack", "Snacks gato", "snack gato", ["gato", "snack|premio|stick|malta|crema"], ["arena", "juguete"], "kg"),
  ]),
  p("otras-mascotas", "Otras mascotas", [
    v("alimento-peces", "Alimento peces", "alimento peces", ["pez|peces|acuario|tropical"], ["atun", "jurel", "conserva", "congelad"], "kg"),
    v("alimento-aves", "Alimento aves (alpiste, mezcla)", "alimento aves alpiste", ["ave|alpiste|canario|loro|periquito|mezcla para aves"], ["pollo", "pavo", "huevo"], "kg"),
    v("alimento-roedores", "Alimento roedores (hámster, conejo)", "alimento hamster conejo", ["hamster|roedor|conejo|cuy|cobayo"], ["juguete", "jaula"], "kg"),
    v("viruta", "Viruta / lecho", "viruta hamster", ["viruta|aserrin|lecho|sustrato"], [], "kg"),
  ]),
 ]},
]


# Ícono propio de cada producto (variante o producto); si falta, se usa el de la categoría
EMOJI = {
 "leche": "🥛", "leche-sabor": "🍫", "bebida-vegetal": "🌰", "leche-polvo": "🥛",
 "yogur": "🍦", "queso": "🧀", "mantequilla": "🧈", "margarina": "🧈", "crema-leche": "🥛",
 "leche-condensada": "🥫", "manjar": "🍯", "huevos": "🥚",
 "pan": "🍞", "marraqueta": "🥖", "hallulla": "🫓", "pan-pita": "🌯",
 "avena": "🥣", "cereal": "🥣", "granola": "🥣",
 "cafe-instantaneo": "☕", "cafe-molido": "☕", "cafe-capsulas": "☕", "te": "🍵", "hierbas": "🌿", "saborizante": "🍫",
 "azucar": "🍬", "endulzante": "🍬", "mermelada": "🍓", "mantequilla-mani": "🥜", "palta-pasta": "🥫",
 "arroz": "🍚", "fideos": "🍝", "lasana": "🍝", "aceite": "🫒", "aceite-vegetal": "🌻", "aceite-maravilla": "🌻",
 "harina": "🌾", "lentejas": "🫘", "porotos": "🫘", "garbanzos": "🫘",
 "atun-agua": "🐟", "atun-aceite": "🐟", "jurel": "🐟", "choclo-conserva": "🌽", "arvejas-conserva": "🫛",
 "salsa-tomate": "🍅", "tomate-trozos": "🥫", "mayonesa": "🫙", "ketchup": "🍅", "mostaza": "🌭", "sal": "🧂", "caldo": "🍲",
 "galletas": "🍪", "galletas-soda": "🍘", "papas-fritas": "🥔", "frutos-secos": "🥜",
 "papa": "🥔", "tomate": "🍅", "cebolla": "🧅", "zanahoria": "🥕", "lechuga": "🥬", "ajo": "🧄", "zapallo": "🎃",
 "palta": "🥑", "platano": "🍌", "manzana": "🍎", "naranja": "🍊", "limon": "🍋", "mandarina": "🍊",
 "pollo": "🍗", "pechuga-pollo": "🍗", "trutro-pollo": "🍗", "pollo-entero": "🐔",
 "carne-molida": "🥩", "posta-negra": "🥩", "asiento": "🥩", "chuleta-cerdo": "🍖", "costillar-cerdo": "🍖",
 "vienesas": "🌭", "jamon": "🥓", "hamburguesas": "🍔",
 "verduras-congeladas": "🥦", "papas-prefritas": "🍟", "helado": "🍨", "pescado-congelado": "🐠",
 "agua": "💧", "bebida-cola": "🥤", "bebida": "🥤", "jugo-liquido": "🧃", "jugo-polvo": "🧃", "cerveza": "🍺",
 "detergente-liquido": "🧴", "detergente-polvo": "📦", "suavizante": "🌸", "quitamanchas": "✨",
 "lavalozas": "🍽️", "cloro": "🧪", "limpiador-pisos": "🧹", "esponjas": "🧽", "bolsas-basura": "🗑️",
 "papel-higienico": "🧻", "toalla-papel": "🧻", "servilletas": "🧻",
 "shampoo": "🧴", "acondicionador": "🧴", "jabon-barra": "🧼", "jabon-liquido": "🧼", "desodorante": "💨",
 "toallas-higienicas": "🌸", "pasta-dental": "🪥", "cepillo-dental": "🪥",
 "panales": "👶", "toallitas-humedas": "🧻", "formula-infantil": "🍼", "papilla": "🥣",
 "alimento-perro": "🐕", "perro-cachorro": "🐶", "perro-senior": "🐕", "perro-humedo": "🥫", "perro-snack": "🦴", "bolsas-fecas": "💩",
 "alimento-gato": "🐈", "gato-gatito": "🐱", "gato-humedo": "🥫", "arena-gato": "🪣", "gato-snack": "🐟",
 "alimento-peces": "🐠", "alimento-aves": "🐦", "alimento-roedores": "🐹", "viruta": "🪵",
}

# Productos que son grupos: en la lista se muestra solo el nombre de la variante ("Salsa de tomate", no "Conservas")
GRUPOS = {"mantequilla", "crema", "cereales", "cafe", "azucar", "untables", "legumbres", "conservas", "aderezos",
          "snacks", "verduras", "frutas", "vacuno", "embutidos", "congelados", "bebidas", "ropa", "hogar", "papel",
          "cabello", "cuerpo", "dental", "bebe-otros", "perro", "gato", "otras-mascotas"}

# Variantes que NO entran en "cualquier tipo" del producto (son otra cosa en la práctica)
APARTE = {"leche-polvo", "leche-sabor", "bebida-vegetal", "yogur-protein", "queso-crema", "queso-rallado",
          "leche-condensada", "manjar", "pan-pita", "cafe-capsulas", "hierbas", "saborizante", "endulzante",
          "mantequilla-mani", "palta-pasta", "lasana", "caldo", "cerveza", "jugo-polvo", "quitamanchas",
          "pescado-congelado", "helado", "arena-gato", "papilla", "formula-infantil"}


def main():
    for c in C:
        for pr in c["p"]:
            if pr["id"] in GRUPOS:
                pr["g"] = 1
            if pr["id"] in EMOJI:
                pr["e"] = EMOJI[pr["id"]]
            for x in pr["v"]:
                if x["id"] in EMOJI:
                    x["e"] = EMOJI[x["id"]]
                if x["id"] in APARTE:
                    x["x"] = 1
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = {"version": 1, "categorias": C}
    ids = [x["id"] for c in C for pr in c["p"] for x in pr["v"]]
    assert len(ids) == len(set(ids)), "ids repetidos"
    with open(os.path.join(base, "catalogo.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"{len(C)} categorías, {sum(len(c['p']) for c in C)} productos, {len(ids)} variantes")


if __name__ == "__main__":
    main()
