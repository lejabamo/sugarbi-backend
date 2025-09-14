# 📡 SugarBI API Reference

## Base URL
```
http://localhost:5001/api
```

## Autenticación
Actualmente no requiere autenticación. Para producción, se recomienda implementar JWT o API keys.

## Endpoints

### 1. Procesar Consulta del Chatbot

**POST** `/api/chat`

Procesa una consulta en lenguaje natural y retorna visualizaciones, datos y análisis.

#### Request
```http
POST /api/chat
Content-Type: application/json

{
    "query": "muestra el top 10 de fincas por producción"
}
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "query": "muestra el top 10 de fincas por producción",
        "intent": {
            "type": "top_ranking",
            "metric": "toneladas",
            "dimension": "finca",
            "filters": {},
            "limit": 10
        },
        "sql": "SELECT f.nombre_finca, SUM(h.toneladas_cana_molida) as total_toneladas, AVG(h.toneladas_cana_molida) as promedio_toneladas, COUNT(*) as total_registros, f.codigo_finca, z.nombre_zona as zona\nFROM hechos_cosecha h\nJOIN dimfinca f ON h.id_finca = f.finca_id\nJOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id\nJOIN dimzona z ON h.codigo_zona = z.codigo_zona\nGROUP BY f.nombre_finca, f.codigo_finca, z.nombre_zona\nORDER BY total_toneladas DESC\nLIMIT 10",
        "visualization": {
            "type": "bar",
            "data": {
                "labels": ["Finca A", "Finca B", "Finca C"],
                "datasets": [{
                    "label": "Total Toneladas",
                    "data": [15000, 12000, 10000],
                    "backgroundColor": ["#1f77b4", "#ff7f0e", "#2ca02c"],
                    "borderColor": ["#1f77b4", "#ff7f0e", "#2ca02c"],
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": true,
                "plugins": {
                    "title": {
                        "display": true,
                        "text": "Top 10 Fincas por Producción"
                    }
                }
            }
        },
        "raw_data": [
            {
                "nombre_finca": "Finca A",
                "total_toneladas": 15000.5,
                "promedio_toneladas": 1250.04,
                "total_registros": 12,
                "codigo_finca": "F001",
                "zona": "Zona Norte"
            }
        ],
        "record_count": 10
    }
}
```

#### Response (400 Bad Request)
```json
{
    "success": false,
    "error": "Consulta vacía"
}
```

#### Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Error interno del servidor"
}
```

---

### 2. Parsear Consulta (Sin Ejecutar)

**POST** `/api/query/parse`

Solo parsea la consulta y genera SQL sin ejecutar la consulta en la base de datos.

#### Request
```http
POST /api/query/parse
Content-Type: application/json

{
    "query": "mejores variedades por TCH"
}
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "query": "mejores variedades por TCH",
        "intent": {
            "type": "top_ranking",
            "metric": "tch",
            "dimension": "variedad",
            "filters": {},
            "limit": null,
            "time_period": null
        },
        "sql": "SELECT v.nombre_variedad, SUM(h.tch) as total_tch, AVG(h.tch) as promedio_tch, COUNT(*) as total_registros, v.variedad_id, f.nombre_finca as finca_principal\nFROM hechos_cosecha h\nJOIN dimvariedad v ON h.codigo_variedad = v.variedad_id\nJOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id\nJOIN dimfinca f ON h.id_finca = f.finca_id\nGROUP BY v.nombre_variedad, v.variedad_id, f.nombre_finca\nORDER BY total_tch DESC\nLIMIT 10"
    }
}
```

---

### 3. Crear Visualización

**POST** `/api/visualization/create`

Crea una visualización personalizada a partir de datos proporcionados.

#### Request
```http
POST /api/visualization/create
Content-Type: application/json

