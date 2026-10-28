"""Limpieza del dataset Sample Superstore.

El CSV original trae tres tablas pegadas una debajo de otra (pedidos,
responsables por region y devoluciones). Este modulo las separa, corrige
formatos, elimina duplicados, trata nulos y deja un registro de cada cambio.
"""
import csv
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw" / "superstore.csv"
PROCESADOS = RAIZ / "data" / "processed"

COLUMNAS_PEDIDOS = {
    "Row ID": "id_fila",
    "Order ID": "id_pedido",
    "Order Date": "fecha_pedido",
    "Ship Date": "fecha_envio",
    "Ship Mode": "modo_envio",
    "Customer ID": "id_cliente",
    "Customer Name": "cliente",
    "Segment": "segmento",
    "Country": "pais",
    "City": "ciudad",
    "State": "estado",
    "Postal Code": "codigo_postal",
    "Region": "region",
    "Product ID": "id_producto",
    "Category": "categoria",
    "Sub-Category": "subcategoria",
    "Product Name": "producto",
    "Sales": "ventas",
    "Quantity": "cantidad",
    "Discount": "descuento",
    "Profit": "ganancia",
}
COLUMNAS_TEXTO = [
    "id_pedido", "modo_envio", "id_cliente", "cliente", "segmento", "pais",
    "ciudad", "estado", "region", "id_producto", "categoria", "subcategoria",
    "producto",
]
COLUMNAS_NUMERICAS = ["ventas", "cantidad", "descuento", "ganancia"]
# Codigos postales conocidos para ciudades que vienen sin codigo en el dataset
CP_REFERENCIA = {("Burlington", "Vermont"): "05401"}


def separar_secciones(ruta: Path) -> dict[str, pd.DataFrame]:
    """Divide el CSV en tablas: cada cambio de cabecera inicia una seccion nueva."""
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.reader(f))

    cabeceras_conocidas = {
        ("Person", "Region"): "responsables",
        ("Returned", "Order ID"): "devoluciones",
    }
    secciones, nombre, cabecera, datos = {}, "pedidos", filas[0], []
    for fila in filas[1:]:
        clave = tuple(c.strip() for c in fila[:2])
        if len(fila) == 2 and clave in cabeceras_conocidas:
            secciones[nombre] = pd.DataFrame(datos, columns=cabecera)
            nombre, cabecera, datos = cabeceras_conocidas[clave], list(clave), []
        elif any(c.strip() for c in fila):
            datos.append(fila[: len(cabecera)])
    secciones[nombre] = pd.DataFrame(datos, columns=cabecera)
    return secciones


def limpiar_texto(serie: pd.Series) -> pd.Series:
    """Quita espacios sobrantes y convierte cadenas vacias en nulos."""
    serie = serie.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    return serie.replace("", pd.NA)


