# 📊 Guía OLAP - SugarBI

## 🎯 Descripción

El sistema OLAP (Online Analytical Processing) de SugarBI permite realizar análisis multidimensionales avanzados sobre el data mart de cosecha de caña de azúcar. Implementa las operaciones típicas de cubo OLAP: drill-down, roll-up, slice, dice y pivot.

## 🏗️ Arquitectura OLAP

### Modelo Dimensional
```
┌─────────────────┐
│   Tabla de      │
│   Hechos        │
│   (hechos_      │
│   cosecha)      │
└─────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│Dimensión│ │Dimensión│
│ Tiempo  │ │Geografía│
└─────────┘ └─────────┘
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│Dimensión│ │Dimensión│
│Producto │ │ Clima   │
└─────────┘ └─────────┘
```

### Jerarquías de Dimensiones

#### 1. Dimensión Tiempo
```
Año → Semestre → Trimestre → Mes → Fecha
```

#### 2. Dimensión Geografía
```
Región → Zona → Finca
```

#### 3. Dimensión Producto
```
Tipo de Caña → Variedad
```

## 🔧 Operaciones OLAP

### 1. Drill-Down (Perforar hacia abajo)
**Descripción**: Aumenta el nivel de detalle de los datos.

**Ejemplo**: Ver producción por año → por semestre → por mes

```json
{
    "operation": "drill_down",
    "measures": ["toneladas"],
    "dimensions": ["tiempo"],
    "dimension_levels": {"tiempo": "year"},
    "aggregation_functions": ["sum"]
}
```

### 2. Roll-Up (Enrollar hacia arriba)
**Descripción**: Disminuye el nivel de detalle, agregando datos.

**Ejemplo**: Ver producción por finca → por zona → por región

```json
{
    "operation": "roll_up",
    "measures": ["toneladas", "tch"],
    "dimensions": ["geografia"],
    "dimension_levels": {"geografia": "farm"},
    "aggregation_functions": ["sum", "avg"]
}
```

### 3. Slice (Cortar)
**Descripción**: Filtra una dimensión específica.

**Ejemplo**: Analizar solo datos del año 2025

```json
{
    "operation": "slice",
    "measures": ["toneladas", "brix"],
    "dimensions": ["tiempo", "geografia"],
    "dimension_levels": {"tiempo": "month", "geografia": "zone"},
    "filters": {"año": 2025},
    "aggregation_functions": ["sum", "avg"]
}
```

### 4. Dice (Cortar múltiple)
**Descripción**: Filtra múltiples dimensiones simultáneamente.

**Ejemplo**: Analizar datos del 2025 en la Zona Norte

```json
{
    "operation": "dice",
    "measures": ["toneladas", "tch", "brix"],
    "dimensions": ["tiempo", "geografia", "producto"],
    "dimension_levels": {"tiempo": "month", "geografia": "farm", "producto": "variety"},
    "filters": {"año": 2025, "zona": "Zona Norte"},
    "aggregation_functions": ["sum", "avg", "max"]
}
```

### 5. Pivot (Rotar)
**Descripción**: Reorganiza las dimensiones para cambiar la perspectiva.

**Ejemplo**: Comparar variedades por año

```json
{
    "operation": "pivot",
    "measures": ["toneladas"],
    "dimensions": ["tiempo", "producto"],
    "dimension_levels": {"tiempo": "year", "producto": "variety"},
    "pivot_dimension": "producto",
    "aggregation_functions": ["sum"]
}
```

### 6. Aggregate (Agregar)
**Descripción**: Operación básica de agregación.

**Ejemplo**: Suma total de toneladas por año

```json
{
    "operation": "aggregate",
    "measures": ["toneladas"],
    "dimensions": ["tiempo"],
    "dimension_levels": {"tiempo": "year"},
    "aggregation_functions": ["sum"]
}
```

## 📡 API Endpoints

### Base URL
```
http://localhost:5001/api/olap
```

### 1. Ejecutar Consulta OLAP

**POST** `/api/olap/query`

Ejecuta una consulta OLAP multidimensional.

