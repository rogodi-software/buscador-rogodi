"""
Extrae el catalogo publico de ROGODI (http://producto.rogodi.mx) y lo guarda
en una base de datos SQLite local.

Navega 3 niveles: tipo de articulo -> grupo/marca -> productos.

Uso:
    python extraer_catalogo.py --tipo 1614      # solo un tipo (prueba)
    python extraer_catalogo.py                  # catalogo completo
"""
import argparse
import re
import sqlite3
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://producto.rogodi.mx"
PAUSA_SEGUNDOS = 0.4
DB_PATH = Path(__file__).resolve().parent.parent / "catalogo.db"

sesion = requests.Session()
sesion.headers.update({"User-Agent": "ROGODI-buscador-interno/1.0"})


def obtener_html(url: str) -> str:
    resp = sesion.get(url, timeout=20)
    resp.raise_for_status()
    resp.encoding = "iso-8859-1"
    time.sleep(PAUSA_SEGUNDOS)
    return resp.text


def listar_tipos() -> list[tuple[int, str]]:
    html = obtener_html(f"{BASE_URL}/pi_busqueda.jsp")
    pares = re.findall(r'id_articulotipo=(\d+)">([^<]*)</a>', html)
    return [(int(idt), nombre.strip()) for idt, nombre in pares if nombre.strip()]


def listar_grupos(id_tipo: int) -> list[tuple[int, str]]:
    html = obtener_html(f"{BASE_URL}/pi_busqueda.jsp?id_articulotipo={id_tipo}")
    pares = re.findall(r'id_articulogrupo=(\d+)">([^<]*)</a>', html)
    return [(int(idg), nombre.strip()) for idg, nombre in pares if nombre.strip()]


def parsear_precio(texto: str) -> float:
    limpio = texto.replace("$", "").replace(",", "").strip()
    try:
        return float(limpio)
    except ValueError:
        return 0.0


def parsear_existencia(texto: str) -> float:
    texto = texto.strip()
    if "No Disponible" in texto or not texto:
        return 0.0
    try:
        return float(texto)
    except ValueError:
        return 0.0


def listar_productos(id_tipo: int, id_grupo: int) -> list[dict]:
    html = obtener_html(
        f"{BASE_URL}/pi_resultados.jsp?id_articulotipo={id_tipo}&id_articulogrupo={id_grupo}"
    )
    soup = BeautifulSoup(html, "html.parser")
    productos = []
    for fila in soup.select("tr.tablegridcellb, tr.tablegridcella"):
        celdas = fila.find_all("td")
        if len(celdas) < 6:
            continue
        codigo = celdas[0].get_text(strip=True)
        if not codigo:
            continue
        link = celdas[1].find("a") or celdas[2].find("a")
        id_articulo = None
        if link and link.get("href"):
            m = re.search(r"id_articulo=(\d+)", link["href"])
            if m:
                id_articulo = int(m.group(1))
        img = celdas[1].find("img")
        foto_url = img["src"].strip() if img and img.get("src") else None
        descripcion = celdas[2].get_text(strip=True)
        unidad = celdas[3].get_text(strip=True)
        precio = parsear_precio(celdas[4].get_text(strip=True))
        existencia = parsear_existencia(celdas[5].get_text(strip=True))
        if id_articulo is None:
            continue
        productos.append(
            {
                "id_articulo": id_articulo,
                "codigo": codigo,
                "descripcion": descripcion,
                "unidad": unidad,
                "precio": precio,
                "existencia": existencia,
                "foto_url": foto_url,
            }
        )
    return productos


def preparar_base(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS productos (
            id_articulo INTEGER PRIMARY KEY,
            codigo TEXT NOT NULL,
            descripcion TEXT,
            unidad TEXT,
            precio REAL,
            existencia REAL,
            foto_url TEXT,
            id_articulotipo INTEGER,
            tipo_nombre TEXT,
            id_articulogrupo INTEGER,
            grupo_nombre TEXT,
            fecha_extraccion TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_productos_codigo ON productos(codigo)")
    conn.commit()


def guardar_productos(conn: sqlite3.Connection, productos: list[dict], id_tipo, tipo_nombre, id_grupo, grupo_nombre):
    ahora = time.strftime("%Y-%m-%d %H:%M:%S")
    conn.executemany(
        """
        INSERT INTO productos (
            id_articulo, codigo, descripcion, unidad, precio, existencia, foto_url,
            id_articulotipo, tipo_nombre, id_articulogrupo, grupo_nombre, fecha_extraccion
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id_articulo) DO UPDATE SET
            codigo=excluded.codigo, descripcion=excluded.descripcion, unidad=excluded.unidad,
            precio=excluded.precio, existencia=excluded.existencia, foto_url=excluded.foto_url,
            id_articulotipo=excluded.id_articulotipo, tipo_nombre=excluded.tipo_nombre,
            id_articulogrupo=excluded.id_articulogrupo, grupo_nombre=excluded.grupo_nombre,
            fecha_extraccion=excluded.fecha_extraccion
        """,
        [
            (
                p["id_articulo"], p["codigo"], p["descripcion"], p["unidad"], p["precio"],
                p["existencia"], p["foto_url"], id_tipo, tipo_nombre, id_grupo, grupo_nombre, ahora,
            )
            for p in productos
        ],
    )
    conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tipo", type=int, default=None, help="Limitar a un solo id_articulotipo (prueba)")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    preparar_base(conn)

    print("Obteniendo lista de tipos de articulo...")
    tipos = listar_tipos()
    if args.tipo is not None:
        tipos = [(idt, nombre) for idt, nombre in tipos if idt == args.tipo]
        if not tipos:
            print(f"No encontre el id_articulotipo={args.tipo} en la lista de tipos.")
            return
    print(f"{len(tipos)} tipo(s) a procesar.")

    total_productos = 0
    for id_tipo, tipo_nombre in tipos:
        print(f"\n[TIPO {id_tipo}] {tipo_nombre}")
        grupos = listar_grupos(id_tipo)
        if not grupos:
            print("  (sin grupos listados, se omite)")
            continue
        for id_grupo, grupo_nombre in grupos:
            productos = listar_productos(id_tipo, id_grupo)
            guardar_productos(conn, productos, id_tipo, tipo_nombre, id_grupo, grupo_nombre)
            total_productos += len(productos)
            print(f"  grupo {id_grupo} ({grupo_nombre}): {len(productos)} productos")

    print(f"\nListo. Productos guardados/actualizados en esta corrida: {total_productos}")
    print(f"Base de datos: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
