"""Ejecuta todo el flujo: limpieza -> modelo de datos -> reporte en Excel."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import limpieza  # noqa: E402
import modelo_datos  # noqa: E402
import reporte_excel  # noqa: E402


def main() -> None:
    inicio = time.perf_counter()

    registro = limpieza.ejecutar()
    print(f"1. Limpieza: {registro['filas_originales']} filas -> {registro['filas_finales']} "
          f"({registro['duplicados_eliminados']} duplicados eliminados)")

    tablas = modelo_datos.ejecutar()
    print("2. Modelo:   " + ", ".join(f"{n} ({len(t)})" for n, t in tablas.items()))

    ruta, segundos = reporte_excel.generar()
    print(f"3. Reporte:  {ruta.name} en {segundos:.2f} s")

    print(f"Total: {time.perf_counter() - inicio:.2f} s")


if __name__ == "__main__":
    main()
