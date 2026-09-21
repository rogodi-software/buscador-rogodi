"""
Catalogo publico de Autozeichen (escudos/letreros/mirillas/placas), corre en
el mismo sistema Datologia que Rogodi -- pi_resultados.jsp expone codigo,
foto, descripcion, unidad, precio y existencia SIN necesidad de login. No
tiene un scraper periodico como el de Rogodi (no hay catalogo.db propio):
se lee en vivo, con las peticiones en paralelo para que quepa comodo en el
tiempo limite de la funcion serverless (~5s para las 4 categorias completas).
"""
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from itertools import count

import requests

try:
    from busqueda import normalizar
except ImportError:
    from backend.busqueda import normalizar

BASE = "http://nube.datologia.com/autozeichen"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Los 4 "tipo articulo" que de verdad vende Autozeichen (el resto de filtros
# que trae la plantilla -- Marca con codigos de foco, etc. -- es basura
# heredada de la plantilla generica de Datologia, no aplica a este cliente).
TIPOS = [
    {"id": 1557, "nombre": "Escudos"},
    {"id": 1558, "nombre": "Letreros"},
    {"id": 1559, "nombre": "Mirillas"},
    {"id": 1556, "nombre": "Placas"},
]
TIPOS_POR_ID = {t["id"]: t["nombre"] for t in TIPOS}

FILA_RE = re.compile(
    r'<TD>([\w-]+)</TD>.*?'
    r'<a\s+href="pi_articulo\.jsp\?id_articulo=(\d+)">\s*'
    r'<img src="([^"]*)"[^>]*></a>.*?'
    r'<TD><a\s+href="[^"]*">([^<]*)</a></TD>\s*'
    r'<TD><div align="center">([^<]*)</div></TD>\s*'
    r'<TD><div align="center">\$?([\d,\.]*)</div></TD>\s*'
    r'<TD><div align="center">([^<]*?)\s*</div></TD>',
    re.S,
)

_id_articulo_fallback = count(9_000_000)  # por si algun renglon no trae id real


def marcas_de_tipo(id_tipo: int) -> list[dict]:
    resp = requests.get(f"{BASE}/pi_busqueda.jsp", params={"id_articulotipo": id_tipo},
                         headers=HEADERS, timeout=15)
    resp.encoding = "iso-8859-1"
    vistos, marcas = set(), []
    for i, n in re.findall(r'id_articulogrupo=(\d+)">([^<]*)', resp.text):
        nombre = unicodedata.normalize("NFKC", n).strip()
        if nombre and nombre not in vistos:
            vistos.add(nombre)
            marcas.append({"id": int(i), "nombre": nombre})
    return marcas


def _parsear_productos(html: str) -> list[dict]:
    productos = []
    for m in FILA_RE.finditer(html):
        codigo, id_articulo, foto, descripcion, unidad, precio, existencia = m.groups()
        existencia = existencia.strip()
        productos.append({
            "id_articulo": int(id_articulo) if id_articulo else next(_id_articulo_fallback),
            "codigo": codigo.strip(),
            # autozeichen.com si sirve https para las fotos (aunque el buscador
            # en si solo responde por http) -- forzarlo evita que el navegador
            # bloquee la imagen como "contenido mixto" en nuestra pagina https.
            "foto_url": foto.strip().replace("http://", "https://", 1),
            "descripcion": descripcion.strip(),
            "unidad": unidad.strip(),
            "precio": float(precio.replace(",", "")) if precio.strip() else 0,
            "existencia": 0 if "No Disponible" in existencia else float(existencia or 0),
        })
    return productos


def productos_de_grupo(id_tipo: int, id_grupo: int) -> list[dict]:
    resp = requests.post(f"{BASE}/pi_resultados.jsp", data={
        "id_articulotipo": id_tipo, "id_articulogrupo": id_grupo,
        "id_articulofamilia": "", "descripcion": "",
    }, headers=HEADERS, timeout=20)
    resp.encoding = "iso-8859-1"
    productos = _parsear_productos(resp.text)
    nombre_tipo = TIPOS_POR_ID.get(id_tipo, "")
    for p in productos:
        p["tipo_nombre"] = nombre_tipo
        p["familia"] = p["codigo"].split("-")[0]
    return productos


def _con_texto_busqueda(p: dict) -> dict:
    """Mismos campos derivados que busqueda.cargar_productos() para Rogodi,
    asi buscar() funciona identico sobre el catalogo de Autozeichen."""
    texto = " ".join(normalizar(str(p.get(c) or "")) for c in
                      ("codigo", "descripcion", "grupo_nombre", "tipo_nombre"))
    p["_texto_busqueda"] = texto
    p["_desc_norm"] = normalizar(str(p.get("descripcion") or ""))
    return p


def catalogo_autozeichen() -> list[dict]:
    """Todo el catalogo publico de Autozeichen, tipo por tipo y marca por
    marca (asi cada producto trae su tipo/marca real, no un bote generico),
    listo para buscar() y para generar_excel_bytes()."""
    combos = []
    for tipo in TIPOS:
        for marca in marcas_de_tipo(tipo["id"]):
            combos.append((tipo["id"], tipo["nombre"], marca["id"], marca["nombre"]))

    por_codigo: dict[str, dict] = {}

    def _uno(combo):
        id_tipo, nombre_tipo, id_grupo, nombre_grupo = combo
        productos = productos_de_grupo(id_tipo, id_grupo)
        for p in productos:
            p["grupo_nombre"] = nombre_grupo
        return productos

    with ThreadPoolExecutor(max_workers=12) as ex:
        for productos in ex.map(_uno, combos):
            for p in productos:
                por_codigo[p["codigo"]] = p

    return [_con_texto_busqueda(p) for p in por_codigo.values()]
