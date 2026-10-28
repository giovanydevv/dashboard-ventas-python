# Guía para armar el dashboard en Power BI Desktop

Tiempo estimado: 1 a 2 horas. Antes, ejecuta `python main.py` para generar los CSV de `data/model/`.

## 1. Importar los datos

1. **Inicio > Obtener datos > Texto/CSV** e importa los 6 archivos de `data/model/`:
   `fact_ventas`, `dim_fecha`, `dim_producto`, `dim_cliente`, `dim_geografia`, `dim_region`.
2. En cada uno, pulsa **Transformar datos** y revisa los tipos:
   - `fecha`, `fecha_pedido`, `fecha_envio` → Fecha
   - `codigo_postal` → Texto (para no perder el cero inicial)
   - `ventas`, `ganancia`, `costo`, `descuento` → Número decimal
3. **Cerrar y aplicar**.

## 2. Modelo de datos (vista Modelo)

Modelo estrella: una tabla de hechos al centro y las dimensiones alrededor. Todas las relaciones son
**de varios a uno (*:1)** con filtro en **una sola dirección**, desde la dimensión hacia la tabla de hechos.

| Desde (varios) | Hacia (uno) |
|---|---|
| `fact_ventas[fecha_pedido]` | `dim_fecha[fecha]` |
| `fact_ventas[clave_producto]` | `dim_producto[clave_producto]` |
| `fact_ventas[id_cliente]` | `dim_cliente[id_cliente]` |
| `fact_ventas[clave_geografia]` | `dim_geografia[clave_geografia]` |
| `dim_geografia[region]` | `dim_region[region]` |

```
            dim_fecha        dim_producto
                 \              /
  dim_cliente -- fact_ventas -- dim_geografia -- dim_region
```

Después:
- Marca `dim_fecha` como tabla de fechas (columna `fecha`).
- En `dim_fecha[mes]`, usa **Ordenar por columna** = `mes_num`.
- Oculta en la vista de informe las claves (`clave_producto`, `clave_geografia`, `id_cliente` en la tabla de hechos).

## 3. Medidas

Copia las medidas de [medidas_dax.md](medidas_dax.md).

## 4. Páginas del dashboard

**Página 1: Resumen**
- 6 tarjetas: Ventas Totales, Ganancia Total, Margen %, Pedidos, Ticket Promedio y Tasa Devolucion %.
- Gráfico de líneas: Ventas Totales y Ventas Año Anterior por `dim_fecha[anio_mes]`.
- Segmentadores: `dim_fecha[anio]`, `dim_geografia[region]` y `dim_cliente[segmento]`.

**Página 2: Región**
- Mapa coroplético o de burbujas por `dim_geografia[estado]` con Ventas Totales.
- Barras: Ventas Totales y Margen % por `dim_geografia[region]`.
- Tabla: región, `dim_region[responsable]`, Ventas, Ganancia y Margen %.

**Página 3: Categoría y productos**
- Barras apiladas: Ventas por `categoria` y `subcategoria`.
- Barras horizontales: Top 10 productos (filtro N superior).
- Dispersión: Ventas vs Margen % por subcategoría. Así se ven las subcategorías que venden mucho pero pierden dinero, como Tables.

**Página 4: Tendencia**
- Columnas: Ventas por `anio` con Crecimiento Anual % como línea (gráfico combinado).
- Línea: Ventas Acumuladas YTD por mes.

## 5. Diseño

- Usa un tema con un color principal (por ejemplo, verde `#1E7F5C`, igual que tu portafolio) y fondos claros.
- Pon un título y la fuente de los datos en cada página.
- Formato condicional en Margen %: rojo si es menor a 0.

## 6. Exportar para el portafolio

- **Archivo > Guardar como** → `powerbi/dashboard_ventas.pbix`
- **Archivo > Exportar > PDF** → `powerbi/dashboard_ventas.pdf`
- Toma capturas de cada página y guárdalas en `docs/img/` (`resumen.png`, `region.png`, `productos.png`).
  El README ya apunta a esas rutas.
