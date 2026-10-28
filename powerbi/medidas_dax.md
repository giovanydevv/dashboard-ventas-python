# Medidas DAX

Crea una tabla vacía llamada `_Medidas` (Inicio > Especificar datos > Cargar) y agrega cada medida con **Nueva medida**.
Los nombres de tablas y columnas coinciden con los CSV de `data/model/`.

## Indicadores base

```dax
Ventas Totales = SUM ( fact_ventas[ventas] )
```

```dax
Ganancia Total = SUM ( fact_ventas[ganancia] )
```

```dax
Margen % = DIVIDE ( [Ganancia Total], [Ventas Totales] )
```

```dax
Pedidos = DISTINCTCOUNT ( fact_ventas[id_pedido] )
```

```dax
Clientes = DISTINCTCOUNT ( fact_ventas[id_cliente] )
```

```dax
Ticket Promedio = DIVIDE ( [Ventas Totales], [Pedidos] )
```

```dax
Unidades Vendidas = SUM ( fact_ventas[cantidad] )
```

```dax
Dias Promedio Envio = AVERAGE ( fact_ventas[dias_envio] )
```

```dax
Tasa Devolucion % =
DIVIDE (
    CALCULATE ( [Pedidos], fact_ventas[devuelto] = 1 ),
    [Pedidos]
)
```

## Inteligencia de tiempo

Requieren marcar `dim_fecha` como tabla de fechas (Herramientas de tabla > Marcar como tabla de fechas > columna `fecha`).

```dax
Ventas Año Anterior =
CALCULATE ( [Ventas Totales], SAMEPERIODLASTYEAR ( dim_fecha[fecha] ) )
```

```dax
Crecimiento Anual % =
DIVIDE ( [Ventas Totales] - [Ventas Año Anterior], [Ventas Año Anterior] )
```

```dax
Ventas Acumuladas YTD =
TOTALYTD ( [Ventas Totales], dim_fecha[fecha] )
```

## Ranking de productos

```dax
Ranking Producto =
IF (
    HASONEVALUE ( dim_producto[producto] ),
    RANKX ( ALL ( dim_producto[producto] ), [Ventas Totales], , DESC, DENSE )
)
```

Para el visual "Top 10 productos": arrastra `dim_producto[producto]` y `[Ventas Totales]`, y en el panel de filtros
elige **Filtrado de N superior** = 10 por `[Ventas Totales]`.

## Formato sugerido

| Medida | Formato |
|---|---|
| Ventas Totales, Ganancia Total, Ventas Año Anterior, Ventas Acumuladas YTD | Moneda, 0 decimales |
| Ticket Promedio | Moneda, 2 decimales |
| Margen %, Tasa Devolucion %, Crecimiento Anual % | Porcentaje, 1 decimal |
| Pedidos, Clientes, Unidades Vendidas | Número entero |
| Dias Promedio Envio | Decimal, 1 decimal |