#### Request
```http
POST /api/olap/query
Content-Type: application/json

{
    "operation": "drill_down",
    "measures": ["toneladas", "tch"],
    "dimensions": ["tiempo", "geografia"],
    "dimension_levels": {
        "tiempo": "year",
        "geografia": "zone"
    },
    "filters": {"año": 2025},
    "aggregation_functions": ["sum", "avg"],
    "sort_by": "toneladas_sum",
    "sort_order": "desc",
    "limit": 10
}
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "operation": "drill_down",
        "records": [
            {
                "tiempo_year": 2025,
                "geografia_zone": "Zona Norte",
                "toneladas_sum": 15000.5,
                "toneladas_avg": 1250.04,
                "tch_sum": 1200.3,
                "tch_avg": 100.02
            }
        ],
        "metadata": {
            "operation": "drill_down",
            "dimensions": ["tiempo", "geografia"],
            "measures": ["toneladas", "tch"],
            "dimension_levels": {
                "tiempo": "year",
                "geografia": "zone"
            },
            "aggregation_functions": ["sum", "avg"],
            "filters_applied": {"año": 2025},
            "record_count": 1,
            "columns": ["tiempo_year", "geografia_zone", "toneladas_sum", "toneladas_avg", "tch_sum", "tch_avg"]
        },
        "sql_query": "SELECT t.año as tiempo_year, z.nombre_zona as geografia_zone, SUM(h.toneladas_cana_molida) as toneladas_sum, AVG(h.toneladas_cana_molida) as toneladas_avg, SUM(h.tch) as tch_sum, AVG(h.tch) as tch_avg FROM hechos_cosecha h JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id JOIN dimfinca f ON h.id_finca = f.finca_id JOIN dimzona z ON h.codigo_zona = z.codigo_zona WHERE t.año = 2025 GROUP BY t.año, z.nombre_zona ORDER BY toneladas_sum DESC LIMIT 10",
        "execution_time": 0.045,
        "record_count": 1
    }
}
```

### 2. Obtener Dimensiones Disponibles

**GET** `/api/olap/dimensions`

Retorna las dimensiones disponibles y sus niveles.

#### Response
```json
{
    "success": true,
    "data": {
        "dimensions": ["tiempo", "geografia", "producto"],
        "dimension_levels": {
            "tiempo": ["year", "semester", "quarter", "month", "date"],
            "geografia": ["region", "zone", "farm"],
            "producto": ["variety_type", "variety"]
        },
        "hierarchies": {
            "tiempo": {
                "year": ["año"],
                "semester": ["año", "semestre"],
                "quarter": ["año", "trimestre"],
                "month": ["año", "mes"],
                "date": ["año", "mes", "fecha_completa"]
            }
        }
    }
}
```

### 3. Obtener Medidas Disponibles

**GET** `/api/olap/measures`

Retorna las medidas y funciones de agregación disponibles.

#### Response
```json
{
    "success": true,
    "data": {
        "measures": ["toneladas", "tch", "brix", "sacarosa", "area", "rendimiento"],
        "aggregation_functions": ["sum", "avg", "count", "min", "max", "std"]
    }
}
```

### 4. Obtener Ejemplos de Consultas

**GET** `/api/olap/examples`

Retorna ejemplos de consultas OLAP predefinidas.

#### Response
```json
{
    "success": true,
    "data": {
        "examples": [
            {
                "name": "Drill-down por tiempo",
                "description": "Ver producción por año, luego por semestre, luego por mes",
                "operation": "drill_down",
                "measures": ["toneladas"],
                "dimensions": ["tiempo"],
                "dimension_levels": {"tiempo": "year"},
                "aggregation_functions": ["sum"]
            }
        ]
    }
}
```

## 📊 Medidas Disponibles

| Medida | Descripción | Unidad |
|--------|-------------|---------|
| `toneladas` | Toneladas de caña molida | Toneladas |
| `tch` | Toneladas por hectárea | TCH |
| `brix` | Contenido de azúcar | % |
| `sacarosa` | Porcentaje de sacarosa | % |
| `area` | Área cosechada | Hectáreas |
| `rendimiento` | Rendimiento teórico | % |

## 🎯 Dimensiones y Niveles

### Dimensión Tiempo
- **year**: Año
- **semester**: Semestre (1, 2)
- **quarter**: Trimestre (1, 2, 3, 4)
- **month**: Mes (1-12)
- **date**: Fecha completa