{
    "chart_type": "bar",
    "title": "Producción por Finca",
    "x_axis": "nombre_finca",
    "y_axis": "total_toneladas",
    "data": [
        {
            "nombre_finca": "Finca A",
            "total_toneladas": 15000
        },
        {
            "nombre_finca": "Finca B",
            "total_toneladas": 12000
        }
    ],
    "colors": ["#1f77b4", "#ff7f0e"]
}
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "visualization": {
            "type": "bar",
            "data": {
                "labels": ["Finca A", "Finca B"],
                "datasets": [{
                    "label": "Total Toneladas",
                    "data": [15000, 12000],
                    "backgroundColor": ["#1f77b4", "#ff7f0e"],
                    "borderColor": ["#1f77b4", "#ff7f0e"],
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": true,
                "plugins": {
                    "title": {
                        "display": true,
                        "text": "Producción por Finca"
                    }
                }
            }
        }
    }
}
```

---

### 4. Estadísticas del Sistema

**GET** `/api/estadisticas`

Obtiene estadísticas generales del data mart.

#### Request
```http
GET /api/estadisticas
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "total_hechos_cosecha": 1250,
        "total_dimfinca": 45,
        "total_dimvariedad": 12,
        "total_dimzona": 8,
        "total_dimtiempo": 120,
        "total_toneladas": 1250000.5,
        "promedio_tch": 85.2,
        "promedio_brix": 18.5,
        "promedio_sacarosa": 15.8,
        "año_inicio": 2014,
        "año_fin": 2025
    }
}
```

---

### 5. Ejemplos de Consultas

**GET** `/api/examples`

Retorna una lista de ejemplos de consultas que se pueden hacer al chatbot.

#### Request
```http
GET /api/examples
```

#### Response (200 OK)
```json
{
    "success": true,
    "data": {
        "examples": [
            "muestra la cantidad en toneladas de caña producida del top 10 de las fincas en el 2025",
            "¿cuáles son las 5 mejores variedades por TCH?",
            "muestra la producción por zona en 2024",
            "¿cuál es el promedio de brix por finca?",
            "muestra la tendencia de producción por mes en 2025",
            "¿cuáles son las fincas con mayor rendimiento?",
            "muestra la distribución de producción por variedad",
            "¿cuál es la producción total por año?"
        ]
    }
}
```

---

## Tipos de Datos

### QueryIntent
```typescript
interface QueryIntent {
    type: "top_ranking" | "statistics" | "comparison" | "trend" | "basic";
    metric: "toneladas" | "tch" | "brix" | "sacarosa" | "area" | "rendimiento";
    dimension: "finca" | "variedad" | "zona" | "tiempo";
    filters: Record<string, any>;
    limit: number | null;
    time_period: string | null;
}
```

### ChartConfig
```typescript
interface ChartConfig {
    chart_type: "bar" | "line" | "pie" | "scatter" | "area" | "table";
    title: string;
    x_axis: string;
    y_axis: string;
    data: Array<Record<string, any>>;
    colors?: string[];
    width?: number;
    height?: number;
    show_legend?: boolean;
    show_grid?: boolean;
}
```

## Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| 200 | OK - Solicitud exitosa |
| 400 | Bad Request - Error en la solicitud |
| 404 | Not Found - Recurso no encontrado |
| 500 | Internal Server Error - Error del servidor |

## Ejemplos de Uso

### JavaScript/Fetch
```javascript
// Consulta del chatbot
const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        query: 'muestra el top 5 de fincas por producción'
    })
});

const result = await response.json();
if (result.success) {
    console.log('Visualización:', result.data.visualization);
    console.log('Datos:', result.data.raw_data);
}
```

### Python/Requests
```python
import requests

# Consulta del chatbot
response = requests.post('http://localhost:5001/api/chat', 
    json={'query': 'mejores variedades por TCH'})

if response.status_code == 200:
    data = response.json()
    if data['success']:
        print('SQL generado:', data['data']['sql'])
        print('Datos:', data['data']['raw_data'])
```

### cURL
```bash
# Consulta del chatbot
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "muestra la producción por zona en 2025"}'

# Estadísticas del sistema
curl http://localhost:5001/api/estadisticas

# Ejemplos de consultas
curl http://localhost:5001/api/examples
```

## Limitaciones

- **Tamaño de consulta**: Máximo 1000 caracteres
- **Límite de resultados**: Máximo 1000 registros por consulta
- **Tiempo de respuesta**: Máximo 30 segundos por consulta
- **Concurrencia**: Máximo 10 consultas simultáneas

## Rate Limiting

Actualmente no hay límites de rate. Para producción se recomienda implementar:
- 100 requests por minuto por IP
- 1000 requests por hora por IP

## Errores Comunes

### 1. Consulta Vacía
```json
{
    "success": false,
    "error": "Consulta vacía"
}
```
**Solución**: Proporcionar una consulta válida.

### 2. Error de Codificación
```json
{
    "success": false,
    "error": "Error de codificación: 'utf-8' codec can't decode byte"
}
```
**Solución**: Asegurar que la consulta use caracteres UTF-8 válidos.

### 3. Sin Datos
```json
{
    "success": false,
    "error": "No se encontraron datos para la consulta"
}
```
**Solución**: Verificar que existan datos para los criterios especificados.

### 4. Error de Base de Datos
```json
{
    "success": false,
    "error": "Error de conexión a la base de datos"
}
```
**Solución**: Verificar la configuración de la base de datos.

## Soporte

Para soporte técnico o reportar bugs:
- **Email**: api-support@sugarbi.com
- **Issues**: [GitHub Issues](https://github.com/tu-usuario/SugarBI/issues)
- **Documentación**: [Documentación Técnica](DOCUMENTACION_TECNICA.md)

