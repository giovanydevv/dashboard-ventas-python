"""Construye un modelo estrella a partir de los pedidos limpios.

Salida en data/model/, lista para importar en Power BI:
  fact_ventas  -> una fila por linea de pedido
  dim_fecha, dim_producto, dim_cliente, dim_geografia, dim_region
"""
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROCESADOS = RAIZ / "data" / "processed"
MODELO = RAIZ / "data" / "model"

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def cargar() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pedidos = pd.read_csv(
        PROCESADOS / "pedidos_limpios.csv",
        parse_dates=["fecha_pedido", "fecha_envio"],
        dtype={"codigo_postal": str},
    )
    responsables = pd.read_csv(PROCESADOS / "responsables.csv")
    devoluciones = pd.read_csv(PROCESADOS / "devoluciones.csv")
    return pedidos, responsables, devoluciones


def dim_fecha(inicio: pd.Timestamp, fin: pd.Timestamp) -> pd.DataFrame:
    """Calendario continuo de anios completos (requisito de inteligencia de tiempo en DAX)."""
    fechas = pd.date_range(f"{inicio.year}-01-01", f"{fin.year}-12-31", freq="D")
    return pd.DataFrame({
        "fecha": fechas,
        "anio": fechas.year,
        "trimestre": "T" + fechas.quarter.astype(str),
        "mes_num": fechas.month,
        "mes": [MESES[m - 1] for m in fechas.month],
        "anio_mes": fechas.strftime("%Y-%m"),
        "dia_semana": fechas.dayofweek + 1,
    })


def construir(pedidos: pd.DataFrame, responsables: pd.DataFrame,
              devoluciones: pd.DataFrame) -> dict[str, pd.DataFrame]:
    # Producto: el id original no es unico (hay ids con varios nombres),
    # asi que se usa una clave sustituta por combinacion id + nombre.
    productos = (
        pedidos[["id_producto", "producto", "categoria", "subcategoria"]]
        .drop_duplicates(["id_producto", "producto"])
        .sort_values(["id_producto", "producto"])
        .reset_index(drop=True)
    )
    productos.insert(0, "clave_producto", productos.index + 1)

    geografia = (
        pedidos[["pais", "region", "estado", "ciudad", "codigo_postal"]]
        .drop_duplicates()
        .sort_values(["region", "estado", "ciudad", "codigo_postal"])
        .reset_index(drop=True)
    )
    geografia.insert(0, "clave_geografia", geografia.index + 1)

    clientes = (
        pedidos[["id_cliente", "cliente", "segmento"]]
        .drop_duplicates("id_cliente")
        .sort_values("id_cliente")
        .reset_index(drop=True)
    )

    region = responsables.sort_values("region").reset_index(drop=True)

    devueltos = set(devoluciones["id_pedido"])
    fact = (
        pedidos
        .merge(productos[["clave_producto", "id_producto", "producto"]], on=["id_producto", "producto"])
        .merge(geografia, on=["pais", "region", "estado", "ciudad", "codigo_postal"])
        .assign(devuelto=lambda d: d["id_pedido"].isin(devueltos).astype(int))
    )
    fact = fact[[
        "id_fila", "id_pedido", "fecha_pedido", "fecha_envio", "dias_envio", "modo_envio",
        "id_cliente", "clave_producto", "clave_geografia", "ventas", "cantidad",
        "descuento", "ganancia", "costo", "devuelto",
    ]].sort_values("id_fila").reset_index(drop=True)

    if len(fact) != len(pedidos):
        raise ValueError("Se perdieron filas al unir con las dimensiones")

    return {
        "fact_ventas": fact,
        "dim_fecha": dim_fecha(pedidos["fecha_pedido"].min(), pedidos["fecha_envio"].max()),
        "dim_producto": productos,
        "dim_cliente": clientes,
        "dim_geografia": geografia,
        "dim_region": region,
    }


def ejecutar(destino: Path = MODELO) -> dict[str, pd.DataFrame]:
    tablas = construir(*cargar())
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in tablas.items():
        tabla.to_csv(destino / f"{nombre}.csv", index=False, date_format="%Y-%m-%d")
    return tablas


if __name__ == "__main__":
    for nombre, tabla in ejecutar().items():
        print(f"{nombre:15} {len(tabla):>6} filas")