### Dimensión Geografía
- **region**: Región geográfica
- **zone**: Zona dentro de la región
- **farm**: Finca específica

### Dimensión Producto
- **variety_type**: Tipo de caña
- **variety**: Variedad específica

## 🔧 Funciones de Agregación

| Función | Descripción | Uso |
|---------|-------------|-----|
| `sum` | Suma total | Para totales |
| `avg` | Promedio | Para promedios |
| `count` | Conteo | Para contar registros |
| `min` | Mínimo | Para valores mínimos |
| `max` | Máximo | Para valores máximos |
| `std` | Desviación estándar | Para variabilidad |

## 💡 Ejemplos Prácticos

### 1. Análisis de Tendencias Temporales

```json
{
    "operation": "drill_down",
    "measures": ["toneladas", "tch"],
    "dimensions": ["tiempo"],
    "dimension_levels": {"tiempo": "year"},
    "filters": {},
    "aggregation_functions": ["sum", "avg"],
    "sort_by": "tiempo_year",
    "sort_order": "asc"
}
```

### 2. Comparación Geográfica

```json
{
    "operation": "aggregate",
    "measures": ["toneladas", "brix"],
    "dimensions": ["geografia"],
    "dimension_levels": {"geografia": "zone"},
    "filters": {"año": 2025},
    "aggregation_functions": ["sum", "avg"],
    "sort_by": "toneladas_sum",
    "sort_order": "desc"
}
```

### 3. Análisis de Variedades

```json
{
    "operation": "slice",
    "measures": ["toneladas", "tch", "brix"],
    "dimensions": ["producto", "tiempo"],
    "dimension_levels": {"producto": "variety", "tiempo": "month"},
    "filters": {"año": 2025},
    "aggregation_functions": ["sum", "avg", "max"],
    "limit": 20
}
```

### 4. Análisis Multidimensional Completo

```json
{
    "operation": "dice",
    "measures": ["toneladas", "tch", "brix", "sacarosa"],
    "dimensions": ["tiempo", "geografia", "producto"],
    "dimension_levels": {
        "tiempo": "month",
        "geografia": "farm",
        "producto": "variety"
    },
    "filters": {
        "año": 2025,
        "mes": 8,
        "zona": "Zona Norte"
    },
    "aggregation_functions": ["sum", "avg", "max", "min"],
    "sort_by": "toneladas_sum",
    "sort_order": "desc",
    "limit": 50
}
```

## 🚀 Uso con Diferentes Lenguajes

### JavaScript/Fetch
```javascript
const olapQuery = {
    operation: "drill_down",
    measures: ["toneladas"],
    dimensions: ["tiempo"],
    dimension_levels: {"tiempo": "year"},
    aggregation_functions: ["sum"]
};

const response = await fetch('/api/olap/query', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(olapQuery)
});

const result = await response.json();
console.log('Resultados OLAP:', result.data.records);
```

### Python/Requests
```python
import requests

olap_query = {
    "operation": "roll_up",
    "measures": ["toneladas", "tch"],
    "dimensions": ["geografia"],
    "dimension_levels": {"geografia": "farm"},
    "aggregation_functions": ["sum", "avg"]
}

response = requests.post('http://localhost:5001/api/olap/query', json=olap_query)
if response.status_code == 200:
    data = response.json()
    print(f"Registros: {data['data']['record_count']}")
    print(f"Tiempo: {data['data']['execution_time']:.3f}s")
```

### cURL
```bash
curl -X POST http://localhost:5001/api/olap/query \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "slice",
    "measures": ["toneladas"],
    "dimensions": ["tiempo", "geografia"],
    "dimension_levels": {"tiempo": "month", "geografia": "zone"},
    "filters": {"año": 2025},
    "aggregation_functions": ["sum"]
  }'
```

## 🔍 Casos de Uso Avanzados

### 1. Análisis de Performance por Período
```json
{
    "operation": "drill_down",
    "measures": ["tch", "brix", "sacarosa"],
    "dimensions": ["tiempo"],
    "dimension_levels": {"tiempo": "quarter"},
    "filters": {"año": 2025},
    "aggregation_functions": ["avg", "max", "min"],
    "sort_by": "tch_avg",
    "sort_order": "desc"
}
```

