import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scraper"))
from extraer import de_dom, de_json  # noqa: E402
from texto import cantidad, cumple, formato, precio_num  # noqa: E402

CAT = json.load(open(os.path.join(os.path.dirname(__file__), "..", "catalogo.json"), encoding="utf-8"))
V = {v["id"]: v for c in CAT["categorias"] for p in c["p"] for v in p["v"]}


def test_formato():
    assert cantidad("Leche Entera Colun 1 L", "l") == 1
    assert cantidad("Leche Semidescremada Soprole 6 x 1 L", "l") == 6
    assert cantidad("Arroz Grado 2 Tucapel 900 g", "kg") == 0.9
    assert cantidad("Yoghurt Batido Frutilla 120 g x 4", "kg") == 0.48
    assert cantidad("Papel Higiénico Doble Hoja 24 m 4 un Confort", "un") == 4
    assert cantidad("Pañales Babysec Premium Talla M 52 un", "un") == 52
    assert cantidad("Bebida Coca-Cola 3 L", "l") == 3
    assert cantidad("Bebida Coca Cola Pack 6 un 1,5 L", "l") == 9
    assert cantidad("Huevos Blancos 12 un", "un") == 12
    assert cantidad("Aceite Vegetal 900 ml", "l") == 0.9
    assert cantidad("Atún Lomitos en Agua 160 g", "kg") == 0.16
    assert formato("Detergente Líquido 3 L")["l"] == 3


def test_precio():
    assert precio_num("$1.290") == 1290
    assert precio_num("$ 12.490") == 12490
    assert precio_num(1290.0) == 1290
    assert precio_num("1290") == 1290
    assert precio_num("1.290,00") == 1290


def test_variantes():
    assert cumple("Leche Entera Colun 1 L", V["leche-entera"])
    assert not cumple("Leche Entera Sin Lactosa Colun 1 L", V["leche-entera"])
    assert not cumple("Leche Semidescremada Colun 1 L", V["leche-descremada"])
    assert cumple("Leche Descremada Sin Lactosa Loncoleche 1 L", V["leche-sl-descremada"])
    assert cumple("Leche Semidescremada Soprole 1 L", V["leche-semi"])
    assert cumple("Arroz Grado 2 Largo Delgado 1 kg Tucapel", V["arroz-g2"])
    assert not cumple("Arroz Grado 1 Tucapel 1 kg", V["arroz-g2"])
    assert cumple("Sal de Mesa Lobos 1 kg", V["sal"])
    assert not cumple("Salsa de Tomate Pomarola 200 g", V["sal"])
    assert cumple("Pañales Huggies Natural Care Talla M 80 un", V["panales-m"])
    assert not cumple("Pañales Huggies Natural Care Talla G 80 un", V["panales-m"])
    assert cumple("Té Supremo Ceylán 100 bolsitas", V["te"])
    assert not cumple("Ternera molida", V["te"])
    assert cumple("Papa Lavada Malla 2 kg", V["papa"])
    assert not cumple("Papas Fritas Lays 230 g", V["papa"])


VTEX = [{
    "productId": "123", "productName": "Leche Entera Colun 1 L", "brand": "Colun", "linkText": "leche-entera-colun-1-l",
    "items": [{"itemId": "1", "name": "Leche Entera Colun 1 L",
               "images": [{"imageUrl": "https://img.example/leche.jpg"}],
               "sellers": [{"sellerId": "1", "commertialOffer": {"Price": 1090, "ListPrice": 1290,
                                                                 "PriceWithoutDiscount": 1290}}]}]
}, {
    "productId": "124", "productName": "Arroz Grado 2 Tucapel 1 kg", "brand": "Tucapel", "linkText": "arroz-g2",
    "items": [{"itemId": "2", "name": "Arroz Grado 2 Tucapel 1 kg",
               "sellers": [{"commertialOffer": {"Price": 1890, "ListPrice": 1890}}]}]
}]

OTRO = {"data": {"search": {"products": [
    {"displayName": "Leche Semidescremada Soprole 1 L", "brand": {"name": "Soprole"},
     "price": {"BasePriceSales": 1150, "BasePriceReference": 1250, "BasePriceTLMC": 990},
     "images": {"defaultImage": "https://img.example/x.png"}, "sku": "999"},
    {"name": "Despacho a domicilio", "price": 2990},
]}}}


def test_extraer_vtex():
    ps = de_json(VTEX, "https://www.jumbo.cl/")
    nombres = {p["nombre"]: p for p in ps}
    assert nombres["Leche Entera Colun 1 L"]["precio"] == 1090
    assert nombres["Leche Entera Colun 1 L"]["normal"] == 1290
    assert nombres["Leche Entera Colun 1 L"]["marca"] == "Colun"
    assert nombres["Leche Entera Colun 1 L"]["url"].startswith("https://www.jumbo.cl/leche-entera")
    assert nombres["Arroz Grado 2 Tucapel 1 kg"]["precio"] == 1890


def test_extraer_otro():
    ps = de_json(OTRO, "https://super.lider.cl/")
    assert len(ps) == 1
    assert ps[0]["precio"] == 1150 and ps[0]["marca"] == "Soprole"


def test_dom():
    ps = de_dom([{"nombre": "Leche Entera Colun 1 L", "precios": ["$1.090", "$1.290"], "url": "u", "img": ""}])
    assert ps[0]["precio"] == 1090 and ps[0]["normal"] == 1290




def test_escalas_dom_alvi():
    d = de_dom([{"nombre": "Leche en polvo Calo 850 g", "precios": ["$6.490", "$6.790", "$7.090"],
                 "escalas": ["Desde 2 un $6.490 c/u", "Desde 1 un $6.790 c/u"], "url": "", "img": ""}])[0]
    assert d["precio"] == 7090 and d["escalas"] == [[1, 6790], [2, 6490]], d


def test_escalas():
    alvi = {"availableProducts": [{"productId": "1", "name": "Leche en polvo Calo 850 g", "brand": "Calo",
            "sellers": [{"price": 7090, "listPrice": 7090}],
            "priceSteps": [{"promotionalPrice": 6790, "minQuantity": 1, "ppum": "$7.988 x Kg"},
                           {"promotionalPrice": 6490, "minQuantity": 2, "ppum": "$7.635 x Kg"}]}]}
    p = de_json(alvi)[0]
    assert p["precio"] == 7090 and p["escalas"] == [[1, 6790], [2, 6490]], p
    tottus = {"results": [{"displayName": "Arroz Grado 2 1 kg", "brand": "Tucapel", "productId": "9",
              "prices": [{"price": ["1.290"], "type": "internetPrice"}, {"price": ["1.490"], "type": "normalPrice"}]}]}
    t = de_json(tottus)[0]
    assert t["precio"] == 1290, t
    d = de_dom([{"nombre": "Leche Entera 1 L", "precios": ["$1.190", "$3.300"], "escalas": ["Lleva 3 x $3.300"], "url": "", "img": ""}])[0]
    assert d["precio"] == 1190 and d["escalas"] == [[3, 1100]], d


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)
