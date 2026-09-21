from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

try:
    # Ejecucion local: uvicorn corre desde dentro de backend/, asi que
    # busqueda.py es un modulo hermano directamente importable.
    from busqueda import (
        TEMPORADAS, _buscar_definicion_categoria, alternativas, buscar, cargar_productos,
        categorias_de_temporada, productos_de_categoria,
    )
    from catalogo_excel import generar_excel_bytes
    from autozeichen import TIPOS as AZ_TIPOS, catalogo_autozeichen, marcas_de_tipo, productos_de_grupo
except ImportError:
    # Vercel ejecuta el proyecto desde la raiz (backend.main:app), asi que
    # busqueda.py solo es visible como parte del paquete backend.
    from backend.busqueda import (
        TEMPORADAS, _buscar_definicion_categoria, alternativas, buscar, cargar_productos,
        categorias_de_temporada, productos_de_categoria,
    )
    from backend.catalogo_excel import generar_excel_bytes
    from backend.autozeichen import TIPOS as AZ_TIPOS, catalogo_autozeichen, marcas_de_tipo, productos_de_grupo

app = FastAPI(title="Buscador ROGODI")

PRODUCTOS: list[dict] = []
ESTATICOS = Path(__file__).resolve().parent / "static"


@app.on_event("startup")
def cargar():
    global PRODUCTOS
    PRODUCTOS = cargar_productos()
    print(f"Catalogo cargado en memoria: {len(PRODUCTOS)} productos.")


def _producto_publico(p: dict) -> dict:
    """Solo los campos que la pantalla del vendedor debe ver."""
    return {
        "id_articulo": p["id_articulo"],
        "codigo": p["codigo"],
        "descripcion": p["descripcion"],
        "unidad": p["unidad"],
        "precio": p["precio"],
        "existencia": p["existencia"],
        "foto_url": p["foto_url"],
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "productos": len(PRODUCTOS)}


def _seccion_publica(seccion: dict) -> dict:
    salida = []
    for p in seccion["resultados"]:
        item = _producto_publico(p)
        if (p.get("existencia") or 0) <= 0:
            item["alternativas"] = [_producto_publico(a) for a in alternativas(p, PRODUCTOS)]
        salida.append(item)
    return {"titulo": seccion["titulo"], "total": len(salida), "resultados": salida}


@app.get("/api/buscar")
def api_buscar(q: str = ""):
    resultado = buscar(q, PRODUCTOS)
    secciones = [_seccion_publica(s) for s in resultado["secciones"]]
    return {"modo": resultado["modo"], "secciones": secciones}


@app.get("/api/temporadas")
def api_temporadas():
    return [
        {"clave": clave, "nombre": t["nombre"], "meses": t["meses"], "emoji": t["emoji"]}
        for clave, t in TEMPORADAS.items()
    ]


@app.get("/api/temporada/{clave}/categorias")
def api_temporada_categorias(clave: str):
    if clave not in TEMPORADAS:
        return {"error": "temporada desconocida", "categorias": []}
    t = TEMPORADAS[clave]
    return {
        "temporada": {"clave": clave, "nombre": t["nombre"], "meses": t["meses"], "emoji": t["emoji"]},
        "categorias": categorias_de_temporada(clave, PRODUCTOS),
    }


@app.get("/api/temporada/{clave}/categoria/{slug}")
def api_temporada_categoria(clave: str, slug: str):
    if clave not in TEMPORADAS:
        return {"error": "categoria desconocida", "total": 0, "resultados": []}
    definicion = _buscar_definicion_categoria(clave, slug)
    if not definicion:
        return {"error": "categoria desconocida", "total": 0, "resultados": []}
    productos = productos_de_categoria(definicion["familias"], definicion["palabras"], PRODUCTOS)
    salida = []
    for p in productos:
        item = _producto_publico(p)
        if (p.get("existencia") or 0) <= 0:
            item["alternativas"] = [_producto_publico(a) for a in alternativas(p, PRODUCTOS)]
        salida.append(item)
    return {
        "categoria": {"slug": slug, "nombre": definicion["nombre"]},
        "total": len(salida),
        "resultados": salida,
    }


@app.get("/api/productos")
def api_productos(ids: str = ""):
    """Datos frescos (precio/existencia en vivo) para una lista de
    id_articulo, usados al generar el PDF de cotizacion: el carrito vive en
    localStorage y puede tener dias de antiguedad, pero el PDF debe reflejar
    lo mismo que el buscador muestra en este momento."""
    try:
        buscados = {int(x) for x in ids.split(",") if x.strip()}
    except ValueError:
        return {"resultados": []}
    por_id = {p["id_articulo"]: p for p in PRODUCTOS}
    return {"resultados": [_producto_publico(por_id[i]) for i in buscados if i in por_id]}


