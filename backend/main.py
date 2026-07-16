from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

try:
    # Ejecucion local: uvicorn corre desde dentro de backend/, asi que
    # busqueda.py es un modulo hermano directamente importable.
    from busqueda import (
        TEMPORADAS, _buscar_definicion_categoria, alternativas, buscar, cargar_productos,
        categorias_de_temporada, productos_de_categoria,
    )
except ImportError:
    # Vercel ejecuta el proyecto desde la raiz (backend.main:app), asi que
    # busqueda.py solo es visible como parte del paquete backend.
    from backend.busqueda import (
        TEMPORADAS, _buscar_definicion_categoria, alternativas, buscar, cargar_productos,
        categorias_de_temporada, productos_de_categoria,
    )

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
