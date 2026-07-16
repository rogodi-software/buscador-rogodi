"""
Motor de busqueda del catalogo ROGODI: normaliza texto, detecta medida,
aplica sinonimos y tolerancia a errores de escritura, rankea resultados, y
encuentra alternativas en stock para productos agotados.
"""
import re
import sqlite3
import unicodedata
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "catalogo.db"

PATRON_MEDIDA = re.compile(
    r"(?<![A-Z0-9])(9004|9005|9006|9007|H11|H13|H4|H7|H3|H1)(?![0-9])"
)
PATRON_FAMILIA = re.compile(r"^\d{3}$")

# Familias que son focos de verdad. Cuando alguien busca una medida (H4, H7,
# 9007...) casi siempre quiere el foco, no el soquet/base/accesorio que
# tambien menciona esa medida en su descripcion.
FOCO_FAMILIAS = {"038", "049", "124", "050", "051"}

TEMPORADAS = {
    "calor": {"nombre": "Calor / Verano", "meses": "abr–jun", "emoji": "☀️",
              "familias": ["092", "039"]},
    "lluvia": {"nombre": "Lluvias", "meses": "jun–sep", "emoji": "🌧️",
               "familias": ["037", "026", "029", "035", "059", "098", "131"]},
    "finDeAnio": {"nombre": "Iluminación", "meses": "oct–dic", "emoji": "🌙",
                  "familias": ["038", "049", "050", "051", "070", "075", "077",
                               "078", "080", "105", "106", "109", "124", "057"]},
    "refacciones": {"nombre": "Refacciones", "meses": "todo el año", "emoji": "🔩",
                     "familias": ["003", "004", "005", "006", "009", "010", "011"]},
    "regalo": {"nombre": "Regalo / Decoración", "meses": "nov–dic", "emoji": "🎁",
               "familias": ["030", "040", "041", "043", "093", "094",
                            "129", "089", "100", "134"]},
    "verificacion": {"nombre": "Seguridad", "meses": "semestral", "emoji": "🔧",
                      "familias": ["067", "037", "038", "049", "055",
                                   "132", "046"]},
    "camion": {"nombre": "Camión", "meses": "todo el año", "emoji": "🚛",
               "familias": ["002", "023", "024", "044", "058", "048", "069",
                            "060", "087", "045", "104"]},
    "moto": {"nombre": "Moto", "meses": "todo el año", "emoji": "🏍️",
             "familias": ["114", "115", "117", "118", "119", "133"]},
}

# Sinonimos: cada lista incluye todas las formas en que un vendedor podria
# escribir el mismo concepto. Si la busqueda usa cualquiera de estas
# palabras, se considera coincidencia si el producto contiene CUALQUIERA
# de las palabras del mismo grupo (no solo la que escribio el vendedor).
GRUPOS_SINONIMOS = [
    ["foco", "focos", "bulbo", "bulbos", "lampara", "lamparas"],
    ["limpiaparabrisas", "pluma", "plumilla", "plumillas", "wiper", "limpiador"],
    ["canbus", "cambus", "can bus"],
    ["estrobo", "estroboscopico", "estroboscopica", "flash"],
    ["multicolor", "rgb", "colores"],
    ["calavera", "calaveras", "stop", "tail light"],
    ["plafon", "plafones", "cuarto", "cuartos"],
    ["aromatizante", "aromatizantes", "ambientador", "ambientadores"],
    ["funda", "fundas", "cubre volante"],
    ["torreta", "torretas", "barra de luces"],
]


