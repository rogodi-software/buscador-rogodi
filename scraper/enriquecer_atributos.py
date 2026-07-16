"""
Fase 2: separa de la descripcion de cada producto sus atributos en columnas
propias (familia, medida, linea comercial, voltaje, caras, numero de LED,
color, caracteristicas especiales).

Uso:
    python enriquecer_atributos.py --muestra      # solo muestra, no escribe en la BD
    python enriquecer_atributos.py                # aplica a las 7224 filas reales
"""
import argparse
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "catalogo.db"

# --- medida -----------------------------------------------------------
# Orden: los mas largos primero (H13/H11 antes de H1/H3) para que no se
# detecte "H1" dentro de "H13".
PATRON_MEDIDA = re.compile(
    r"(?<![A-Z0-9])(9004|9005|9006|9007|H11|H13|H4|H7|H3|H1)(?![0-9])"
)


def detectar_medida(desc: str, grupo_nombre: str = None):
    # Para "FOCO MINIATURA DE LED" la medida es el codigo de base del foco
    # (3157, 7443, 7507, 0073...), que el sitio ya trae como nombre de grupo
    # y es mas confiable que tratar de leerlo del texto libre.
    if grupo_nombre and grupo_nombre.isdigit():
        return grupo_nombre
    m = PATRON_MEDIDA.search(desc)
    return m.group(1) if m else None


# --- linea comercial ----------------------------------------------------
# El nombre de la linea aparece justo despues de "COB", "CSP" o "SERIE" en
# la descripcion (es la convencion que usa Rogodi para nombrar sus lineas
# de focos). Tomamos las palabras siguientes hasta topar con la medida, un
# numero suelto (caras/watts/volt) o una palabra generica/de caracteristica.
DISPARADORES_LINEA = ["SERIE", "COB", "CSP"]

PALABRAS_NO_LINEA = {
    "FOCO", "FOCOS", "LED", "CHIP", "COB", "CSP", "HALOGENO", "H/L", "H", "L",
    "CON", "Y", "DE", "PARA", "KIT", "PIEZA", "NEOLUX", "OCN",
    "BLANCO", "AMBAR", "AZUL", "ROJO", "VERDE", "NEGRO", "NEGRA", "CROMO", "DORADO",
    "ESTROBO", "ESTROBOSCOPICA", "MULTICOLOR", "RGB", "CANBUS", "CAMBUS",
    "GEL", "LUPA", "LENTE", "AUMENTO", "CERAMICA", "BICOLOR", "FIJO", "FIJA",
    "CLEAR", "BLUE", "DARK", "OSCURO", "DRL", "APP", "MOVIL", "FUNCIONES",
    "DIRECCIONAL", "MICA", "HUMO", "DC", "AC", "FLEXIBLE", "RECORTABLE",
}


def detectar_linea(desc: str):
    mejor_idx, mejor_disp = None, None
    for disp in DISPARADORES_LINEA:
        m = re.search(rf"\b{disp}\b", desc)
        if m and (mejor_idx is None or m.start() < mejor_idx):
            mejor_idx, mejor_disp = m.start(), disp
    if mejor_idx is None:
        return None
    resto = desc[mejor_idx + len(mejor_disp):].strip()
    candidatos = []
    for token in resto.split():
        token_limpio = token.strip(",.")
        if PATRON_MEDIDA.match(token_limpio) or token_limpio in PALABRAS_NO_LINEA:
            break
        if re.match(r"^\d", token_limpio):
            break
        candidatos.append(token_limpio)
    if not candidatos:
        return "BASE" if mejor_disp in ("COB", "CSP") else None
    return " ".join(candidatos)


# --- voltaje, caras, numero de led --------------------------------------
PATRON_VOLTAJE = re.compile(r"\b(\d{1,2}[/-]\d{1,2}V|\d{1,2}V)\b")
# (?<![A-Z0-9]) evita que el "1" de "H1" o el "4" de "H4" se confunda con un
# numero suelto de caras/LED cuando le sigue justo la palabra CARAS/LED.
PATRON_CARAS = re.compile(r"(?<![A-Z0-9])(\d+)\s*CARAS?\b")
PATRON_LED = re.compile(r"(?<![A-Z0-9])(\d+)\s*LED\b")


def detectar_voltaje(desc: str):
    m = PATRON_VOLTAJE.search(desc)
    return m.group(1) if m else None


def detectar_caras(desc: str):
    m = PATRON_CARAS.search(desc)
    return int(m.group(1)) if m else None


def detectar_numero_led(desc: str):
    m = PATRON_LED.search(desc)
    return int(m.group(1)) if m else None


# --- color ---------------------------------------------------------------
COLORES = {
    "BLANCO": ["BLANCO", "BLANCA"], "AMBAR": ["AMBAR"], "AZUL": ["AZUL"],
    "ROJO": ["ROJO", "ROJA"], "VERDE": ["VERDE"], "NEGRO": ["NEGRO", "NEGRA"],
    "GRIS": ["GRIS"], "BEIGE": ["BEIGE"], "CROMO": ["CROMO"], "DORADO": ["DORADO"],
    "MULTICOLOR": ["MULTICOLOR", "RGB"], "AZUL_EN": ["BLUE"],
}
# alias: si detecta el nombre en ingles, se reporta como su equivalente
ALIAS_COLOR = {"AZUL_EN": "AZUL"}


def detectar_color(desc: str):
    encontrados = []
    for canon, variantes in COLORES.items():
        if any(re.search(rf"\b{v}\b", desc) for v in variantes):
            canon = ALIAS_COLOR.get(canon, canon)
            if canon not in encontrados:
                encontrados.append(canon)
    return ",".join(encontrados) if encontrados else None