### 2. Comparación de Zonas
```json
{
    "operation": "aggregate",
    "measures": ["toneladas", "area"],
    "dimensions": ["geografia"],
    "dimension_levels": {"geografia": "zone"},
    "filters": {"año": 2025},
    "aggregation_functions": ["sum", "avg"],
    "sort_by": "toneladas_sum",
    "sort_order": "desc"
}
```

### 3. Análisis de Variedades por Rendimiento
```json
{
    "operation": "slice",
    "measures": ["rendimiento", "tch", "brix"],
    "dimensions": ["producto"],
    "dimension_levels": {"producto": "variety"},
    "filters": {"año": 2025},
    "aggregation_functions": ["avg", "max", "min"],
    "sort_by": "rendimiento_avg",
    "sort_order": "desc",
    "limit": 10
}
```

## ⚡ Optimización y Rendimiento

### Mejores Prácticas
1. **Usar filtros**: Siempre aplicar filtros para reducir el dataset
2. **Limitar resultados**: Usar `limit` para consultas grandes
3. **Seleccionar medidas**: Solo incluir las medidas necesarias
4. **Niveles apropiados**: Elegir el nivel de granularidad correcto

### Índices Recomendados
```sql
-- Índices para optimizar consultas OLAP
CREATE INDEX idx_hechos_tiempo ON hechos_cosecha(codigo_tiempo);
CREATE INDEX idx_hechos_finca ON hechos_cosecha(id_finca);
CREATE INDEX idx_hechos_variedad ON hechos_cosecha(codigo_variedad);
CREATE INDEX idx_hechos_zona ON hechos_cosecha(codigo_zona);
CREATE INDEX idx_tiempo_año ON dimtiempo(año);
CREATE INDEX idx_tiempo_mes ON dimtiempo(mes);
```

## 🐛 Solución de Problemas

### Errores Comunes

#### 1. Error de Dimensión No Válida
```json
{
    "success": false,
    "error": "Dimensión no válida: 'dimension_invalida'"
}
```
**Solución**: Verificar dimensiones disponibles con `/api/olap/dimensions`

#### 2. Error de Nivel de Dimensión
```json
{
    "success": false,
    "error": "Nivel de dimensión no válido: 'nivel_invalido'"
}
```
**Solución**: Verificar niveles disponibles para cada dimensión

#### 3. Error de Medida No Válida
```json
{
    "success": false,
    "error": "Medida no válida: 'medida_invalida'"
}
```
**Solución**: Verificar medidas disponibles con `/api/olap/measures`

#### 4. Error de Función de Agregación
```json
{
    "success": false,
    "error": "Función de agregación no válida: 'funcion_invalida'"
}
```
**Solución**: Usar solo funciones válidas: sum, avg, count, min, max, std

### Debugging
1. **Verificar SQL generado**: Revisar el campo `sql_query` en la respuesta
2. **Probar con datos simples**: Empezar con consultas básicas
3. **Verificar filtros**: Asegurar que los filtros sean válidos
4. **Revisar logs**: Consultar logs del servidor para errores detallados

## 📈 Métricas de Rendimiento

### Tiempos Típicos de Ejecución
- **Consultas simples**: < 0.1s
- **Consultas con filtros**: 0.1-0.5s
- **Consultas complejas**: 0.5-2.0s
- **Consultas con muchos datos**: 2.0-10.0s

### Límites Recomendados
- **Límite por defecto**: 1000 registros
- **Límite máximo**: 10000 registros
- **Tiempo máximo**: 30 segundos

## 🔮 Roadmap Futuro

### Próximas Características
- [ ] **Caché de consultas**: Mejora de rendimiento
- [ ] **Consultas asíncronas**: Para consultas muy grandes
- [ ] **Exportación**: CSV, Excel, PDF
- [ ] **Visualizaciones automáticas**: Gráficos OLAP
- [ ] **Consultas guardadas**: Reutilización de consultas
- [ ] **Alertas**: Notificaciones basadas en umbrales

---

**Versión**: 1.0.0  
**Última actualización**: Septiembre 2025  
**Autor**: Equipo SugarBI