def limpiar_pedidos(df: pd.DataFrame, registro: dict) -> pd.DataFrame:
    df = df.rename(columns=COLUMNAS_PEDIDOS).copy()
    registro["filas_originales"] = len(df)

    for col in COLUMNAS_TEXTO:
        df[col] = limpiar_texto(df[col])

    # Formatos: fechas M/D/YYYY en texto -> fecha; numeros en texto -> float
    for col in ["fecha_pedido", "fecha_envio"]:
        df[col] = pd.to_datetime(limpiar_texto(df[col]), format="%m/%d/%Y", errors="coerce")
    for col in COLUMNAS_NUMERICAS:
        df[col] = pd.to_numeric(limpiar_texto(df[col]), errors="coerce")
    df["id_fila"] = pd.to_numeric(df["id_fila"], errors="coerce").astype("Int64")

    # Codigo postal: se lee como "10024.0" o "5401"; se normaliza a 5 digitos
    cp = limpiar_texto(df["codigo_postal"]).str.replace(r"\.0$", "", regex=True)
    df["codigo_postal"] = cp.str.zfill(5)
    registro["formatos_corregidos"] = {
        "fechas_texto_a_fecha": int(df[["fecha_pedido", "fecha_envio"]].notna().all(axis=1).sum()),
        "codigos_postales_rellenados_con_cero": int((cp.str.len() < 5).sum()),
    }

    # Nulos
    nulos = df.isna().sum()
    registro["nulos_por_columna"] = {c: int(n) for c, n in nulos.items() if n > 0}
    sin_cp = df["codigo_postal"].isna()
    if sin_cp.any():
        # Primero el codigo de referencia; si no hay, el mas frecuente de la misma ciudad
        moda = (
            df[~sin_cp].groupby(["ciudad", "estado"])["codigo_postal"]
            .agg(lambda s: s.mode().iat[0])
            .to_dict()
        )
        moda.update(CP_REFERENCIA)
        claves = list(zip(df.loc[sin_cp, "ciudad"], df.loc[sin_cp, "estado"]))
        df.loc[sin_cp, "codigo_postal"] = [moda.get(k, "SIN_CP") for k in claves]
        registro["codigos_postales_imputados"] = {
            "filas": int(sin_cp.sum()),
            "ciudades": sorted({f"{c}, {e}" for c, e in claves}),
            "valor_usado": sorted(set(df.loc[sin_cp, "codigo_postal"])),
        }
    criticas = ["id_pedido", "fecha_pedido", "id_producto", "ventas", "cantidad", "ganancia"]
    incompletas = df[criticas].isna().any(axis=1)
    registro["filas_sin_datos_criticos_eliminadas"] = int(incompletas.sum())
    df = df[~incompletas]

    # Duplicados: misma fila salvo el id_fila (que es un correlativo)
    columnas_negocio = [c for c in df.columns if c != "id_fila"]
    duplicadas = df.duplicated(subset=columnas_negocio, keep="first")
    registro["duplicados_eliminados"] = int(duplicadas.sum())
    df = df[~duplicadas]

    # Reglas de negocio
    invalidas = (
        (df["fecha_envio"] < df["fecha_pedido"])
        | (df["cantidad"] <= 0)
        | (df["ventas"] <= 0)
        | ~df["descuento"].between(0, 1)
    )
    registro["filas_invalidas_eliminadas"] = int(invalidas.sum())
    df = df[~invalidas]

    # Un mismo id_producto aparece con nombres distintos en el dataset original
    nombres = df.groupby("id_producto")["producto"].nunique()
    registro["ids_producto_con_varios_nombres"] = int((nombres > 1).sum())

    df = df.assign(
        costo=(df["ventas"] - df["ganancia"]).round(4),
        dias_envio=(df["fecha_envio"] - df["fecha_pedido"]).dt.days,
    )
    registro["filas_finales"] = len(df)
    return df.reset_index(drop=True)


def limpiar_responsables(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={"Person": "responsable", "Region": "region"})
    return df.apply(limpiar_texto).dropna().drop_duplicates("region")


def limpiar_devoluciones(df: pd.DataFrame, registro: dict) -> pd.DataFrame:
    df = df.rename(columns={"Returned": "devuelto", "Order ID": "id_pedido"}).apply(limpiar_texto)
    registro["devoluciones_filas_originales"] = len(df)
    df = df[df["devuelto"].str.lower() == "yes"].drop_duplicates("id_pedido")
    registro["devoluciones_pedidos_unicos"] = len(df)
    return df[["id_pedido"]].reset_index(drop=True)


def ejecutar(ruta_raw: Path = RAW, destino: Path = PROCESADOS) -> dict:
    secciones = separar_secciones(ruta_raw)
    registro = {"fuente": ruta_raw.name, "tablas_encontradas": list(secciones)}

    pedidos = limpiar_pedidos(secciones["pedidos"], registro)
    responsables = limpiar_responsables(secciones["responsables"])
    devoluciones = limpiar_devoluciones(secciones["devoluciones"], registro)

    destino.mkdir(parents=True, exist_ok=True)
    pedidos.to_csv(destino / "pedidos_limpios.csv", index=False, date_format="%Y-%m-%d")
    responsables.to_csv(destino / "responsables.csv", index=False)
    devoluciones.to_csv(destino / "devoluciones.csv", index=False)
    with open(destino / "registro_limpieza.json", "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)
    return registro


if __name__ == "__main__":
    print(json.dumps(ejecutar(), ensure_ascii=False, indent=2))