def normalizar(s: str) -> str:
    s = str(s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s


def detectar_medida_query(q: str):
    qn = normalizar(q).upper().replace("-", "").replace(" ", "")
    m = PATRON_MEDIDA.search(qn)
    return m.group(1) if m else None


def distancia_acotada(a: str, b: str, limite: int = 2) -> int:
    """Levenshtein, pero deja de calcular si ya se sabe que pasara el limite."""
    a, b = normalizar(a), normalizar(b)
    if a == b:
        return 0
    if abs(len(a) - len(b)) > limite:
        return limite + 1
    m, n = len(a), len(b)
    fila_prev = list(range(n + 1))
    for i in range(1, m + 1):
        fila = [i] + [0] * n
        for j in range(1, n + 1):
            costo = 0 if a[i - 1] == b[j - 1] else 1
            fila[j] = min(fila_prev[j] + 1, fila[j - 1] + 1, fila_prev[j - 1] + costo)
        fila_prev = fila
    return fila_prev[n]


def cargar_productos() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    filas = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()
    productos = []
    for f in filas:
        d = dict(f)
        texto = " ".join(
            normalizar(str(d.get(c) or ""))
            for c in (
                "codigo", "descripcion", "linea_comercial", "medida", "color",
                "caracteristicas", "grupo_nombre", "tipo_nombre",
            )
        )
        d["_texto_busqueda"] = texto
        d["_desc_norm"] = normalizar(str(d.get("descripcion") or ""))
        productos.append(d)
    return productos


def _grupo_de(palabra: str):
    for grupo in GRUPOS_SINONIMOS:
        if palabra in grupo:
            return grupo
    return None


def _orden_stock_primero(p: dict):
    return ((p.get("existencia") or 0) <= 0, -(p.get("existencia") or 0))


def _buscar_por_familia(q_familia: str, productos: list[dict], limite: int) -> dict:
    """Regla 1: 3 digitos exactos -> familia (por codigo) primero, y como
    seccion aparte, productos que mencionen ese numero en la descripcion."""
    primarios = [p for p in productos if p.get("familia") == q_familia]
    primarios.sort(key=_orden_stock_primero)
    ids_primarios = {p["id_articulo"] for p in primarios}
    secundarios = [
        p for p in productos
        if p["id_articulo"] not in ids_primarios and q_familia in p["_desc_norm"]
    ]
    secundarios.sort(key=_orden_stock_primero)
    tope = max(limite, 300)  # una familia entera puede tener cientos de productos
    secciones = [{"titulo": f"Familia {q_familia}", "resultados": primarios[:tope]}]
    if secundarios:
        secciones.append({
            "titulo": f"También contienen \"{q_familia}\"",
            "resultados": secundarios[:tope],
        })
    return {"modo": "familia", "secciones": secciones}


def _buscar_por_codigo(q_codigo: str, productos: list[dict], limite: int) -> dict:
    """Regla 2: si el texto trae guion, se trata como busqueda de codigo:
    exacto primero, luego codigos que lo contengan."""
    exactos, parecidos = [], []
    for p in productos:
        codigo_norm = normalizar(p["codigo"]).replace(" ", "")
        if codigo_norm == q_codigo:
            exactos.append(p)
        elif q_codigo in codigo_norm:
            parecidos.append(p)
    exactos.sort(key=_orden_stock_primero)
    parecidos.sort(key=_orden_stock_primero)
    return {"modo": "codigo", "secciones": [{"titulo": None, "resultados": (exactos + parecidos)[:limite]}]}


def _buscar_por_texto(query: str, q: str, productos: list[dict], limite: int) -> dict:
    """Regla 3: palabra o medida -> prioriza descripcion que EMPIEZA con la
    frase, luego que la CONTIENE, y de ahi cae al ranking por sinonimos /
    medida / tolerancia a errores que ya existia."""
    medida = detectar_medida_query(query)
    palabras = [p for p in q.split() if p]

    resultados = []
    for p in productos:
        score = 0.0
        texto = p["_texto_busqueda"]
        desc = p["_desc_norm"]

        if desc.startswith(q):
            score += 500
        elif q in desc:
            score += 300

        if medida:
            if p.get("medida") and normalizar(p["medida"]) == normalizar(medida):
                # Las familias de focos de verdad van primero; un soquet o
                # base que tambien mencione esa medida sigue apareciendo,
                # pero mas abajo.
                score += 130 if p.get("familia") in FOCO_FAMILIAS else 70
            elif p.get("medida"):
                score -= 40

        for palabra in palabras:
            if medida and palabra.upper().replace("-", "") == medida:
                continue  # ya se conto arriba
            grupo = _grupo_de(palabra)
            if grupo and any(v in texto for v in grupo):
                score += 25
                continue
            if palabra in texto:
                score += 30
                continue
            tokens = texto.split()
            if any(len(t) > 2 and distancia_acotada(palabra, t, 1) <= 1 for t in tokens):
                score += 15

        if score > 0:
            p2 = dict(p)
            p2["score"] = score
            resultados.append(p2)

    resultados.sort(key=lambda r: (-r["score"], r["existencia"] <= 0))
    return {"modo": "texto", "secciones": [{"titulo": None, "resultados": resultados[:limite]}]}


def buscar(query: str, productos: list[dict], limite: int = 50) -> dict:
    q = normalizar(query)
    if not q:
        return {"modo": "vacio", "secciones": []}
    q_compacto = q.replace(" ", "")

    if PATRON_FAMILIA.match(q_compacto):
        return _buscar_por_familia(q_compacto, productos, limite)
    if "-" in q:
        return _buscar_por_codigo(q_compacto, productos, limite)
    return _buscar_por_texto(query, q, productos, limite)


def _slug(nombre: str) -> str:
    s = normalizar(nombre)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "categoria"


# Categorias dentro de cada temporada. Cada categoria agrupa una o varias
# familias (3 primeros digitos del codigo) bajo un nombre comercial, mas
# palabras clave opcionales para atrapar productos mal catalogados (codigo
# en otra familia pero descripcion que claramente pertenece aqui). Las
# temporadas que no aparecen aqui (o las familias sueltas que no quedaron en
# ninguna categoria de su temporada) usan un nombre generico "Familia XXX".
CATEGORIAS_TEMPORADA = {
    "lluvia": {
        "limpiaparabrisas": {"nombre": "Limpiaparabrisas", "familias": ["037"],
                              "palabras": ["LIMPIAPARABRISAS", "PLUMA"]},
        "botaguas": {"nombre": "Botaguas", "familias": ["026"], "palabras": ["BOTAGUA"]},
        "loderas": {"nombre": "Loderas", "familias": ["029"], "palabras": ["LODERA"]},
        "deflector-de-cofre": {"nombre": "Deflector de cofre", "familias": ["035"],
                                "palabras": ["DEFLECTOR"]},
        "chisguetero-con-luz": {"nombre": "Chisguetero con luz", "familias": ["059"],
                                 "palabras": ["CHISGUETERO"]},
        "rog-shine": {"nombre": "ROG SHINE", "familias": ["098"], "palabras": []},
        "car-cover": {"nombre": "Car Cover", "familias": ["131"], "palabras": []},
    },
    # las demas temporadas se completan despues con la misma forma:
    # "slug": {"nombre": str, "familias": [str, ...], "palabras": [str, ...]}
}


def _definiciones_categoria(clave_temporada: str) -> list[dict]:
    """Lista de categorias definidas explicitamente para una temporada, mas
    una categoria generica por cada familia suya que no quedo en ninguna."""
    temporada = TEMPORADAS.get(clave_temporada)
    if not temporada:
        return []
    mapa = CATEGORIAS_TEMPORADA.get(clave_temporada, {})
    definiciones = [
        {"slug": slug, "nombre": info["nombre"], "familias": info["familias"], "palabras": info["palabras"]}
        for slug, info in mapa.items()
    ]
    familias_ya_usadas = {f for info in mapa.values() for f in info["familias"]}
    for familia in temporada["familias"]:
        if familia not in familias_ya_usadas:
            definiciones.append({
                "slug": familia, "nombre": f"Familia {familia}", "familias": [familia], "palabras": [],
            })
    return definiciones


def _buscar_definicion_categoria(clave_temporada: str, slug: str) -> dict | None:
    for definicion in _definiciones_categoria(clave_temporada):
        if definicion["slug"] == slug:
            return definicion
    return None


def productos_de_categoria(familias: list[str], palabras: list[str], productos: list[dict]) -> list[dict]:
    familias_set = set(familias)
    por_codigo = [p for p in productos if p.get("familia") in familias_set]
    por_palabra = []
    if palabras:
        palabras_norm = [normalizar(w) for w in palabras]
        por_palabra = [
            p for p in productos
            if p.get("familia") not in familias_set
            and any(w in p["_desc_norm"] for w in palabras_norm)
        ]
    vistos = set()
    combinados = []
    for p in por_codigo + por_palabra:
        if p["id_articulo"] not in vistos:
            vistos.add(p["id_articulo"])
            combinados.append(p)
    combinados.sort(key=_orden_stock_primero)
    return combinados


def categorias_de_temporada(clave: str, productos: list[dict]) -> list[dict]:
    categorias = []
    for definicion in _definiciones_categoria(clave):
        items = productos_de_categoria(definicion["familias"], definicion["palabras"], productos)
        if not items:
            continue
        categorias.append({
            "slug": definicion["slug"],
            "nombre": definicion["nombre"],
            "total": len(items),
            "con_stock": sum(1 for p in items if (p.get("existencia") or 0) > 0),
        })
    return categorias


def alternativas(producto: dict, productos: list[dict], n: int = 3) -> list[dict]:
    familia = producto.get("familia")
    medida = producto.get("medida")
    if not familia:
        return []
    candidatos = [
        p for p in productos
        if p["id_articulo"] != producto["id_articulo"]
        and p.get("familia") == familia
        and (p.get("existencia") or 0) > 0
        and (medida is None or p.get("medida") == medida)
    ]
    if not candidatos and medida:
        # si no hay nada de la misma medida exacta, ampliar a toda la familia
        candidatos = [
            p for p in productos
            if p["id_articulo"] != producto["id_articulo"]
            and p.get("familia") == familia
            and (p.get("existencia") or 0) > 0
        ]

    def distancia_similitud(p):
        d_caras = abs((p.get("caras") or 0) - (producto.get("caras") or 0))
        d_precio = abs((p.get("precio") or 0) - (producto.get("precio") or 0))
        return (d_caras, d_precio)

    candidatos.sort(key=distancia_similitud)
    return candidatos[:n]
