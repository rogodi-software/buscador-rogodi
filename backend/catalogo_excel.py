"""
Genera el Excel de existencias (formato .xls 97-2003) que la disenadora usa
para armar el catalogo en su app (My Business Catalogue). Solo lee datos en
vivo de catalogo.db: nunca usa el Excel maestro viejo como fuente de precio,
existencia, descripcion o unidad, porque esos datos cambian con el tiempo y
un mismo codigo puede reciclarse para un producto distinto.

Columnas del archivo original menos CODIGO ALTERNO y SAT (pedido explicito:
no se necesitan). CLASE se llena con la familia del codigo (primeros 3
digitos), que es el unico dato de clasificacion disponible en vivo. Las filas
de categoria (CATALOGO ROGODI / TIPO / GRUPO) no tienen precio ni medida —
llevan relleno de color para distinguirlas de las filas de producto.
"""
import io

import xlwt

RAIZ = "CATÁLOGO ROGODI "

ENCABEZADOS = [
    "CODIGO", "PARENT LEVEL ID", "CLASE", " DESCRIPCION ", "MEDIDA", "PRECIO",
    "JPG", "NOMBRE DE FOTOS", "TIPO", "GRUPO", "EXISTENCIA",
]

_ESTILO_ENCABEZADO = xlwt.easyxf(
    "font: bold on; pattern: pattern solid, fore_colour gray25;"
)
_ESTILO_CATEGORIA = xlwt.easyxf(
    "font: bold on; pattern: pattern solid, fore_colour light_yellow;"
)


def _fila_categoria(nombre: str, padre: str) -> list:
    return [nombre, padre, "", nombre, "", "", "", f"{nombre}.JPG", "", "", ""]


def _fila_producto(p: dict, grupo: str) -> list:
    return [
        p["codigo"], grupo, p.get("familia") or "", p["descripcion"],
        p.get("unidad") or "", p.get("precio") or 0, ".JPG", f"{p['codigo']}.JPG",
        p.get("tipo_nombre") or "", p.get("grupo_nombre") or "",
        p.get("existencia") or 0,
    ]


def _escribir_fila(hoja, fila: int, valores: list, estilo=None) -> None:
    for col, valor in enumerate(valores):
        if estilo is not None:
            hoja.write(fila, col, valor, estilo)
        else:
            hoja.write(fila, col, valor)


def generar_excel_bytes(productos: list[dict], min_existencia: float = 3) -> bytes:
    """Arma el .xls agrupado TIPO -> GRUPO -> productos, solo con productos
    cuya existencia actual (en vivo) sea mayor a min_existencia."""
    calificados = [p for p in productos if (p.get("existencia") or 0) > min_existencia]

    por_tipo: dict[str, dict[str, list[dict]]] = {}
    for p in calificados:
        tipo = p.get("tipo_nombre") or "SIN TIPO"
        grupo = p.get("grupo_nombre") or "SIN GRUPO"
        por_tipo.setdefault(tipo, {}).setdefault(grupo, []).append(p)

    wb = xlwt.Workbook(encoding="utf-8")
    hoja = wb.add_sheet("Hoja1")

    _escribir_fila(hoja, 0, ENCABEZADOS, _ESTILO_ENCABEZADO)

    fila = 1
    _escribir_fila(hoja, fila, _fila_categoria(RAIZ, ""), _ESTILO_CATEGORIA)
    fila += 1

    for tipo in sorted(por_tipo):
        _escribir_fila(hoja, fila, _fila_categoria(tipo, RAIZ), _ESTILO_CATEGORIA)
        fila += 1

        for grupo in sorted(por_tipo[tipo]):
            _escribir_fila(hoja, fila, _fila_categoria(grupo, tipo), _ESTILO_CATEGORIA)
            fila += 1

            productos_grupo = sorted(por_tipo[tipo][grupo], key=lambda p: p["codigo"])
            for p in productos_grupo:
                _escribir_fila(hoja, fila, _fila_producto(p, grupo))
                fila += 1

    salida = io.BytesIO()
    wb.save(salida)
    return salida.getvalue()