HOSTS_FOTO_PERMITIDOS = ("rogodi.mx", "autozeichen.com")


@app.get("/api/foto")
def api_foto(url: str):
    """Reenvia una foto de producto (rogodi.mx o autozeichen.com) bajo
    nuestro propio dominio. Necesario por dos razones: (1) el PDF de
    cotizacion dibuja cada foto en un canvas, y una imagen de otro origen lo
    deja "contaminado" sin poder exportarse; (2) autozeichen.com solo sirve
    por http, y una pagina https no puede cargar imagenes http directo
    (contenido mixto bloqueado por el navegador)."""
    host = (urlparse(url).hostname or "")
    if not any(host == h or host.endswith("." + h) for h in HOSTS_FOTO_PERMITIDOS):
        return Response(status_code=400)
    try:
        # autozeichen.com (no asi rogodi.mx) responde 403 a peticiones sin
        # User-Agent de navegador.
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except requests.RequestException:
        return Response(status_code=502)
    return Response(
        content=resp.content,
        media_type=resp.headers.get("Content-Type", "image/jpeg"),
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.get("/api/catalogo-excel")
def api_catalogo_excel():
    """Excel de existencias para la app de catalogos de la disenadora
    (My Business Catalogue): mismo formato que ROGODI_AGOSTO2026.xls, pero
    precio/existencia/descripcion siempre en vivo desde catalogo.db, y solo
    productos con mas de 3 piezas de existencia."""
    contenido = generar_excel_bytes(PRODUCTOS, min_existencia=3)
    nombre = f"ROGODI_{datetime.now().strftime('%d%b%Y').upper()}.xls"
    return Response(
        content=contenido,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@app.get("/api/catalogo-excel-autozeichen")
def api_catalogo_excel_autozeichen():
    """Mismo formato de Excel que el de Rogodi, pero leyendo en vivo el
    catalogo publico de Autozeichen (escudos/letreros/mirillas/placas) --
    ese catalogo no tiene un scraper propio guardando datos, asi que se
    consulta al momento cada vez que se pide el archivo."""
    productos = catalogo_autozeichen()
    contenido = generar_excel_bytes(productos, min_existencia=0)
    nombre = f"AUTOZEICHEN_{datetime.now().strftime('%d%b%Y').upper()}.xls"
    return Response(
        content=contenido,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


# ---------------------------------------------------------------------------
# Modo Autozeichen: mismo buscador, pero para el catalogo de emblemas (no
# hay que hacer una pagina aparte). Navegacion en vivo tipo->marca->productos
# (cada paso es una sola peticion, rapido) y busqueda sobre un cache en
# memoria que se llena la primera vez que alguien busca (toma ~5s esa
# primera vez nada mas).
# ---------------------------------------------------------------------------
_AUTOZEICHEN_CACHE: list[dict] = []


def _autozeichen_publico(p: dict) -> dict:
    item = _producto_publico(p)
    item["tipo_nombre"] = p.get("tipo_nombre")
    item["grupo_nombre"] = p.get("grupo_nombre")
    return item


@app.get("/api/autozeichen/tipos")
def api_autozeichen_tipos():
    return AZ_TIPOS


@app.get("/api/autozeichen/marcas")
def api_autozeichen_marcas(id_tipo: int):
    return marcas_de_tipo(id_tipo)


@app.get("/api/autozeichen/productos")
def api_autozeichen_productos(id_tipo: int, id_grupo: int):
    productos = productos_de_grupo(id_tipo, id_grupo)
    return {"total": len(productos), "resultados": [_autozeichen_publico(p) for p in productos]}


@app.get("/api/autozeichen/buscar")
def api_autozeichen_buscar(q: str = ""):
    global _AUTOZEICHEN_CACHE
    if not _AUTOZEICHEN_CACHE:
        _AUTOZEICHEN_CACHE = catalogo_autozeichen()
    resultado = buscar(q, _AUTOZEICHEN_CACHE)
    secciones = [
        {"titulo": s["titulo"], "total": len(s["resultados"]),
         "resultados": [_autozeichen_publico(p) for p in s["resultados"]]}
        for s in resultado["secciones"]
    ]
    return {"modo": resultado["modo"], "secciones": secciones}


@app.middleware("http")
async def sin_cache(request: Request, call_next):
    """Mientras el buscador sigue en desarrollo, evita que el navegador se
    quede con una version vieja de la pantalla o de las respuestas."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


if ESTATICOS.exists():
    # Solo para desarrollo local (uvicorn). En Vercel la carpeta public/ no
    # forma parte del paquete de la funcion: su CDN la sirve directo, sin
    # pasar por este servidor.
    app.mount("/", StaticFiles(directory=ESTATICOS, html=True), name="static")