# --- caracteristicas especiales -------------------------------------------
CARACTERISTICAS = {
    "ESTROBO": ["ESTROBO", "ESTROBOSCOPICA"],
    "CANBUS": ["CANBUS", "CAMBUS"],
    "MULTICOLOR": ["MULTICOLOR", "RGB"],
    "GEL": ["GEL"],
    "FUNCIONES": ["FUNCIONES"],
    "DIRECCIONAL": ["DIRECCIONAL"],
    "BICOLOR": ["BICOLOR"],
    "LUPA": ["LUPA"],
    "MICA HUMO": ["MICA HUMO"],
}


def detectar_caracteristicas(desc: str):
    encontradas = []
    for canon, variantes in CARACTERISTICAS.items():
        if any(re.search(rf"\b{v}\b", desc) for v in variantes):
            encontradas.append(canon)
    return ",".join(encontradas) if encontradas else None


# --- familia ---------------------------------------------------------------
def detectar_familia(codigo: str):
    m = re.match(r"^(\d{3})-", codigo)
    if m:
        return m.group(1)
    m = re.match(r"^([A-Z]+)-", codigo)
    if m:
        return m.group(1)
    return None


def enriquecer(codigo: str, desc: str, grupo_nombre: str = None) -> dict:
    desc = desc or ""
    return {
        "familia": detectar_familia(codigo),
        "medida": detectar_medida(desc, grupo_nombre),
        "linea_comercial": detectar_linea(desc),
        "voltaje": detectar_voltaje(desc),
        "caras": detectar_caras(desc),
        "numero_led": detectar_numero_led(desc),
        "color": detectar_color(desc),
        "caracteristicas": detectar_caracteristicas(desc),
    }


COLUMNAS_NUEVAS = [
    ("familia", "TEXT"), ("medida", "TEXT"), ("linea_comercial", "TEXT"),
    ("voltaje", "TEXT"), ("caras", "INTEGER"), ("numero_led", "INTEGER"),
    ("color", "TEXT"), ("caracteristicas", "TEXT"),
]


def asegurar_columnas(conn):
    existentes = {row[1] for row in conn.execute("PRAGMA table_info(productos)")}
    for nombre, tipo in COLUMNAS_NUEVAS:
        if nombre not in existentes:
            conn.execute(f"ALTER TABLE productos ADD COLUMN {nombre} {tipo}")
    conn.commit()


def mostrar_muestra():
    conn = sqlite3.connect(DB_PATH)
    plan = [
        ("FOCO LUZ PRINCIPAL", "", 5),
        ("FOCO MINIATURA DE LED", "", 3),
        ("FOCO MINIATURA DE LED", "AND (descripcion LIKE '%ESTROBO%' OR descripcion LIKE '%CAMBUS%')", 3),
        ("FOCO MINIATURA DE FILAMENTO", "", 2),
        ("PLAFONES DE LED", "", 5),
        ("FUNDA DE VOLANTE", "", 4),
        ("CALAVERAS", "", 4),
        ("AROMATIZANTES", "", 3),
        ("ACCESORIOS DE ILUMINACION IOL", "AND codigo LIKE 'IOL-LHL%'", 2),
        ("ACCESORIOS DE ILUMINACION IOL", "AND codigo LIKE 'IOL-LBLD%'", 2),
    ]
    lineas = [f"{'Tipo':<28} {'Codigo':<14} {'Fam':<5} {'Medida':<7} {'Linea':<12} {'Volt':<8} {'Caras':<6} {'#LED':<5} {'Color':<10} {'Caracteristicas':<22} Descripcion"]
    for tipo_nombre, filtro_extra, limite in plan:
        sql = (
            f"SELECT codigo, descripcion, grupo_nombre FROM productos "
            f"WHERE tipo_nombre = ? {filtro_extra} ORDER BY codigo LIMIT ?"
        )
        filas = conn.execute(sql, (tipo_nombre, limite)).fetchall()
        for codigo, desc, grupo_nombre in filas:
            a = enriquecer(codigo, desc, grupo_nombre)
            lineas.append(
                f"{tipo_nombre:<28} {codigo:<14} {str(a['familia']):<5} {str(a['medida']):<7} "
                f"{str(a['linea_comercial']):<12} {str(a['voltaje']):<8} {str(a['caras']):<6} "
                f"{str(a['numero_led']):<5} {str(a['color']):<10} {str(a['caracteristicas']):<22} {desc}"
            )
    texto = "\n".join(lineas)
    print(texto)
    with open(Path(__file__).resolve().parent.parent / "_muestra_fase2.txt", "w", encoding="utf-8") as f:
        f.write(texto)
    conn.close()


def aplicar_a_todo():
    conn = sqlite3.connect(DB_PATH)
    asegurar_columnas(conn)
    filas = conn.execute("SELECT id_articulo, codigo, descripcion, grupo_nombre FROM productos").fetchall()
    datos = []
    for id_articulo, codigo, desc, grupo_nombre in filas:
        a = enriquecer(codigo, desc, grupo_nombre)
        datos.append((
            a["familia"], a["medida"], a["linea_comercial"], a["voltaje"],
            a["caras"], a["numero_led"], a["color"], a["caracteristicas"], id_articulo,
        ))
    conn.executemany(
        """
        UPDATE productos SET
            familia=?, medida=?, linea_comercial=?, voltaje=?, caras=?,
            numero_led=?, color=?, caracteristicas=?
        WHERE id_articulo=?
        """,
        datos,
    )
    conn.commit()
    print(f"Atributos actualizados en {len(datos)} productos.")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--muestra", action="store_true", help="Solo mostrar muestra, no escribir en la BD")
    args = parser.parse_args()
    if args.muestra:
        mostrar_muestra()
    else:
        aplicar_a_todo()
